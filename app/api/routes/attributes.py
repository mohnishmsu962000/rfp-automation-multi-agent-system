from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.attribute import Attribute
from app.api.schemas.attribute import AttributeResponse, AttributeCreate, AttributeUpdate
from typing import List, Optional
from uuid import UUID

router = APIRouter()

HARDCODED_USER_ID = "550e8400-e29b-41d4-a716-446655440000"

@router.get("", response_model=List[AttributeResponse])
def list_attributes(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Attribute).filter(Attribute.user_id == HARDCODED_USER_ID)
    
    if category:
        query = query.filter(Attribute.category == category)
    
    if search:
        query = query.filter(
            (Attribute.key.ilike(f"%{search}%")) | 
            (Attribute.value.ilike(f"%{search}%"))
        )
    
    return query.order_by(Attribute.last_updated.desc()).all()

@router.get("/{attribute_id}", response_model=AttributeResponse)
def get_attribute(
    attribute_id: UUID,
    db: Session = Depends(get_db)
):
    attr = db.query(Attribute).filter(
        Attribute.id == attribute_id,
        Attribute.user_id == HARDCODED_USER_ID
    ).first()
    
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    return attr

@router.post("", response_model=AttributeResponse)
def create_attribute(
    data: AttributeCreate,
    db: Session = Depends(get_db)
):
    attr = Attribute(
        user_id=HARDCODED_USER_ID,
        key=data.key,
        value=data.value,
        category=data.category
    )
    db.add(attr)
    db.commit()
    db.refresh(attr)
    return attr

@router.patch("/{attribute_id}", response_model=AttributeResponse)
def update_attribute(
    attribute_id: UUID,
    data: AttributeUpdate,
    db: Session = Depends(get_db)
):
    attr = db.query(Attribute).filter(
        Attribute.id == attribute_id,
        Attribute.user_id == HARDCODED_USER_ID
    ).first()
    
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    if data.key is not None:
        attr.key = data.key
    if data.value is not None:
        attr.value = data.value
    if data.category is not None:
        attr.category = data.category
    
    db.commit()
    db.refresh(attr)
    return attr

@router.delete("/{attribute_id}")
def delete_attribute(
    attribute_id: UUID,
    db: Session = Depends(get_db)
):
    attr = db.query(Attribute).filter(
        Attribute.id == attribute_id,
        Attribute.user_id == HARDCODED_USER_ID
    ).first()
    
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found")
    
    db.delete(attr)
    db.commit()
    return {"message": "Attribute deleted"}