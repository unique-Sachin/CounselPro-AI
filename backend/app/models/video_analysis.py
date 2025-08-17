from pydantic import BaseModel
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

class ProofData(BaseModel):
    frames_count: int
    frames: List[Dict[str, Any]]

class CameraAnalysis(BaseModel):
    overall_status: str
    metrics: CameraMetrics
    off_periods: OffPeriods
    proof_data: ProofData
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

class VisualIntelligence(BaseModel):
    overall_success: bool
    analyses: VisualAnalyses
    metrics: VisualMetrics
    error: Optional[str] = None

class AnalysisSummary(BaseModel):
    overall_success: bool
    camera_working: bool
    visual_analysis_completed: bool
    total_people_detected: int
    static_images_detected: int

class AnalysisMethods(BaseModel):
    camera_detection: str
    visual_analysis_model: str
    sampling_strategy: str
    extraction_method: str

class StaticDetection(BaseModel):
    enabled: bool
    method: str
    ssim_threshold: float
    landmark_threshold: float

class Metadata(BaseModel):
    analysis_timestamp: str
    analysis_version: str
    methods: AnalysisMethods
    static_detection: StaticDetection

class VideoAnalysisResponse(BaseModel):
    video_info: VideoInfo
    camera_analysis: CameraAnalysis
    visual_intelligence: VisualIntelligence
    analysis_summary: AnalysisSummary
    metadata: Metadata