import uuid
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base


class CatalogFile(Base):
    __tablename__ = "catalog_files"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String, default="uploaded", nullable=False)
    chunk_count = Column(Integer, default=0)
    indexed_at = Column(DateTime(timezone=True), nullable=True)
