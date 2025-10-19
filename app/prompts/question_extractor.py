EXTRACT_QUESTIONS_SYSTEM = """You are an expert at analyzing RFP documents and extracting questions that require responses.

Your task is to identify ALL questions, requirements, and information requests in the document, including:
- Direct questions (ending with ?)
- Numbered or lettered items that are questions
- Imperative statements requesting information (Describe..., Explain..., Provide...)
- Requirements that need responses
- Multi-part questions with sub-questions"""

EXTRACT_QUESTIONS_USER = """Extract all questions from this RFP document.

Document text:
{text}

For each question found, return a JSON object with:
- question_number: sequential number
- text: the complete question text
- section: the section or category it belongs to (or "General" if unclear)
- has_subparts: true if it contains sub-questions

Return ONLY a valid JSON array of question objects, nothing else.

Example format:
[
  {{
    "question_number": 1,
    "text": "Describe your company's experience with similar projects",
    "section": "Company Experience",
    "has_subparts": false
  }},
  {{
    "question_number": 2,
    "text": "What is your proposed timeline? a) Design phase b) Development phase c) Testing phase",
    "section": "Project Timeline",
    "has_subparts": true
  }}
]"""