from app.agents.kb_manager.graph import create_kb_manager_graph
from app.agents.kb_manager.state import KBManagerState
from typing import List, Dict
from uuid import UUID

def run_kb_manager(user_id: str, company_id: UUID, new_attributes: List[Dict]) -> Dict:
    graph = create_kb_manager_graph()
    
    initial_state = {
        "user_id": user_id,
        "company_id": company_id,
        "new_attributes": new_attributes,
        "existing_attributes": [],
        "conflicts": [],
        "resolutions": [],
        "processed_keys": set(),
        "stats": {}
    }
    
    result = graph.invoke(initial_state)
    
    return result["stats"]

__all__ = ["run_kb_manager", "create_kb_manager_graph", "KBManagerState"]