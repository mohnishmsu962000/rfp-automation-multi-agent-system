from app.agents.kb_manager.state import KBManagerState
from app.services.llm_factory import LLMFactory
from app.prompts.kb_manager import CONFLICT_RESOLUTION_SYSTEM, CONFLICT_RESOLUTION_USER
from langchain_core.messages import SystemMessage, HumanMessage
import json

def resolve_conflicts(state: KBManagerState) -> KBManagerState:
    if not state["conflicts"]:
        state["resolutions"] = []
        return state
    
    llm = LLMFactory.get_llm("gpt-4o-mini")
    resolutions = []
    
    for conflict in state["conflicts"]:
        new = conflict["new"]
        existing = conflict["existing"]
        
        prompt = CONFLICT_RESOLUTION_USER.format(
            existing_key=existing["key"],
            existing_value=existing["value"],
            existing_date=existing["last_updated"],
            new_key=new["key"],
            new_value=new["value"]
        )
        
        try:
            response = llm.invoke(
                [
                    SystemMessage(content=CONFLICT_RESOLUTION_SYSTEM),
                    HumanMessage(content=prompt)
                ],
                response_format={"type": "json_object"}
            )
            
            resolution = json.loads(response.content)
            resolutions.append({
                "conflict": conflict,
                "decision": resolution.get("decision", "keep_existing"),
                "reason": resolution.get("reason", ""),
                "merged_value": resolution.get("merged_value")
            })
            
        except Exception as e:
            print(f"Conflict resolution error: {str(e)}")
            resolutions.append({
                "conflict": conflict,
                "decision": "keep_existing",
                "reason": "Error during resolution"
            })
    
    state["resolutions"] = resolutions
    return state