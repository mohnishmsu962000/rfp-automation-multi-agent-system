from fastapi import HTTPException, Header
from typing import Optional
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.user_company import UserCompany
import jwt
from jwt import PyJWKClient
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
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
        logger.info(f"Checking user company for user_id: {user_id}")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        db = SessionLocal()
        try:
            db.expire_all()
            
            user_company = db.query(UserCompany).filter(
                UserCompany.user_id == user_id
            ).first()
            
            if not user_company:
                logger.warning(f"No company found for user: {user_id}")
                raise HTTPException(status_code=403, detail="User not associated with any company")
            
            logger.info(f"Found company {user_company.company_id} for user {user_id}")
            
            return {
                "user_id": user_id,
                "company_id": str(user_company.company_id),
            }
        finally:
            db.close()
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")