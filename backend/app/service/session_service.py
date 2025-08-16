import logging
from uuid import UUID
from service.video_processing.video_processing import VideoProcessor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from models.session import CounselingSession
from models.counselor import Counselor
from schemas.session_schema import SessionCreate, SessionUpdate

logger = logging.getLogger(__name__)


async def create_session(
    db: AsyncSession, session_in: SessionCreate
) -> CounselingSession:
    try:
        # 1. Find counselor by UID
        result = await db.execute(
            select(Counselor).where(Counselor.uid == session_in.counselor_uid)
        )
        counselor = result.scalar_one_or_none()

        if not counselor:
            raise HTTPException(status_code=404, detail="Counselor not found")

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
        return new_session

    except SQLAlchemyError as e:
        logger.error(f"Database error during session creation: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Internal server error while creating session"
        )


async def get_session_by_id(db: AsyncSession, session_uid: UUID) -> CounselingSession:
    result = await db.execute(
        select(CounselingSession).filter(CounselingSession.uid == session_uid)
    )
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


async def get_all_sessions(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(CounselingSession).offset(skip).limit(limit))
    return result.scalars().all()


async def get_sessions_by_counselor(
    db: AsyncSession, counselor_id: int, skip: int = 0, limit: int = 10
):
    result = await db.execute(
        select(CounselingSession)
        .filter(CounselingSession.counselor_id == counselor_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_session(
    db: AsyncSession, session_uid: UUID, session_in: SessionUpdate
) -> CounselingSession:
    session = await get_session_by_id(db, session_uid)
    for key, value in session_in.model_dump(exclude_unset=True).items():
        setattr(session, key, value)
    try:
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    except SQLAlchemyError as e:
        logger.error(f"Database error during session update: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Internal server error while updating session"
        )


async def delete_session(db: AsyncSession, session_uid: UUID):
    session = await get_session_by_id(db, session_uid)
    try:
        await db.delete(session)
        await db.commit()
        return {"message": "Session deleted successfully"}
    except SQLAlchemyError as e:
        logger.error(f"Database error during session deletion: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=500, detail="Internal server error while deleting session"
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

        # Here you can add logic to store the results in the database
        # or send them to another service for further processing

    except Exception as e:
        logger.error(f"Error processing video for session {session_uid}: {e}")
        # You might want to update the session status to indicate processing failed
