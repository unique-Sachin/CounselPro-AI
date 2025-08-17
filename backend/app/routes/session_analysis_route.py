from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.database import get_async_db
from app.schemas.session_analysis_schema import (
    SessionAnalysisCreate,
    SessionAnalysisResponse,
)
from app.service.session_analysis_service import (
    create_session_analysis as create_analysis,
    get_analysis_by_uid,
    get_analysis_by_session_uid,
    update_session_analysis as update_analysis,
    delete_session_analysis as delete_analysis,
)
from app.exceptions.custom_exception import (
    BaseAppException,
    NotFoundException,
    BadRequestException,
)
from uuid import UUID

router = APIRouter(prefix="/session-analysis", tags=["session-analysis"])


@router.post("/", response_model=SessionAnalysisResponse)
async def create_session_analysis(
    session_analysis: SessionAnalysisCreate, db: AsyncSession = Depends(get_async_db)
):
    return await create_analysis(db, session_analysis)


@router.get("/{uid}", response_model=SessionAnalysisResponse)
async def get_session_analysis(uid: UUID, db: AsyncSession = Depends(get_async_db)):
    analysis = await get_analysis_by_uid(db, uid)
    if not analysis:
        raise NotFoundException(details="Session analysis not found")
    return analysis


@router.get("/by-session/{session_uid}", response_model=SessionAnalysisResponse)
async def get_analysis_by_session(
    session_uid: UUID, db: AsyncSession = Depends(get_async_db)
):
    analysis = await get_analysis_by_session_uid(db, session_uid)
    if not analysis:
        raise NotFoundException(details="Session analysis not found")
    return analysis


@router.put("/{uid}", response_model=SessionAnalysisResponse)
async def update_session_analysis(
    uid: UUID,
    session_analysis: SessionAnalysisCreate,
    db: AsyncSession = Depends(get_async_db),
):
    updated_analysis = await update_analysis(db, uid, session_analysis)
    if not updated_analysis:
        raise NotFoundException(details="Session analysis not found")
    return updated_analysis


@router.delete("/{uid}")
async def delete_session_analysis(uid: UUID, db: AsyncSession = Depends(get_async_db)):
    success = await delete_analysis(db, uid)
    if not success:
        raise NotFoundException(details="Session analysis not found")
    return {"message": "Session analysis deleted successfully"}
