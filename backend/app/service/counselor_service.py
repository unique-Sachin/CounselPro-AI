import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from models.counselor import Counselor
from schemas.counselor_schema import CounselorCreate, CounselorUpdate
from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def create_counselor(
    db: AsyncSession, counselor_in: CounselorCreate
) -> Counselor:
    try:
        new_counselor = Counselor(**counselor_in.model_dump())
        db.add(new_counselor)
        await db.commit()
        await db.refresh(new_counselor)
        return new_counselor
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error creating counselor: {e}")
        print(e)
        raise HTTPException(status_code=500, detail="Failed to create counselor")


async def get_counselor(db: AsyncSession, counselor_id: str) -> Counselor:
    try:
        result = await db.execute(select(Counselor).where(Counselor.id == counselor_id))
        counselor = result.scalars().first()
        if not counselor:
            raise HTTPException(status_code=404, detail="Counselor not found")
        return counselor
    except SQLAlchemyError as e:
        logger.error(f"Error fetching counselor {counselor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch counselor")


async def update_counselor(
    db: AsyncSession, counselor_id: str, updates: CounselorUpdate
) -> Counselor:
    try:
        counselor = await get_counselor(db, counselor_id)
        for key, value in updates.model_dump(exclude_unset=True).items():
            setattr(counselor, key, value)
        await db.commit()
        await db.refresh(counselor)
        return counselor
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error updating counselor {counselor_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update counselor")
