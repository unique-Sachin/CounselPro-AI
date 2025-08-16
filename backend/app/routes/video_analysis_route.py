from fastapi import APIRouter, HTTPException
from schemas.video_analysis_schema import VideoAnalysisRequest, VideoAnalysisResponse
from service.video_processing import VideoProcessor
import logging

router = APIRouter(prefix="/video-analysis", tags=["Video Analysis"])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(request: VideoAnalysisRequest):
    """
    Analyze a video from Google Drive for counseling session assessment.
    
    This endpoint analyzes the video to determine:
    - Camera status (on/off)
    - Professional attire assessment
    """
    try:
        logger.info(f"Starting video analysis for URL: {request.video_url}")
        
        # Initialize video processor
        processor = VideoProcessor()
        
        # Perform video analysis
        results = await processor.analyze_video(
            video_url=str(request.video_url)
        )
        
        # Return successful analysis results
        return VideoAnalysisResponse(
            camera_status=results["camera_status"],
            attire_status=results["attire_status"],
            video_duration=results.get("video_duration"),
            frame_count=results.get("frame_count"),
            fps=results.get("fps"),
            audio_path=results.get("audio_path"),
            analysis_success=True,
            error_message=None
        )
        
    except Exception as e:
        logger.error(f"Video analysis failed: {str(e)}")
        
        # Return error response
        return VideoAnalysisResponse(
            camera_status="Unknown",
            attire_status="Unknown",
            video_duration=None,
            frame_count=None,
            fps=None,
            audio_path=None,
            analysis_success=False,
            error_message=str(e)
        )


@router.get("/health", tags=["Health Check"])
async def video_analysis_health():
    """Health check endpoint for video analysis service"""
    return {"status": "healthy", "service": "video-analysis"}



