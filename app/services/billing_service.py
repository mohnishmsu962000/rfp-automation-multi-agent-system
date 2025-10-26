import razorpay
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.plans import SUBSCRIPTION_PLANS, get_plan_config
from app.models.company import Company
from app.core.database import get_db

settings = get_settings()

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class BillingService:
    
    @staticmethod
    def create_customer(company_id: str, email: str, name: str, db: Session):
        try:
            customer = razorpay_client.customer.create({
                "name": name,
                "email": email,
                "notes": {
                    "company_id": company_id
                }
            })
            
            company = db.query(Company).filter(Company.id == company_id).first()
            if company:
                company.razorpay_customer_id = customer['id']
                db.commit()
            
            return customer
        except Exception as e:
            print(f"Error creating Razorpay customer: {e}")
            raise
    
    @staticmethod
    def create_subscription(company_id: str, plan_tier: str, user_email: str, db: Session):
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise ValueError("Company not found")
            
            if not company.razorpay_customer_id:
                customer = BillingService.create_customer(
                    company_id=str(company.id),
                    email=user_email,
                    name=company.name,
                    db=db
                )
                customer_id = customer['id']
            else:
                customer_id = company.razorpay_customer_id
            
            plan_config = get_plan_config(plan_tier)
            if not plan_config['plan_id']:
                raise ValueError("Invalid plan tier")
            
            subscription = razorpay_client.subscription.create({
                "plan_id": plan_config['plan_id'],
                "customer_id": customer_id,
                "quantity": 1,
                "total_count": 12,
                "customer_notify": 1,
                "notes": {
                    "company_id": company_id,
                    "plan_tier": plan_tier
                }
            })
            
            company.subscription_tier = plan_tier
            company.razorpay_subscription_id = subscription['id']
            company.subscription_status = subscription['status']
            db.commit()
            
            return subscription
        except Exception as e:
            print(f"Error creating subscription: {e}")
            raise
    
    @staticmethod
    def cancel_subscription(company_id: str, db: Session):
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company or not company.razorpay_subscription_id:
                raise ValueError("No active subscription found")
            
            subscription = razorpay_client.subscription.cancel(
                company.razorpay_subscription_id,
                cancel_at_cycle_end=1
            )
            
            company.subscription_status = "cancelled"
            db.commit()
            
            return subscription
        except Exception as e:
            print(f"Error cancelling subscription: {e}")
            raise
    
    @staticmethod
    def get_subscription_status(company_id: str, db: Session):
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None
        
        plan_config = get_plan_config(company.subscription_tier)
        
        return {
            "tier": company.subscription_tier,
            "status": company.subscription_status,
            "plan_name": plan_config['name'],
            "price": plan_config['price'],
            "rfp_limit": plan_config['rfp_limit'],
            "doc_limit": plan_config['doc_limit'],
            "razorpay_subscription_id": company.razorpay_subscription_id,
            "current_period_end": company.current_period_end
        }