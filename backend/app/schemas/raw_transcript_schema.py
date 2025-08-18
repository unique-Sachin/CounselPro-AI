from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime
from uuid import UUID


class CounselorInfo(BaseModel):
    uid: str
    name: str

    model_config = {"from_attributes": True}


class SessionInfo(BaseModel):
    uid: str
    description: str
    session_date: datetime
    counselor: CounselorInfo

    model_config = {"from_attributes": True}


class RawTranscriptBase(BaseModel):
    session_uid: str
    total_segments: int
    raw_transcript: Any  # JSON data


class RawTranscriptCreate(RawTranscriptBase):
    pass


class RawTranscriptUpdate(BaseModel):
    total_segments: Optional[int] = None
    raw_transcript: Optional[Any] = None


class RawTranscriptResponse(BaseModel):
    uid: str
    total_segments: int
    raw_transcript: Any
    created_at: datetime
    updated_at: datetime
    session: SessionInfo

    model_config = {"from_attributes": True}
