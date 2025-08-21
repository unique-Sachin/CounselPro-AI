import os
import uuid
from celery import Celery
from dotenv import load_dotenv

from app.models.session import CounselingSession
from app.models.session_analysis import AnalysisStatus, SessionAnalysis
from app.schemas.raw_transcript_schema import RawTranscriptCreate
from app.schemas.session_analysis_schema import SessionAnalysisCreate

# from app.service.raw_transcript_service import create_raw_transcript
from app.service.celery.video_processing_for_celery import (
    create_or_update_raw_transcript,
    create_or_update_session_analysis,
)
from app.service.celery.video_processing_for_celery import process_video_background
from app.db.database import SyncSessionLocal
from sqlalchemy.orm import joinedload

load_dotenv()

celery_app = Celery(
    "tasks",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
)


@celery_app.task
def process_video(session_uid: str, video_path: str):
    db = SyncSessionLocal()
    analysis_entry = None

    try:
        # Fetch or create analysis entry
        session_obj = (
            db.query(CounselingSession)
            .filter(CounselingSession.uid == str(session_uid))
            .first()
        )
        print("Session:", session_obj)

        analysis_entry = (
            db.query(SessionAnalysis)
            .filter(SessionAnalysis.session_id == session_obj.id)
            .first()
        )
        print("Analysis:", analysis_entry)

        if not analysis_entry:  # if not found then create new one
            analysis_entry = SessionAnalysis(
                session_id=session_obj.id,
                status=AnalysisStatus.STARTED,
            )
            db.add(analysis_entry)
            db.commit()
            db.refresh(analysis_entry)
        else:
            # STARTED
            analysis_entry.status = AnalysisStatus.STARTED
            db.commit()

        # ---- Run pure video processing ----
        results = process_video_background(uuid.UUID(session_uid), video_path)

        # ---- Save transcript ----
        if results.get("transcript_data"):
            transcript_create = RawTranscriptCreate(
                session_uid=str(session_uid),
                total_segments=len(results["transcript_data"].get("utterances", [])),
                raw_transcript=results["transcript_data"],
            )
            create_or_update_raw_transcript(db, transcript_create)

        # ---- Save analysis ----
        session_analysis_create = SessionAnalysisCreate(
            session_uid=str(session_uid),
            video_analysis_data=results["video_analysis_data"],
            audio_analysis_data=results["audio_analysis_data"],
        )
        saved_analysis = create_or_update_session_analysis(db, session_analysis_create)

        # COMPLETED
        analysis_entry.status = AnalysisStatus.COMPLETED
        db.commit()
        print(f"Session analysis saved/updated with UID: {saved_analysis.uid}")

    except Exception as e:
        print(f"Error processing video: {e}")
        if analysis_entry:
            analysis_entry.status = AnalysisStatus.FAILED
            db.commit()
        raise

    finally:
        db.close()
