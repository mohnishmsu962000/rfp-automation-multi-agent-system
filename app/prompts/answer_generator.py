DECOMPOSE_QUERY_PROMPT = """Break this RFP question into simple sub-questions that can be answered independently.
If the question is already simple, return just the original question.

Question: {question}

Return ONLY the sub-questions, one per line."""

GENERATE_ANSWER_PROMPT = """Based on the following context, answer the question professionally and accurately.

Context:
{context}

Question: {question}

Answer:"""



ATTRIBUTE_BASED_ANSWER = """Based on the following company attribute, answer this question:

Question: {question}

Attribute: {key}
Value: {value}
Category: {category}

Provide a clear, professional answer using this information."""



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