from app.services.llm_factory import LLMFactory
from app.agents.answer_generator.state import AnswerGeneratorState
from app.prompts.answer_generator import DECOMPOSE_QUERY_PROMPT, SHOULD_DECOMPOSE_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

def decompose_query_node(state: AnswerGeneratorState) -> AnswerGeneratorState:
    question = state["question"]
    
    should_decompose = _check_if_decompose_needed(question)
    
    if not should_decompose:
        state["decomposed_queries"] = [question]
        return state
    
    llm = LLMFactory.get_llm("gpt-4o-mini")
    prompt = DECOMPOSE_QUERY_PROMPT.format(question=question)
    
    response = llm.invoke(prompt)
    queries = [q.strip() for q in response.content.split("\n") if q.strip()]
    
    if not queries or len(queries) == 1:
        state["decomposed_queries"] = [question]
    else:
        state["decomposed_queries"] = queries[:5]
    
    return state


def _check_if_decompose_needed(question: str) -> bool:
    """Use LLM to determine if decomposition is needed"""
    try:
        llm = LLMFactory.get_llm("gpt-4o-mini")
        prompt = SHOULD_DECOMPOSE_PROMPT.format(question=question)
        
        response = llm.invoke(prompt)
        answer = response.content.strip().upper()
        
        return "YES" in answer
    except Exception as e:
        return len(question.split()) > 30 and ("?" in question[:-1])