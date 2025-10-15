from sqlalchemy.orm import Session
from app.models.attribute import Attribute
from app.services.embedding_service import EmbeddingService
from typing import List, Dict
from uuid import UUID

class AttributeSearchService:
    @staticmethod
    def search_attributes(query: str, company_id: UUID, db: Session, top_k: int = 3) -> List[Dict]:
        query_embedding = EmbeddingService.generate_embedding(query)
        
        all_attributes = db.query(Attribute).filter(
            Attribute.company_id == company_id
        ).all()
        
        if not all_attributes:
            return []
        
        attribute_texts = [f"{attr.key}: {attr.value}" for attr in all_attributes]
        attribute_embeddings = EmbeddingService.generate_embeddings(attribute_texts)
        
        from numpy import dot
        from numpy.linalg import norm
        
        similarities = []
        for i, attr in enumerate(all_attributes):
            similarity = dot(query_embedding, attribute_embeddings[i]) / (
                norm(query_embedding) * norm(attribute_embeddings[i])
            )
            similarities.append({
                "attribute": attr,
                "similarity": float(similarity),
                "text": attribute_texts[i]
            })
        
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return [
            {
                "key": s["attribute"].key,
                "value": s["attribute"].value,
                "category": s["attribute"].category,
                "similarity": s["similarity"]
            }
            for s in similarities[:top_k]
        ]