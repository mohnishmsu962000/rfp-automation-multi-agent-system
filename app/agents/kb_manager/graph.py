from langgraph.graph import StateGraph, END
from app.agents.kb_manager.state import KBManagerState
from app.agents.kb_manager.nodes.load_existing import load_existing_attributes
from app.agents.kb_manager.nodes.find_conflicts import find_conflicts
from app.agents.kb_manager.nodes.resolve_conflicts import resolve_conflicts
from app.agents.kb_manager.nodes.save_attributes import save_attributes

def create_kb_manager_graph():
    workflow = StateGraph(KBManagerState)
    
    workflow.add_node("load_existing", load_existing_attributes)
    workflow.add_node("find_conflicts", find_conflicts)
    workflow.add_node("resolve_conflicts", resolve_conflicts)
    workflow.add_node("save_attributes", save_attributes)
    
    workflow.set_entry_point("load_existing")
    workflow.add_edge("load_existing", "find_conflicts")
    workflow.add_edge("find_conflicts", "resolve_conflicts")
    workflow.add_edge("resolve_conflicts", "save_attributes")
    workflow.add_edge("save_attributes", END)
    
    return workflow.compile()