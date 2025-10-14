from typing import Any, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse

class APIError(HTTPException):
   
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Any] = None
    ):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail=message)

class APIResponse:
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200
    ):
        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def error(
        message: str,
        status_code: int = 400,
        details: Any = None
    ):
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": message,
                "details": details
            }
        )