from app.agents.answer_generator.state import AnswerGeneratorState
from app.services.attribute_search import AttributeSearchService
from app.core.database import SessionLocal

def search_attributes(state: AnswerGeneratorState) -> AnswerGeneratorState:
    db = SessionLocal()
    
    try:
        company_id = state.get("company_id")
        if not company_id:
            state["attribute_results"] = []
            return state
        
        query = state["question"]
        
        results = AttributeSearchService.search_attributes(query, company_id, db, top_k=3)
        
        print(f"Attribute search for: {query}")
        print(f"Top result: {results[0] if results else 'None'}")
        
        state["attribute_results"] = results
        
        return state
        
    finally:
        db.close()