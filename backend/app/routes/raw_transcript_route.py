from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.database import get_async_db
from app.schemas.raw_transcript_schema import (
    RawTranscriptCreate,
    RawTranscriptUpdate,
    RawTranscriptResponse,
    RawTranscriptWithStatusResponse,
)
from app.service.raw_transcript_service import (
    create_raw_transcript,
    get_raw_transcript_by_uid,
    get_raw_transcript_by_session_uid,
    get_raw_transcript_by_session_uid_with_status,
    update_raw_transcript,
    delete_raw_transcript,
)

router = APIRouter(prefix="/raw-transcripts", tags=["Raw Transcripts"])


@router.post("/", response_model=RawTranscriptResponse)
async def create_transcript(
    transcript_in: RawTranscriptCreate, db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new raw transcript for a counseling session.
    """
    return await create_raw_transcript(db, transcript_in)


@router.get("/{transcript_uid}", response_model=RawTranscriptResponse)
async def get_transcript(transcript_uid: str, db: AsyncSession = Depends(get_async_db)):
    """
    Get a raw transcript by its UID.
    """
    return await get_raw_transcript_by_uid(db, transcript_uid)


@router.get("/by-session/{session_uid}", response_model=RawTranscriptWithStatusResponse)
async def get_transcript_by_session(
    session_uid: str, db: AsyncSession = Depends(get_async_db)
):
    """
    Get a raw transcript by its associated session UID.
    Returns full transcript data only if analysis status is 'COMPLETED',
    otherwise returns status with empty data.
    """
    return await get_raw_transcript_by_session_uid_with_status(db, session_uid)


@router.put("/{transcript_uid}", response_model=RawTranscriptResponse)
async def update_transcript(
    transcript_uid: str,
    transcript_in: RawTranscriptUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update an existing raw transcript.
    """
    return await update_raw_transcript(db, transcript_uid, transcript_in)


@router.delete("/{transcript_uid}")
async def delete_transcript(
    transcript_uid: str, db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a raw transcript.
    """
    return await delete_raw_transcript(db, transcript_uid)
