from pydantic import BaseModel, Field
from typing import Any, Dict

from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class VideoDimensions(BaseModel):
    width: int
    height: int

class VideoInfo(BaseModel):
    duration_seconds: float
    frame_count: int
    fps: float
    audio_path: str
    dimensions: VideoDimensions

class CameraMetrics(BaseModel):
    on_percentage: float
    total_samples: int
    samples_with_faces: int
    face_detection_rate: float

class OffPeriods(BaseModel):
    count: int
    total_duration: float
    details: List[Dict[str, Any]]

class CameraAnalysis(BaseModel):
    overall_status: str
    metrics: CameraMetrics
    off_periods: OffPeriods
    timeline: List[Dict[str, Any]]

class AnalysisItem(BaseModel):
    success: bool
    summary: str
    frames_analyzed: int
    error: Optional[str] = None

class VisualAnalyses(BaseModel):
    attire: AnalysisItem
    background: AnalysisItem

class VisualMetrics(BaseModel):
    total_frames_analyzed: int
    analysis_coverage_percentage: float

class AttireAndBackgroundAnalysis(BaseModel):
    success: bool = Field(..., description="Whether analysis was successful")
    attire_analysis: str = Field(..., description="Overall assessment of attire professionalism across all frames")
    background_analysis: str = Field(..., description="Overall assessment of background setting professionalism across all frames")
    attire_percentage: float = Field(..., ge=0, le=100, description="Confidence (0–100) in attire being professional overall")
    background_percentage: float = Field(..., ge=0, le=100, description="Confidence (0–100) in background being professional overall")
    error: Optional[str] = Field(None, description="Error message if success is False")

class AnalysisSummary(BaseModel):
    overall_success: bool
    camera_working: bool
    visual_analysis_completed: bool
    total_people_detected: int
    static_images_detected: int

class VideoAnalysisResponse(BaseModel):
    video_info: VideoInfo
    camera_analysis: CameraAnalysis
    attireAndBackgroundAnalysis: AttireAndBackgroundAnalysis
    analysis_summary: AnalysisSummary
