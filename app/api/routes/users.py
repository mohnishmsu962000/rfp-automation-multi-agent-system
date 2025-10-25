from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.database import SessionLocal
from app.models.company import Company
from app.api.routes.auth import get_current_user
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/users", tags=["users"])

class UpdateUserRequest(BaseModel):
    company_name: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.patch("/me")
async def update_user(
    request: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's company name"""
    company_id = current_user["company_id"]
    
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
   
    company.name = request.company_name
    db.commit()
    db.refresh(company)
    
    return {
        "message": "Company name updated successfully",
        "company_name": company.name
    }

@router.get("/me")
async def get_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user and company info"""
    company_id = current_user["company_id"]
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "user_id": current_user["user_id"],
        "company_id": str(company.id),
        "company_name": company.name
    }