from langchain_openai import OpenAIEmbeddings
from app.core.config import get_settings
from typing import List

settings = get_settings()
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=settings.OPENAI_API_KEY
)

class EmbeddingService:
    @staticmethod
    def generate_embeddings(texts: List[str]) -> List[List[float]]:
        return embeddings.embed_documents(texts)
    
    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        return embeddings.embed_query(text)