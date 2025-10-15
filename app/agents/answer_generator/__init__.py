from app.agents.answer_generator.graph import create_answer_generator_graph
from app.agents.answer_generator.state import AnswerGeneratorState
from sqlalchemy.orm import Session
from typing import Dict, Optional
from uuid import UUID

def generate_answer_for_question(question: str, db: Session, user_id: Optional[UUID] = None) -> Dict:
    graph = create_answer_generator_graph(db)
    
    initial_state = {
        "user_id": user_id,
        "question": question,
        "decomposed_queries": [],
        "attribute_results": [],
        "rag_results": [],
        "answer": "",
        "trust_score": 0.0,
        "sources": [],
        "source_type": "none"
    }
    
    result = graph.invoke(initial_state)
    
    return {
        "answer": result["answer"],
        "trust_score": result["trust_score"],
        "sources": result["sources"],
        "source_type": result.get("source_type", "rag")
    }

__all__ = ["generate_answer_for_question", "create_answer_generator_graph", "AnswerGeneratorState"]