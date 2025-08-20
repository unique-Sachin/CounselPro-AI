from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.session_analysis import SessionAnalysis
from app.models.session import CounselingSession
from app.schemas.session_analysis_schema import (
    SessionAnalysisCreate, 
    SessionAnalysisBulkItem,
    VideoAnalysisSummary,
    AudioAnalysisSummary,
    EnvironmentAnalysis,
    AttireAssessment,
    BackgroundAssessment,
    RedFlag
)
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


async def get_analysis_by_uid(db: AsyncSession, uid: str) -> Optional[SessionAnalysis]:
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
    db: AsyncSession, session_uid: str
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


async def create_or_update_session_analysis(
    db: AsyncSession, session_analysis: SessionAnalysisCreate
) -> SessionAnalysis:
    """
    Create a new session analysis or update existing one if it already exists.
    This is an "upsert" operation.
    """
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
        # Update existing analysis
        existing_analysis.video_analysis_data = session_analysis.video_analysis_data
        existing_analysis.audio_analysis_data = session_analysis.audio_analysis_data
        # updated_at will be automatically set by SQLAlchemy onupdate
        await db.commit()
        await db.refresh(existing_analysis)
        
        # Reload with relationships
        stmt = (
            select(SessionAnalysis)
            .options(
                joinedload(SessionAnalysis.session).joinedload(CounselingSession.counselor)
            )
            .where(SessionAnalysis.id == existing_analysis.id)
        )
        result = await db.execute(stmt)
        return result.scalar_one()
    else:
        # Create new analysis
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
        return result.scalar_one()


async def update_session_analysis(
    db: AsyncSession, uid: str, session_analysis: SessionAnalysisCreate
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
        # updated_at will be automatically set by SQLAlchemy onupdate
        await db.commit()
        await db.refresh(db_analysis)
    return db_analysis


async def delete_session_analysis(db: AsyncSession, uid: str) -> bool:
    stmt = select(SessionAnalysis).where(SessionAnalysis.uid == uid)
    result = await db.execute(stmt)
    db_analysis = result.scalar_one_or_none()

    if db_analysis:
        await db.delete(db_analysis)
        await db.commit()
        return True
    return False


async def get_analyses_by_session_uids(db: AsyncSession, session_uids: list[str]) -> list[SessionAnalysis]:
    """Get session analyses for multiple session UIDs."""
    stmt = (
        select(SessionAnalysis)
        .join(SessionAnalysis.session)
        .options(
            joinedload(SessionAnalysis.session).joinedload(CounselingSession.counselor)
        )
        .where(CounselingSession.uid.in_(session_uids))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _extract_limited_data(analysis: SessionAnalysis) -> SessionAnalysisBulkItem:
    """Transform full SessionAnalysis data into limited format for bulk response."""
    
    # Extract video analysis summary
    video_data = analysis.video_analysis_data or {}
    environment_data = video_data.get("environment_analysis", {})
    
    video_summary = VideoAnalysisSummary(
        environment_analysis=EnvironmentAnalysis(
            attire_assessment=AttireAssessment(
                meets_professional_standards=environment_data.get("attire_assessment", {}).get("meets_professional_standards", False)
            ),
            background_assessment=BackgroundAssessment(
                meets_professional_standards=environment_data.get("background_assessment", {}).get("meets_professional_standards", False)
            )
        )
    )
    
    # Extract audio analysis summary
    audio_data = analysis.audio_analysis_data or {}
    red_flags_data = audio_data.get("red_flags", [])
    
    red_flags = []
    for flag in red_flags_data:
        if isinstance(flag, dict):
            red_flags.append(RedFlag(
                type=flag.get("type", ""),
                description=flag.get("description", ""),
                severity=flag.get("severity", "low")
            ))
    
    audio_summary = AudioAnalysisSummary(red_flags=red_flags)
    
    return SessionAnalysisBulkItem(
        session_uid=str(analysis.session.uid),
        status=analysis.status.value if hasattr(analysis.status, 'value') else str(analysis.status),
        created_at=analysis.created_at if isinstance(analysis.created_at, datetime) else datetime.utcnow(),
        updated_at=analysis.updated_at if isinstance(analysis.updated_at, datetime) else datetime.utcnow(),
        video_analysis_summary=video_summary,
        audio_analysis_summary=audio_summary
    )


async def get_limited_analyses_by_session_uids(db: AsyncSession, session_uids: list[str]) -> list[SessionAnalysisBulkItem]:
    """Get limited session analyses data for multiple session UIDs."""
    # Get full data first
    full_analyses = await get_analyses_by_session_uids(db, session_uids)
    
    # Transform to limited format
    limited_analyses = []
    for analysis in full_analyses:
        try:
            limited_data = _extract_limited_data(analysis)
            limited_analyses.append(limited_data)
        except Exception as e:
            # Log error but continue with other analyses
            print(f"Error processing analysis for session {analysis.session.uid}: {e}")
            continue
    
    return limited_analyses
