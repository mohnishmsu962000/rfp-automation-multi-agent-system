from sqlalchemy.orm import Session
from app.agents.answer_generator.state import AnswerGeneratorState
from app.services.rag_service import RAGService

def search_rag_node(state: AnswerGeneratorState, db: Session) -> AnswerGeneratorState:
    all_results = []
    
    for query in state["decomposed_queries"]:
        results = RAGService.search_similar_chunks(query, db, top_k=3)
        all_results.extend(results)
    
    state["rag_results"] = all_results
    return state