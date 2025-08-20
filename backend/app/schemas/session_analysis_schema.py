from pydantic import BaseModel
from typing import Optional, Any, List, Literal
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


# Bulk response schemas with limited data
class AttireAssessment(BaseModel):
    meets_professional_standards: bool


class BackgroundAssessment(BaseModel):
    meets_professional_standards: bool


class EnvironmentAnalysis(BaseModel):
    attire_assessment: AttireAssessment
    background_assessment: BackgroundAssessment


class VideoAnalysisSummary(BaseModel):
    environment_analysis: EnvironmentAnalysis


class RedFlag(BaseModel):
    type: str
    description: str
    severity: Literal["low", "medium", "high"]


class AudioAnalysisSummary(BaseModel):
    red_flags: List[RedFlag]


class SessionAnalysisBulkItem(BaseModel):
    session_uid: str
    created_at: datetime
    updated_at: datetime
    video_analysis_summary: VideoAnalysisSummary
    audio_analysis_summary: AudioAnalysisSummary


class SessionAnalysisBulkResponse(BaseModel):
    analyses: List[SessionAnalysisBulkItem]
