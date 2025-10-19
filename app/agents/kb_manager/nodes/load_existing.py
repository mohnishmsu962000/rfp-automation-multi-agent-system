from app.agents.kb_manager.state import KBManagerState
from app.core.database import SessionLocal
from app.models.attribute import Attribute

def load_existing_attributes(state: KBManagerState) -> KBManagerState:
    db = SessionLocal()
    try:
        query = db.query(Attribute).filter(
            Attribute.company_id == state["company_id"]
        )
        
        if state.get("user_id"):
            query = query.filter(Attribute.user_id == str(state["user_id"]))
        
        existing = query.all()
        
        state["existing_attributes"] = [
            {
                "id": str(attr.id),
                "key": attr.key,
                "value": attr.value,
                "category": attr.category,
                "last_updated": attr.last_updated.isoformat() if attr.last_updated else None
            }
            for attr in existing
        ]
        
        return state
    finally:
        db.close()