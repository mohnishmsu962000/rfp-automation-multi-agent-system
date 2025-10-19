DECOMPOSE_QUERY_PROMPT = """Break this RFP question into simple sub-questions that can be answered independently.
If the question is already simple, return just the original question.

Question: {question}

Return ONLY the sub-questions, one per line."""

SHOULD_DECOMPOSE_PROMPT = """Determine if this question needs to be broken down into sub-questions.

Question: {question}

Answer with ONLY: YES or NO"""

GENERATE_ANSWER_PROMPT = """Based on the following context sources, answer the question professionally and accurately.

Context Sources:
{context}

Question: {question}

Instructions:
- Provide a clear, professional answer
- Use information from the sources provided
- If sources contain conflicting information, note this
- Keep the answer concise but complete
- Do not make up information not in the sources
- If information is insufficient, state that clearly

Answer:"""

ATTRIBUTE_BASED_ANSWER = """Based on the following company attribute, answer this question:

Question: {question}

Attribute: {key}
Value: {value}
Category: {category}

Provide a clear, professional answer using this information."""

VALIDATE_ANSWER_PROMPT = """Evaluate if this answer properly addresses the question based on the provided sources.

Question: {question}

Answer: {answer}

Sources: {sources}

Respond with: VALID or INVALID"""

REPHRASE_ANSWER_SYSTEM = """You are an expert at rewriting RFP answers while maintaining accuracy and using only the provided source information."""

REPHRASE_ANSWER_USER = """Rewrite this RFP answer based on the user's instruction.

**Original Question:**
{question}

**Current Answer:**
{current_answer}

**Source Information:**
{sources}

**User Instruction:**
{instruction}

Important:
- Only use information from the sources provided
- Follow the user's instruction for tone/style
- Maintain accuracy and completeness
- Keep it professional

Provide the rewritten answer:"""