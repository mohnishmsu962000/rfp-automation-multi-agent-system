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

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    tags: str = Form(""),
    #current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    file_content = await file.read()
    file_url = StorageService.upload_file(file_content, file.filename)
    
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    document = Document(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        filename=file.filename,
        file_url=file_url,
        doc_type=DocType(doc_type),
        tags=tag_list,
        processing_status=ProcessingStatus.PENDING
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    process_document_task.delay(str(document.id))
    
    job_id = f"doc_{document.id}"
    
    return {
        "success": True,
        "message": "Document upload started",
        "job_id": job_id
    }

@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    #current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    documents = db.query(Document).filter(
        Document.user_id == "550e8400-e29b-41d4-a716-446655440000"
    ).all()
    return documents

@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: str,
    #current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == "550e8400-e29b-41d4-a716-446655440000"
    ).first()
    
    if not document:
        raise APIError(status_code=404, message="Document not found")
    
    return document

@router.delete("/{doc_id}")
def delete_document(
    doc_id: str,
    #current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == doc_id,
        Document.user_id == "550e8400-e29b-41d4-a716-446655440000"
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
    db: Session = Depends(get_db)
):
    from uuid import UUID
    HARDCODED_USER_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
    result = generate_answer_for_question(question, db, HARDCODED_USER_ID)
    return result