from app.agents.answer_generator.graph import create_answer_generator_graph
from app.agents.answer_generator.state import AnswerGeneratorState
from sqlalchemy.orm import Session
from typing import Dict

def generate_answer_for_question(question: str, db: Session) -> Dict:
    graph = create_answer_generator_graph(db)
    
    initial_state = {
        "question": question,
        "decomposed_queries": [],
        "rag_results": [],
        "answer": "",
        "trust_score": 0.0,
        "sources": []
    }
    
    result = graph.invoke(initial_state)
    
    return {
        "answer": result["answer"],
        "trust_score": result["trust_score"],
        "sources": result["sources"]
    }

__all__ = ["generate_answer_for_question", "create_answer_generator_graph", "AnswerGeneratorState"]