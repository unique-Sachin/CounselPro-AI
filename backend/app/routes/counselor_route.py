from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from service.counselor_service import create_counselor, get_counselor, update_counselor
from schemas.counselor_schema import CounselorCreate, CounselorUpdate, CounselorResponse
from db.database import get_async_db

router = APIRouter(prefix="/counselors", tags=["Counselors"])


@router.post("/", response_model=CounselorResponse)
async def create_counselor_route(
    counselor: CounselorCreate, db: AsyncSession = Depends(get_async_db)
):
    return await create_counselor(db, counselor)


@router.get("/{counselor_id}", response_model=CounselorResponse)
async def get_counselor_route(
    counselor_id: str, db: AsyncSession = Depends(get_async_db)
):
    return await get_counselor(db, counselor_id)


@router.put("/{counselor_id}", response_model=CounselorResponse)
async def update_counselor_route(
    counselor_id: str,
    updates: CounselorUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    return await update_counselor(db, counselor_id, updates)
