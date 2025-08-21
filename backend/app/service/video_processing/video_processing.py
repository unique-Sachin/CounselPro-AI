from app.models.video_analysis import AttireAndBackgroundAnalysis
from app.service.video_processing.video_response import VideoResponse
import cv2
import numpy as np
import os
import base64
from deepface import DeepFace
from datetime import datetime
from langchain.chat_models import init_chat_model
from typing import Optional, Dict
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
FRAME_SAMPLING_INTERVAL = int(os.getenv("FRAME_SAMPLING_INTERVAL", "2"))
MIN_OFF_PERIOD_DURATION = int(os.getenv("MIN_OFF_PERIOD_DURATION", "6"))
MAX_EMBEDDING_HISTORY = 5  # Number of face images to keep per person


class VideoProcessor:
    """
    Optimized video processor for analyzing counseling session videos.
    Uses DeepFace for face detection, anti-spoofing, and person tracking.
    """

    def __init__(self):
        """Initialize the video processor"""
        logger.info("Initializing VideoProcessor")

        # Validate API key early
        self.llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

        # Person tracking state
        self.next_person_id = 1
        self.person_embeddings = {}  # person_id -> List[face images] for DeepFace.verify()
        self.person_display_images = {}  # person_id -> face image with bounding box for UI

        # Pre-load DeepFace models
        try:
            logger.info("Initializing DeepFace models...")
            # Warm up face detection and recognition using official API
            dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
            _ = DeepFace.extract_faces(
                img_path=dummy_img,
                enforce_detection=False
            )
            _ = DeepFace.represent(
                img_path=dummy_img,
                enforce_detection=False
            )
            logger.info("DeepFace models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DeepFace: {e}")
            raise

        logger.info("VideoProcessor initialized successfully")

    def cleanup_resources(self):
        """Clean up video processing resources"""
        try:
            # Clear person tracking data
            self.person_embeddings.clear()
            logger.debug("Video processing resources cleaned up")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_resources()

    def _find_matching_person(self, face_img: np.ndarray) -> Optional[int]:
        """Find if this face matches any known person using DeepFace verification"""
        if face_img is None:
            return None
            
        best_match = None
        lowest_distance = float('inf')
            
        for person_id, stored_face_imgs in self.person_embeddings.items():
            for stored_face in stored_face_imgs:
                try:
                    # Use DeepFace.verify for proper face matching
                    result = DeepFace.verify(
                        img1_path=face_img,
                        img2_path=stored_face,
                        enforce_detection=False
                    )
                    
                    if result["verified"] and result["distance"] < lowest_distance:
                        lowest_distance = result["distance"]
                        best_match = person_id
                        
                except Exception as e:
                    logger.debug(f"Face verification error: {e}")
                    continue
                    
        return best_match

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as MM:SS"""
        return f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"

    async def analyze_video(self, video_data: dict):

        try:
            # Extract file ID from Google Drive URL
            logger.info("Extracting video frames")
            frames_data = video_data["frames"]
            audio_path = video_data["audio_path"]
            metadata = video_data["metadata"]

            fps = metadata["fps"]
            duration = metadata["duration"]
            frame_count = metadata["total_frames"]

            logger.info(
                f"Video metadata: {duration:.1f}s, {fps:.1f} fps, {frame_count} frames"
            )

            # Analyze camera status using extracted frames
            logger.info("Starting camera status analysis")
            camera_analysis = self.analyze_camera_status_from_frames(
                frames_data, duration, fps
            )

            # Check if camera analysis was successful
            if not camera_analysis.get("success", False):
                error_msg = f"Camera analysis failed: {camera_analysis.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.info("Camera analysis completed successfully")

            # Perform visual intelligence analysis
            logger.info("Starting visual intelligence analysis")
            attireAndBackgroundAnalysis = self._perform_visual_analysis_from_frames(
                frames_data, camera_analysis["detailed_results"]["camera_timeline"]
            )

            video_response = VideoResponse()
            results = video_response._format_ui_friendly_results(
                camera_analysis, attireAndBackgroundAnalysis, metadata, audio_path
            )

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

    # This is for celery use
    def analyze_video_for_celery(self, video_data: dict):
        """
        Analyze video synchronously (for Celery task usage).
        """

        try:
            # Extract file ID from Google Drive URL
            logger.info("Extracting video frames")
            frames_data = video_data["frames"]
            audio_path = video_data["audio_path"]
            metadata = video_data["metadata"]

            fps = metadata["fps"]
            duration = metadata["duration"]
            frame_count = metadata["total_frames"]

            logger.info(
                f"Video metadata: {duration:.1f}s, {fps:.1f} fps, {frame_count} frames"
            )

            # Analyze camera status using extracted frames
            logger.info("Starting camera status analysis")
            camera_analysis = self.analyze_camera_status_from_frames(
                frames_data, duration, fps
            )

            # Check if camera analysis was successful
            if not camera_analysis.get("success", False):
                error_msg = f"Camera analysis failed: {camera_analysis.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            logger.info("Camera analysis completed successfully")

            # Perform visual intelligence analysis
            logger.info("Starting visual intelligence analysis")
            attireAndBackgroundAnalysis = self._perform_visual_analysis_from_frames(
                frames_data, camera_analysis["detailed_results"]["camera_timeline"]
            )

            video_response = VideoResponse()
            results = video_response._format_ui_friendly_results(
                camera_analysis, attireAndBackgroundAnalysis, metadata, audio_path
            )

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

    def analyze_camera_status_from_frames(
        self, frames_data: dict, duration: float, fps: float
    ):
        """
        Analyzes camera status from pre-extracted frames using DeepFace.
        
        Detects faces, performs anti-spoofing, and tracks individual people
        across frames using face recognition.

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
            static_image_alerts = []  # Track static image/spoofing detections
            face_detected_count = 0
            total_samples = 0

            # Camera OFF period tracking
            current_off_start = None
            consecutive_off_count = 0

            logger.info(f"Analyzing {len(frames_data)} extracted frames")

            # Process each frame
            for timestamp in sorted(frames_data.keys()):
                frame = frames_data[timestamp]
                total_samples += 1

                detected_faces = []  # List of (person_id, bbox, is_spoofed)
                current_persons = set()  # Track active persons in this frame

                try:
                    # Use DeepFace for face detection with facial area information
                    analysis_results = DeepFace.analyze(
                        img_path=frame,
                        actions=['emotion'],  # Minimal analysis to get face regions
                        enforce_detection=False,
                        silent=True
                    )
                    
                    # Handle both single face and multiple faces
                    if not isinstance(analysis_results, list):
                        analysis_results = [analysis_results]

                    if analysis_results:
                        for result in analysis_results:
                            # Get facial area coordinates - DeepFace provides 'region' key
                            region = result.get("region", {})
                            x = region.get("x", 0)
                            y = region.get("y", 0)
                            w = region.get("w", 0)
                            h = region.get("h", 0)
                            
                            if w > 0 and h > 0:  # Valid face detection
                                # Extract face region from original frame
                                face_region = frame[y:y+h, x:x+w]
                                
                                # Anti-spoofing check using DeepFace's extract_faces with anti_spoofing
                                try:
                                    face_objs = DeepFace.extract_faces(
                                        img_path=face_region,
                                        enforce_detection=False,
                                        anti_spoofing=True
                                    )
                                    is_real = face_objs[0].get("is_real", True) if face_objs else True
                                except:
                                    is_real = True  # Default to real if anti-spoofing fails
                                
                                if is_real:
                                    # Extract just the face region for matching
                                    face_img = cv2.resize(face_region, (224, 224))
                                    
                                    # Find matching person using DeepFace verification
                                    person_id = self._find_matching_person(face_img)
                                    if person_id is None:
                                        person_id = self.next_person_id
                                        self.person_embeddings[person_id] = []
                                        self.next_person_id += 1
                                    
                                    # Store face image for future verification
                                    self.person_embeddings[person_id].append(face_img)
                                    if len(self.person_embeddings[person_id]) > MAX_EMBEDDING_HISTORY:
                                        self.person_embeddings[person_id].pop(0)
                                    
                                    # Create cropped face with border for UI display
                                    padding = 20
                                    x_start = max(0, x - padding)
                                    y_start = max(0, y - padding)
                                    x_end = min(frame.shape[1], x + w + padding)
                                    y_end = min(frame.shape[0], y + h + padding)
                                    
                                    face_with_border = frame[y_start:y_end, x_start:x_end].copy()
                                    # Draw green bounding box on the cropped image
                                    bbox_x = x - x_start
                                    bbox_y = y - y_start
                                    cv2.rectangle(face_with_border, (bbox_x, bbox_y), (bbox_x+w, bbox_y+h), (0, 255, 0), 2)
                                    # Add person label
                                    cv2.putText(face_with_border, f"Person {person_id}", 
                                              (bbox_x, bbox_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                                    
                                    # Store display image
                                    self.person_display_images[person_id] = face_with_border
                                    
                                    # Add to detected faces with display image
                                    detected_faces.append((person_id, face_with_border, False))
                                    current_persons.add(person_id)
                                else:
                                    # This is a spoofed/static face - create display image with red box
                                    padding = 20
                                    x_start = max(0, x - padding)
                                    y_start = max(0, y - padding)
                                    x_end = min(frame.shape[1], x + w + padding)
                                    y_end = min(frame.shape[0], y + h + padding)
                                    
                                    face_with_border = frame[y_start:y_end, x_start:x_end].copy()
                                    # Draw red bounding box for spoofed faces
                                    bbox_x = x - x_start
                                    bbox_y = y - y_start
                                    cv2.rectangle(face_with_border, (bbox_x, bbox_y), (bbox_x+w, bbox_y+h), (0, 0, 255), 2)
                                    cv2.putText(face_with_border, "Spoofed", 
                                              (bbox_x, bbox_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                                    
                                    detected_faces.append((None, face_with_border, True))
                                    static_image_alerts.append({
                                        "timestamp": self._format_timestamp(timestamp),
                                        "is_real": is_real
                                    })
                                    logger.info(f"Static/spoofed face detected at timestamp {self._format_timestamp(timestamp)}")
                                
                except Exception as e:
                    logger.error(f"Face detection error: {e}")
                    
                # Log progress every 10 frames
                if total_samples % 10 == 0:
                    logger.debug(
                        f"Frame {total_samples}: {len(detected_faces)} faces detected at {timestamp:.1f}s"
                    )

                # Update person timelines for valid faces
                for person_id, face_data, is_spoofed in detected_faces:
                    if person_id is not None:  # Only track real faces
                        # Add to person's timeline if not already tracking
                        if person_id not in person_timelines:
                            person_timelines[person_id] = []
                        
                        # Add timeline entry (simplified since we don't have exact bbox coordinates)
                        person_timelines[person_id].append({
                            "timestamp": timestamp,
                            "camera_on": True,
                            "face_detected": True
                        })
                            
                # Check if this frame indicates camera off period
                frame_camera_on = len([f for f in detected_faces if not f[2]]) > 0  # Count non-spoofed faces
                
                # Add timeline event for every frame
                camera_timeline.append({
                    "timestamp": timestamp,
                    "camera_on": frame_camera_on,
                    "face_detected": frame_camera_on
                })
                
                if frame_camera_on:
                    face_detected_count += 1
                    consecutive_off_count = 0
                else:
                    consecutive_off_count += 1
                        
            # Calculate statistics
            total_off_duration = 0  # Will be calculated from camera timeline later
            camera_availability = round((face_detected_count / total_samples) * 100, 1) if total_samples > 0 else 0

            # Generate person statistics with face images
            person_stats = {}
            for person_id, timeline in person_timelines.items():
                on_count = sum(1 for event in timeline if event.get("camera_on", False))
                total_count = len(timeline) if timeline else 1  # Avoid division by zero
                
                on_percentage = (on_count / total_count * 100) if total_count > 0 else 0
                
                # Get the latest face image with bounding box for this person
                face_image_b64 = None
                if person_id in self.person_display_images:
                    display_image = self.person_display_images[person_id]
                    face_image_b64 = self._image_to_base64(display_image)
                
                person_stats[person_id] = {
                    "camera_on_percentage": round(on_percentage, 2),
                    "camera_static_percentage": 0.0,  # No longer tracking static images separately
                    "camera_active_percentage": round(on_percentage, 2),  # Same as on_percentage
                    "samples_with_faces": on_count,
                    "samples_with_static_images": 0,  # DeepFace handles anti-spoofing
                    "samples_with_active_camera": on_count,
                    "total_samples": total_count,
                    "camera_on_overall": on_percentage > 10,  # Same threshold as overall
                    "using_static_image": False,  # DeepFace anti-spoofing handles this
                    "face_image": face_image_b64,  # Base64 encoded face image with bounding box
                    "person_name": f"Person {person_id}"  # Default name, can be updated later
                }

            # Create summary statistics for the expected format
            camera_on_percentage = round(face_detected_count / total_samples * 100, 1) if total_samples > 0 else 0
            using_static_image = len(static_image_alerts) > 0
            
            summary = {
                "camera_on_percentage": camera_on_percentage,
                "camera_static_percentage": round(len(static_image_alerts) / total_samples * 100, 1) if total_samples > 0 else 0,
                "camera_active_percentage": camera_on_percentage,  # Same as camera_on since we filter out static
                "samples_with_faces": face_detected_count,
                "samples_with_static_images": len(static_image_alerts),
                "samples_with_active_camera": face_detected_count,
                "total_samples": total_samples,
                "total_samples_analyzed": total_samples,  # Add this field that video_response.py expects
                "camera_on_overall": camera_on_percentage > 10,
                "using_static_image": using_static_image
            }

            # Calculate off periods from camera timeline
            off_periods = self._detect_off_periods(camera_timeline)

            # Format results
            detailed_results = {
                "camera_timeline": camera_timeline,
                "person_timelines": person_timelines,
                "person_stats": person_stats,
                "static_image_alerts": static_image_alerts,
                "off_periods": off_periods,  # Add the missing off_periods field
                "total_off_duration": round(total_off_duration, 1),
                "camera_availability": camera_availability,
                "face_detection_rate": round(face_detected_count / total_samples * 100, 1)
            }

            return {
                "success": True,
                "detailed_results": detailed_results,
                "summary": summary,  # Add the missing summary section
                "error": None
            }

        except Exception as e:
            logger.error(f"Camera status analysis failed: {e}", exc_info=True)
            return {
                "success": False,
                "detailed_results": None,
                "summary": None,
                "error": str(e)
            }

    def _detect_off_periods(self, camera_timeline, person_timelines=None):
        """Detect significant camera OFF periods from timeline"""
        # Overall camera off periods
        off_periods = []
        current_off_start = None

        for event in camera_timeline:
            timestamp = event.get("timestamp", 0)
            camera_on = event.get("camera_on", False)

            if not camera_on and current_off_start is None:
                current_off_start = timestamp
            elif camera_on and current_off_start is not None:
                duration = timestamp - current_off_start

                # Only include significant OFF periods
                if duration >= MIN_OFF_PERIOD_DURATION:
                    off_periods.append({
                        "start": self._format_timestamp(current_off_start),
                        "end": self._format_timestamp(timestamp),
                        "start_formatted": self._format_timestamp(current_off_start),
                        "end_formatted": self._format_timestamp(timestamp),
                        "duration": round(duration, 1)
                    })

                current_off_start = None

        # Handle case where video ends during OFF period
        if current_off_start is not None and camera_timeline:
            last_event = camera_timeline[-1]
            last_timestamp = last_event.get("timestamp", 0)
            duration = last_timestamp - current_off_start

            if duration >= MIN_OFF_PERIOD_DURATION:
                off_periods.append({
                    "start": self._format_timestamp(current_off_start),
                    "end": self._format_timestamp(last_timestamp),
                    "start_formatted": self._format_timestamp(current_off_start),
                    "end_formatted": self._format_timestamp(last_timestamp),
                    "duration": round(duration, 1)
                })

        return off_periods

    def _encode_frame_to_base64(self, frame):
        """Encode a frame to base64 for Gemini API"""
        try:
            # Convert BGR to RGB (Gemini expects RGB)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Encode to JPEG
            _, buffer = cv2.imencode(".jpg", frame_rgb, [cv2.IMWRITE_JPEG_QUALITY, 85])

            # Convert to base64
            base64_image = base64.b64encode(buffer).decode("utf-8")
            return base64_image

        except Exception as e:
            logger.error(f"Error encoding frame to base64: {e}")
            return None

    def _image_to_base64(self, image):
        """Convert an image (face image with bounding box) to base64 for UI display"""
        try:
            # Handle both BGR and RGB images
            if len(image.shape) == 3:
                # If it's BGR (OpenCV default), convert to RGB for web display
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                image_rgb = image
            
            # Encode to JPEG
            _, buffer = cv2.imencode(".jpg", image_rgb, [cv2.IMWRITE_JPEG_QUALITY, 90])
            
            # Convert to base64
            base64_image = base64.b64encode(buffer).decode("utf-8")
            return base64_image
            
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
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

            # Select best frames for analysis - use simple timestamp-based selection
            if not camera_timeline:
                return AttireAndBackgroundAnalysis(
                    success=False,
                    attire_analysis="No frames available for analysis",
                    background_analysis="No frames available for analysis",
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error="No frames available for analysis",
                )

            # Select up to 3 frames evenly distributed across the timeline
            timestamps = list(frames_data.keys())
            if len(timestamps) <= 3:
                selected_timestamps = timestamps
            else:
                # Select beginning, middle, and end frames
                selected_timestamps = [
                    timestamps[0],
                    timestamps[len(timestamps) // 2],
                    timestamps[-1]
                ]

            logger.info(f"Selected {len(selected_timestamps)} frames for visual analysis")

            # Prepare frames for batch analysis
            valid_frames = []
            valid_timestamps = []

            for timestamp in selected_timestamps:
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
                    attire_analysis="No valid frames available for analysis",
                    background_analysis="No valid frames available for analysis",
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error="No valid frames available for analysis",
                )

            # Perform batch analysis for all frames at once
            logger.info(f"Analyzing {len(valid_frames)} frames in a single batch")

            # Encode frames
            encoded_frames = [
                self._encode_frame_to_base64(frame) for frame in valid_frames
            ]
            encoded_frames = [f for f in encoded_frames if f]

            if not encoded_frames:
                return AttireAndBackgroundAnalysis(
                    success=False,
                    attire_analysis="Failed to encode any frames",
                    background_analysis="Failed to encode any frames",
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error="Failed to encode any frames",
                )

            # Build a single user message with multimodal content (role + content parts)
            prompt = (
                "You are analyzing multiple counseling session images. "
                "Provide a single overall assessment considering all frames together for attire and background."
            )
            user_content = [{"type": "text", "text": prompt}]
            for img_b64 in encoded_frames:
                user_content.append(
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{img_b64}",
                    }
                )
            messages = [{"role": "user", "content": user_content}]

            # Define structured output using Pydantic
            structured_llm = self.llm.with_structured_output(AttireAndBackgroundAnalysis)

            # Invoke with chat-style messages
            try:
                response = structured_llm.invoke(messages)
                
                # Validate and return response
                if isinstance(response, AttireAndBackgroundAnalysis):
                    if response.success:
                        logger.info("Visual analysis completed successfully")
                    else:
                        logger.warning(f"Visual analysis returned unsuccessful: {response.error}")
                    return response
                else:
                    error_msg = "Invalid response type from visual analysis"
                    logger.error(error_msg)
                    return AttireAndBackgroundAnalysis(
                        success=False,
                        attire_analysis="Analysis failed: invalid response type",
                        background_analysis="Analysis failed: invalid response type",
                        attire_percentage=0.0,
                        background_percentage=0.0,
                        error=error_msg
                    )
                    
            except Exception as e:
                error_msg = f"Error in visual analysis: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return AttireAndBackgroundAnalysis(
                    success=False,
                    attire_analysis="Analysis failed",
                    background_analysis="Analysis failed",
                    attire_percentage=0.0,
                    background_percentage=0.0,
                    error=error_msg
                )
                    
        except Exception as e:
            error_msg = f"Error in visual analysis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return AttireAndBackgroundAnalysis(
                success=False,
                attire_analysis="Analysis failed",
                background_analysis="Analysis failed",
                attire_percentage=0.0,
                background_percentage=0.0,
                error=error_msg
            )
            

        except Exception as e:
            logger.error(f"Error in batch analysis: {str(e)}", exc_info=True)
            return AttireAndBackgroundAnalysis(success=False, error=str(e))
