from app.services.llm_factory import LLMFactory
from app.agents.answer_generator.state import AnswerGeneratorState
from app.prompts.answer_generator import GENERATE_ANSWER_PROMPT, ATTRIBUTE_BASED_ANSWER
import logging

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
        
        response = llm.invoke(prompt)
        
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
    
    deduplicated_results = _deduplicate_chunks(rag_results)
    
    context_parts = []
    for i, r in enumerate(deduplicated_results[:5], 1):
        context_parts.append(f"[Source {i}]\n{r['text']}")
    
    context = "\n\n".join(context_parts)
    
    prompt = GENERATE_ANSWER_PROMPT.format(context=context, question=question)
    response = llm.invoke(prompt)
    
    trust_score = _calculate_rag_trust_score(deduplicated_results)
    
    state["answer"] = response.content
    state["trust_score"] = trust_score
    state["source_type"] = "rag"
    state["sources"] = deduplicated_results[:5]
    
    logger.info(f"Generated answer with trust score: {trust_score:.2f}")
    
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


def _calculate_attribute_trust_score(top_similarity: float, all_results: list) -> float:
    base_score = top_similarity * 100
    
    if len(all_results) > 1 and all_results[1]["similarity"] > 0.6:
        base_score = min(base_score + 5, 100)
    
    return round(base_score, 2)


def _calculate_rag_trust_score(results: list) -> float:
    if not results:
        return 0.0
    
    top_rerank_score = results[0].get("rerank_score", 0)
    
    num_sources = len(results)
    
    avg_rerank = sum(r.get("rerank_score", 0) for r in results[:3]) / min(3, len(results))
    
    base_score = top_rerank_score * 70
    
    source_bonus = min(num_sources * 3, 15)
    
    consistency_bonus = avg_rerank * 15
    
    trust_score = base_score + source_bonus + consistency_bonus
    
    trust_score = min(max(trust_score, 0), 100)
    
    return round(trust_score, 2)