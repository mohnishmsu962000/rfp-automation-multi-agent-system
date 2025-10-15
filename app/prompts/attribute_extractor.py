ATTRIBUTE_EXTRACTION_SYSTEM = """You are an expert at extracting structured company information from documents. Return valid JSON only."""

ATTRIBUTE_EXTRACTION_USER = """Extract company facts and attributes from this document as structured key-value pairs.

Rules:
- Only extract concrete, factual information
- Key should be concise (2-5 words)
- Value should be specific and complete
- Category must be one of: technical, compliance, business, product
- Skip vague or uncertain information

Examples:
{{"key": "soc2_certified", "value": "Yes, Type II, expires December 2026", "category": "compliance"}}
{{"key": "tech_stack", "value": "React, Node.js, PostgreSQL, Redis", "category": "technical"}}
{{"key": "team_size", "value": "75 employees across 3 offices", "category": "business"}}
{{"key": "uptime_sla", "value": "99.9% guaranteed uptime", "category": "product"}}

Document text:
{text}

Return JSON array of attributes with this exact structure:
{{"attributes": [{{"key": "...", "value": "...", "category": "..."}}]}}"""