from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from datetime import datetime
import uuid

class ResyncQuota(Base):
    __tablename__ = "resync_quota"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    month_year = Column(String, nullable=False)  # Format: "2025-01"
    resync_count = Column(Integer, default=0)
    last_resync_at = Column(DateTime)