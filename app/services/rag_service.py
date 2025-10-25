from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.vector_chunk import VectorChunk
from app.models.document import Document
from app.services.embedding_service import EmbeddingService
from typing import List, Dict
from rank_bm25 import BM25Okapi
from app.core.config import get_settings
from uuid import UUID
import cohere
import logging
import numpy as np

settings = get_settings()
logger = logging.getLogger(__name__)

class RAGService:
    @staticmethod
    def search_similar_chunks(query: str, db: Session, company_id: UUID, top_k: int = 5) -> List[Dict]:
        logger.info(f"RAG search called with company_id: {company_id}, query: {query[:100]}")
        
        all_chunks = db.query(VectorChunk).join(Document).filter(
            Document.company_id == company_id
        ).all()
        
        logger.info(f"Found {len(all_chunks)} chunks in database for company {company_id}")
        
        if not all_chunks:
            logger.warning(f"No chunks found for company {company_id}")
            return []
        
        query_embedding = EmbeddingService.generate_embedding(query)
        logger.info(f"Generated query embedding, length: {len(query_embedding)}")
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        vector_scores = []
        for chunk in all_chunks:
            if chunk.embedding is None:
                logger.warning(f"Chunk {chunk.id} has NULL embedding, skipping")
                continue
            similarity = cosine_similarity(query_embedding, chunk.embedding)
            vector_scores.append((chunk, float(similarity)))
        
        logger.info(f"Calculated similarities for {len(vector_scores)} chunks")
        
        vector_results = sorted(vector_scores, key=lambda x: x[1], reverse=True)[:top_k * 3]
        
        logger.info(f"Vector search returned {len(vector_results)} results, top score: {vector_results[0][1] if vector_results else 0}")
        
        corpus = [chunk.chunk_text for chunk in all_chunks]
        tokenized_corpus = [doc.split() for doc in corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        
        tokenized_query = query.split()
        bm25_scores = bm25.get_scores(tokenized_query)
        
        bm25_results = sorted(
            zip(all_chunks, bm25_scores),
            key=lambda x: x[1],
            reverse=True
        )[:top_k * 3]
        
        combined_chunks = {}
        for chunk, score in vector_results:
            combined_chunks[str(chunk.id)] = {
                "id": str(chunk.id),
                "text": chunk.chunk_text,
                "metadata": chunk.chunk_metadata,
                "vector_score": float(score),
                "bm25_score": 0.0
            }
        
        for chunk, score in bm25_results:
            chunk_id = str(chunk.id)
            if chunk_id in combined_chunks:
                combined_chunks[chunk_id]["bm25_score"] = float(score)
            else:
                combined_chunks[chunk_id] = {
                    "id": chunk_id,
                    "text": chunk.chunk_text,
                    "metadata": chunk.chunk_metadata,
                    "vector_score": 0.0,
                    "bm25_score": float(score)
                }
        
        hybrid_results = []
        for chunk_id, data in combined_chunks.items():
            hybrid_score = float(data["vector_score"] * 0.7 + (data["bm25_score"] / 10) * 0.3)
            data["hybrid_score"] = hybrid_score
            hybrid_results.append(data)
        
        hybrid_results = sorted(
            hybrid_results,
            key=lambda x: x["hybrid_score"],
            reverse=True
        )[:top_k * 2]
        
        logger.info(f"Hybrid search returned {len(hybrid_results)} results")
        
        if not hybrid_results:
            logger.warning("No hybrid results after combining vector and BM25")
            return []
        
        try:
            co = cohere.Client(settings.COHERE_API_KEY)
            
            documents = [r["text"] for r in hybrid_results]
            
            rerank_response = co.rerank(
                model="rerank-english-v3.0",
                query=query,
                documents=documents,
                top_n=top_k,
                return_documents=True
            )
            
            reranked_results = []
            for result in rerank_response.results:
                original_data = hybrid_results[result.index]
                reranked_results.append({
                    "id": original_data["id"],
                    "text": original_data["text"],
                    "metadata": original_data["metadata"],
                    "vector_score": original_data["vector_score"],
                    "bm25_score": original_data["bm25_score"],
                    "hybrid_score": original_data["hybrid_score"],
                    "rerank_score": float(result.relevance_score)
                })
            
            logger.info(f"Reranked {len(reranked_results)} chunks, top rerank score: {reranked_results[0]['rerank_score'] if reranked_results else 0}")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Cohere reranking failed: {str(e)}, using hybrid scores")
            
            for r in hybrid_results[:top_k]:
                r["rerank_score"] = r["hybrid_score"]
            
            return hybrid_results[:top_k]