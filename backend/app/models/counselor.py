import uuid
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from db.database import Base
from sqlalchemy.orm import relationship


class Counselor(Base):
    __tablename__ = "counselors"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    uid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, nullable=False)
    employee_id = Column(String, unique=True, nullable=False)
    dept = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    mobile_number = Column(String, unique=True, nullable=False)

    sessions = relationship(
        "CounselingSession", back_populates="counselor", cascade="all, delete-orphan"
    )
