from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from datetime import datetime
import uuid

class Attribute(Base):
    __tablename__ = "attributes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)
    category = Column(String)
    source_doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)