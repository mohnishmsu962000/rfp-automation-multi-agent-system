from app.services.llm_factory import LLMFactory
from app.agents.answer_generator.state import AnswerGeneratorState
from app.prompts.answer_generator import GENERATE_ANSWER_PROMPT, ATTRIBUTE_BASED_ANSWER, SYSTEM_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage
import logging
import tiktoken

logger = logging.getLogger(__name__)

def generate_answer_node(state: AnswerGeneratorState) -> AnswerGeneratorState:
    llm = LLMFactory.get_llm("claude-sonnet")
    attribute_results = state.get("attribute_results", [])
    
    if attribute_results and attribute_results[0]["similarity"] > 0.7:
        top_attr = attribute_results[0]
        
        prompt = ATTRIBUTE_BASED_ANSWER.format(
            question=state["question"],
            key=top_attr["key"],
            value=top_attr["value"],
            category=top_attr["category"]
        )
        
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT), 
            HumanMessage(content=prompt)
        ])
        
        trust_score = _calculate_attribute_trust_score(top_attr["similarity"], attribute_results)
        
        state["answer"] = response.content
        state["trust_score"] = trust_score
        state["source_type"] = "attribute"
        state["sources"] = [{
            "type": "attribute",
            "key": top_attr["key"],
            "value": top_attr["value"],
            "similarity": top_attr["similarity"]
        }]
        
        return state
    
    question = state["question"]
    rag_results = state["rag_results"]
    
    if not rag_results or (rag_results and rag_results[0].get("rerank_score", 0) < 0.05):
        state["answer"] = "Based on the available information in our knowledge base, we do not have sufficient details to answer this question comprehensively. Please provide additional context or documentation."
        state["trust_score"] = 0.0
        state["source_type"] = "none"
        state["sources"] = []
        return state
    
    deduplicated_results = _deduplicate_chunks(rag_results)
    
    packed_context = _pack_context_smart(deduplicated_results, max_tokens=5000)
    
    context = "\n\n".join([f"[Source {i+1}]\n{c['text']}" for i, c in enumerate(packed_context)])
    
    prompt = GENERATE_ANSWER_PROMPT.format(context=context, question=question)
    
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    answer = response.content
    
    is_valid, validation_score = _validate_answer(answer, question, packed_context)
    
    if not is_valid:
        answer = f"{answer}\n\n*Note: This answer may be incomplete. Please verify with additional sources.*"
    
    trust_score = _calculate_rag_trust_score(packed_context, validation_score, answer, question)
    
    state["answer"] = answer
    state["trust_score"] = trust_score
    state["source_type"] = "rag"
    state["sources"] = packed_context
    
    logger.info(f"Generated answer with trust score: {trust_score:.2f}, validation: {is_valid}")
    
    return state


def _deduplicate_chunks(chunks: list) -> list:
    if not chunks:
        return []
    
    seen_texts = set()
    deduplicated = []
    
    for chunk in chunks:
        text_lower = chunk["text"].lower().strip()
        
        text_signature = text_lower[:200]
        
        if text_signature not in seen_texts:
            seen_texts.add(text_signature)
            deduplicated.append(chunk)
    
    return deduplicated


def _pack_context_smart(chunks: list, max_tokens: int = 3000) -> list:
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


def _validate_answer(answer: str, question: str, sources: list) -> tuple[bool, float]:
    if len(answer.strip()) < 20:
        return False, 0.0
    
    if "i don't know" in answer.lower() or "cannot answer" in answer.lower():
        return False, 0.0
    
    answer_lower = answer.lower()
    question_lower = question.lower()
    
    question_keywords = set([w for w in question_lower.split() if len(w) > 4])
    answer_keywords = set([w for w in answer_lower.split() if len(w) > 4])
    
    keyword_overlap = len(question_keywords & answer_keywords) / max(len(question_keywords), 1)
    
    if keyword_overlap < 0.2:
        return False, 0.5
    
    source_terms = set()
    for source in sources[:3]:
        source_terms.update([w.lower() for w in source["text"].split() if len(w) > 4])
    
    answer_terms = set([w.lower() for w in answer.split() if len(w) > 4])
    source_grounding = len(answer_terms & source_terms) / max(len(answer_terms), 1)
    
    if source_grounding < 0.3:
        return False, 0.6
    
    validation_score = (keyword_overlap + source_grounding) / 2
    
    is_valid = validation_score > 0.5
    
    return is_valid, validation_score


def _calculate_attribute_trust_score(top_similarity: float, all_results: list) -> float:
    base_score = top_similarity * 100
    
    if len(all_results) > 1 and all_results[1]["similarity"] > 0.6:
        base_score = min(base_score + 5, 100)
    
    return round(base_score, 2)


def _calculate_rag_trust_score(results: list, validation_score: float, answer: str, question: str) -> float:
    
    if not results:
        return 0.0
    
    try:
        from app.services.llm_factory import LLMFactory
        from app.prompts.answer_generator import SCORE_ANSWER_QUALITY_PROMPT
        from langchain_core.messages import SystemMessage, HumanMessage
        
        llm = LLMFactory.get_llm("claude-haiku-4")
        
        prompt = SCORE_ANSWER_QUALITY_PROMPT.format(
            question=question,
            answer=answer[:1500]  
        )
        
        response = llm.invoke([
            SystemMessage(content="You are an expert RFP evaluator. Respond only with a number."),
            HumanMessage(content=prompt)
        ])
        
        
        score_text = response.content.strip()
        score = float(score_text)
        
       
        score = min(max(score, 0), 100)
        
        logger.info(f"LLM trust score: {score}")
        return round(score, 2)
        
    except Exception as e:
        logger.error(f"LLM scoring failed: {str(e)}, falling back to retrieval-based")
        
       
        top_score = results[0].get("rerank_score", 0)
        avg_top_3 = sum(r.get("rerank_score", 0) for r in results[:3]) / min(3, len(results))
        num_sources = len(results)
        
        base_score = min(top_score * 100, 80)
        consistency_bonus = avg_top_3 * 18
        source_bonus = min(num_sources * 3, 12)
        
        trust_score = base_score + consistency_bonus + source_bonus
        return round(min(trust_score, 100), 2)