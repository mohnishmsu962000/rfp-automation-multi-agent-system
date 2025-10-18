from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents, rfps, attributes, auth
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(documents.router)
app.include_router(rfps.router)
app.include_router(attributes.router, prefix="/api/attributes", tags=["attributes"])
app.include_router(auth.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}