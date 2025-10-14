from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from app.agents.answer_generator.state import AnswerGeneratorState
from app.agents.answer_generator.nodes.decompose import decompose_query_node
from app.agents.answer_generator.nodes.search import search_rag_node
from app.agents.answer_generator.nodes.generate import generate_answer_node

def create_answer_generator_graph(db: Session):
    workflow = StateGraph(AnswerGeneratorState)
    
    workflow.add_node("decompose", decompose_query_node)
    workflow.add_node("search", lambda state: search_rag_node(state, db))
    workflow.add_node("generate", generate_answer_node)
    
    workflow.set_entry_point("decompose")
    workflow.add_edge("decompose", "search")
    workflow.add_edge("search", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()