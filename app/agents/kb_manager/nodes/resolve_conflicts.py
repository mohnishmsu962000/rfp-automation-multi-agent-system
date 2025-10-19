from app.agents.kb_manager.state import KBManagerState
from app.services.llm_factory import LLMFactory
from app.prompts.kb_manager import CONFLICT_RESOLUTION_SYSTEM, CONFLICT_RESOLUTION_USER
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

def resolve_conflicts(state: KBManagerState) -> KBManagerState:
    if not state["conflicts"]:
        state["resolutions"] = []
        return state
    
    resolutions = []
    
    for conflict in state["conflicts"]:
        conflict_type = conflict.get("conflict_type", "ambiguous")
        
        if conflict_type == "duplicate":
            resolution = _resolve_duplicate(conflict)
        elif conflict_type == "update":
            resolution = _resolve_update(conflict)
        else:
            resolution = _resolve_with_llm(conflict)
        
        resolutions.append(resolution)
    
    state["resolutions"] = resolutions
    return state


def _resolve_duplicate(conflict: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "conflict": conflict,
        "decision": "keep_existing",
        "reason": "Duplicate - values are identical",
        "merged_value": None,
        "method": "rule"
    }


def _resolve_update(conflict: Dict[str, Any]) -> Dict[str, Any]:
    new = conflict["new"]
    existing = conflict["existing"]
    
    new_value_longer = len(new["value"]) > len(existing["value"]) * 1.2
    
    if new_value_longer:
        return {
            "conflict": conflict,
            "decision": "keep_new",
            "reason": "New value is more detailed",
            "merged_value": None,
            "method": "rule"
        }
    else:
        return {
            "conflict": conflict,
            "decision": "keep_new",
            "reason": "Updated information",
            "merged_value": None,
            "method": "rule"
        }


def _resolve_with_llm(conflict: Dict[str, Any]) -> Dict[str, Any]:
    try:
        llm = LLMFactory.get_llm("gpt-4o-mini")
        
        new = conflict["new"]
        existing = conflict["existing"]
        
        prompt = CONFLICT_RESOLUTION_USER.format(
            existing_key=existing["key"],
            existing_value=existing["value"],
            existing_date=existing.get("last_updated", "Unknown"),
            new_key=new["key"],
            new_value=new["value"]
        )
        
        response = llm.invoke(
            [
                SystemMessage(content=CONFLICT_RESOLUTION_SYSTEM),
                HumanMessage(content=prompt)
            ],
            response_format={"type": "json_object"}
        )
        
        resolution = json.loads(response.content)
        
        if not _validate_resolution(resolution):
            logger.warning(f"Invalid LLM resolution, defaulting to keep_existing")
            return _get_fallback_resolution(conflict)
        
        return {
            "conflict": conflict,
            "decision": resolution.get("decision", "keep_existing"),
            "reason": resolution.get("reason", ""),
            "merged_value": resolution.get("merged_value"),
            "method": "llm"
        }
        
    except Exception as e:
        logger.error(f"LLM resolution error: {str(e)}")
        return _get_fallback_resolution(conflict)


def _validate_resolution(resolution: Dict[str, Any]) -> bool:
    if not isinstance(resolution, dict):
        return False
    
    decision = resolution.get("decision")
    if decision not in ["keep_existing", "keep_new", "merge_both"]:
        return False
    
    if decision == "merge_both" and not resolution.get("merged_value"):
        return False
    
    return True


def _get_fallback_resolution(conflict: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "conflict": conflict,
        "decision": "keep_existing",
        "reason": "Fallback - error during resolution",
        "merged_value": None,
        "method": "fallback"
    }