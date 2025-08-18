import logging
import json
from uuid import UUID
from app.service.video_processing.video_processing import VideoProcessor

# from service.video_processing.video_processing import VideoProcessor
from app.service.audio_processing.deepgram_transcriber import DeepgramTranscriber
from app.service.course_verification.course_verifier import CourseVerifier
from app.service.raw_transcript_service import create_raw_transcript
from app.schemas.raw_transcript_schema import RawTranscriptCreate
from app.service.video_processing.video_extraction import VideoExtractor
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
from app.config.log_config import get_logger

from app.config.log_config import get_logger

logger = get_logger("session_service")


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
            counselor=CounselorInfo(uid=str(counselor.uid), name=counselor.name),
        )

    except SQLAlchemyError as e:
        await db.rollback()
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
                uid=str(session.counselor.uid), name=session.counselor.name
            ),
        )
    except SQLAlchemyError as e:
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

        # Get total count of sessions for this counselor
        total_result = await db.execute(
            select(CounselingSession).filter(
                CounselingSession.counselor_id == counselor.id
            )
        )
        total = len(total_result.scalars().all())

        # Fetch paginated sessions
        result = await db.execute(
            select(CounselingSession)
            .options(joinedload(CounselingSession.counselor))
            .filter(CounselingSession.counselor_id == counselor.id)
            .offset(skip)
            .limit(limit)
        )
        sessions = result.scalars().all()

        # Format the response
        items = [
            SessionResponse(
                uid=session.uid,
                description=session.description,
                session_date=session.session_date,
                recording_link=session.recording_link,
                counselor=CounselorInfo(
                    uid=session.counselor.uid,
                    name=session.counselor.name,
                ),
            )
            for session in sessions
        ]

        return items, total

    except SQLAlchemyError as e:
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def get_all_sessions(db: AsyncSession, skip: int = 0, limit: int = 10):
    try:
        # Get total count
        total_result = await db.execute(select(CounselingSession))
        total = len(total_result.scalars().all())

        # Fetch paginated sessions with their counselors
        result = await db.execute(
            select(CounselingSession)
            .options(joinedload(CounselingSession.counselor))
            .offset(skip)
            .limit(limit)
        )
        sessions = result.scalars().all()

        # Format the response
        items = [
            SessionResponse(
                uid=session.uid,
                description=session.description,
                session_date=session.session_date,
                recording_link=session.recording_link,
                counselor=CounselorInfo(
                    uid=session.counselor.uid,
                    name=session.counselor.name,
                ),
            )
            for session in sessions
        ]
        return items, total

    except SQLAlchemyError as e:
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def update_session(
    db: AsyncSession, session_uid: str, session_in: SessionUpdate
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
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def delete_session(db: AsyncSession, session_uid: str):
    session = await get_session_by_id(db, session_uid)
    try:
        await db.delete(session)
        await db.commit()
        return {"message": "Session deleted successfully"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def process_video_background(db: AsyncSession, session_uid: UUID):
    """
    Background task to process video for a counseling session.
    This function runs asynchronously after session creation.
    """
    try:
        print(f"Starting video processing for session {session_uid}")
        sessionResponse = await get_session_by_id(db, session_uid)

        extraction = VideoExtractor()
        extraction_data = extraction.get_video_frames_and_audio_paths(str(sessionResponse.recording_link))

        # Initialize video processor
        video_processor = VideoProcessor()
        results = await video_processor.analyze_video(extraction_data)

        audio_path = extraction_data.get("audio_path")
        transcript_data = None
        
        # If transcription wasn't already done in video processing, do it here
        if audio_path:
            try:
                print(f"Starting Deepgram transcription for audio: {audio_path}")
                transcriber = DeepgramTranscriber()
                transcript_data = transcriber.transcribe_chunk(audio_path, str(session_uid))
                print(f"Transcription completed successfully")
                
                # Save transcript to database
                try:
                    total_segments = len(transcript_data.get("utterances", []))
                    transcript_create = RawTranscriptCreate(
                        session_uid=str(session_uid),
                        total_segments=total_segments,
                        raw_transcript=transcript_data
                    )
                    
                    saved_transcript = await create_raw_transcript(db, transcript_create)
                    print(f"Transcript saved to database with UID: {saved_transcript.uid}")
                    results["transcript_saved"] = True
                    results["transcript_uid"] = saved_transcript.uid
                    
                except Exception as db_error:
                    print(f"Warning: Failed to save transcript to database: {db_error}")
                    results["transcript_db_error"] = str(db_error)
                    
            except Exception as transcription_error:
                print(f"Warning: Transcription failed: {transcription_error}")
                results["transcription_error"] = str(transcription_error)

        print(f"Video processing completed for session {session_uid}")

        # Verify course information if transcription was successful
        if transcript_data:
            try:
                print(f"Starting course verification for session {session_uid}")

                # Use transcript data directly instead of loading from file
                # Initialize course verifier
                verifier = CourseVerifier()

                # Verify course information
                verification_result = verifier.verify_full_transcript(transcript_data)

                # Save verification results
                from pathlib import Path

                verification_dir = Path("assets/verification_results")
                verification_dir.mkdir(parents=True, exist_ok=True)

                verification_file = (
                    verification_dir / f"verification_{session_uid}.json"
                )
                with open(verification_file, "w", encoding="utf-8") as f:
                    json.dump(verification_result, f, indent=2, ensure_ascii=False)

                results["verification_path"] = str(verification_file)
                results["accuracy_score"] = str(verification_result["accuracy_score"])
                results["red_flags_count"] = str(len(verification_result["red_flags"]))

                print(f"Course verification completed: {verification_file}")
                print(f"Accuracy score: {verification_result['accuracy_score']:.2f}")

                if verification_result["red_flags"]:
                    print(
                        f"⚠️  {len(verification_result['red_flags'])} red flags detected:"
                    )
                    for flag in verification_result["red_flags"]:
                        print(f"   • {flag}")

            except Exception as verification_error:
                print(f"Warning: Course verification failed: {verification_error}")
                results["verification_error"] = str(verification_error)

        return results

        # Here you can add logic to store the results in the database
        # or send them to another service for further processing

    except Exception as e:
        logger.error(f"Error processing video for session {session_uid}: {e}")
        # Background task failure might not need raising API exception
        # but for consistency:
        raise BaseAppException(
            error="Video Processing Error",
            details=str(e),
            status_code=500,
        )
    finally:
            try:
                extraction.cleanup()
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")