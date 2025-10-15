from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.attribute import Attribute
from app.api.schemas.attribute import AttributeResponse, AttributeUpdate
from uuid import UUID
import uuid

router = APIRouter(prefix="/api/attributes", tags=["attributes"])

@router.get("/", response_model=List[AttributeResponse])
def get_attributes(
    search: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = uuid.UUID(current_user["company_id"])
    
    query = db.query(Attribute).filter(Attribute.company_id == company_id)
    
    if search:
        query = query.filter(
            (Attribute.key.ilike(f"%{search}%")) | 
            (Attribute.value.ilike(f"%{search}%"))
        )
    
    if category:
        query = query.filter(Attribute.category == category)
    
    attributes = query.all()
    return attributes

@router.get("/{attribute_id}", response_model=AttributeResponse)
def get_attribute(
    attribute_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = uuid.UUID(current_user["company_id"])
    
    attribute = db.query(Attribute).filter(
        Attribute.id == attribute_id,
        Attribute.company_id == company_id
    ).first()
    
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    return attribute

@router.patch("/{attribute_id}", response_model=AttributeResponse)
def update_attribute(
    attribute_id: UUID,
    data: AttributeUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = uuid.UUID(current_user["company_id"])
    
    attribute = db.query(Attribute).filter(
        Attribute.id == attribute_id,
        Attribute.company_id == company_id
    ).first()
    
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    if data.value is not None:
        attribute.value = data.value
    if data.category is not None:
        attribute.category = data.category
    
    db.commit()
    db.refresh(attribute)
    
    return attribute

@router.delete("/{attribute_id}")
def delete_attribute(
    attribute_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = uuid.UUID(current_user["company_id"])
    
    attribute = db.query(Attribute).filter(
        Attribute.id == attribute_id,
        Attribute.company_id == company_id
    ).first()
    
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    db.delete(attribute)
    db.commit()
    
    return {"success": True, "message": "Attribute deleted"}