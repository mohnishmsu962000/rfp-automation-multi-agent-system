from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.models.company import Company
from app.models.usage import UsageTracking as UsageModel
from app.models.user import User
from app.models.user_company import UserCompany
from app.core.plans import get_plan_config
from app.core.database import SessionLocal
from app.services.email_service import EmailService


class UsageService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_current_month(self) -> str:
        return datetime.now().strftime("%Y-%m")
    
    def get_or_create_usage(self, company_id: str):
        
        month = self.get_current_month()
        usage = self.db.query(UsageModel).filter(
            and_(
                UsageModel.company_id == company_id,
                UsageModel.month == month
            )
        ).first()
        
        if not usage:
            usage = UsageModel(
                company_id=company_id,
                month=month,
                rfps_used=0,
                docs_uploaded=0
            )
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)
        
        return usage
    
    def _get_admin_user(self, company_id: str):
        user_company = self.db.query(UserCompany).filter(
            UserCompany.company_id == company_id,
            UserCompany.role == 'admin'
        ).first()
        
        if user_company:
            return self.db.query(User).filter(User.id == user_company.user_id).first()
        return None
    
    def _send_usage_emails(self, company_id: str, used: int, limit: int, quota_type: str):
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return
        
        admin = self._get_admin_user(company_id)
        if not admin:
            return
        
        percentage = int((used / limit) * 100)
        
        if percentage == 100:
            next_month = datetime.now().replace(day=1)
            if next_month.month == 12:
                next_month = next_month.replace(year=next_month.year + 1, month=1)
            else:
                next_month = next_month.replace(month=next_month.month + 1)
            
            EmailService.send_quota_limit_reached(
                email=admin.email,
                name=admin.name or admin.email.split('@')[0],
                limit=limit,
                quota_type=quota_type,
                tier=company.subscription_tier,
                reset_date=next_month.strftime("%B 1, %Y")
            )
        elif percentage >= 80:
            EmailService.send_quota_warning(
                email=admin.email,
                name=admin.name or admin.email.split('@')[0],
                used=used,
                limit=limit,
                quota_type=quota_type,
                tier=company.subscription_tier
            )
    
    def increment_rfp_usage(self, company_id: str):
        usage = self.get_or_create_usage(company_id)
        usage.rfps_used += 1
        usage.updated_at = datetime.now()
        self.db.commit()
        
        company = self.db.query(Company).filter(Company.id == company_id).first()
        plan = get_plan_config(company.subscription_tier)
        
        self._send_usage_emails(company_id, usage.rfps_used, plan['rfp_limit'], "RFPs")
    
    def increment_doc_usage(self, company_id: str):
        usage = self.get_or_create_usage(company_id)
        usage.docs_uploaded += 1
        usage.updated_at = datetime.now()
        self.db.commit()
        
        company = self.db.query(Company).filter(Company.id == company_id).first()
        plan = get_plan_config(company.subscription_tier)
        
        self._send_usage_emails(company_id, usage.docs_uploaded, plan['doc_limit'], "Documents")
    
    def check_rfp_limit(self, company_id: str) -> tuple[bool, dict]:
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False, {"error": "Company not found"}
        
        plan = get_plan_config(company.subscription_tier)
        usage = self.get_or_create_usage(company_id)
        
        if usage.rfps_used >= plan['rfp_limit']:
            return False, {
                "error": "RFP limit reached",
                "used": usage.rfps_used,
                "limit": plan['rfp_limit'],
                "plan": company.subscription_tier
            }
        
        return True, {
            "used": usage.rfps_used,
            "limit": plan['rfp_limit'],
            "remaining": plan['rfp_limit'] - usage.rfps_used
        }
    
    def check_doc_limit(self, company_id: str) -> tuple[bool, dict]:
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False, {"error": "Company not found"}
        
        plan = get_plan_config(company.subscription_tier)
        usage = self.get_or_create_usage(company_id)
        
        if usage.docs_uploaded >= plan['doc_limit']:
            return False, {
                "error": "Document limit reached",
                "used": usage.docs_uploaded,
                "limit": plan['doc_limit'],
                "plan": company.subscription_tier
            }
        
        return True, {
            "used": usage.docs_uploaded,
            "limit": plan['doc_limit'],
            "remaining": plan['doc_limit'] - usage.docs_uploaded
        }
    
    def get_usage_stats(self, company_id: str):
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None
        
        plan = get_plan_config(company.subscription_tier)
        usage = self.get_or_create_usage(company_id)
        
        return {
            "month": usage.month,
            "rfps": {
                "used": usage.rfps_used,
                "limit": plan['rfp_limit'],
                "remaining": plan['rfp_limit'] - usage.rfps_used
            },
            "docs": {
                "used": usage.docs_uploaded,
                "limit": plan['doc_limit'],
                "remaining": plan['doc_limit'] - usage.docs_uploaded
            },
            "plan": {
                "tier": company.subscription_tier,
                "name": plan['name']
            }
        }