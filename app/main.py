from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents, rfps, attributes, auth, users, billing, webhooks
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.scalerfp.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(documents.router)
app.include_router(rfps.router)
app.include_router(attributes.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(billing.router)
app.include_router(webhooks.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}