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
