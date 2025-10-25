from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.user_company import UserCompany
from app.models.user import User
from app.api.routes.auth import get_current_user
from sqlalchemy.orm import Session
import uuid
from fastapi import Header

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
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        from jwt import PyJWKClient
        import jwt
        
        jwks_url = "https://helping-grizzly-76.clerk.accounts.dev/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True}
        )
        
        user_id = decoded.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # Create user
            user = User(id=user_id)
            db.add(user)
            db.commit()
        
        user_company = db.query(UserCompany).filter(
            UserCompany.user_id == user_id
        ).first()
        
        if user_company:
            company = db.query(Company).filter(Company.id == user_company.company_id).first()
            company.name = request.company_name
        else:
            company = Company(
                id=uuid.uuid4(),
                name=request.company_name
            )
            db.add(company)
            db.flush()
            
            user_company = UserCompany(
                user_id=user_id,
                company_id=company.id
            )
            db.add(user_company)
        
        db.commit()
        
        return {
            "message": "Company created successfully",
            "company_name": company.name,
            "company_id": str(company.id)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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