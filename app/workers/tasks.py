from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document, ProcessingStatus
from app.models.vector_chunk import VectorChunk as DocumentChunk
from app.models.attribute import Attribute
from app.models.company import Company
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.attribute_extractor import AttributeExtractor
import httpx
import tempfile
import os

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
        
        attributes = AttributeExtractor.extract_attributes(text_content)
        
        for attr_data in attributes:
            try:
                existing = db.query(Attribute).filter(
                    Attribute.company_id == document.company_id,
                    Attribute.key == attr_data["key"]
                ).first()
                
                if existing:
                    existing.value = attr_data["value"]
                    existing.category = attr_data.get("category")
                    existing.source_doc_id = document.id
                else:
                    attribute = Attribute(
                        user_id=document.user_id,
                        company_id=document.company_id,
                        key=attr_data["key"],
                        value=attr_data["value"],
                        category=attr_data.get("category"),
                        source_doc_id=document.id
                    )
                    db.add(attribute)
                
                db.commit()
            except Exception as attr_error:
                db.rollback()
                print(f"Error saving attribute {attr_data.get('key')}: {str(attr_error)}")
                continue
        
        document.processing_status = ProcessingStatus.COMPLETED
        db.commit()
        
        return {"status": "completed", "document_id": str(document_id), "chunks_count": len(chunks)}
    
    except Exception as e:
        db.rollback()
        if document:
            document.processing_status = ProcessingStatus.FAILED
            db.commit()
        return {"error": str(e)}
    
    finally:
        db.close()