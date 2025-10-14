from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from clerk_backend_api import Clerk
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()

clerk_client = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = security
):
   
    try:
        token = credentials.credentials
        
        session = clerk_client.sessions.verify_token(token)
        
        if not session or not session.user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        
        return {
            "user_id": session.user_id,
            "session_id": session.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )