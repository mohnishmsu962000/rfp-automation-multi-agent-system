from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.attribute import Attribute
from app.models.resync_quota import ResyncQuota
from app.api.schemas.attribute import AttributeResponse, AttributeCreate, AttributeUpdate, ResyncResponse, QuotaResponse
from app.workers.attribute_tasks import resync_attributes_task
from typing import List, Optional
from uuid import UUID
from datetime import datetime

router = APIRouter()

HARDCODED_USER_ID = "550e8400-e29b-41d4-a716-446655440000"

@router.get("/quota", response_model=QuotaResponse)
def get_resync_quota(db: Session = Depends(get_db)):
    month_year = datetime.utcnow().strftime("%Y-%m")
    
    quota = db.query(ResyncQuota).filter(
        ResyncQuota.user_id == HARDCODED_USER_ID,
        ResyncQuota.month_year == month_year
    ).first()
    
    resyncs_used = quota.resync_count if quota else 0
    
    return QuotaResponse(
        month_year=month_year,
        resyncs_used=resyncs_used,
        resyncs_remaining=2 - resyncs_used,
        last_resync_at=quota.last_resync_at if quota else None
    )

@router.post("/resync", response_model=ResyncResponse)
def resync_attributes(db: Session = Depends(get_db)):
    month_year = datetime.utcnow().strftime("%Y-%m")
    
    quota = db.query(ResyncQuota).filter(
        ResyncQuota.user_id == HARDCODED_USER_ID,
        ResyncQuota.month_year == month_year
    ).first()
    
    resyncs_used = quota.resync_count if quota else 0
    
    if resyncs_used >= 2:
        raise HTTPException(
            status_code=429,
            detail="Monthly resync quota exceeded. Limit is 2 resyncs per month."
        )
    
    task = resync_attributes_task.delay(str(HARDCODED_USER_ID))
    
    return ResyncResponse(
        job_id=task.id,
        message=f"Resync started. {2 - resyncs_used - 1} resyncs remaining this month."
    )

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