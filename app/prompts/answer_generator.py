DECOMPOSE_QUERY_PROMPT = """Break this RFP question into simple sub-questions that can be answered independently.
If the question is already simple, return just the original question.

Question: {question}

Return ONLY the sub-questions, one per line."""

GENERATE_ANSWER_PROMPT = """Based on the following context, answer the question professionally and accurately.

Context:
{context}

Question: {question}

Answer:"""