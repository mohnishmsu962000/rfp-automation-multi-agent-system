from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.user_company import UserCompany
from app.models.user import User
from app.core.auth import get_current_user
from app.services.email_service import EmailService
from sqlalchemy.orm import Session
import uuid
import logging
from jwt import PyJWKClient
import jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

class UpdateUserRequest(BaseModel):
    company_name: str
    clerk_organization_id: str
    rfps_per_month: Optional[str] = None
    team_size: Optional[str] = None
    industry: Optional[str] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.patch("/me")
async def update_user(
    request: UpdateUserRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Received company name update request: {request.company_name}")
        
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing authorization")
        
        token = authorization.replace("Bearer ", "")
        
        jwks_url = "https://clerk.scalerfp.com/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True}
        )
        
        user_id = decoded.get("sub")
        email = decoded.get("email", f"{user_id}@temp.local")
        name = decoded.get("name") or decoded.get("first_name", "") or email.split("@")[0]
        
        logger.info(f"User ID: {user_id}, Email: {email}, Name: {name}")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.info(f"Creating new user: {user_id}")
            user = User(
                id=user_id,
                email=email.strip(),
                name=name.strip()
            )
            db.add(user)
            db.commit()
        
        existing_company = db.query(Company).filter(
            Company.clerk_organization_id == request.clerk_organization_id
        ).first()
        
        is_new_company = False
        
        if existing_company:
            logger.info(f"Updating existing company: {existing_company.id}")
            existing_company.name = request.company_name
            company = existing_company
        else:
            logger.info("Creating new company")
            company = Company(
                id=uuid.uuid4(),
                name=request.company_name,
                clerk_organization_id=request.clerk_organization_id
            )
            db.add(company)
            db.flush()
            
            user_company = UserCompany(
                user_id=user_id,
                company_id=company.id,
                role='admin'
            )
            db.add(user_company)
            is_new_company = True
        
        db.commit()
        logger.info("Company saved successfully")
        
        if is_new_company:
            logger.info(f"Sending welcome email to {email}")
            EmailService.send_welcome_email(
                email=email,
                name=name,
                company_name=request.company_name
            )
        
        return {
            "message": "Company created successfully",
            "company_name": company.name,
            "company_id": str(company.id),
            "clerk_organization_id": company.clerk_organization_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_user: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me")
async def get_user(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = current_user["company_id"]
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {
        "user_id": current_user["user_id"],
        "company_id": str(company.id),
        "company_name": company.name
    }