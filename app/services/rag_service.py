from sqlalchemy.orm import Session
from app.models.vector_chunk import VectorChunk
from app.services.embedding_service import EmbeddingService
from typing import List, Dict
from rank_bm25 import BM25Okapi
from app.core.config import get_settings

settings = get_settings()

class RAGService:
    @staticmethod
    def search_similar_chunks(query: str, db: Session, top_k: int = 5) -> List[Dict]:
        all_chunks = db.query(VectorChunk).all()
        
        query_embedding = EmbeddingService.generate_embedding(query)
        
        vector_results = db.query(
            VectorChunk.id,
            VectorChunk.chunk_text,
            VectorChunk.chunk_metadata,
            VectorChunk.embedding.cosine_distance(query_embedding).label("distance")
        ).order_by("distance").limit(top_k * 2).all()
        
        corpus = [chunk.chunk_text for chunk in all_chunks]
        tokenized_corpus = [doc.split() for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        
        tokenized_query = query.split()
        bm25_scores = bm25.get_scores(tokenized_query)
        
        bm25_results = sorted(
            zip(all_chunks, bm25_scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k * 2]
        
        combined_chunks = {}
        for result in vector_results:
            combined_chunks[str(result.id)] = {
                "text": result.chunk_text,
                "metadata": result.chunk_metadata,
                "vector_score": float(1 - result.distance),
                "bm25_score": 0.0
            }
        
        for chunk, score in bm25_results:
            chunk_id = str(chunk.id)
            if chunk_id in combined_chunks:
                combined_chunks[chunk_id]["bm25_score"] = float(score)
            else:
                combined_chunks[chunk_id] = {
                    "text": chunk.chunk_text,
                    "metadata": chunk.chunk_metadata,
                    "vector_score": 0.0,
                    "bm25_score": float(score)
                }
        
        combined_list = []
        for chunk_id, data in combined_chunks.items():
            hybrid_score = float(data["vector_score"] + (data["bm25_score"] / 10))
            data["rerank_score"] = hybrid_score
            combined_list.append(data)
        
        final_results = sorted(
            combined_list,
            key=lambda x: x["rerank_score"],
            reverse=True
        )[:top_k]
        
        return final_results