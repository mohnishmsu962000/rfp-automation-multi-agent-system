from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings

settings = get_settings()

class LLMFactory:
    
    AVAILABLE_MODELS = {
        "claude-opus-4.1": "Most powerful Claude model",
        "claude-sonnet-4.5": "Best balanced Claude model",
        "claude-sonnet-4": "Previous generation Claude",
        "claude-haiku-4": "Fastest/cheapest Claude",
        "gpt-4o": "Most capable OpenAI model",
        "gpt-4o-mini": "Balanced OpenAI model",
        "o1-preview": "Advanced reasoning model",
        "o1-mini": "Faster reasoning model",
        "gemini-2.0-flash": "Fastest Google model",
        "gemini-1.5-pro": "Most powerful Google model",
    }
    
    MODEL_ALIASES = {
        "gemini-flash": "gemini-2.0-flash",
        "claude-sonnet": "claude-sonnet-4.5",
        "gpt-4o-mini": "gpt-4o-mini",
    }
    
    @staticmethod
    def get_llm(model_type: str, temperature: float = 0):
        if model_type in LLMFactory.MODEL_ALIASES:
            model_type = LLMFactory.MODEL_ALIASES[model_type]
        
        if model_type == "claude-opus-4.1":
            return ChatAnthropic(
                model="claude-opus-4-20250514",
                temperature=temperature,
                api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=8192
            )
        
        elif model_type == "claude-sonnet-4.5":
            return ChatAnthropic(
                model="claude-sonnet-4-5-20250929",
                temperature=temperature,
                api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=8192
            )
        
        elif model_type == "claude-sonnet-4":
            return ChatAnthropic(
                model="claude-sonnet-4-20250514",
                temperature=temperature,
                api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=8192
            )
        
        elif model_type == "claude-haiku-4":
            return ChatAnthropic(
                model="claude-haiku-4-20250514",
                temperature=temperature,
                api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=8192
            )
        
        elif model_type == "gpt-4o":
            return ChatOpenAI(
                model="gpt-4o",
                temperature=temperature,
                api_key=settings.OPENAI_API_KEY,
                max_tokens=8192
            )
        
        elif model_type == "gpt-4o-mini":
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=temperature,
                api_key=settings.OPENAI_API_KEY,
                max_tokens=8192
            )
        
        elif model_type == "o1-preview":
            return ChatOpenAI(
                model="o1-preview",
                temperature=1,
                api_key=settings.OPENAI_API_KEY,
                max_completion_tokens=8192
            )
        
        elif model_type == "o1-mini":
            return ChatOpenAI(
                model="o1-mini",
                temperature=1,
                api_key=settings.OPENAI_API_KEY,
                max_completion_tokens=8192
            )
        
        elif model_type == "gemini-2.0-flash":
            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                temperature=temperature,
                google_api_key=settings.GOOGLE_API_KEY,
                max_tokens=8192
            )
        
        elif model_type == "gemini-1.5-pro":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                temperature=temperature,
                google_api_key=settings.GOOGLE_API_KEY,
                max_tokens=8192
            )
        
        else:
            raise ValueError(
                f"Unknown model type: {model_type}. "
                f"Available models: {', '.join(LLMFactory.AVAILABLE_MODELS.keys())}"
            )
    
    @staticmethod
    def get_recommended_model(task: str) -> str:
        recommendations = {
            "question_extraction": "gemini-2.0-flash",
            "answer_generation": "claude-sonnet-4.5",
            "answer_rephrase": "gpt-4o-mini",
            "trust_scoring": "claude-haiku-4",
            "complex_analysis": "claude-opus-4.1",
            "reasoning": "o1-mini",
        }
        
        return recommendations.get(task, "claude-sonnet-4.5")
    
    @staticmethod
    def list_models():
        return LLMFactory.AVAILABLE_MODELS