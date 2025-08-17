from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


class SessionAnalysis(Base):
    __tablename__ = "session_analysis"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    session_id = Column(
        Integer,
        ForeignKey("counseling_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    video_analysis_data = Column(JSON)  # Using JSON type for structured data
    audio_analysis_data = Column(JSON)  # Using JSON type for structured data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-one relationship with CounselingSession
    session = relationship(
        "CounselingSession", uselist=False, back_populates="analysis"
    )
