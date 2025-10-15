from app.agents.kb_manager.graph import create_kb_manager_graph
from app.agents.kb_manager.state import KBManagerState
from uuid import UUID
from typing import List, Dict

def run_kb_manager(user_id: UUID, new_attributes: List[Dict]) -> Dict:
    graph = create_kb_manager_graph()
    
    initial_state: KBManagerState = {
        "user_id": user_id,
        "new_attributes": new_attributes,
        "existing_attributes": [],
        "conflicts": [],
        "resolutions": [],
        "stats": {}
    }
    
    result = graph.invoke(initial_state)
    
    return result["stats"]