"""
Cloudinary Upload Service

This module provides function-based utilities for uploading files to Cloudinary.
It serves as a simplified interface for file upload operations.
"""

import logging
import os
from typing import Dict, Optional, Union, List
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)


# Initialize Cloudinary configuration
def _initialize_cloudinary():
    """Initialize Cloudinary configuration from environment variables"""
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        raise ValueError(
            "Missing Cloudinary credentials. Please set CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET environment variables."
        )

    cloudinary.config(
        cloud_name=cloud_name, api_key=api_key, api_secret=api_secret, secure=True
    )

    logger.info("Cloudinary configuration initialized")


# Initialize on module import
_initialize_cloudinary()


async def upload_file_to_cloudinary(
    file: UploadFile,
    folder: str = "counselpro",
    resource_type: str = "auto",
    public_id: Optional[str] = None,
    overwrite: bool = False,
    tags: Optional[List[str]] = None,
    context: Optional[Dict[str, str]] = None,
) -> Dict[str, Union[str, int]]:
    """
    Upload a file to Cloudinary

    Args:
        file: FastAPI UploadFile object
        folder: Cloudinary folder to upload to
        resource_type: Type of resource (auto, image, video, raw)
        public_id: Custom public ID for the file
        overwrite: Whether to overwrite existing files
        tags: List of tags to add to the file
        context: Additional context metadata

    Returns:
        Dictionary containing upload result information

    Raises:
        HTTPException: If upload fails or file is invalid
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Read file content
        content = await file.read()

        # Reset file pointer for potential future use
        await file.seek(0)

        # Prepare upload options
        upload_options = {
            "folder": folder,
            "resource_type": resource_type,
            "overwrite": overwrite,
            "use_filename": True,
            "unique_filename": not overwrite,
        }

        if public_id:
            upload_options["public_id"] = public_id

        if tags:
            upload_options["tags"] = tags

        # Add context metadata
        if not context:
            context = {}

        context.update(
            {
                "uploaded_at": datetime.now().isoformat(),
                "original_filename": file.filename,
            }
        )
        upload_options["context"] = context

        # Upload to Cloudinary
        result = cloudinary.uploader.upload(content, **upload_options)

        logger.info(
            f"Successfully uploaded {file.filename} to Cloudinary: {result['public_id']}"
        )

        return {
            "public_id": result["public_id"],
            "secure_url": result["secure_url"],
            "url": result["url"],
            "format": result["format"],
            "resource_type": result["resource_type"],
            "bytes": result["bytes"],
            "created_at": result["created_at"],
            "folder": result.get("folder", ""),
            "original_filename": file.filename,
            "version": result["version"],
            "etag": result["etag"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload {file.filename} to Cloudinary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file to Cloudinary: {str(e)}"
        )


async def upload_multiple_files_to_cloudinary(
    files: List[UploadFile],
    folder: str = "counselpro",
    resource_type: str = "auto",
    tags: Optional[List[str]] = None,
    context: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Union[str, int]]]:
    """
    Upload multiple files to Cloudinary

    Args:
        files: List of FastAPI UploadFile objects
        folder: Cloudinary folder to upload to
        resource_type: Type of resource (auto, image, video, raw)
        tags: List of tags to add to all files
        context: Additional context metadata for all files

    Returns:
        List of dictionaries containing upload results
    """
    results = []
    failed_uploads = []

    for file in files:
        try:
            result = await upload_file_to_cloudinary(
                file=file,
                folder=folder,
                resource_type=resource_type,
                tags=tags,
                context=context,
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to upload {file.filename}: {e}")
            failed_uploads.append({"filename": file.filename, "error": str(e)})

    if failed_uploads:
        logger.warning(f"Some files failed to upload: {failed_uploads}")

    return results


def delete_file_from_cloudinary(public_id: str, resource_type: str = "auto") -> bool:
    """
    Delete a file from Cloudinary

    Args:
        public_id: The public ID of the file to delete
        resource_type: Type of resource (auto, image, video, raw)

    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)

        if result.get("result") == "ok":
            logger.info(f"Successfully deleted {public_id} from Cloudinary")
            return True
        else:
            logger.warning(f"Failed to delete {public_id}: {result}")
            return False

    except Exception as e:
        logger.error(f"Error deleting {public_id} from Cloudinary: {e}")
        return False


def get_cloudinary_file_info(
    public_id: str, resource_type: str = "auto"
) -> Optional[Dict]:
    """
    Get information about a file in Cloudinary

    Args:
        public_id: The public ID of the file
        resource_type: Type of resource (auto, image, video, raw)

    Returns:
        Dictionary containing file information or None if not found
    """
    try:
        result = cloudinary.api.resource(public_id, resource_type=resource_type)
        return result
    except Exception as e:
        logger.error(f"Error getting info for {public_id}: {e}")
        return None


async def upload_course_catalog_file(file: UploadFile) -> Dict[str, Union[str, int]]:
    """
    Specialized function for uploading course catalog files

    Args:
        file: FastAPI UploadFile object containing the course catalog

    Returns:
        Dictionary containing upload result information
    """
    return await upload_file_to_cloudinary(
        file=file,
        folder="course_catalogs",
        resource_type="raw",  # Documents are uploaded as raw files
        tags=["course_catalog", "document"],
        context={
            "uploaded_by": "course_catalog_service",
            "file_type": "course_catalog",
        },
    )


async def upload_transcript_file(
    file: UploadFile, session_id: str
) -> Dict[str, Union[str, int]]:
    """
    Specialized function for uploading transcript files

    Args:
        file: FastAPI UploadFile object containing the transcript
        session_id: ID of the session this transcript belongs to

    Returns:
        Dictionary containing upload result information
    """
    return await upload_file_to_cloudinary(
        file=file,
        folder="transcripts",
        resource_type="raw",
        tags=["transcript", "session_data"],
        context={"uploaded_by": "transcript_service", "session_id": session_id},
    )


async def upload_audio_file(
    file: UploadFile, session_id: str
) -> Dict[str, Union[str, int]]:
    """
    Specialized function for uploading audio files

    Args:
        file: FastAPI UploadFile object containing the audio
        session_id: ID of the session this audio belongs to

    Returns:
        Dictionary containing upload result information
    """
    return await upload_file_to_cloudinary(
        file=file,
        folder="audio_files",
        resource_type="video",  # Audio files use 'video' resource type in Cloudinary
        tags=["audio", "session_recording"],
        context={"uploaded_by": "audio_service", "session_id": session_id},
    )


async def upload_video_file(
    file: UploadFile, session_id: str
) -> Dict[str, Union[str, int]]:
    """
    Specialized function for uploading video files

    Args:
        file: FastAPI UploadFile object containing the video
        session_id: ID of the session this video belongs to

    Returns:
        Dictionary containing upload result information
    """
    return await upload_file_to_cloudinary(
        file=file,
        folder="video_files",
        resource_type="video",
        tags=["video", "session_recording"],
        context={"uploaded_by": "video_service", "session_id": session_id},
    )
