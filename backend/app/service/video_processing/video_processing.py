from app.models.video_analysis import AttireAndBackgroundAnalysis
import cv2
import numpy as np
import os
import base64
import google.generativeai as genai
from datetime import datetime
from skimage.metrics import structural_similarity as ssim
import logging
from pathlib import Path
from ultralytics import YOLO as UltralyticsYOLO
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing import Optional
import logging
from dotenv import load_dotenv

load_dotenv()


# Configure logging
logger = logging.getLogger(__name__)

FRAME_SAMPLING_INTERVAL = int(os.getenv("FRAME_SAMPLING_INTERVAL", "2"))  # Extract frame every N seconds
MIN_OFF_PERIOD_DURATION = int(os.getenv("MIN_OFF_PERIOD_DURATION", "6"))  # Minimum seconds for significant off period
YOLO_FACE_WEIGHTS = "backend/assets/models/yolov8n-face.pt"

class VideoProcessor:
    """
    Optimized video processor for analyzing counseling session videos.
    Uses frame-based processing instead of saving temporary video files.
    """

    def __init__(self):
        """Initialize the video processor"""
        logger.info("Initializing VideoProcessor")

        # Validate API key early
        self.llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

        # For storing latest detection results (IDs only)
        self.latest_person_ids = {}

        # Initialize YOLO model (YOLO-only implementation)
        self.yolo_model = None
        yolo_weights = YOLO_FACE_WEIGHTS
        yolo_device = os.getenv("YOLO_DEVICE", "cpu").strip()
        if not yolo_weights:
            logger.warning("YOLO_FACE_WEIGHTS not set; defaulting to backend/assets/models/yolov8n-face.pt")
            # Resolve default relative to project root
            project_root = Path(__file__).resolve().parents[4]
            default_path = project_root / "backend" / "assets" / "models" / "yolov8n-face.pt"
            yolo_weights = str(default_path)
        else:
            # Resolve relative paths to absolute
            p = Path(yolo_weights)
            if not p.is_absolute():
                project_root = Path(__file__).resolve().parents[4]
                yolo_weights = str((project_root / p).resolve())
        if not Path(yolo_weights).exists():
            raise FileNotFoundError(f"YOLO weights not found at: {yolo_weights}")
        try:
            self.yolo_model = UltralyticsYOLO(yolo_weights)
            # Move model to desired device if supported
            try:
                if hasattr(self.yolo_model, 'to'):
                    self.yolo_model.to(yolo_device)
            except Exception:
                pass
            logger.info(f"YOLO model loaded: {yolo_weights} on device: {yolo_device}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model with weights '{yolo_weights}': {e}")
            raise

        logger.info("VideoProcessor initialized successfully")

    def cleanup_resources(self):
        """Clean up video processing resources"""
        try:
            if hasattr(self, 'face_detection') and self.face_detection:
                self.face_detection.close()
                logger.debug("Face detection resources cleaned up")

        except Exception as e:
            logger.warning(f"Error during video processing resource cleanup: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_resources()

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as MM:SS"""
        return f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"

    async def analyze_video(self, video_data: dict):

        try:
            # Extract file ID from Google Drive URL
            logger.info("Extracting video frames")
            frames_data = video_data['frames']
            audio_path = video_data['audio_path']
            metadata = video_data['metadata']

            fps = metadata['fps']
            duration = metadata['duration']
            frame_count = metadata['total_frames']

            logger.info(f"Video metadata: {duration:.1f}s, {fps:.1f} fps, {frame_count} frames")

            # Analyze camera status using extracted frames
            logger.info("Starting camera status analysis")
            camera_analysis = self.analyze_camera_status_from_frames(frames_data, duration, fps)

            # Check if camera analysis was successful
            if not camera_analysis.get('success', False):
                error_msg = f"Camera analysis failed: {camera_analysis.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.info("Camera analysis completed successfully")

            # Perform visual intelligence analysis
            logger.info("Starting visual intelligence analysis")
            attireAndBackgroundAnalysis = self._perform_visual_analysis_from_frames(frames_data, camera_analysis['detailed_results']['camera_timeline'])


            # Construct the structured response for frontend
            logger.info("Constructing final results")
            results = {
                # Basic video information
                "video_info": {
                    "duration_seconds": round(duration, 2),
                    "frame_count": frame_count,
                    "fps": round(fps, 2),
                    "audio_path": audio_path,
                    "dimensions": {
                        "width": metadata['width'],
                        "height": metadata['height']
                    }
                },
                "audio_path" : audio_path,

                # Camera analysis results
                "camera_analysis": {
                    "overall_status": "On" if camera_analysis['summary']['camera_on_overall'] else "Off",
                    "metrics": {
                        "on_percentage": round(camera_analysis['summary']['camera_on_percentage'], 2),
                        "total_samples": camera_analysis['summary']['total_samples_analyzed'],
                        "samples_with_faces": camera_analysis['summary']['samples_with_faces'],
                        "face_detection_rate": round(
                            (camera_analysis['summary']['samples_with_faces'] /
                            max(camera_analysis['summary']['total_samples_analyzed'], 1)) * 100, 2
                        )
                    },
                    "off_periods": {
                        "count": camera_analysis['summary']['significant_off_periods'],
                        "total_duration": camera_analysis['summary']['total_off_duration'],
                        "details": camera_analysis['detailed_results']['off_periods']
                    },

                    # Detailed frame-by-frame timeline for UI
                    "timeline": [
                        {
                            "timestamp": frame['timestamp'],
                            "timestamp_formatted": self._format_timestamp(frame['timestamp']),
                            "camera_status": "on" if frame['camera_on'] else "off",
                            "faces": {
                                "count": frame['face_count'],
                                "positions": frame['face_positions']
                            },
                            "has_static_images": frame.get('has_static_images', False),
                            "static_count": frame.get('static_count', 0),
                            "person_ids": frame.get('person_ids', {})
                        }
                        for frame in camera_analysis['detailed_results']['camera_timeline']
                    ]
                },

                # Visual intelligence results
                "attireAndBackgroundAnalysis": attireAndBackgroundAnalysis,

                # Analysis summary
                "analysis_summary": {
                    "overall_success": True,
                    "camera_working": camera_analysis['summary']['camera_on_overall'],
                    "visual_analysis_completed": bool(getattr(attireAndBackgroundAnalysis, 'success', False)),
                    "total_people_detected": camera_analysis['summary'].get('person_count', 0),
                    "static_images_detected": camera_analysis['summary'].get('static_image_detection', {}).get('persons_with_static_images', 0)
                },

            }

            logger.info("Video analysis completed successfully")
            return results

        except ValueError as e:
            # Input validation errors
            logger.error(f"Input validation error during video analysis: {e}")
            raise e
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error during video analysis: {e}", exc_info=True)
            raise Exception(f"Video analysis failed: {str(e)}") from e

        finally:
            # Cleanup
            try:
                self.cleanup_resources()
                logger.debug("Cleanup completed successfully")
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")

    def analyze_camera_status_from_frames(self, frames_data: dict, duration: float, fps: float):
        """
        Analyzes camera status from pre-extracted frames.

        Args:
            frames_data (dict): Dictionary mapping timestamp to frame data
            duration (float): Video duration
            fps (float): Video FPS

        Returns:
            dict: Complete analysis with timeline, proof images, and summary statistics
        """

        try:
            # Analysis tracking variables
            camera_timeline = []
            person_timelines = {}  # Dictionary to track each person's camera status

            face_detected_count = 0
            total_samples = 0

            # Camera OFF period tracking
            current_off_start = None
            consecutive_off_count = 0

            # Person tracking variables
            last_face_positions = {}  # Store last known positions of each person
            person_ids = {}  # Map face positions to consistent person IDs
            next_person_id = 1  # Counter for assigning new person IDs

            # Static image detection variables
            person_frame_history = {}  # Store recent frames for each person
            static_image_status = {}  # Track which persons have static images

            logger.info(f"Analyzing {len(frames_data)} extracted frames")

            # Process each frame
            for timestamp in sorted(frames_data.keys()):
                frame = frames_data[timestamp]
                total_samples += 1

                faces = []

                # YOLO-only face detection
                try:
                    yolo_results = self.yolo_model(frame, verbose=False)
                    if yolo_results and len(yolo_results) > 0:
                        result0 = yolo_results[0]
                        if hasattr(result0, 'boxes') and result0.boxes is not None:
                            for b in result0.boxes:
                                try:
                                    xyxy = b.xyxy[0].tolist() if hasattr(b.xyxy[0], 'tolist') else list(b.xyxy[0])
                                    x1, y1, x2, y2 = map(int, xyxy[:4])
                                    w = max(0, x2 - x1)
                                    h = max(0, y2 - y1)
                                    if w > 0 and h > 0:
                                        faces.append((x1, y1, w, h))
                                except Exception:
                                    continue
                except Exception as det_err:
                    logger.error(f"YOLO detection failed: {det_err}")

                camera_on = len(faces) > 0
                if camera_on:
                    face_detected_count += 1

                # Log progress every 10 frames or when faces are detected
                if total_samples % 10 == 0 or len(faces) > 0:
                    logger.debug(f"Frame {total_samples}: {len(faces)} faces detected at {timestamp:.1f}s ({'ON' if camera_on else 'OFF'})")

                # Assign person IDs to detected faces
                current_person_ids = self._assign_person_ids(faces, last_face_positions, person_ids, next_person_id)

                # Store the current person IDs for reference
                self.latest_person_ids = current_person_ids

                # YOLO-only mode: no facial landmarks captured

                # Update next_person_id if new people were detected
                if current_person_ids:
                    next_person_id = max([pid for _, pid in current_person_ids.items()]) + 1

                # Update person timelines
                current_timestamp_persons = {}
                for face_idx, (x, y, w, h) in enumerate(faces):
                    face_key = f"{face_idx}"
                    if face_key in current_person_ids:
                        person_id = current_person_ids[face_key]

                        # Extract face region for static image detection
                        face_region = frame[y:y+h, x:x+w].copy()

                        # Initialize frame history for this person if needed
                        if person_id not in person_frame_history:
                            person_frame_history[person_id] = []

                        # Add current face region to history (keep last 5 frames)
                        person_frame_history[person_id].append(face_region)
                        if len(person_frame_history[person_id]) > 5:
                            person_frame_history[person_id].pop(0)

                        # Check if this is a static image
                        is_static = False
                        if len(person_frame_history[person_id]) >= 3:
                            is_static = self._is_static_image(face_region, person_id, person_frame_history)

                        # Update static image status
                        static_image_status[person_id] = is_static

                        # Add to person's timeline
                        if person_id not in person_timelines:
                            person_timelines[person_id] = []

                        person_timelines[person_id].append({
                            'timestamp': timestamp,
                            'camera_on': True,
                            'camera_static': is_static,
                            'face_position': [int(x), int(y), int(w), int(h)]
                        })

                        current_timestamp_persons[person_id] = True

                # Mark absent people as camera off
                for pid in person_timelines.keys():
                    if pid not in current_timestamp_persons:
                        person_timelines[pid].append({
                            'timestamp': timestamp,
                            'camera_on': False,
                            'camera_static': False,
                            'face_position': None
                        })

                # Check if any detected faces are static images
                has_static_images = any(static_image_status.get(pid, False) for pid in current_person_ids.values())
                static_count = sum(1 for pid in current_person_ids.values() if static_image_status.get(pid, False))

                # Add to overall timeline
                camera_timeline.append({
                    'timestamp': timestamp,
                    'camera_on': camera_on,
                    'has_static_images': has_static_images,
                    'static_count': static_count,
                    'face_count': len(faces),
                    'face_positions': list(faces) if len(faces) > 0 else [],
                    'person_ids': current_person_ids
                })



                # Update OFF period tracking
                if not camera_on:
                    if current_off_start is None:
                        current_off_start = timestamp
                        consecutive_off_count = 1
                    else:
                        consecutive_off_count += 1
                else:
                    if current_off_start is not None:
                        current_off_start = None
                        consecutive_off_count = 0

            # Calculate final statistics
            face_detection_ratio = face_detected_count / total_samples if total_samples > 0 else 0
            camera_on_overall = face_detection_ratio > 0.1

            # Detect significant camera OFF periods (overall and per-person)
            off_periods, person_off_periods = self._detect_off_periods(camera_timeline, person_timelines)

            logger.info(f"Camera analysis complete: {face_detected_count}/{total_samples} samples with faces detected")

            # Process per-person statistics
            person_stats = {}
            for person_id, timeline in person_timelines.items():
                on_count = sum(1 for event in timeline if event['camera_on'])
                static_count = sum(1 for event in timeline if event.get('camera_static', False))
                active_count = on_count - static_count
                total_count = len(timeline)

                on_percentage = (on_count / total_count * 100) if total_count > 0 else 0
                static_percentage = (static_count / total_count * 100) if total_count > 0 else 0
                active_percentage = (active_count / total_count * 100) if total_count > 0 else 0

                person_stats[person_id] = {
                    'camera_on_percentage': round(on_percentage, 2),
                    'camera_static_percentage': round(static_percentage, 2),
                    'camera_active_percentage': round(active_percentage, 2),
                    'samples_with_faces': on_count,
                    'samples_with_static_images': static_count,
                    'samples_with_active_camera': active_count,
                    'total_samples': total_count,
                    'camera_on_overall': on_percentage > 10,  # Same threshold as overall
                    'using_static_image': static_count > 0 and static_count / on_count > 0.8  # Mostly static
                }

            return {
                'success': True,
                'video_info': {
                    'duration_seconds': duration,
                    'fps': fps,
                    'analysis_timestamp': datetime.now().isoformat()
                },

                'summary': {
                    'camera_on_overall': camera_on_overall,
                    'camera_on_percentage': round(face_detection_ratio * 100, 2),
                    'total_samples_analyzed': total_samples,
                    'samples_with_faces': face_detected_count,
                    'person_count': len(person_timelines),
                    'sampling_interval_seconds': 2.0,
                    'significant_off_periods': len(off_periods),
                    'total_off_duration': sum(p['duration'] for p in off_periods),
                    'static_image_detection': {
                        'enabled': True,
                        'persons_with_static_images': sum(1 for _pid, stats in person_stats.items() if stats.get('using_static_image', False)),
                        'detection_method': 'SSIM',
                        'ssim_threshold': 0.95
                    }
                },

                'detailed_results': {
                    'camera_timeline': camera_timeline,
                    'person_timelines': person_timelines,
                    'person_stats': person_stats,
                    'off_periods': off_periods,
                    'person_off_periods': person_off_periods,
                    
                },

                'analysis_metadata': {
                    'detection_method': 'YOLO Face Detection + SSIM (static detection)',
                    'sampling_strategy': f'Every {FRAME_SAMPLING_INTERVAL} seconds',
                    'minimum_off_period_for_documentation': MIN_OFF_PERIOD_DURATION,
                    'static_image_detection': 'SSIM only (no facial landmarks)'
                }
            }

        except Exception as e:
            logger.error(f"Error analyzing camera status: {e}", exc_info=True)
            return {
                'error': f'Error analyzing camera status: {e}',
                'success': False
            }


    def _calculate_frame_similarity(self, frame1, frame2):
        """Calculate similarity between two frames using SSIM"""
        # Convert frames to grayscale for comparison
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        # Ensure both images have same dimensions
        if gray1.shape != gray2.shape:
            gray2 = cv2.resize(gray2, (gray1.shape[1], gray1.shape[0]))

        # Calculate SSIM between the two frames
        score, _ = ssim(gray1, gray2, full=True)
        return score




    def _is_static_image(self, current_frame, person_id, person_frame_history, similarity_threshold=0.95):
        """Determine if a person's image is static (like a profile picture)"""
        if person_id not in person_frame_history or len(person_frame_history[person_id]) < 3:
            return False

        # Get the last few frames for this person
        recent_frames = person_frame_history[person_id][-3:]

        # First check: Calculate similarity between current frame and recent frames using SSIM
        similarities = [self._calculate_frame_similarity(current_frame, frame) for frame in recent_frames]
        frame_similarity_static = all(sim > similarity_threshold for sim in similarities)

        # YOLO-only mode: fallback to SSIM-only decision
        return frame_similarity_static

    def _assign_person_ids(self, faces, last_face_positions, person_ids, next_person_id):
        """Assign consistent IDs to people across frames based on face positions"""
        current_person_ids = {}

        # No faces detected in this frame
        if len(faces) == 0:
            return current_person_ids

        # Process each detected face
        for i, (x, y, w, h) in enumerate(faces):
            face_key = f"{i}"
            face_center = (x + w//2, y + h//2)
            matched_person = None
            min_distance = float('inf')

            # Try to match with existing people based on position
            for person_id, last_pos in last_face_positions.items():
                last_x, last_y, last_w, last_h = last_pos
                last_center = (last_x + last_w//2, last_y + last_h//2)

                # Calculate distance between face centers
                distance = np.sqrt((face_center[0] - last_center[0])**2 +
                                  (face_center[1] - last_center[1])**2)

                # Consider it a match if distance is less than average face size
                avg_size = (w + h + last_w + last_h) / 4
                if distance < avg_size * 0.8 and distance < min_distance:
                    min_distance = distance
                    matched_person = person_id

            # Assign ID (either matched or new)
            if matched_person is not None:
                current_person_ids[face_key] = matched_person
            else:
                # Assign new ID
                current_person_ids[face_key] = next_person_id
                next_person_id += 1

            # Update last known position
            last_face_positions[current_person_ids[face_key]] = (x, y, w, h)

        return current_person_ids

    def _detect_off_periods(self, camera_timeline, person_timelines=None):
        """Detect significant camera OFF periods from timeline"""
        # Overall camera off periods
        off_periods = []
        current_off_start = None

        for event in camera_timeline:
            if not event['camera_on'] and current_off_start is None:
                current_off_start = event['timestamp']
            elif event['camera_on'] and current_off_start is not None:
                duration = event['timestamp'] - current_off_start

                # Only include significant OFF periods
                if duration >= MIN_OFF_PERIOD_DURATION:
                    off_periods.append({
                        'start_time': current_off_start,
                        'end_time': event['timestamp'],
                        'duration': duration,
                        'start_formatted': self._format_timestamp(current_off_start),
                        'end_formatted': self._format_timestamp(event['timestamp'])
                    })

                current_off_start = None

        # Handle case where video ends during OFF period
        if current_off_start is not None and camera_timeline:
            last_timestamp = camera_timeline[-1]['timestamp']
            duration = last_timestamp - current_off_start

            if duration >= MIN_OFF_PERIOD_DURATION:
                off_periods.append({
                    'start_time': current_off_start,
                    'end_time': last_timestamp,
                    'duration': duration,
                    'start_formatted': self._format_timestamp(current_off_start),
                    'end_formatted': self._format_timestamp(last_timestamp)
                })

        # Per-person off periods if person_timelines is provided
        person_off_periods = {}
        if person_timelines:
            for person_id, timeline in person_timelines.items():
                person_off_periods[person_id] = []
                current_off_start = None

                for event in timeline:
                    if not event['camera_on'] and current_off_start is None:
                        current_off_start = event['timestamp']
                    elif event['camera_on'] and current_off_start is not None:
                        duration = event['timestamp'] - current_off_start

                        # Only include significant OFF periods
                        if duration >= MIN_OFF_PERIOD_DURATION:
                            person_off_periods[person_id].append({
                                'start_time': current_off_start,
                                'end_time': event['timestamp'],
                                'duration': duration,
                                'start_formatted': self._format_timestamp(current_off_start),
                                'end_formatted': self._format_timestamp(event['timestamp'])
                            })

                        current_off_start = None

                # Handle case where video ends during OFF period
                if current_off_start is not None and timeline:
                    last_timestamp = timeline[-1]['timestamp']
                    duration = last_timestamp - current_off_start

                    if duration >= MIN_OFF_PERIOD_DURATION:
                        person_off_periods[person_id].append({
                            'start_time': current_off_start,
                            'end_time': last_timestamp,
                            'duration': duration,
                            'start_formatted': self._format_timestamp(current_off_start),
                            'end_formatted': self._format_timestamp(last_timestamp)
                        })

        return off_periods, person_off_periods if person_timelines else off_periods

    # --- Visual Analysis Methods (Updated for Frame-Based Processing) ---

    def _encode_frame_to_base64(self, frame):
        """Encode a frame to base64 for Gemini API"""
        try:
            # Convert BGR to RGB (Gemini expects RGB)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Encode to JPEG
            _, buffer = cv2.imencode('.jpg', frame_rgb, [cv2.IMWRITE_JPEG_QUALITY, 85])

            # Convert to base64
            base64_image = base64.b64encode(buffer).decode('utf-8')
            return base64_image

        except Exception as e:
            logger.error(f"Error encoding frame to base64: {e}")
            return None


    def _perform_visual_analysis_from_frames(self, frames_data, camera_timeline):
        """
        Perform attire and background analysis on selected frames using pre-extracted frame data
        Optimized to make a single Gemini API call for all frames

        Args:
            frames_data: Dictionary mapping timestamp to frame data
            camera_timeline: Timeline with face detection data

        Returns:
            dict: Visual analysis results
        """
        try:
            logger.info("Starting visual intelligence analysis from extracted frames")

            # Select best frames for analysis (inlined from _select_best_frames_for_analysis)
            try:
                frames_with_faces = [
                    event for event in camera_timeline
                    if event['face_count'] > 0
                ]
                frames_with_faces.sort(
                    key=lambda x: (x['face_count'], x['timestamp']),
                    reverse=True
                )
                selected_frames = frames_with_faces[:3]
                logger.info(f"Selected {len(selected_frames)} frames for visual analysis")
                for i, frame in enumerate(selected_frames):
                    logger.debug(f"   Frame {i+1}: {frame['face_count']} faces at {frame['timestamp']:.1f}s")
            except Exception as e:
                logger.error(f"Error selecting frames for analysis: {e}")
                selected_frames = []

            if not selected_frames:
                return AttireAndBackgroundAnalysis(
                    success=False,
                    attire_analysis='No suitable frames found for visual analysis',
                    background_analysis='No suitable frames found for visual analysis',
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error='No suitable frames found for visual analysis'
                )

            # Prepare frames for batch analysis
            valid_frames = []
            valid_timestamps = []

            for i, frame_data in enumerate(selected_frames):
                timestamp = frame_data['timestamp']
                logger.debug(f"Preparing frame {i+1} at {timestamp:.1f}s")

                # Get frame from pre-extracted data
                frame = frames_data.get(timestamp)
                if frame is None:
                    logger.warning(f"Frame not available at {timestamp:.1f}s")
                    continue

                valid_frames.append(frame)
                valid_timestamps.append(timestamp)

            if not valid_frames:
                return AttireAndBackgroundAnalysis(
                    success=False,
                    attire_analysis='No valid frames available for analysis',
                    background_analysis='No valid frames available for analysis',
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error='No valid frames available for analysis'
                )

            # Perform batch analysis for all frames at once (inlined)
            logger.info(f"Analyzing {len(valid_frames)} frames in a single batch")

            # Encode frames
            encoded_frames = [
                self._encode_frame_to_base64(frame) for frame in valid_frames
            ]
            encoded_frames = [f for f in encoded_frames if f]

            if not encoded_frames:
                return AttireAndBackgroundAnalysis(
                    success=False,
                    attire_analysis='Failed to encode any frames',
                    background_analysis='Failed to encode any frames',
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error="Failed to encode any frames"
                )

            # Build a single user message with multimodal content (role + content parts)
            prompt = (
                "You are analyzing multiple counseling session images. "
                "Provide a single overall assessment considering all frames together for attire and background."
            )
            user_content = [{"type": "text", "text": prompt}]
            for img_b64 in encoded_frames:
                user_content.append({"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"})
            messages = [{"role": "user", "content": user_content}]

            # Define structured output using Pydantic
            structured_llm = self.llm.with_structured_output(AttireAndBackgroundAnalysis)

            # Invoke with chat-style messages
            try:
                response = structured_llm.invoke(messages)
            except Exception as e:
                logger.error(f"Error in batch analysis: {str(e)}", exc_info=True)
                return AttireAndBackgroundAnalysis(
                    success=False,
                    attire_analysis='LLM invocation failed',
                    background_analysis='LLM invocation failed',
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error=str(e)
                )

            # Ensure response is the correct type
            if isinstance(response, AttireAndBackgroundAnalysis):
                response.success = True
                return response

            # Attempt coercion if dict-like
            try:
                return AttireAndBackgroundAnalysis(**(response if isinstance(response, dict) else {}))
            except Exception as e:
                logger.error(f"Invalid response structure from LLM: {e}")
                return AttireAndBackgroundAnalysis(
                    success=False,
                    attire_analysis='Invalid response structure',
                    background_analysis='Invalid response structure',
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error='Invalid response structure'
                )

        except Exception as e:
            logger.error(f"Error in batch analysis: {str(e)}", exc_info=True)
            return AttireAndBackgroundAnalysis(success=False, error=str(e))



