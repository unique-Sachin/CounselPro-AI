import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class CounselingSession(Base):
    __tablename__ = "counseling_sessions"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    counselor_id = Column(
        Integer, ForeignKey("counselors.id", ondelete="CASCADE"), nullable=False
    )
    description = Column(String, nullable=True)
    session_date = Column(DateTime(timezone=True), nullable=False)
    recording_link = Column(String, nullable=False)

    counselor = relationship("Counselor", back_populates="sessions")
    analysis = relationship("SessionAnalysis", back_populates="session", uselist=False)
