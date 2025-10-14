from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.core.database import Base
from datetime import datetime
import uuid
import enum

class DocType(str, enum.Enum):
    RFP = "rfp"
    PRODUCT_DOC = "product_doc"
    WEBSITE = "website"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    doc_type = Column(Enum(DocType), nullable=False)
    tags = Column(ARRAY(String), default=[])
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)