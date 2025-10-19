from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, ProcessingStatus
from app.models.vector_chunk import VectorChunk as DocumentChunk
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.attribute_extractor import AttributeExtractor
from app.agents.kb_manager import run_kb_manager
import httpx
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="process_document")
def process_document_task(document_id: str):
    db = SessionLocal()
    document = None
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": "Document not found"}
        
        document.processing_status = ProcessingStatus.PROCESSING
        db.commit()
        
        response = httpx.get(document.file_url)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(document.filename)[1]) as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        text_content = DocumentProcessor.extract_text(tmp_path, document.filename)
        os.unlink(tmp_path)
        
        chunks = DocumentProcessor.chunk_text(text_content)
        
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = EmbeddingService.generate_embeddings(chunk_texts)
        
        for i, chunk in enumerate(chunks):
            doc_chunk = DocumentChunk(
                doc_id=document.id,
                chunk_index=i,
                chunk_text=chunk["text"],
                embedding=embeddings[i],
                chunk_metadata=chunk["metadata"]
            )
            db.add(doc_chunk)
        
        db.commit()
        
        logger.info(f"Extracting attributes from document {document.id}")
        attributes = AttributeExtractor.extract_attributes(text_content)
        logger.info(f"Extracted {len(attributes)} raw attributes")
        
        if attributes:
            new_attrs = [
                {
                    "key": attr["key"],
                    "value": attr["value"],
                    "category": attr["category"],
                    "source_doc_id": str(document.id)
                }
                for attr in attributes
            ]
            
            kb_stats = run_kb_manager(document.user_id, document.company_id, new_attrs)
            logger.info(f"KB Manager processed attributes: {kb_stats}")
        else:
            kb_stats = {"new_added": 0}
        
        document.processing_status = ProcessingStatus.COMPLETED
        db.commit()
        
        return {
            "status": "completed",
            "document_id": str(document_id),
            "chunks_count": len(chunks),
            "attributes_stats": kb_stats
        }
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing document {document_id}: {str(e)}")
        if document:
            document.processing_status = ProcessingStatus.FAILED
            db.commit()
        return {"error": str(e)}
    
    finally:
        db.close()