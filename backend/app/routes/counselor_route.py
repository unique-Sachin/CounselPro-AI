from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.service.counselor_service import (
    create_counselor,
    get_counselor,
    update_counselor,
    delete_counselor,
    get_all_counselors,
)
from app.schemas.counselor_schema import (
    CounselorCreate,
    CounselorUpdate,
    CounselorResponse,
    CounselorListResponse,
)
from app.db.database import get_async_db

router = APIRouter(prefix="/counselors", tags=["Counselors"])


@router.post("/", response_model=CounselorResponse)
async def create_counselor_route(
    counselor: CounselorCreate, db: AsyncSession = Depends(get_async_db)
):
    return await create_counselor(db, counselor)


@router.get("/{counselor_uid}", response_model=CounselorResponse)
async def get_counselor_route(
    counselor_uid: str, db: AsyncSession = Depends(get_async_db)
):
    return await get_counselor(db, counselor_uid)


@router.put("/{counselor_uid}", response_model=CounselorResponse)
async def update_counselor_route(
    counselor_uid: str,
    updates: CounselorUpdate,
    db: AsyncSession = Depends(get_async_db),
):
    return await update_counselor(db, counselor_uid, updates)


@router.delete("/{counselor_uid}", status_code=204)
async def delete_counselor_route(
    counselor_uid: str,
    db: AsyncSession = Depends(get_async_db),
):
    await delete_counselor(db, counselor_uid)


@router.get("/", response_model=CounselorListResponse)
async def get_all_counselors_route(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
):
    items, total = await get_all_counselors(db, skip=skip, limit=limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }
