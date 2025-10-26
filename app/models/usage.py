from sqlalchemy import Column, Integer, String, DateTime, UUID
from sqlalchemy.sql import func
from app.core.database import Base


class UsageTracking(Base):
    __tablename__ = "usage_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    month = Column(String(7), nullable=False)
    rfps_used = Column(Integer, default=0)
    docs_uploaded = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())