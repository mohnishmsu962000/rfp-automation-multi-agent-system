from app.agents.kb_manager.state import KBManagerState
from app.core.database import SessionLocal
from app.models.attribute import Attribute

def load_existing_attributes(state: KBManagerState) -> KBManagerState:
    db = SessionLocal()
    try:
        existing = db.query(Attribute).filter(
            Attribute.user_id == state["user_id"]
        ).all()
        
        state["existing_attributes"] = [
            {
                "id": str(attr.id),
                "key": attr.key,
                "value": attr.value,
                "category": attr.category,
                "last_updated": attr.last_updated.isoformat()
            }
            for attr in existing
        ]
        
        return state
    finally:
        db.close()