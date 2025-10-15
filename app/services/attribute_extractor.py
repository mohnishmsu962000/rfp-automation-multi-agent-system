from app.services.llm_factory import LLMFactory
from app.prompts.attribute_extractor import ATTRIBUTE_EXTRACTION_SYSTEM, ATTRIBUTE_EXTRACTION_USER
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict
import json

class AttributeExtractor:
    VALID_CATEGORIES = {"technical", "compliance", "business", "product"}
    MAX_TEXT_LENGTH = 3000
    MODEL = "gpt-4o-mini"
    
    @staticmethod
    def extract_attributes(text: str) -> List[Dict[str, str]]:
        if not text or len(text.strip()) < 50:
            return []
        
        truncated_text = text[:AttributeExtractor.MAX_TEXT_LENGTH]
        prompt = ATTRIBUTE_EXTRACTION_USER.format(text=truncated_text)
        
        try:
            llm = LLMFactory.get_llm(AttributeExtractor.MODEL)
            
            response = llm.invoke(
                [
                    SystemMessage(content=ATTRIBUTE_EXTRACTION_SYSTEM),
                    HumanMessage(content=prompt)
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.content)
            attributes = result.get("attributes", [])
            
            return AttributeExtractor._validate_attributes(attributes)
            
        except Exception as e:
            print(f"Attribute extraction error: {str(e)}")
            return []
    
    @staticmethod
    def _validate_attributes(attributes: List[Dict]) -> List[Dict[str, str]]:
        valid = []
        for attr in attributes:
            if not isinstance(attr, dict):
                continue
            if not all(k in attr for k in ["key", "value", "category"]):
                continue
            if attr["category"] not in AttributeExtractor.VALID_CATEGORIES:
                continue
            valid.append(attr)
        return valid