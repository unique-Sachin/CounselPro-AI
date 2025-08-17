from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class CatalogFileResponse(BaseModel):
    uid: UUID
    filename: str
    uploaded_at: datetime
    status: str
    chunk_count: int
    indexed_at: Optional[datetime]
