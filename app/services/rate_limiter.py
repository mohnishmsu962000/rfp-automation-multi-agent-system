from sqlalchemy.orm import Session
from app.models.document_quota import DocumentQuota
from app.models.resync_quota import ResyncQuota
from app.models.rfp_project import RFPProject
from datetime import datetime
from uuid import UUID

RATE_LIMITS = {
    "documents": 100,
    "rfps": 20,
    "rephrase": 1000,
    "resync": 2
}

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_DOCUMENT_PAGES = 100
MAX_DOCUMENT_TOKENS = 50000

class RateLimiter:
    
    @staticmethod
    def validate_file_size(file_size: int) -> tuple[bool, str]:
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        return True, ""
    
    @staticmethod
    def validate_document_content(text: str, page_count: int = None) -> tuple[bool, str]:
        if page_count and page_count > MAX_DOCUMENT_PAGES:
            return False, f"Document too long. Maximum {MAX_DOCUMENT_PAGES} pages allowed"
        
        token_count = len(text.split())
        if token_count > MAX_DOCUMENT_TOKENS:
            return False, f"Document too large. Maximum {MAX_DOCUMENT_TOKENS} words allowed"
        
        return True, ""
    
    @staticmethod
    def check_document_quota(company_id: UUID, db: Session) -> tuple[bool, int, int]:
        quota = db.query(DocumentQuota).filter(
            DocumentQuota.company_id == company_id
        ).first()
        
        current_count = quota.document_count if quota else 0
        remaining = RATE_LIMITS["documents"] - current_count
        
        if current_count >= RATE_LIMITS["documents"]:
            return False, current_count, remaining
        
        return True, current_count, remaining
    
    @staticmethod
    def increment_document_quota(company_id: UUID, db: Session):
        quota = db.query(DocumentQuota).filter(
            DocumentQuota.company_id == company_id
        ).first()
        
        if quota:
            quota.document_count += 1
            quota.updated_at = datetime.utcnow()
        else:
            quota = DocumentQuota(
                company_id=company_id,
                document_count=1
            )
            db.add(quota)
        
        db.commit()
    
    @staticmethod
    def check_rfp_quota(company_id: UUID, db: Session) -> tuple[bool, int, int]:
        month_year = datetime.utcnow().strftime("%Y-%m")
        
        count = db.query(RFPProject).filter(
            RFPProject.company_id == company_id,
            RFPProject.created_at >= datetime.strptime(month_year, "%Y-%m")
        ).count()
        
        remaining = RATE_LIMITS["rfps"] - count
        
        if count >= RATE_LIMITS["rfps"]:
            return False, count, remaining
        
        return True, count, remaining
    
    @staticmethod
    def get_usage_stats(company_id: UUID, db: Session) -> dict:
        doc_quota = db.query(DocumentQuota).filter(
            DocumentQuota.company_id == company_id
        ).first()
        
        docs_used = doc_quota.document_count if doc_quota else 0
        
        month_year = datetime.utcnow().strftime("%Y-%m")
        rfps_used = db.query(RFPProject).filter(
            RFPProject.company_id == company_id,
            RFPProject.created_at >= datetime.strptime(month_year, "%Y-%m")
        ).count()
        
        resync_quota = db.query(ResyncQuota).filter(
            ResyncQuota.company_id == company_id,
            ResyncQuota.month_year == month_year
        ).first()
        
        resyncs_used = resync_quota.resync_count if resync_quota else 0
        
        return {
            "documents": {
                "used": docs_used,
                "limit": RATE_LIMITS["documents"],
                "remaining": RATE_LIMITS["documents"] - docs_used
            },
            "rfps": {
                "used": rfps_used,
                "limit": RATE_LIMITS["rfps"],
                "remaining": RATE_LIMITS["rfps"] - rfps_used
            },
            "rephrase": {
                "used": 0,
                "limit": RATE_LIMITS["rephrase"],
                "remaining": RATE_LIMITS["rephrase"]
            },
            "resync": {
                "used": resyncs_used,
                "limit": RATE_LIMITS["resync"],
                "remaining": RATE_LIMITS["resync"] - resyncs_used
            }
        }