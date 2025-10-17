from sqlalchemy import Column, String, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid

class RFPQuestion(Base):
    __tablename__ = "rfp_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("rfp_projects.id"), nullable=False, index=True)
    question_text = Column(String, nullable=False)
    answer_text = Column(String)
    trust_score = Column(Float, default=0.0)
    source_type = Column(String)
    source_ids = Column(ARRAY(String), default=[])
    user_edited = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = relationship("RFPProject", back_populates="questions")