from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, HttpUrl, Field


# Base schema (shared fields)
class SessionBase(BaseModel):
    counselor_uid: str
    description: str
    session_date: datetime
    recording_link: HttpUrl


# Create schema
class SessionCreate(SessionBase):
    pass


# Update schema
class SessionUpdate(BaseModel):
    counselor_uid: str | None = None
    session_date: datetime | None = None
    recording_link: HttpUrl | None = None


# Response schema
class SessionResponse(BaseModel):
    uid: UUID
    description: str
    session_date: datetime
    recording_link: HttpUrl

    model_config = {"from_attributes": True}
