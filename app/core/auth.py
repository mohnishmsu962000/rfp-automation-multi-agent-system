from fastapi import Request, HTTPException, Header
from typing import Optional
from app.core.config import get_settings
import httpx

settings = get_settings()

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.clerk.com/v1/sessions/{token}/verify",
                headers={"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            session_data = response.json()
            return {
                "user_id": session_data.get("user_id"),
                "session_id": session_data.get("id")
            }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")