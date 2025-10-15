from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.company import Company
from app.models.user_company import UserCompany
from app.models.user import User
from pydantic import BaseModel
from uuid import UUID

router = APIRouter(prefix="/api/auth", tags=["auth"])

class OnboardingRequest(BaseModel):
    company_name: str
    user_name: str
    user_email: str

class OnboardingResponse(BaseModel):
    company_id: str
    message: str

@router.post("/onboard", response_model=OnboardingResponse)
def onboard_user(
    data: OnboardingRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    
    existing = db.query(UserCompany).filter(UserCompany.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already onboarded")
    
    company = Company(name=data.company_name)
    db.add(company)
    db.flush()
    
    user = User(
        id=user_id,
        name=data.user_name,
        email=data.user_email
    )
    db.add(user)
    
    user_company = UserCompany(
        user_id=user_id,
        company_id=company.id
    )
    db.add(user_company)
    
    db.commit()
    
    return {
        "company_id": str(company.id),
        "message": "Onboarding successful"
    }

@router.get("/me")
def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user["user_id"]
    company_id = current_user["company_id"]
    
    user = db.query(User).filter(User.id == user_id).first()
    company = db.query(Company).filter(Company.id == company_id).first()
    
    return {
        "user_id": user_id,
        "user_name": user.name if user else None,
        "user_email": user.email if user else None,
        "company_id": company_id,
        "company_name": company.name if company else None
    }