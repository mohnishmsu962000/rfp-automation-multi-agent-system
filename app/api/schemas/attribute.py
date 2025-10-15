from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class AttributeCreate(BaseModel):
    key: str
    value: str
    category: str

class AttributeUpdate(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    category: Optional[str] = None

class AttributeResponse(BaseModel):
    id: UUID
    user_id: UUID
    key: str
    value: str
    category: str
    source_doc_id: Optional[UUID]
    last_updated: datetime
    
    class Config:
        from_attributes = True