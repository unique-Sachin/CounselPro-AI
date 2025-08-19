from celery import Celery
from app.exceptions.custom_exception import BadRequestException, BaseAppException
from app.models.session_analysis import AnalysisStatus, SessionAnalysis
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

celery_app = Celery(
    "tasks",
    broker=os.getenv("REDIS_URL/{0}"),
    backend=os.getenv("REDIS_URL/{1}"),
)


@celery_app.task
def process_video(db: AsyncSession, session_uid: str, video_path: str):
    try:
        # Update status → started
        analysis_entry = (
            db.query(SessionAnalysis)
            .filter(SessionAnalysis.session.uid == session_uid)
            .first()
        )
        analysis_entry.status = AnalysisStatus.STARTED
        db.commit()

        # 🔽 Place your video analysis logic here
        # e.g., speech-to-text, duration, participants, etc.
        result_data = {"summary": "Video analyzed successfully"}  # <-- dummy result

        # Save result in DB
        analysis_entry.status = AnalysisStatus.COMPLETED
        # analysis_entry.analysis_result = str(result_data)  # can use json.dumps
        db.commit()
    except Exception as e:
        analysis_entry.status = AnalysisStatus.FAILED
        db.commit()
        raise BaseAppException(
            error="Video analysis failed",
            details=str(e),
            status_code=500,
        )
    finally:
        db.close()
