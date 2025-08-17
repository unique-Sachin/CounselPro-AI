from uuid import UUID
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from db.database import get_async_db
from schemas.session_schema import SessionCreate, SessionUpdate, SessionResponse
from service.session_service import (
    create_session,
    get_session_by_id,
    get_all_sessions,
    get_sessions_by_counselor,
    update_session,
    delete_session,
    process_video_background,
)

router = APIRouter(prefix="/sessions", tags=["Counseling Sessions"])


@router.post("/", response_model=SessionResponse)
async def create_counseling_session(
    session_in: SessionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    # Create the session first
    session = await create_session(db, session_in)

    # Add video processing as background task
    background_tasks.add_task(
        process_video_background,
        session.uid,
        str(session.recording_link)
    )

    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_counseling_session(
    session_id: int, db: AsyncSession = Depends(get_async_db)
):
    return await get_session_by_id(db, session_id)


# @router.get("/", response_model=List[SessionResponse])
# async def list_counseling_sessions(
#     skip: int = Query(0, ge=0),
#     limit: int = Query(10, ge=1, le=100),
#     db: AsyncSession = Depends(get_async_db),
# ):
#     return await get_all_sessions(db, skip=skip, limit=limit)


@router.get("/by-counselor/{counselor_id}", response_model=List[SessionResponse])
async def list_sessions_by_counselor(
    counselor_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    return await get_sessions_by_counselor(
        db, counselor_id=counselor_id, skip=skip, limit=limit
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_counseling_session(
    session_id: int, session_in: SessionUpdate, db: AsyncSession = Depends(get_async_db)
):
    return await update_session(db, session_id, session_in)


@router.delete("/{session_id}")
async def delete_counseling_session(
    session_id: int, db: AsyncSession = Depends(get_async_db)
):
    return await delete_session(db, session_id)

from pydantic import BaseModel
from typing import Any, Dict

from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class VideoDimensions(BaseModel):
    width: int
    height: int

class VideoInfo(BaseModel):
    duration_seconds: float
    frame_count: int
    fps: float
    audio_path: str
    dimensions: VideoDimensions

class CameraMetrics(BaseModel):
    on_percentage: float
    total_samples: int
    samples_with_faces: int
    face_detection_rate: float

class OffPeriods(BaseModel):
    count: int
    total_duration: float
    details: List[Dict[str, Any]]

class ProofData(BaseModel):
    frames_count: int
    frames: List[Dict[str, Any]]

class CameraAnalysis(BaseModel):
    overall_status: str
    metrics: CameraMetrics
    off_periods: OffPeriods
    proof_data: ProofData
    timeline: List[Dict[str, Any]]

class AnalysisItem(BaseModel):
    success: bool
    summary: str
    frames_analyzed: int
    error: Optional[str] = None

class VisualAnalyses(BaseModel):
    attire: AnalysisItem
    background: AnalysisItem

class VisualMetrics(BaseModel):
    total_frames_analyzed: int
    analysis_coverage_percentage: float

class VisualIntelligence(BaseModel):
    overall_success: bool
    analyses: VisualAnalyses
    metrics: VisualMetrics
    error: Optional[str] = None

class AnalysisSummary(BaseModel):
    overall_success: bool
    camera_working: bool
    visual_analysis_completed: bool
    total_people_detected: int
    static_images_detected: int

class AnalysisMethods(BaseModel):
    camera_detection: str
    visual_analysis_model: str
    sampling_strategy: str
    extraction_method: str

class StaticDetection(BaseModel):
    enabled: bool
    method: str
    ssim_threshold: float
    landmark_threshold: float

class Metadata(BaseModel):
    analysis_timestamp: str
    analysis_version: str
    methods: AnalysisMethods
    static_detection: StaticDetection

class VideoAnalysisResponse(BaseModel):
    video_info: VideoInfo
    camera_analysis: CameraAnalysis
    visual_intelligence: VisualIntelligence
    analysis_summary: AnalysisSummary
    metadata: Metadata


@router.get("/{session_id}/analysis", response_model=VideoAnalysisResponse)
async def get_session_analysis(
    session_id: UUID, video_url: str, db: AsyncSession = Depends(get_async_db)
):
    results = await process_video_background(session_id, video_url)
    return VideoAnalysisResponse(**results)
