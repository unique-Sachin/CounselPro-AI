from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.session_analysis import SessionAnalysis
from app.models.session import CounselingSession
from app.schemas.session_analysis_schema import SessionAnalysisCreate
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.exceptions.custom_exception import BadRequestException, NotFoundException


async def create_session_analysis(
    db: AsyncSession, session_analysis: SessionAnalysisCreate
) -> SessionAnalysis:
    # First get the session by its uid
    stmt = select(CounselingSession).where(
        CounselingSession.uid == session_analysis.session_uid
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise NotFoundException(details="Session not found")

    # Check if analysis already exists for this session
    stmt = select(SessionAnalysis).where(SessionAnalysis.session_id == session.id)
    result = await db.execute(stmt)
    existing_analysis = result.scalar_one_or_none()

    if existing_analysis:
        raise BadRequestException(details="Analysis already exists for this session")

    db_session_analysis = SessionAnalysis(
        session_id=session.id,
        video_analysis_data=session_analysis.video_analysis_data,
        audio_analysis_data=session_analysis.audio_analysis_data,
    )
    db.add(db_session_analysis)
    await db.commit()
    await db.refresh(db_session_analysis)

    # Reload with relationships
    stmt = (
        select(SessionAnalysis)
        .options(
            joinedload(SessionAnalysis.session).joinedload(CounselingSession.counselor)
        )
        .where(SessionAnalysis.id == db_session_analysis.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_analysis_by_uid(db: AsyncSession, uid: UUID) -> Optional[SessionAnalysis]:
    stmt = (
        select(SessionAnalysis)
        .options(
            joinedload(SessionAnalysis.session).joinedload(CounselingSession.counselor)
        )
        .where(SessionAnalysis.uid == uid)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_analysis_by_session_uid(
    db: AsyncSession, session_uid: UUID
) -> Optional[SessionAnalysis]:
    stmt = (
        select(SessionAnalysis)
        .join(SessionAnalysis.session)
        .options(
            joinedload(SessionAnalysis.session).joinedload(CounselingSession.counselor)
        )
        .where(CounselingSession.uid == session_uid)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_session_analysis(
    db: AsyncSession, uid: UUID, session_analysis: SessionAnalysisCreate
) -> Optional[SessionAnalysis]:
    stmt = (
        select(SessionAnalysis)
        .options(
            joinedload(SessionAnalysis.session).joinedload(CounselingSession.counselor)
        )
        .where(SessionAnalysis.uid == uid)
    )
    result = await db.execute(stmt)
    db_analysis = result.scalar_one_or_none()

    if db_analysis:
        db_analysis.video_analysis_data = session_analysis.video_analysis_data
        db_analysis.audio_analysis_data = session_analysis.audio_analysis_data
        db_analysis.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(db_analysis)
    return db_analysis


async def delete_session_analysis(db: AsyncSession, uid: UUID) -> bool:
    stmt = select(SessionAnalysis).where(SessionAnalysis.uid == uid)
    result = await db.execute(stmt)
    db_analysis = result.scalar_one_or_none()

    if db_analysis:
        await db.delete(db_analysis)
        await db.commit()
        return True
    return False
