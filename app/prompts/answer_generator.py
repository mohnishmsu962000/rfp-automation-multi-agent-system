SYSTEM_PROMPT = """You are an expert RFP response writer for ACME Technologies.
Write professional, detailed answers using the provided information.
Use markdown formatting with ## headers for organization.
Include specific facts, numbers, dates, and examples when available."""

SIMPLE_ATTRIBUTE_ANSWER = """Answer this RFP question using the company information provided.

Question: {question}

Company Information:
{key}: {value}

Write a complete, professional answer with markdown headers (##) for organization."""

GENERATE_ANSWER_PROMPT = """Answer this RFP question using the sources provided below.

Question: {question}

Sources:
{context}

Instructions:
- Write a comprehensive answer addressing all parts of the question
- Use markdown ## headers to organize your response
- Include specific facts, numbers, and details from the sources
- Maintain a professional tone suitable for enterprise clients"""

ATTRIBUTE_BASED_ANSWER = """Answer this RFP question using the company attribute provided.

Question: {question}

Company Attribute:
Category: {category}
Key: {key}
Value: {value}

Write a detailed, professional response using this information. Format with markdown headers."""

REPHRASE_ANSWER_SYSTEM = """You are an expert at rewriting RFP answers to match specific tones and styles while maintaining complete accuracy. You only use information from provided sources and never fabricate details."""

REPHRASE_ANSWER_USER = """Rewrite this RFP answer based on the user's instruction while maintaining accuracy.

**Original Question:**
{question}

**Current Answer:**
{current_answer}

**Source Information:**
{sources}

**User's Rewriting Instruction:**
{instruction}

Requirements:
- Follow the user's instruction for tone, length, or style changes
- Use ONLY information from the sources - never add new facts
- Maintain professional quality
- Keep formatting clean with markdown (##, **, -, etc.)
- Preserve all key metrics and facts

Provide the rewritten answer:"""

DECOMPOSE_QUERY_PROMPT = """Break this RFP question into simple sub-questions that can be answered independently.
If the question is already simple, return just the original question.

Question: {question}

Return ONLY the sub-questions, one per line."""

SHOULD_DECOMPOSE_PROMPT = """Determine if this question needs to be broken down into sub-questions.

Question: {question}

Answer with ONLY: YES or NO"""

VALIDATE_ANSWER_PROMPT = """Evaluate if this RFP answer properly addresses the question and is supported by the sources.

Question: {question}

Answer: {answer}

Sources: {sources}

Check:
1. Does the answer directly address the question?
2. Is all information supported by the sources?
3. Is it professionally written?
4. Are there any hallucinations or unsupported claims?

Respond with ONLY: VALID or INVALID"""