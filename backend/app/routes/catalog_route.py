from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.database import get_async_db
from app.schemas.catalog_schema import CatalogFileResponse
from app.service.catalog_service import (
    save_uploaded_file,
    get_all_files,
    index_catalog_files,
    delete_catalog_file,
    unindex_catalog_file,
)

router = APIRouter(prefix="/catalog", tags=["Catalog Management"])


@router.post("/upload", response_model=CatalogFileResponse)
async def upload_catalog(
    file: UploadFile = File(..., description="Course catalog file (PDF, DOCX, TXT, MD)"),
    db: AsyncSession = Depends(get_async_db)
):
    catalog_file = await save_uploaded_file(db, file)
    return CatalogFileResponse(
        uid=getattr(catalog_file, "uid"),
        filename=getattr(catalog_file, "filename"),
        uploaded_at=getattr(catalog_file, "uploaded_at"),
        status=getattr(catalog_file, "status"),
        chunk_count=getattr(catalog_file, "chunk_count"),
        indexed_at=getattr(catalog_file, "indexed_at")
    )


@router.get("/files", response_model=List[CatalogFileResponse])
async def list_catalog_files(db: AsyncSession = Depends(get_async_db)):
    files = await get_all_files(db)
    return [
        CatalogFileResponse(
            uid=getattr(file, "uid"),
            filename=getattr(file, "filename"),
            uploaded_at=getattr(file, "uploaded_at"),
            status=getattr(file, "status"),
            chunk_count=getattr(file, "chunk_count"),
            indexed_at=getattr(file, "indexed_at")
        )
        for file in files
    ]


@router.post("/index")
async def index_catalogs(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    background_tasks.add_task(index_catalog_files, db)
    return {"message": "Indexing started"}


@router.delete("/files/{file_uid}")
async def delete_catalog(
    file_uid: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    await delete_catalog_file(db, file_uid)
    return {"message": "File deleted successfully"}


@router.post("/unindex/{file_uid}")
async def unindex_catalog(
    file_uid: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    await unindex_catalog_file(db, file_uid)
    return {"message": "File unindexed successfully"}
