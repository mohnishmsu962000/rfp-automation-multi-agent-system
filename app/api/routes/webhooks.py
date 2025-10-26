from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import razorpay
import hmac
import hashlib
from app.core.config import get_settings
from app.core.database import get_db
from app.models.company import Company
from app.models.user import User
from app.models.user_company import UserCompany
from app.services.email_service import EmailService
from app.core.plans import get_plan_config
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


def get_admin_email(company_id: str, db: Session):
    user_company = db.query(UserCompany).filter(
        UserCompany.company_id == company_id,
        UserCompany.role == 'admin'
    ).first()
    
    if user_company:
        user = db.query(User).filter(User.id == user_company.user_id).first()
        if user:
            return user.email, user.name or user.email.split('@')[0]
    return None, None


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
                old_tier = company.subscription_tier
                company.subscription_status = "active"
                company.current_period_end = datetime.fromtimestamp(subscription["current_end"])
                db.commit()
                
                email, name = get_admin_email(company_id, db)
                if email:
                    plan_config = get_plan_config(company.subscription_tier)
                    EmailService.send_subscription_activated(
                        email=email,
                        name=name,
                        plan_name=plan_config['name'],
                        price=plan_config['price']
                    )
    
    elif event_type == "subscription.charged":
        payment = event["payload"]["payment"]["entity"]
        subscription = event["payload"]["subscription"]["entity"]
        notes = subscription.get("notes", {})
        company_id = notes.get("company_id")
        
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                old_tier = company.subscription_tier
                company.subscription_status = "active"
                company.current_period_end = datetime.fromtimestamp(subscription["current_end"])
                
                plan_id = subscription.get("plan_id")
                new_tier = None
                
                if plan_id == settings.RAZORPAY_STARTER_PLAN_ID:
                    new_tier = "starter"
                elif plan_id == settings.RAZORPAY_GROWTH_PLAN_ID:
                    new_tier = "growth"
                elif plan_id == settings.RAZORPAY_PRO_PLAN_ID:
                    new_tier = "pro"
                
                if new_tier and new_tier != old_tier:
                    company.subscription_tier = new_tier
                    db.commit()
                    
                    email, name = get_admin_email(company_id, db)
                    if email:
                        old_plan = get_plan_config(old_tier)
                        new_plan = get_plan_config(new_tier)
                        EmailService.send_subscription_upgraded(
                            email=email,
                            name=name,
                            old_plan=old_plan['name'],
                            new_plan=new_plan['name'],
                            new_price=new_plan['price'],
                            rfp_limit=new_plan['rfp_limit'],
                            doc_limit=new_plan['doc_limit']
                        )
                else:
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
                
                email, name = get_admin_email(company_id, db)
                if email:
                    plan_config = get_plan_config(company.subscription_tier)
                    end_date = company.current_period_end.strftime("%B %d, %Y") if company.current_period_end else "end of billing period"
                    EmailService.send_subscription_cancelled(
                        email=email,
                        name=name,
                        plan_name=plan_config['name'],
                        end_date=end_date
                    )
    
    elif event_type == "subscription.paused":
        subscription = event["payload"]["subscription"]["entity"]
        notes = subscription.get("notes", {})
        company_id = notes.get("company_id")
        
        if company_id:
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.subscription_status = "paused"
                db.commit()
    
    elif event_type == "payment.failed":
        payment = event["payload"]["payment"]["entity"]
        subscription_id = payment.get("subscription_id")
        
        if subscription_id:
            company = db.query(Company).filter(Company.razorpay_subscription_id == subscription_id).first()
            if company:
                email, name = get_admin_email(str(company.id), db)
                if email:
                    plan_config = get_plan_config(company.subscription_tier)
                    EmailService.send_payment_failed(
                        email=email,
                        name=name,
                        plan_name=plan_config['name']
                    )
    
    return {"status": "success"}