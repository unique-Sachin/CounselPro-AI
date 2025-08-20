from uuid import UUID
from app.models.raw_transcript import RawTranscript
from app.schemas.raw_transcript_schema import RawTranscriptCreate, RawTranscriptResponse
from app.service.video_processing.video_processing import VideoProcessor
from app.service.video_processing.video_extraction import VideoExtractor
from app.service.audio_processing.deepgram_transcriber import DeepgramTranscriber
from app.service.course_verification.course_verifier import CourseVerifier
from app.config.log_config import get_logger
from sqlalchemy.exc import SQLAlchemyError

# ============================================================
from sqlalchemy.orm import joinedload, Session
from app.db.database import SyncSessionLocal
from sqlalchemy.future import select
from app.models.session_analysis import SessionAnalysis
from app.models.session import CounselingSession
from app.schemas.session_analysis_schema import SessionAnalysisCreate
from app.exceptions.custom_exception import (
    BadRequestException,
    BaseAppException,
    NotFoundException,
)

logger = get_logger("video_processing_for_celery")


def process_video_background(session_uid: UUID, recording_link: str):
    """
    Pure async function for video processing (no DB writes).
    - Extracts video & audio
    - Runs video analysis
    - Runs transcription
    - Runs course verification
    - Returns structured results for DB persistence
    """

    extraction = None
    transcript_data = None
    video_analysis_data = None
    audio_analysis_data = None

    try:
        print(f"Starting video processing for session {session_uid}")

        # Extract frames + audio
        extraction = VideoExtractor()
        extraction_data = extraction.get_video_frames_and_audio_paths(
            str(recording_link)
        )

        # ---- Video Analysis ----
        video_processor = VideoProcessor()
        video_analysis_data = video_processor.analyze_video_for_celery(extraction_data)

        # ---- Transcription ----
        audio_path = extraction_data.get("audio_path")
        if audio_path:
            try:
                print(f"Starting Deepgram transcription for audio: {audio_path}")
                transcriber = DeepgramTranscriber()
                transcript_data = transcriber.transcribe_chunk(
                    audio_path, str(session_uid)
                )
                print("Transcription completed successfully")
            except Exception as transcription_error:
                print(f"Warning: Transcription failed: {transcription_error}")

        # ---- Course Verification ----
        if transcript_data:
            try:
                print(f"Starting course verification for session {session_uid}")
                verifier = CourseVerifier()
                audio_analysis_data = verifier.verify_full_transcript(transcript_data)
            except Exception as verification_error:
                print(f"Warning: Course verification failed: {verification_error}")

        print(f"Video processing completed for session {session_uid}")

        # ✅ Return all results to Celery task
        return {
            "video_analysis_data": video_analysis_data,
            "audio_analysis_data": audio_analysis_data,
            "transcript_data": transcript_data,
        }

    except Exception as e:
        logger.error(f"Error processing video for session {session_uid}: {e}")
        raise

    finally:
        try:
            if extraction:
                extraction.cleanup()
        except Exception as cleanup_error:
            logger.warning(f"Error during cleanup: {cleanup_error}")


def create_or_update_session_analysis(
    db: Session, session_analysis: SessionAnalysisCreate
) -> SessionAnalysis:
    """
    Create a new session analysis or update existing one if it already exists.
    This is a synchronous "upsert" operation.
    """

    # First get the session by its uid
    session = (
        db.query(CounselingSession)
        .filter(CounselingSession.uid == session_analysis.session_uid)
        .first()
    )

    if not session:
        raise NotFoundException(details="Session not found")

    # Check if analysis already exists for this session
    existing_analysis = (
        db.query(SessionAnalysis)
        .filter(SessionAnalysis.session_id == session.id)
        .first()
    )

    if existing_analysis:
        # Update existing analysis
        existing_analysis.video_analysis_data = session_analysis.video_analysis_data
        existing_analysis.audio_analysis_data = session_analysis.audio_analysis_data
        db.commit()
        db.refresh(existing_analysis)

        # Reload with relationships
        analysis = (
            db.query(SessionAnalysis)
            .options(
                joinedload(SessionAnalysis.session).joinedload(
                    CounselingSession.counselor
                )
            )
            .filter(SessionAnalysis.id == existing_analysis.id)
            .first()
        )
        return analysis
    else:
        # Create new analysis
        db_session_analysis = SessionAnalysis(
            session_id=session.id,
            video_analysis_data=session_analysis.video_analysis_data,
            audio_analysis_data=session_analysis.audio_analysis_data,
        )
        db.add(db_session_analysis)
        db.commit()
        db.refresh(db_session_analysis)

        # Reload with relationships
        analysis = (
            db.query(SessionAnalysis)
            .options(
                joinedload(SessionAnalysis.session).joinedload(
                    CounselingSession.counselor
                )
            )
            .filter(SessionAnalysis.id == db_session_analysis.id)
            .first()
        )
        return analysis


def create_raw_transcript(
    db: Session, transcript_in: RawTranscriptCreate
) -> RawTranscriptResponse:
    try:
        # Find session by UID
        result = db.execute(
            select(CounselingSession)
            .options(joinedload(CounselingSession.counselor))
            .where(CounselingSession.uid == transcript_in.session_uid)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundException(details="Counseling session not found")

        # Check if transcript already exists for this session
        result = db.execute(
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
        db.commit()
        db.refresh(new_transcript)

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
        result = db.execute(stmt)
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
        db.rollback()
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )
