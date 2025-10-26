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