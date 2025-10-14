from typing import TypedDict, List, Dict

class AnswerGeneratorState(TypedDict):
    question: str
    decomposed_queries: List[str]
    rag_results: List[Dict]
    answer: str
    trust_score: float
    sources: List[Dict]