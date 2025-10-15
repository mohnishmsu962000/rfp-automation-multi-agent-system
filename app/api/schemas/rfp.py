from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class RFPProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    rfp_name: str
    rfp_file_url: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RFPQuestionResponse(BaseModel):
    id: UUID
    project_id: UUID
    question_text: str
    answer_text: Optional[str]
    trust_score: float
    source_type: Optional[str]
    user_edited: bool
    
    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None
    rfp_id: Optional[str] = None
    
    
class QuestionUpdate(BaseModel):
    answer_text: str
    
class RephraseRequest(BaseModel):
    instruction: str