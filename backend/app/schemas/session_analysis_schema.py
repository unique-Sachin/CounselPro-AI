from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import enum


class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


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


class SessionAnalysisBase(BaseModel):
    session_uid: str
    video_analysis_data: Any
    audio_analysis_data: Any
    status: Optional[AnalysisStatus] = AnalysisStatus.PENDING  # default pending


class SessionAnalysisCreate(SessionAnalysisBase):
    pass


class SessionAnalysisResponse(BaseModel):
    uid: str
    video_analysis_data: Any
    audio_analysis_data: Any
    status: AnalysisStatus
    created_at: datetime
    updated_at: datetime
    session: SessionInfo

    model_config = {"from_attributes": True}
