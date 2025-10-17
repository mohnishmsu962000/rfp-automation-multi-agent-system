from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import uuid
import enum

class DocType(str, enum.Enum):
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    REPORT = "report"
    PRESENTATION = "presentation"
    OTHER = "other"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    company_id = Column(UUID(as_uuid=True), nullable=False)
    filename = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    doc_type = Column(SQLEnum(DocType), nullable=False)
    tags = Column(ARRAY(String), default=[])
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    
    chunks = relationship("VectorChunk", back_populates="document", cascade="all, delete-orphan")