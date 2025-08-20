from uuid import UUID
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from app.models.video_analysis import VideoAnalysisResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import List
from app.service.celery.celery_worker import process_video
from app.db.database import SyncSessionLocal
from app.db.database import get_sync_db

from app.db.database import get_async_db
from app.schemas.session_schema import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
)
from app.service.session_service import (
    create_session,
    get_session_by_id,
    get_all_sessions,
    get_sessions_by_counselor,
    update_session,
    delete_session,
    process_video_background,
    get_session_by_id_sync,
)

router = APIRouter(prefix="/sessions", tags=["Counseling Sessions"])


@router.post("/", response_model=SessionResponse)
async def create_counseling_session(
    session_in: SessionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
):
    # Create the session first
    session = await create_session(db, session_in)
    return session


@router.get("/all", response_model=SessionListResponse)
async def list_all_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all counseling sessions, paginated
    """
    items, total = await get_all_sessions(db, skip=skip, limit=limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{session_uid}", response_model=SessionResponse)
async def get_counseling_session(
    session_uid: UUID, db: AsyncSession = Depends(get_async_db)
):
    return await get_session_by_id(db, session_uid)


@router.get("/by-counselor/{counselor_uid}", response_model=SessionListResponse)
async def list_sessions_by_counselor(
    counselor_uid: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    items, total = await get_sessions_by_counselor(
        db, counselor_uid=counselor_uid, skip=skip, limit=limit
    )
    return {
        "items": items,
        "total": total,
        "skip": 0,
        "limit": 1,
    }


@router.put("/{session_uid}", response_model=SessionResponse)
async def update_counseling_session(
    session_uid: str,
    session_in: SessionUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    return await update_session(db, session_uid, session_in)


@router.delete("/{session_uid}")
async def delete_counseling_session(
    session_uid: str, db: AsyncSession = Depends(get_async_db)
):
    return await delete_session(db, session_uid)


@router.get("/{session_uid}/analysis")
async def get_session_analysis(
    session_id: UUID, db: AsyncSession = Depends(get_async_db)
):
    results = await process_video_background(db, session_id)
    return results


@router.get("/{session_uid}/analysis_by_celery")
async def get_session_analysis_using_celery_background_task(
    session_uid: str, db: Session = Depends(get_sync_db)
):
    print(f"Starting video processing for session {session_uid}")
    sessionResponse = get_session_by_id_sync(db, session_uid)

    video_path = sessionResponse.recording_link

    if not video_path:
        return {"error": "Video path not found"}

    # Send task to Celery worker
    task = process_video.delay(session_uid, str(video_path))
    return {"task_id": task.id, "status": "Processing started"}
