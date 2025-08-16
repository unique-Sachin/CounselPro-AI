from pydantic import BaseModel, HttpUrl, Field
from typing import Optional


class VideoAnalysisRequest(BaseModel):
    """Schema for video analysis request"""
    video_url: HttpUrl = Field(..., description="Google Drive URL of the private video to analyze")


class VideoAnalysisResponse(BaseModel):
    """Schema for video analysis response"""
    camera_status: str = Field(..., description="Status of the camera (On/Off)")
    attire_status: str = Field(..., description="Professional attire assessment")
    video_duration: Optional[float] = Field(None, description="Duration of the video in seconds")
    frame_count: Optional[int] = Field(None, description="Total number of frames in the video")
    fps: Optional[float] = Field(None, description="Frames per second of the video")
    audio_path: Optional[str] = Field(None, description="Path to the extracted audio file for Whisper processing")
    analysis_success: bool = Field(..., description="Whether the analysis was successful")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
