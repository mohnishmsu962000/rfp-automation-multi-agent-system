from typing import TypedDict, List, Dict
from uuid import UUID

class KBManagerState(TypedDict):
    user_id: UUID
    new_attributes: List[Dict]
    existing_attributes: List[Dict]
    conflicts: List[Dict]
    resolutions: List[Dict]
    stats: Dict