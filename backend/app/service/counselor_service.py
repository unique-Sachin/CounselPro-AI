import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.counselor import Counselor
from app.schemas.counselor_schema import (
    CounselorCreate,
    CounselorUpdate,
    CounselorResponse,
)
from fastapi import HTTPException
from uuid import UUID
from app.exceptions.custom_exception import BaseAppException, NotFoundException
import traceback

logger = logging.getLogger(__name__)


async def create_counselor(
    db: AsyncSession, counselor_in: CounselorCreate
) -> Counselor:
    try:
        new_counselor = Counselor(**counselor_in.model_dump())
        print(new_counselor.__dict__)  # Debugging line to check the counselor data
        db.add(new_counselor)
        await db.commit()
        await db.refresh(new_counselor)
        return new_counselor
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error creating counselor: {e}")

        traceback.print_exc()
        # return {"error": "Database Error", "details": str(e)}

        raise BaseAppException(
            error="Database Error",
            details=str(e),  # 👈 actual SQLAlchemy error message
            status_code=500,
        )


async def get_counselor(db: AsyncSession, counselor_uid: UUID) -> Counselor:
    try:
        result = await db.execute(
            select(Counselor).where(Counselor.uid == counselor_uid)
        )
        counselor = result.scalars().first()
        if not counselor:
            raise NotFoundException(details=f"Counselor {counselor_uid} not found")
        return counselor
    except SQLAlchemyError as e:
        logger.error(f"Error fetching counselor {counselor_uid}: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def update_counselor(
    db: AsyncSession, counselor_uid: UUID, updates: CounselorUpdate
) -> Counselor:
    try:
        counselor = await get_counselor(db, counselor_uid)
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(counselor, key, value)
        await db.commit()
        await db.refresh(counselor)
        return counselor
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error updating counselor {counselor_uid}: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def delete_counselor(db: AsyncSession, counselor_uid: UUID) -> dict:
    try:
        counselor = await get_counselor(db, counselor_uid)
        await db.delete(counselor)
        await db.commit()
        return {}
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error deleting counselor {counselor_uid}: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )


async def get_all_counselors(db: AsyncSession, skip: int = 0, limit: int = 10):
    try:
        query = select(Counselor).offset(skip).limit(limit)
        result = await db.execute(query)
        counselors = result.scalars().all()
        return counselors
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all counselors: {e}")
        raise BaseAppException(
            error="Database Error",
            details=str(e),
            status_code=500,
        )
