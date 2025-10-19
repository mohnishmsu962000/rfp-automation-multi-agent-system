from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.document import Document
from app.models.attribute import Attribute
from app.models.resync_quota import ResyncQuota
from app.services.document_processor import DocumentProcessor
from app.services.attribute_extractor import AttributeExtractor
from app.agents.kb_manager import run_kb_manager
from datetime import datetime
import httpx
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="resync_attributes")
def resync_attributes_task(user_id: str, company_id: str):
    db = SessionLocal()
    
    try:
        db.query(Attribute).filter(
            Attribute.user_id == user_id,
            Attribute.company_id == company_id
        ).delete()
        db.commit()
        
        documents = db.query(Document).filter(
            Document.user_id == user_id,
            Document.company_id == company_id
        ).all()
        
        total_attributes = 0
        
        for doc in documents:
            try:
                response = httpx.get(doc.file_url)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(doc.filename)[1]) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                text = DocumentProcessor.extract_text(tmp_path, doc.filename)
                os.unlink(tmp_path)
                
                attributes = AttributeExtractor.extract_attributes(text)
                
                if attributes:
                    new_attrs = [
                        {
                            "key": attr["key"],
                            "value": attr["value"],
                            "category": attr["category"],
                            "source_doc_id": str(doc.id)
                        }
                        for attr in attributes
                    ]
                    
                    kb_stats = run_kb_manager(doc.user_id, doc.company_id, new_attrs)
                    total_attributes += kb_stats.get("new_added", 0)
                
            except Exception as e:
                logger.error(f"Error processing document {doc.id}: {str(e)}")
                continue
        
        month_year = datetime.utcnow().strftime("%Y-%m")
        quota = db.query(ResyncQuota).filter(
            ResyncQuota.user_id == user_id,
            ResyncQuota.month_year == month_year
        ).first()
        
        if quota:
            quota.resync_count += 1
            quota.last_resync_at = datetime.utcnow()
        else:
            quota = ResyncQuota(
                user_id=user_id,
                month_year=month_year,
                resync_count=1,
                last_resync_at=datetime.utcnow()
            )
            db.add(quota)
        
        db.commit()
        
        return {
            "status": "completed",
            "documents_processed": len(documents),
            "total_attributes": total_attributes
        }
        
    except Exception as e:
        logger.error(f"Resync error: {str(e)}")
        return {"error": str(e)}
    
    finally:
        db.close()