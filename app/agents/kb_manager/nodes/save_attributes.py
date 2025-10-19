from app.agents.kb_manager.state import KBManagerState
from app.core.database import SessionLocal
from app.models.attribute import Attribute
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def save_attributes(state: KBManagerState) -> KBManagerState:
    db = SessionLocal()
    
    try:
        stats = {
            "kept_existing": 0,
            "kept_new": 0,
            "merged": 0,
            "new_added": 0,
            "total_conflicts": len(state["conflicts"])
        }
        
        resolved_keys = set()
        
        for resolution in state["resolutions"]:
            conflict = resolution["conflict"]
            decision = resolution["decision"]
            
            new_attr = conflict["new"]
            existing_attr = conflict["existing"]
            resolved_keys.add((new_attr["key"].lower(), new_attr["category"]))
            
            if decision == "keep_existing":
                stats["kept_existing"] += 1
                logger.info(f"Kept existing: {existing_attr['key']}")
                
            elif decision == "keep_new":
                attr = db.query(Attribute).filter(
                    Attribute.id == UUID(existing_attr["id"])
                ).first()
                if attr:
                    attr.value = new_attr["value"]
                    attr.last_updated = datetime.utcnow()
                    if new_attr.get("source_doc_id"):
                        attr.source_doc_id = UUID(new_attr["source_doc_id"])
                stats["kept_new"] += 1
                logger.info(f"Updated to new: {new_attr['key']}")
                
            elif decision == "merge_both":
                attr = db.query(Attribute).filter(
                    Attribute.id == UUID(existing_attr["id"])
                ).first()
                if attr:
                    merged_value = resolution.get("merged_value", new_attr["value"])
                    attr.value = merged_value
                    attr.last_updated = datetime.utcnow()
                    if new_attr.get("source_doc_id"):
                        attr.source_doc_id = UUID(new_attr["source_doc_id"])
                stats["merged"] += 1
                logger.info(f"Merged: {new_attr['key']}")
        
        for new_attr in state["new_attributes"]:
            key_category_pair = (new_attr["key"].lower(), new_attr["category"])
            
            if key_category_pair not in resolved_keys:
                attr = Attribute(
                    user_id=state["user_id"],
                    company_id=state["company_id"],
                    key=new_attr["key"],
                    value=new_attr["value"],
                    category=new_attr["category"],
                    source_doc_id=UUID(new_attr["source_doc_id"]) if new_attr.get("source_doc_id") else None
                )
                db.add(attr)
                stats["new_added"] += 1
                logger.info(f"Added new: {new_attr['key']}")
        
        db.commit()
        
        state["stats"] = stats
        logger.info(f"KB Manager stats: {stats}")
        
        return state
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving attributes: {str(e)}")
        state["stats"] = {"error": str(e)}
        return state
        
    finally:
        db.close()