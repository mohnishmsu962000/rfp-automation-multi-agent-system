from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from datetime import datetime
import uuid

class Attribute(Base):
    __tablename__ = "attributes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)  # technical, compliance, business, product
    source_doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)