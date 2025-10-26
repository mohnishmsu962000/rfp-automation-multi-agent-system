from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import razorpay
import hmac
import hashlib
from app.core.config import get_settings
from app.core.database import get_db
from app.models.company import Company
from datetime import datetime

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
settings = get_settings()


def verify_razorpay_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    if not verify_razorpay_signature(payload, signature, settings.RAZORPAY_WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event = await request.json()
    event_type = event.get("event")
    
    if event_type == "subscription.activated":
        subscription = event["payload"]["subscription"]["entity"]
        notes = subscription.get("notes", {})
        company_id = notes.get("company_id")
        
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.subscription_status = "active"
                company.current_period_end = datetime.fromtimestamp(subscription["current_end"])
                db.commit()
    
    elif event_type == "subscription.charged":
        payment = event["payload"]["payment"]["entity"]
        subscription = event["payload"]["subscription"]["entity"]
        notes = subscription.get("notes", {})
        company_id = notes.get("company_id")
        
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.subscription_status = "active"
                company.current_period_end = datetime.fromtimestamp(subscription["current_end"])
                db.commit()
    
    elif event_type == "subscription.cancelled":
        subscription = event["payload"]["subscription"]["entity"]
        notes = subscription.get("notes", {})
        company_id = notes.get("company_id")
        
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.subscription_status = "cancelled"
                db.commit()
    
    elif event_type == "subscription.paused":
        subscription = event["payload"]["subscription"]["entity"]
        notes = subscription.get("notes", {})
        company_id = notes.get("company_id")
        
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.subscription_status = "paused"
                db.commit()
    
    return {"status": "success"}