from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.errors import APIResponse, APIError
from app.models.document import Document, DocType, ProcessingStatus
from app.api.schemas.document import DocumentResponse, JobStatusResponse
from app.services.storage import StorageService
import uuid
from app.workers.tasks import process_document_task
from app.agents.answer_generator import generate_answer_for_question
from app.services.rate_limiter import RateLimiter

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.get("/usage")
def get_usage_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = uuid.UUID(current_user["company_id"])
    return RateLimiter.get_usage_stats(company_id, db)

@router.post("/", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    tags: str = Form(""),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    company_id = uuid.UUID(current_user["company_id"])
    
    allowed, used, remaining = RateLimiter.check_document_quota(company_id, db)
    
    if not allowed:
        raise APIError(
            status_code=429,
            message=f"Document upload limit reached. You have uploaded {used}/100 documents (lifetime limit)."
        )
    
    file_content = await file.read()
    file_url = StorageService.upload_file(file_content, file.filename)
    
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    document = Document(
        user_id=user_id,
        company_id=company_id,
        filename=file.filename,
        file_url=file_url,
        doc_type=doc_type.upper(),
        tags=tag_list,
        processing_status=ProcessingStatus.PENDING
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    RateLimiter.increment_document_quota(company_id, db)
    
    process_document_task.delay(str(document.id))
    
    job_id = f"doc_{document.id}"
    
    return {
        "success": True,
        "message": f"Document upload started. {remaining - 1} uploads remaining.",
        "job_id": job_id
    }

@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = uuid.UUID(current_user["company_id"])
    
    documents = db.query(Document).filter(
        Document.company_id == company_id
    ).all()
    return documents

@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = uuid.UUID(current_user["company_id"])
    
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.company_id == company_id
    ).first()
    
    if not document:
        raise APIError(status_code=404, message="Document not found")
    
    return document

@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = uuid.UUID(current_user["company_id"])
    
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.company_id == company_id
    ).first()
    
    if not document:
        raise APIError(status_code=404, message="Document not found")
    
    StorageService.delete_file(document.file_url)
    db.delete(document)
    db.commit()
    
    return {"success": True, "message": "Document deleted"}

@router.post("/test-answer")
def test_answer_generation(
    question: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    result = generate_answer_for_question(question, db, user_id)
    return result