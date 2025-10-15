from app.agents.kb_manager.state import KBManagerState
from difflib import SequenceMatcher

def find_conflicts(state: KBManagerState) -> KBManagerState:
    conflicts = []
    
    for new_attr in state["new_attributes"]:
        for existing_attr in state["existing_attributes"]:
            key_similarity = SequenceMatcher(
                None, 
                new_attr["key"].lower(), 
                existing_attr["key"].lower()
            ).ratio()
            
            if key_similarity > 0.8:
                conflicts.append({
                    "new": new_attr,
                    "existing": existing_attr,
                    "similarity": key_similarity
                })
                break
    
    state["conflicts"] = conflicts
    return state