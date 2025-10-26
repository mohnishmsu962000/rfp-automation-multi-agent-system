from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.models.company import Company
from app.models.usage import UsageTracking as UsageModel
from app.core.plans import get_plan_config
from app.core.database import SessionLocal


class UsageTracking:
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
    
    def increment_rfp_usage(self, company_id: str):
        usage = self.get_or_create_usage(company_id)
        usage.rfps_used += 1
        usage.updated_at = datetime.now()
        self.db.commit()
    
    def increment_doc_usage(self, company_id: str):
        usage = self.get_or_create_usage(company_id)
        usage.docs_uploaded += 1
        usage.updated_at = datetime.now()
        self.db.commit()
    
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