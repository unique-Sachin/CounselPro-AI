from sqlalchemy import Column, Integer, DateTime, JSON, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SessionAnalysis(Base):
    __tablename__ = "session_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uid = Column(UUID(as_uuid=False), default=uuid.uuid4, unique=True, nullable=False)
    session_id = Column(
        Integer,
        ForeignKey("counseling_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    video_analysis_data = Column(JSON)  # Using JSON type for structured data
    audio_analysis_data = Column(JSON)  # Using JSON type for structured data
    status = Column(
        SQLEnum(AnalysisStatus),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-one relationship with CounselingSession
    session = relationship(
        "CounselingSession", uselist=False, back_populates="analysis"
    )
