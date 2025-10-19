from app.agents.kb_manager.state import KBManagerState
from difflib import SequenceMatcher
from typing import List, Dict

def find_conflicts(state: KBManagerState) -> KBManagerState:
    deduplicated_new = _deduplicate_new_attributes(state["new_attributes"])
    
    conflicts = []
    processed_new_keys = set()
    
    for new_attr in deduplicated_new:
        best_match = None
        best_score = 0
        
        for existing_attr in state["existing_attributes"]:
            key_similarity = _calculate_key_similarity(
                new_attr["key"], 
                existing_attr["key"]
            )
            
            if key_similarity > 0.75:
                value_similarity = _calculate_value_similarity(
                    new_attr["value"],
                    existing_attr["value"]
                )
                
                category_match = new_attr["category"] == existing_attr["category"]
                
                combined_score = (
                    key_similarity * 0.6 + 
                    value_similarity * 0.3 + 
                    (1.0 if category_match else 0.0) * 0.1
                )
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_match = existing_attr
        
        if best_match and best_score > 0.7:
            conflict_type = _determine_conflict_type(
                new_attr, 
                best_match, 
                best_score
            )
            
            conflicts.append({
                "new": new_attr,
                "existing": best_match,
                "similarity": best_score,
                "conflict_type": conflict_type
            })
            processed_new_keys.add(new_attr["key"])
    
    state["conflicts"] = conflicts
    state["new_attributes"] = deduplicated_new
    state["processed_keys"] = processed_new_keys
    
    return state


def _deduplicate_new_attributes(attributes: List[Dict]) -> List[Dict]:
    seen = {}
    deduplicated = []
    
    for attr in attributes:
        key = attr["key"].lower().strip()
        
        if key in seen:
            existing = seen[key]
            if len(attr["value"]) > len(existing["value"]):
                seen[key] = attr
        else:
            seen[key] = attr
    
    return list(seen.values())


def _calculate_key_similarity(key1: str, key2: str) -> float:
    key1_lower = key1.lower().strip()
    key2_lower = key2.lower().strip()
    
    if key1_lower == key2_lower:
        return 1.0
    
    key1_normalized = ''.join(c for c in key1_lower if c.isalnum())
    key2_normalized = ''.join(c for c in key2_lower if c.isalnum())
    
    if key1_normalized == key2_normalized:
        return 0.95
    
    return SequenceMatcher(None, key1_lower, key2_lower).ratio()


def _calculate_value_similarity(value1: str, value2: str) -> float:
    value1_lower = value1.lower().strip()
    value2_lower = value2.lower().strip()
    
    if value1_lower == value2_lower:
        return 1.0
    
    return SequenceMatcher(None, value1_lower, value2_lower).ratio()


def _determine_conflict_type(new_attr: Dict, existing_attr: Dict, similarity: float) -> str:
    if similarity > 0.95:
        value_sim = _calculate_value_similarity(new_attr["value"], existing_attr["value"])
        if value_sim > 0.9:
            return "duplicate"
        else:
            return "update"
    elif similarity > 0.85:
        return "similar"
    else:
        return "ambiguous"