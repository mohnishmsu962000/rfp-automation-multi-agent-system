from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.document import DocType, ProcessingStatus
from uuid import UUID

class DocumentUpload(BaseModel):
    doc_type: DocType
    tags: Optional[List[str]] = []

class DocumentResponse(BaseModel):
    id: UUID
    user_id: str
    company_id: UUID
    filename: str
    file_url: str
    doc_type: str
    tags: List[str]
    uploaded_at: datetime
    processing_status: str
    
    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    doc_id: Optional[str] = None