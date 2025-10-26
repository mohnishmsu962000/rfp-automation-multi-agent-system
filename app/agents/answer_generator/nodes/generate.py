from app.services.llm_factory import LLMFactory
from app.agents.answer_generator.state import AnswerGeneratorState
from app.prompts.answer_generator import GENERATE_ANSWER_PROMPT, SIMPLE_ATTRIBUTE_ANSWER, SYSTEM_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
import logging
import tiktoken
import re

logger = logging.getLogger(__name__)

def generate_answer_node(state: AnswerGeneratorState) -> AnswerGeneratorState:
    attribute_results = state.get("attribute_results", [])
    rag_results = state.get("rag_results", [])
    question = state["question"]
    
    if attribute_results and attribute_results[0]["similarity"] > 0.75:
        return _generate_from_attribute(state, attribute_results)
    
    if rag_results and rag_results[0].get("rerank_score", 0) >= 0.05:
        return _generate_from_rag(state, rag_results)
    
    if attribute_results and attribute_results[0]["similarity"] > 0.5:
        return _generate_from_attribute(state, attribute_results)
    
    state["answer"] = "Based on the available information in our knowledge base, we do not have sufficient details to answer this question comprehensively. Please provide additional context or documentation."
    state["trust_score"] = 0.0
    state["source_type"] = "none"
    state["sources"] = []
    return state


def _generate_from_attribute(state: AnswerGeneratorState, attribute_results: list) -> AnswerGeneratorState:
    llm = LLMFactory.get_llm("claude-haiku-4")
    top_attr = attribute_results[0]
    
    prompt = SIMPLE_ATTRIBUTE_ANSWER.format(
        question=state["question"],
        key=top_attr["key"],
        value=top_attr["value"]
    )
    
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    answer = response.content
    
    trust_score = _calculate_trust_from_metrics(
        answer=answer,
        question=state["question"],
        primary_score=top_attr["similarity"],
        source_type="attribute",
        num_sources=len(attribute_results)
    )
    
    state["answer"] = answer
    state["trust_score"] = trust_score
    state["source_type"] = "attribute"
    state["sources"] = [{
        "type": "attribute",
        "key": top_attr["key"],
        "value": top_attr["value"],
        "similarity": top_attr["similarity"]
    }]
    
    logger.info(f"Attribute answer - trust: {trust_score:.1f}%")
    return state


def _generate_from_rag(state: AnswerGeneratorState, rag_results: list) -> AnswerGeneratorState:
    llm = LLMFactory.get_llm("claude-sonnet")
    
    deduplicated = _deduplicate_chunks(rag_results)
    packed_context = _pack_context_smart(deduplicated, max_tokens=5000)
    
    context = "\n\n".join([
        f"[Source {i+1}]\n{c['text']}" 
        for i, c in enumerate(packed_context)
    ])
    
    prompt = GENERATE_ANSWER_PROMPT.format(
        context=context,
        question=state["question"]
    )
    
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    answer = response.content
    
    trust_score = _calculate_trust_from_metrics(
        answer=answer,
        question=state["question"],
        primary_score=packed_context[0].get("rerank_score", 0),
        source_type="rag",
        num_sources=len(packed_context),
        avg_score=sum(c.get("rerank_score", 0) for c in packed_context[:3]) / min(3, len(packed_context))
    )
    
    state["answer"] = answer
    state["trust_score"] = trust_score
    state["source_type"] = "rag"
    state["sources"] = packed_context
    
    logger.info(f"RAG answer - trust: {trust_score:.1f}%")
    return state


def _calculate_trust_from_metrics(
    answer: str,
    question: str,
    primary_score: float,
    source_type: str,
    num_sources: int,
    avg_score: float = None
) -> float:
    
    if source_type == "attribute":
        base = primary_score * 50
    else:
        base = min(primary_score * 400, 45)
    
    completeness = _calculate_completeness(answer, question)
    
    source_bonus = 0
    if num_sources >= 5:
        source_bonus = 12
    elif num_sources >= 3:
        source_bonus = 8
    elif num_sources == 2:
        source_bonus = 5
    elif num_sources == 1:
        source_bonus = 2
    
    consistency_bonus = 0
    if source_type == "rag" and avg_score:
        if avg_score > 0.08:
            consistency_bonus = 12
        elif avg_score > 0.05:
            consistency_bonus = 8
        elif avg_score > 0.03:
            consistency_bonus = 3
    
    if source_type == "attribute" and num_sources > 2:
        consistency_bonus = 8
    elif source_type == "attribute" and num_sources > 1:
        consistency_bonus = 5
    
    total = base + completeness + source_bonus + consistency_bonus
    
    if total >= 95:
        return round(min(total * 0.95, 98), 1)
    
    return round(min(total, 100), 1)


def _calculate_completeness(answer: str, question: str) -> float:
    
    answer_length = len(answer)
    if answer_length < 150:
        length_score = 2
    elif answer_length < 400:
        length_score = 6
    elif answer_length < 1000:
        length_score = 10
    else:
        length_score = 14
    
    question_keywords = set(re.findall(r'\b\w{4,}\b', question.lower()))
    answer_keywords = set(re.findall(r'\b\w{4,}\b', answer.lower()))
    
    question_keywords.discard('your')
    question_keywords.discard('does')
    question_keywords.discard('what')
    question_keywords.discard('please')
    question_keywords.discard('provide')
    question_keywords.discard('describe')
    
    if question_keywords:
        overlap_ratio = len(question_keywords & answer_keywords) / len(question_keywords)
        keyword_score = min(overlap_ratio * 16, 16)
    else:
        keyword_score = 8
    
    has_numbers = bool(re.search(r'\d+', answer))
    has_bullets = bool(re.search(r'^[\s]*[-*]\s', answer, re.MULTILINE))
    has_headers = bool(re.search(r'^#{1,3}\s', answer, re.MULTILINE))
    
    structure_score = 0
    if has_numbers:
        structure_score += 2
    if has_bullets or has_headers:
        structure_score += 3
    
    return length_score + keyword_score + structure_score


def _deduplicate_chunks(chunks: list) -> list:
    if not chunks:
        return []
    
    seen_texts = set()
    deduplicated = []
    
    for chunk in chunks:
        text_signature = chunk["text"].lower().strip()[:200]
        
        if text_signature not in seen_texts:
            seen_texts.add(text_signature)
            deduplicated.append(chunk)
    
    return deduplicated


def _pack_context_smart(chunks: list, max_tokens: int = 5000) -> list:
    if not chunks:
        return []
    
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
    except:
        encoding = tiktoken.get_encoding("cl100k_base")
    
    packed = []
    total_tokens = 0
    
    for chunk in chunks:
        chunk_tokens = len(encoding.encode(chunk["text"]))
        
        if total_tokens + chunk_tokens > max_tokens:
            break
        
        packed.append(chunk)
        total_tokens += chunk_tokens
    
    return packed if packed else chunks[:1]