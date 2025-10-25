SYSTEM_PROMPT = """You are an expert RFP (Request for Proposal) response writer for enterprise software companies. You write clear, professional, and compelling answers that win contracts. Your responses are accurate, well-structured, and based strictly on provided information."""

DECOMPOSE_QUERY_PROMPT = """Break this RFP question into simple sub-questions that can be answered independently.
If the question is already simple, return just the original question.

Question: {question}

Return ONLY the sub-questions, one per line."""

SHOULD_DECOMPOSE_PROMPT = """Determine if this question needs to be broken down into sub-questions.

Question: {question}

Answer with ONLY: YES or NO"""

GENERATE_ANSWER_PROMPT = """You are writing a professional RFP response for an enterprise software company. Generate a polished, executive-ready answer using ONLY the provided context.

Context Sources:
{context}

Question: {question}

Requirements:
- Write in a confident, professional tone suitable for Fortune 500 clients
- Structure with clear sections using ## headings for complex answers
- Use bullet points (starting with -) for lists of features, capabilities, or specifications
- Use **bold** for key metrics, numbers, certifications, and critical information
- Keep paragraphs concise (2-3 sentences maximum)
- Lead with the most important information first
- Use specific numbers, percentages, and metrics from the context
- If information is partially missing, provide what's available and note gaps professionally
- Do not fabricate information not in the sources

Formatting Guidelines:
- Main sections: ## Section Name
- Sub-sections: ### Subsection Name
- Key metrics: **99.99% uptime**, **$2.16M savings**, **SOC 2 Type II certified**
- Lists: Use - for bullet points with parallel structure
- Notes: Use *italics* for clarifications or caveats

Generate the response:"""

ATTRIBUTE_BASED_ANSWER = """You are writing a professional RFP response. Answer this question directly and professionally using the provided company attribute.

Question: {question}

Company Information:
- **{key}**: {value}
- Category: {category}

Requirements:
- Answer directly in 1-3 sentences
- Use **bold** for the key metric or fact
- Be confident and professional
- If the attribute doesn't fully answer the question, state what information is available

Generate the response:"""

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


SCORE_ANSWER_QUALITY_PROMPT = """Score this RFP answer based on how well it answers the question. Rate 0-100.

Question: {question}

Answer: {answer}

Scoring Guidelines:
- 90-100: Fully answers the question with specific details and facts
- 70-89: Answers most of the question, minor details missing
- 50-69: Partially answers, significant information missing
- 30-49: Minimal relevant information provided
- 0-29: Does not answer the question or completely wrong

IMPORTANT: Score based on information completeness, NOT writing style or polish.
If the answer provides the requested facts and details, score 90+.

Respond with ONLY a number 0-100."""