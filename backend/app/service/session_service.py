import logging
from uuid import UUID
from app.service.video_processing.video_processing import VideoProcessor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from sqlalchemy.orm import joinedload

from app.models.session import CounselingSession
from app.models.counselor import Counselor
from app.schemas.session_schema import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    CounselorInfo,
)
from app.exceptions.custom_exception import BaseAppException, NotFoundException

logger = logging.getLogger(__name__)


async def create_session(
    db: AsyncSession, session_in: SessionCreate
) -> SessionResponse:
    try:
        # 1. Find counselor by UID
        result = await db.execute(
            select(Counselor).where(Counselor.uid == session_in.counselor_uid)
        )
        counselor = result.scalar_one_or_none()

        if not counselor:
            raise NotFoundException(details="Counselor not found")

        # 2. Create new session with counselor_id
        new_session = CounselingSession(
            counselor_id=counselor.id,
            description=session_in.description,
            session_date=session_in.session_date,
            recording_link=str(session_in.recording_link),
        )

        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        # 3. Return response with counselor info
        return SessionResponse(
            uid=new_session.uid,
            description=new_session.description,
            session_date=new_session.session_date,
            recording_link=new_session.recording_link,
            counselor=CounselorInfo(uid=counselor.uid, name=counselor.name),
        )

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during session creation: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def get_session_by_id(db: AsyncSession, session_uid: UUID) -> SessionResponse:
    try:
        result = await db.execute(
            select(CounselingSession)
            .options(joinedload(CounselingSession.counselor))
            .filter(CounselingSession.uid == session_uid)
        )
        session = result.scalars().first()
        if not session:
            raise NotFoundException(details=f"Session {session_uid} not found")

        return SessionResponse(
            uid=session.uid,
            description=session.description,
            session_date=session.session_date,
            recording_link=session.recording_link,
            counselor=CounselorInfo(
                uid=session.counselor.uid, name=session.counselor.name
            ),
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching session {session_uid}: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def get_all_sessions(db: AsyncSession, skip: int = 0, limit: int = 10):
    try:
        result = await db.execute(
            select(CounselingSession)
            .options(joinedload(CounselingSession.counselor))
            .offset(skip)
            .limit(limit)
        )
        sessions = result.scalars().all()

        return [
            SessionResponse(
                uid=s.uid,
                description=s.description,
                session_date=s.session_date,
                recording_link=s.recording_link,
                counselor=CounselorInfo(uid=s.counselor.uid, name=s.counselor.name),
            )
            for s in sessions
        ]
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching all sessions: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def get_sessions_by_counselor(
    db: AsyncSession, counselor_uid: str, skip: int = 0, limit: int = 10
):
    try:
        # First get the counselor ID
        counselor_result = await db.execute(
            select(Counselor).filter(Counselor.uid == counselor_uid)
        )
        counselor = counselor_result.scalar_one_or_none()

        if not counselor:
            raise NotFoundException(details=f"Counselor {counselor_uid} not found")

        # Then get sessions using the counselor's ID
        result = await db.execute(
            select(CounselingSession)
            .options(joinedload(CounselingSession.counselor))
            .filter(CounselingSession.counselor_id == counselor.id)
            .offset(skip)
            .limit(limit)
        )
        sessions = result.scalars().all()

        # Format the response
        return [
            SessionResponse(
                uid=session.uid,
                description=session.description,
                session_date=session.session_date,
                recording_link=session.recording_link,
                counselor=CounselorInfo(
                    uid=str(session.counselor.uid), name=session.counselor.name
                ),
            )
            for session in sessions
        ]

    except SQLAlchemyError as e:
        logger.error(
            f"Database error fetching sessions for counselor {counselor_uid}: {e}"
        )
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def get_all_sessions(db: AsyncSession, skip: int = 0, limit: int = 10):
    try:
        # Fetch all sessions with their counselors
        result = await db.execute(
            select(CounselingSession)
            .options(joinedload(CounselingSession.counselor))
            .offset(skip)
            .limit(limit)
        )
        sessions = result.scalars().all()

        # Format the response
        return [
            SessionResponse(
                uid=session.uid,
                description=session.description,
                session_date=session.session_date,
                recording_link=session.recording_link,
                counselor=CounselorInfo(
                    uid=str(session.counselor.uid),
                    name=session.counselor.name,
                ),
            )
            for session in sessions
        ]

    except SQLAlchemyError as e:
        logger.error(f"Database error fetching all sessions: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def update_session(
    db: AsyncSession, session_uid: UUID, session_in: SessionUpdate
) -> SessionResponse:
    # Get session with counselor eagerly loaded
    result = await db.execute(
        select(CounselingSession)
        .options(joinedload(CounselingSession.counselor))
        .filter(CounselingSession.uid == session_uid)
    )
    session = result.scalars().first()

    if not session:
        raise NotFoundException(details=f"Session {session_uid} not found")

    # Apply updates
    for key, value in session_in.model_dump(exclude_unset=True).items():
        setattr(session, key, value)

    try:
        db.add(session)
        await db.commit()
        await db.refresh(session)

        return SessionResponse(
            uid=session.uid,
            description=session.description,
            session_date=session.session_date,
            recording_link=session.recording_link,
            counselor=CounselorInfo(
                uid=session.counselor.uid,
                name=session.counselor.name,
            ),
        )

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during session update {session_uid}: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def delete_session(db: AsyncSession, session_uid: UUID):
    session = await get_session_by_id(db, session_uid)
    try:
        await db.delete(session)
        await db.commit()
        return {"message": "Session deleted successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error during session deletion {session_uid}: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def process_video_background(session_uid: UUID, video_url: str):
    """
    Background task to process video for a counseling session.
    This function runs asynchronously after session creation.
    """
    try:
        logger.info(f"Starting video processing for session {session_uid}")

        # Initialize video processor
        video_processor = VideoProcessor()

        # Process the video
        results = await video_processor.analyze_video(video_url)

        logger.info(f"Video processing completed for session {session_uid}")
        logger.info(f"Results: {results}")

        # TODO: store results in DB or send to another service

    except Exception as e:
        logger.error(f"Error processing video for session {session_uid}: {e}")
        # Background task failure might not need raising API exception
        # but for consistency:
        raise BaseAppException(
            error="Video Processing Error",
            details=str(e),
            status_code=500,
        )
