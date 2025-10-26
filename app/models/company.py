from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subscription_tier = Column(String(20), default='free')
    razorpay_customer_id = Column(String(50), nullable=True)
    razorpay_subscription_id = Column(String(50), nullable=True)
    subscription_status = Column(String(20), default='inactive')
    current_period_end = Column(DateTime, nullable=True)
    
    documents = relationship("Document", back_populates="company")
    rfp_projects = relationship("RFPProject", back_populates="company")
    attributes = relationship("Attribute", back_populates="company")