from app.services.llm_factory import LLMFactory
from app.agents.answer_generator.state import AnswerGeneratorState
from app.prompts.answer_generator import GENERATE_ANSWER_PROMPT, ATTRIBUTE_BASED_ANSWER

def generate_answer_node(state: AnswerGeneratorState) -> AnswerGeneratorState:
    llm = LLMFactory.get_llm("claude-sonnet")
    attribute_results = state.get("attribute_results", [])
    
    if attribute_results and attribute_results[0]["similarity"] > 0.5:
        top_attr = attribute_results[0]
        
        prompt = ATTRIBUTE_BASED_ANSWER.format(
            question=state["question"],
            key=top_attr["key"],
            value=top_attr["value"],
            category=top_attr["category"]
        )
        
        response = llm.invoke(prompt)
        
        state["answer"] = response.content
        state["trust_score"] = float(top_attr["similarity"] * 100)
        state["source_type"] = "attribute"
        state["sources"] = [{
            "type": "attribute",
            "key": top_attr["key"],
            "value": top_attr["value"],
            "similarity": top_attr["similarity"]
        }]
        
        return state
    
    question = state["question"]
    context = "\n\n".join([r["text"] for r in state["rag_results"]])
    
    prompt = GENERATE_ANSWER_PROMPT.format(context=context, question=question)
    response = llm.invoke(prompt)
    
    if state["rag_results"]:
        trust_score = max([r.get("rerank_score", 0) for r in state["rag_results"]]) * 100
    else:
        trust_score = 0.0
    
    state["answer"] = response.content
    state["trust_score"] = trust_score
    state["source_type"] = "rag"
    state["sources"] = state["rag_results"]
    
    return state