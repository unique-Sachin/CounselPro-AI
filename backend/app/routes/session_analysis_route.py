from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_async_db
from app.schemas.session_analysis_schema import (
    SessionAnalysisCreate,
    SessionAnalysisResponse,
    SessionAnalysisBulkResponse,
    SessionAnalysisWithStatusResponse,
)
from app.service.session_analysis_service import (
    create_session_analysis as create_analysis,
    get_analysis_by_uid,
    get_analysis_by_session_uid,
    get_analysis_by_session_uid_with_status,
    update_session_analysis as update_analysis,
    delete_session_analysis as delete_analysis,
    get_limited_analyses_by_session_uids,
)
from app.exceptions.custom_exception import (
    BaseAppException,
    NotFoundException,
    BadRequestException,
)
from uuid import UUID

router = APIRouter(prefix="/session-analysis", tags=["Session Analysis"])


@router.post("/", response_model=SessionAnalysisResponse)
async def create_session_analysis(
    session_analysis: SessionAnalysisCreate, db: AsyncSession = Depends(get_async_db)
):
    return await create_analysis(db, session_analysis)


@router.get("/bulk", response_model=SessionAnalysisBulkResponse)
async def get_bulk_session_analyses(
    session_ids: str, db: AsyncSession = Depends(get_async_db)
):
    """Get session analyses for multiple session UIDs (comma-separated)."""
    if not session_ids:
        raise BadRequestException(details="session_ids parameter is required")
    
    # Split the comma-separated session IDs
    session_uid_list = [uid.strip() for uid in session_ids.split(",") if uid.strip()]
    
    if not session_uid_list:
        raise BadRequestException(details="No valid session IDs provided")
    
    limited_analyses = await get_limited_analyses_by_session_uids(db, session_uid_list)
    return SessionAnalysisBulkResponse(analyses=limited_analyses)


@router.get("/{uid}", response_model=SessionAnalysisResponse)
async def get_session_analysis(uid: str, db: AsyncSession = Depends(get_async_db)):
    analysis = await get_analysis_by_uid(db, uid)
    if not analysis:
        raise NotFoundException(details="Session analysis not found")
    return analysis


@router.get("/by-session/{session_uid}", response_model=SessionAnalysisWithStatusResponse)
async def get_analysis_by_session(
    session_uid: str, db: AsyncSession = Depends(get_async_db)
):
    """
    Get session analysis by session UID.
    Returns full analysis data only if status is 'COMPLETED',
    otherwise returns status with empty data.
    """
    return await get_analysis_by_session_uid_with_status(db, session_uid)


@router.put("/{uid}", response_model=SessionAnalysisResponse)
async def update_session_analysis(
    uid: str,
    session_analysis: SessionAnalysisCreate,
    db: AsyncSession = Depends(get_async_db),
):
    updated_analysis = await update_analysis(db, uid, session_analysis)
    if not updated_analysis:
        raise NotFoundException(details="Session analysis not found")
    return updated_analysis


@router.delete("/{uid}")
async def delete_session_analysis(uid: str, db: AsyncSession = Depends(get_async_db)):
    success = await delete_analysis(db, uid)
    if not success:
        raise NotFoundException(details="Session analysis not found")
    return {"message": "Session analysis deleted successfully"}
