from typing import TypedDict, List, Dict, Set
from uuid import UUID

class KBManagerState(TypedDict):
    user_id: str
    company_id: UUID
    new_attributes: List[Dict]
    existing_attributes: List[Dict]
    conflicts: List[Dict]
    resolutions: List[Dict]
    processed_keys: Set[str]
    stats: Dict