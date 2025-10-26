from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.billing_service import BillingService
from app.services.usage_service import UsageTracking
from app.core.plans import SUBSCRIPTION_PLANS

router = APIRouter(prefix="/billing", tags=["billing"])


class CreateSubscriptionRequest(BaseModel):
    plan_tier: str


@router.get("/plans")
async def get_plans():
    return {"plans": SUBSCRIPTION_PLANS}


@router.get("/status")
async def get_subscription_status(
    auth_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = auth_data["company_id"]
    status = BillingService.get_subscription_status(company_id, db)
    
    if not status:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return status


@router.get("/usage")
async def get_usage_stats(
    auth_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = auth_data["company_id"]
    usage_service = UsageTracking(db)
    stats = usage_service.get_usage_stats(company_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return stats


@router.post("/subscribe")
async def create_subscription(
    request: CreateSubscriptionRequest,
    auth_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = auth_data["company_id"]
    user_email = auth_data["email"]
    
    if request.plan_tier not in ["starter", "growth", "pro"]:
        raise HTTPException(status_code=400, detail="Invalid plan tier")
    
    try:
        subscription = BillingService.create_subscription(company_id, request.plan_tier, user_email, db)
        return {
            "success": True,
            "subscription_id": subscription['id'],
            "status": subscription['status'],
            "short_url": subscription.get('short_url')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_subscription(
    auth_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    company_id = auth_data["company_id"]
    
    try:
        subscription = BillingService.cancel_subscription(company_id, db)
        return {
            "success": True,
            "message": "Subscription cancelled",
            "status": subscription['status']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))