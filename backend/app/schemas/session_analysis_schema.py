from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID


class CounselorInfo(BaseModel):
    uid: UUID
    name: str

    model_config = {"from_attributes": True}


class SessionInfo(BaseModel):
    uid: UUID
    description: str
    session_date: datetime
    counselor: CounselorInfo

    model_config = {"from_attributes": True}


class SessionAnalysisBase(BaseModel):
    session_uid: UUID  # Changed to UUID for input
    video_analysis_data: Any
    audio_analysis_data: Any


class SessionAnalysisCreate(SessionAnalysisBase):
    pass


class SessionAnalysisResponse(BaseModel):
    uid: UUID  # Changed to UUID for response
    video_analysis_data: Any
    audio_analysis_data: Any
    created_at: datetime
    updated_at: datetime
    session: SessionInfo

    model_config = {"from_attributes": True}
