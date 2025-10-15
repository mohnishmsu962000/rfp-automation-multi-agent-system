from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents
from app.core.config import get_settings
from app.api.routes import documents, rfps
from app.api.routes import documents, rfps, attributes

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(rfps.router)
app.include_router(attributes.router, prefix="/api/attributes", tags=["attributes"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}