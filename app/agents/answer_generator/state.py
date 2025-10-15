from typing import TypedDict, List, Dict, Optional
from uuid import UUID

class AnswerGeneratorState(TypedDict):
    user_id: Optional[UUID]
    question: str
    decomposed_queries: List[str]
    attribute_results: List[Dict]
    rag_results: List[Dict]
    answer: str
    trust_score: float
    sources: List[Dict]
    source_type: str