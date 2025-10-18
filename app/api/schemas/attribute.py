from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class AttributeCreate(BaseModel):
    key: str
    value: str
    category: Optional[str] = None

class AttributeUpdate(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    category: Optional[str] = None

class AttributeResponse(BaseModel):
    id: UUID
    user_id: str
    company_id: UUID
    key: str
    value: str
    category: Optional[str] = None
    
    class Config:
        from_attributes = True