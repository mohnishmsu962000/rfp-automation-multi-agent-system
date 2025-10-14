from langchain_anthropic import ChatAnthropic
from app.core.config import get_settings
from app.agents.answer_generator.state import AnswerGeneratorState
from app.prompts.answer_generator import GENERATE_ANSWER_PROMPT

settings = get_settings()
llm = ChatAnthropic(model="claude-sonnet-4-20250514", api_key=settings.ANTHROPIC_API_KEY)

def generate_answer_node(state: AnswerGeneratorState) -> AnswerGeneratorState:
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
    state["sources"] = state["rag_results"]
    
    return state