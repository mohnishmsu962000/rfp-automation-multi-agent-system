from langchain_openai import ChatOpenAI
from app.core.config import get_settings
from app.agents.answer_generator.state import AnswerGeneratorState
from app.prompts.answer_generator import DECOMPOSE_QUERY_PROMPT

settings = get_settings()
llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)

def decompose_query_node(state: AnswerGeneratorState) -> AnswerGeneratorState:
    question = state["question"]
    prompt = DECOMPOSE_QUERY_PROMPT.format(question=question)
    
    response = llm.invoke(prompt)
    queries = [q.strip() for q in response.content.split("\n") if q.strip()]
    
    state["decomposed_queries"] = queries if queries else [question]
    return state