from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
   
    APP_NAME: str = "RFP Generator"
    DEBUG: bool = True
    
 
    DATABASE_URL: str
    
 
    CLERK_SECRET_KEY: str
    
  
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
  
    REDIS_URL: str = "redis://localhost:6379/0"
    
   
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    GOOGLE_API_KEY: str
    
    COHERE_API_KEY: str
    TAVILY_API_KEY: str
    
    LANGCHAIN_API_KEY: str
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_PROJECT: str = "rfp-generator"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()