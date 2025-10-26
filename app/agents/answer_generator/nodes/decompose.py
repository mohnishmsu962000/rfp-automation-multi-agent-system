from app.agents.answer_generator.state import AnswerGeneratorState
import logging
import re

logger = logging.getLogger(__name__)

def decompose_query_node(state: AnswerGeneratorState) -> AnswerGeneratorState:
    question = state["question"]
    
    should_decompose = (
        len(question.split()) > 20 and
        any(word in question.lower() for word in [' and ', ' also ', ' additionally', 'provide details on', 'describe', 'explain', 'what about'])
    )
    
    if not should_decompose:
        state["decomposed_queries"] = [question]
        return state
    
    patterns = [
        r'\.\s+(?:Also|Additionally|Furthermore|Moreover|Specifically)',
        r'\?\s+(?:Also|Additionally|What about|How about)',
    ]
    
    parts = [question]
    for pattern in patterns:
        new_parts = []
        for part in parts:
            split_parts = re.split(pattern, part, flags=re.IGNORECASE)
            new_parts.extend([p.strip() for p in split_parts if p.strip()])
        parts = new_parts
    
    decomposed = parts[:4] if len(parts) > 1 else [question]
    
    state["decomposed_queries"] = decomposed
    logger.info(f"Decomposed into {len(decomposed)} queries")
    
    return state