CONFLICT_RESOLUTION_SYSTEM = """You are an expert at resolving conflicts between company attribute records. Your goal is to maintain accurate, up-to-date information."""

CONFLICT_RESOLUTION_USER = """Two attributes may refer to the same information:

**Existing Attribute:**
Key: {existing_key}
Value: {existing_value}
Last Updated: {existing_date}

**New Attribute:**
Key: {new_key}
Value: {new_value}
Source: Just extracted from document

Decide what to do:
- keep_existing: New info is redundant or less accurate
- keep_new: New info is more accurate or updates old info
- merge_both: Both contain unique information worth keeping

Return JSON:
{{"decision": "keep_existing|keep_new|merge_both", "reason": "brief explanation", "merged_value": "only if merge_both"}}"""