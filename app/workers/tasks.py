from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, ProcessingStatus
from app.models.vector_chunk import VectorChunk
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.storage import StorageService
from app.services.attribute_extractor import AttributeExtractor
from app.agents.kb_manager import run_kb_manager
import httpx
import tempfile
import os
from app.workers.rfp_tasks import process_rfp_task

@celery_app.task(name="process_document")
def process_document_task(doc_id: str):
    db = SessionLocal()
    
    try:
        document = db.query(Document).filter(Document.id == doc_id).first()
        if not document:
            return {"error": "Document not found"}
        
        document.processing_status = ProcessingStatus.PROCESSING
        db.commit()
        
        response = httpx.get(document.file_url)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(document.filename)[1]) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        text = DocumentProcessor.extract_text(tmp_path, document.filename)
        os.unlink(tmp_path)
        
        chunks = DocumentProcessor.chunk_text(text)
        
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = EmbeddingService.generate_embeddings(chunk_texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            vector_chunk = VectorChunk(
                doc_id=document.id,
                chunk_text=chunk["text"],
                embedding=embedding,
                chunk_index=chunk["index"],
                chunk_metadata=chunk["metadata"]
            )
            db.add(vector_chunk)
        
        attributes = AttributeExtractor.extract_attributes(text)
        
        new_attrs = [
            {
                "key": attr["key"],
                "value": attr["value"],
                "category": attr["category"],
                "source_doc_id": str(document.id)
            }
            for attr in attributes
        ]
        
        kb_stats = run_kb_manager(document.user_id, new_attrs)
        
        document.processing_status = ProcessingStatus.COMPLETED
        db.commit()
        
        return {
            "status": "completed", 
            "doc_id": str(doc_id),
            "attributes_extracted": len(attributes),
            "kb_stats": kb_stats
        }
    
    except Exception as e:
        document.processing_status = ProcessingStatus.FAILED
        db.commit()
        return {"error": str(e)}
    
    finally:
        db.close()