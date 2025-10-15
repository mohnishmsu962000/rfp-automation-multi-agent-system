from app.agents.kb_manager.state import KBManagerState
from app.core.database import SessionLocal
from app.models.attribute import Attribute
from uuid import UUID
from datetime import datetime

def save_attributes(state: KBManagerState) -> KBManagerState:
    db = SessionLocal()
    
    try:
        kept_existing = 0
        kept_new = 0
        merged = 0
        
        resolved_new_attrs = set()
        
        for resolution in state["resolutions"]:
            conflict = resolution["conflict"]
            decision = resolution["decision"]
            
            new_attr = conflict["new"]
            existing_attr = conflict["existing"]
            resolved_new_attrs.add(new_attr["key"])
            
            if decision == "keep_existing":
                kept_existing += 1
                
            elif decision == "keep_new":
                attr = db.query(Attribute).filter(
                    Attribute.id == UUID(existing_attr["id"])
                ).first()
                if attr:
                    attr.value = new_attr["value"]
                    attr.last_updated = datetime.utcnow()
                kept_new += 1
                
            elif decision == "merge_both":
                attr = db.query(Attribute).filter(
                    Attribute.id == UUID(existing_attr["id"])
                ).first()
                if attr:
                    attr.value = resolution.get("merged_value", new_attr["value"])
                    attr.last_updated = datetime.utcnow()
                merged += 1
        
        for new_attr in state["new_attributes"]:
            if new_attr["key"] not in resolved_new_attrs:
                attr = Attribute(
                    user_id=state["user_id"],
                    key=new_attr["key"],
                    value=new_attr["value"],
                    category=new_attr["category"],
                    source_doc_id=UUID(new_attr["source_doc_id"]) if new_attr.get("source_doc_id") else None
                )
                db.add(attr)
                kept_new += 1
        
        db.commit()
        
        state["stats"] = {
            "kept_existing": kept_existing,
            "kept_new": kept_new,
            "merged": merged,
            "total_conflicts": len(state["conflicts"]),
            "new_attributes_added": kept_new
        }
        
        return state
        
    finally:
        db.close()