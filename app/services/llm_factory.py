from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings

settings = get_settings()

class LLMFactory:
    @staticmethod
    def get_llm(model_type: str):
        if model_type == "gpt-4o-mini":
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=settings.OPENAI_API_KEY
            )
        elif model_type == "claude-sonnet":
            return ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=0,
                api_key=settings.ANTHROPIC_API_KEY
            )
        elif model_type == "gemini-flash":
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=0,
                google_api_key=settings.GOOGLE_API_KEY
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")