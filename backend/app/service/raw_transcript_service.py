from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.models.raw_transcript import RawTranscript
from app.models.session import CounselingSession
from app.models.session_analysis import SessionAnalysis
from app.schemas.raw_transcript_schema import (
    RawTranscriptCreate,
    RawTranscriptUpdate,
    RawTranscriptResponse,
    RawTranscriptWithStatusResponse,
)
from app.exceptions.custom_exception import (
    BaseAppException,
    NotFoundException,
    BadRequestException,
)
from app.config.log_config import get_logger

logger = get_logger("raw_transcript_service")


async def create_raw_transcript(
    db: AsyncSession, transcript_in: RawTranscriptCreate
) -> RawTranscriptResponse:
    try:
        # Find session by UID
        result = await db.execute(
            select(CounselingSession)
            .options(joinedload(CounselingSession.counselor))
            .where(CounselingSession.uid == transcript_in.session_uid)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundException(details="Counseling session not found")

        # Check if transcript already exists for this session
        result = await db.execute(
            select(RawTranscript).where(RawTranscript.session_id == session.id)
        )
        existing_transcript = result.scalar_one_or_none()

        if existing_transcript:
            raise BadRequestException(
                details="Transcript already exists for this session"
            )

        # Create new transcript with session_id
        new_transcript = RawTranscript(
            session_id=session.id,
            total_segments=transcript_in.total_segments,
            raw_transcript=transcript_in.raw_transcript,
        )

        db.add(new_transcript)
        await db.commit()
        await db.refresh(new_transcript)

        # Reload with relationships
        stmt = (
            select(RawTranscript)
            .options(
                joinedload(RawTranscript.session).joinedload(
                    CounselingSession.counselor
                )
            )
            .where(RawTranscript.id == new_transcript.id)
        )
        result = await db.execute(stmt)
        transcript_with_relations = result.scalar_one_or_none()

        return RawTranscriptResponse(
            uid=transcript_with_relations.uid,
            total_segments=transcript_with_relations.total_segments,
            raw_transcript=transcript_with_relations.raw_transcript,
            created_at=transcript_with_relations.created_at,
            updated_at=transcript_with_relations.updated_at,
            session=transcript_with_relations.session,
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def get_raw_transcript_by_uid(
    db: AsyncSession, transcript_uid: str
) -> RawTranscriptResponse:
    try:
        stmt = (
            select(RawTranscript)
            .options(
                joinedload(RawTranscript.session).joinedload(
                    CounselingSession.counselor
                )
            )
            .where(RawTranscript.uid == transcript_uid)
        )
        result = await db.execute(stmt)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise NotFoundException(details=f"Transcript {transcript_uid} not found")

        return RawTranscriptResponse(
            uid=transcript.uid,
            total_segments=transcript.total_segments,
            raw_transcript=transcript.raw_transcript,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            session=transcript.session,
        )

    except SQLAlchemyError as e:
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


# async def get_raw_transcript_by_session_uid(
#     db: AsyncSession, session_uid: str
# ) -> RawTranscriptResponse:
#     try:
#         stmt = (
#             select(RawTranscript)
#             .join(RawTranscript.session)
#             .options(
#                 joinedload(RawTranscript.session).joinedload(
#                     CounselingSession.counselor
#                 )
#             )
#             .where(CounselingSession.uid == session_uid)
#         )
#         result = await db.execute(stmt)
#         transcript = result.scalar_one_or_none()

#         if not transcript:
#             raise NotFoundException(
#                 details=f"No transcript found for session {session_uid}"
#             )

#         return RawTranscriptResponse(
#             uid=transcript.uid,
#             total_segments=transcript.total_segments,
#             raw_transcript=transcript.raw_transcript,
#             created_at=transcript.created_at,
#             updated_at=transcript.updated_at,
#             session=transcript.session,
#         )

#     except SQLAlchemyError as e:
#         raise BaseAppException(
#             error="Database Error",
#             details=str(e),
#             status_code=500,
#         )


async def get_raw_transcript_by_session_uid_with_status(
    db: AsyncSession, session_uid: str
) -> RawTranscriptWithStatusResponse:
    """
    Get raw transcript by session UID, but only return full data if analysis is completed.
    Returns status and empty data if analysis is not completed.
    """
    try:
        # First, check the session analysis status
        analysis_stmt = (
            select(SessionAnalysis)
            .join(SessionAnalysis.session)
            .where(CounselingSession.uid == session_uid)
        )
        analysis_result = await db.execute(analysis_stmt)
        analysis = analysis_result.scalar_one_or_none()
        
        # Get status
        status = "PENDING"  # Default status
        if analysis and hasattr(analysis, 'status'):
            status = analysis.status.value if hasattr(analysis.status, 'value') else str(analysis.status)
        
        # If analysis is not completed, return only status with empty data
        if status != "COMPLETED":
            return RawTranscriptWithStatusResponse(
                status=status,
                uid=None,
                total_segments=None,
                raw_transcript=None,
                created_at=None,
                updated_at=None,
                session=None
            )
        
        # If completed, get and return full transcript data
        stmt = (
            select(RawTranscript)
            .join(RawTranscript.session)
            .options(
                joinedload(RawTranscript.session).joinedload(
                    CounselingSession.counselor
                )
            )
            .where(CounselingSession.uid == session_uid)
        )
        result = await db.execute(stmt)
        transcript = result.scalar_one_or_none()

        if not transcript:
            # Analysis is completed but no transcript found
            return RawTranscriptWithStatusResponse(
                status=status,
                uid=None,
                total_segments=None,
                raw_transcript=None,
                created_at=None,
                updated_at=None,
                session=None
            )

        return RawTranscriptWithStatusResponse(
            status=status,
            uid=str(transcript.uid),
            total_segments=transcript.total_segments,
            raw_transcript=transcript.raw_transcript,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            session=transcript.session,
        )

    except SQLAlchemyError as e:
        raise BaseAppException(
            error="Database Error", details=str(e), status_code=500
        )


async def update_raw_transcript(
    db: AsyncSession, transcript_uid: str, transcript_in: RawTranscriptUpdate
) -> RawTranscriptResponse:
    try:
        stmt = (
            select(RawTranscript)
            .options(
                joinedload(RawTranscript.session).joinedload(
                    CounselingSession.counselor
                )
            )
            .where(RawTranscript.uid == transcript_uid)
        )
        result = await db.execute(stmt)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise NotFoundException(details=f"Transcript {transcript_uid} not found")

        # Apply updates only for fields that are set
        update_data = transcript_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(transcript, key, value)

        await db.commit()
        await db.refresh(transcript)

        return RawTranscriptResponse(
            uid=transcript.uid,
            total_segments=transcript.total_segments,
            raw_transcript=transcript.raw_transcript,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
            session=transcript.session,
        )

    except SQLAlchemyError as e:
        await db.rollback()
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def delete_raw_transcript(db: AsyncSession, transcript_uid: str) -> dict:
    try:
        stmt = select(RawTranscript).where(RawTranscript.uid == transcript_uid)
        result = await db.execute(stmt)
        transcript = result.scalar_one_or_none()

        if not transcript:
            raise NotFoundException(details=f"Transcript {transcript_uid} not found")

        await db.delete(transcript)
        await db.commit()

        return {"message": "Transcript deleted successfully"}

    except SQLAlchemyError as e:
        await db.rollback()
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )
