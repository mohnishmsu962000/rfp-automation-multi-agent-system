from fastapi import HTTPException, Header
from typing import Optional
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.company import Company
import jwt
from jwt import PyJWKClient
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

async def get_current_user(authorization: Optional[str] = Header(None)):
    logger.info("=== AUTH START ===")
    logger.info(f"Authorization header present: {authorization is not None}")
    
    if not authorization or not authorization.startswith("Bearer "):
        logger.error("Missing or invalid authorization header")
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    logger.info(f"Token extracted, length: {len(token)}")
    
    try:
        jwks_url = "https://clerk.scalerfp.com/.well-known/jwks.json"
        
        jwks_client = PyJWKClient(jwks_url)
        import jwt
        header = jwt.get_unverified_header(token)
        logger.info(f"JWT Header: {header}")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True}
        )
        
        logger.info(f"FULL TOKEN: {decoded}")
        logger.info(f"org_id in token: {decoded.get('org_id')}")
        logger.info(f"org_role in token: {decoded.get('org_role')}")
        
        user_id = decoded.get("sub")
        org_id = decoded.get("org_id")
        org_role = decoded.get("org_role")
        
        logger.info(f"User: {user_id}, Org: {org_id}, Role: {org_role}")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        if not org_id:
            logger.error(f"No org_id in token for user {user_id}")
            raise HTTPException(status_code=403, detail="User not in any organization. Please complete onboarding.")
        
        db = SessionLocal()
        try:
            company = db.query(Company).filter(
                Company.clerk_organization_id == org_id
            ).first()
            
            if not company:
                logger.warning(f"No company found for org_id: {org_id}")
                raise HTTPException(status_code=404, detail="Company not found for organization")
            
            logger.info(f"Found company {company.id} for org {org_id}")
            
            return {
                "user_id": user_id,
                "company_id": str(company.id),
                "org_id": org_id,
                "role": org_role,
                "email": decoded.get("email", "noemail@example.com")
            }
        finally:
            db.close()
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")