from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.service.cloudinary_upload_service import upload_file_to_cloudinary
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test"])


@router.post("/upload")
async def test_cloudinary_upload(file: UploadFile = File(...)):
    """
    Test route for uploading files to Cloudinary

    Args:
        file: File to upload

    Returns:
        JSON response with upload result or error
    """
    try:
        # Validate file exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Test upload with basic settings
        result = await upload_file_to_cloudinary(
            file=file, folder="catalogues", tags=["test", "upload_verification"]
        )

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "File uploaded successfully",
                "data": result,
            },
        )

    except HTTPException as he:
        logger.error(f"HTTP error during test upload: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during test upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload test failed: {str(e)}")
