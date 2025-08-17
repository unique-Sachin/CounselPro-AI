import logging
import os
from pathlib import Path
from uuid import UUID
from typing import List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import UploadFile, HTTPException

from app.models.catalog_file import CatalogFile
from app.service.course_verification.catalog_indexer import CourseCatalogIndexer

logger = logging.getLogger(__name__)


async def save_uploaded_file(db: AsyncSession, file: UploadFile) -> CatalogFile:
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    allowed_extensions = {'.pdf', '.docx', '.txt', '.md'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create directory if not exists
    catalog_dir = Path("assets/course_catalogs")
    catalog_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate file path
    file_path = catalog_dir / f"{file.filename}"
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create database record
    catalog_file = CatalogFile(
        filename=file.filename,
        file_path=str(file_path),
        status="uploaded"
    )
    
    db.add(catalog_file)
    await db.commit()
    await db.refresh(catalog_file)
    
    return catalog_file


async def get_all_files(db: AsyncSession) -> List[CatalogFile]:
    result = await db.execute(select(CatalogFile))
    return list(result.scalars().all())


async def index_catalog_files(db: AsyncSession):
    # Get all uploaded files
    result = await db.execute(
        select(CatalogFile).where(CatalogFile.status == "uploaded")
    )
    files = result.scalars().all()
    
    if not files:
        return
    
    # Initialize indexer
    indexer = CourseCatalogIndexer()
    
    for file in files:
        try:
            # Index single file with custom IDs
            documents = indexer.load_documents_from_file(getattr(file, "file_path"))
            chunks = indexer.chunk_documents(documents)
            chunk_count = indexer.index_documents_with_ids(chunks, str(getattr(file, "uid")))
            
            # Update status with chunk count and indexed timestamp
            setattr(file, "status", "indexed")
            setattr(file, "chunk_count", chunk_count)
            setattr(file, "indexed_at", datetime.now())
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to index {getattr(file, 'filename')}: {e}")
            setattr(file, "status", "failed")
            await db.commit()


async def delete_catalog_file(db: AsyncSession, file_uid: UUID):
    # Get file from database
    result = await db.execute(
        select(CatalogFile).where(CatalogFile.uid == file_uid)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is indexed
    if getattr(file, "status") == "indexed":
        raise HTTPException(status_code=400, detail="Cannot delete indexed file")
    
    # Delete physical file
    file_path = Path(getattr(file, "file_path"))
    if file_path.exists():
        file_path.unlink()
    
    # Delete database record
    await db.delete(file)
    await db.commit()


async def unindex_catalog_file(db: AsyncSession, file_uid: UUID):
    # Get file from database
    result = await db.execute(
        select(CatalogFile).where(CatalogFile.uid == file_uid)
    )
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check if file is indexed
    if getattr(file, "status") != "indexed":
        raise HTTPException(status_code=400, detail="File is not indexed")
    
    # Initialize indexer and unindex
    indexer = CourseCatalogIndexer()
    chunk_count = getattr(file, "chunk_count")
    indexer.unindex_file(str(getattr(file, "uid")), chunk_count)
    
    # Update database record
    setattr(file, "status", "uploaded")
    setattr(file, "chunk_count", 0)
    setattr(file, "indexed_at", None)
    await db.commit()
