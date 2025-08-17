from .video_extraction import VideoExtractor
import cv2
import numpy as np
import os
import base64
import mediapipe as mp
import google.generativeai as genai
from datetime import datetime
from skimage.metrics import structural_similarity as ssim
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # Using Gemini 2.0 Flash experimental
FRAME_SAMPLING_INTERVAL = int(os.getenv("FRAME_SAMPLING_INTERVAL", "2"))  # Extract frame every N seconds
PROOF_FRAME_PERIODIC_INTERVAL = int(os.getenv("PROOF_FRAME_PERIODIC_INTERVAL", "15"))  # Periodic proof frames every N seconds
PROOF_FRAME_VERIFICATION_INTERVAL = int(os.getenv("PROOF_FRAME_VERIFICATION_INTERVAL", "30"))  # Verification frames every N seconds
PROOF_FRAME_SAMPLE_INTERVAL = int(os.getenv("PROOF_FRAME_SAMPLE_INTERVAL", "300"))  # Sample frames every N seconds (5 min)
MIN_OFF_PERIOD_DURATION = int(os.getenv("MIN_OFF_PERIOD_DURATION", "6"))  # Minimum seconds for significant off period

class VideoProcessor:
    """
    Optimized video processor for analyzing counseling session videos.
    Uses frame-based processing instead of saving temporary video files.
    """
    
    def __init__(self):
        """Initialize the video processor"""
        logger.info("Initializing VideoProcessor")

        # Validate API key early
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            logger.error("GEMINI_API_KEY environment variable not found")
            raise ValueError("GEMINI_API_KEY environment variable is required")

        self.extractor = VideoExtractor()

        # Initialize MediaPipe face detection and face mesh
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Initialize face detection and face mesh with appropriate settings
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 0 for short-range, 1 for full-range detection
            min_detection_confidence=0.5
        )

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # For storing latest detection results
        self.latest_person_ids = {}
        self.latest_static_status = {}

        logger.info("VideoProcessor initialized successfully")

    def cleanup_resources(self):
        """Clean up MediaPipe resources"""
        try:
            if hasattr(self, 'face_detection') and self.face_detection:
                self.face_detection.close()
                logger.debug("Face detection resources cleaned up")

            if hasattr(self, 'face_mesh') and self.face_mesh:
                self.face_mesh.close()
                logger.debug("Face mesh resources cleaned up")

        except Exception as e:
            logger.warning(f"Error during MediaPipe cleanup: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_resources()

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as MM:SS"""
        return f"{int(timestamp//60):02d}:{int(timestamp%60):02d}"

    def _validate_video_url(self, video_url: str) -> None:
        """Validate the video URL format"""
        if not video_url or not isinstance(video_url, str):
            raise ValueError("video_url must be a non-empty string")

        if not ('/file/d/' in video_url or '/id=' in video_url):
            raise ValueError("Invalid Google Drive URL format. URL must contain '/file/d/' or '/id='")

        logger.debug(f"Video URL validation passed: {video_url[:50]}...")

    async def analyze_video(self, video_url: str):
        """
        Main function to analyze a private video from Google Drive.
        Optimized to work with frames directly without temporary video files.

        Args:
            video_url (str): The Google Drive shareable link of the video.

        Returns:
            dict: A dictionary with the analysis results.
        """
        logger.info(f"Starting video analysis for URL: {video_url[:50]}...")

        # Validate input
        try:
            self._validate_video_url(video_url)
        except ValueError as e:
            logger.error(f"Video URL validation failed: {e}")
            raise e

        try:
            # Extract file ID from Google Drive URL
            logger.info("Extracting video frames and audio")
            result = self.extractor.get_video_frames_and_audio_paths(video_url)
            frames_data = result['frames']
            audio_path = result['audio_path']
            metadata = result['metadata']
            logger.info(f"Audio extracted to: {audio_path}")

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
            visual_analysis = self._perform_visual_analysis_from_frames(frames_data, camera_analysis['detailed_results']['camera_timeline'])
            

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
                    "proof_data": {
                        "frames_count": camera_analysis['detailed_results']['proof_frames_count'],
                        "frames": camera_analysis['detailed_results']['proof_frames']  # Now contains base64 data
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
                "visual_intelligence": {
                    "overall_success": (
                        visual_analysis.get('attire_analysis', {}).get('success', False) or
                        visual_analysis.get('background_analysis', {}).get('success', False)
                    ),
                    "analyses": {
                        "attire": {
                            "success": visual_analysis.get('attire_analysis', {}).get('success', False),
                            "summary": visual_analysis.get('attire_analysis', {}).get('summary', 'Analysis not available'),
                            "frames_analyzed": len(visual_analysis.get('attire_analysis', {}).get('analyses', [])),
                            "error": visual_analysis.get('attire_analysis', {}).get('error', None)
                        },
                        "background": {
                            "success": visual_analysis.get('background_analysis', {}).get('success', False),
                            "summary": visual_analysis.get('background_analysis', {}).get('summary', 'Analysis not available'),
                            "frames_analyzed": len(visual_analysis.get('background_analysis', {}).get('analyses', [])),
                            "error": visual_analysis.get('background_analysis', {}).get('error', None)
                        }
                    },
                    "metrics": {
                        "total_frames_analyzed": visual_analysis.get('frames_analyzed', 0),
                        "analysis_coverage_percentage": round(
                            (visual_analysis.get('frames_analyzed', 0) / max(frame_count, 1)) * 100, 2
                        )
                    },
                    "error": visual_analysis.get('error', None)
                },
                
                # Analysis summary
                "analysis_summary": {
                    "overall_success": True,
                    "camera_working": camera_analysis['summary']['camera_on_overall'],
                    "visual_analysis_completed": visual_analysis.get('success', False),
                    "total_people_detected": camera_analysis['summary'].get('person_count', 0),
                    "static_images_detected": camera_analysis['summary'].get('static_image_detection', {}).get('persons_with_static_images', 0)
                },
                
                # Technical metadata
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_version": "1.0",
                    "methods": {
                        "camera_detection": "MediaPipe Face Detection and Face Mesh",
                        "visual_analysis_model": GEMINI_MODEL,
                        "sampling_strategy": "Every 2 seconds",
                        "extraction_method": "Direct frame extraction (no temporary video files)"
                    },
                    "static_detection": {
                        "enabled": True,
                        "method": "MediaPipe Face Mesh + SSIM",
                        "ssim_threshold": 0.95,
                        "landmark_threshold": 0.002
                    }
                }
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
                self.extractor.cleanup()
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
        
        # We'll use MediaPipe for face detection and landmark tracking instead of Haar Cascade
        # MediaPipe is already initialized in __init__
        
        try:
            # Analysis tracking variables
            camera_timeline = []
            person_timelines = {}  # Dictionary to track each person's camera status
            proof_frames = []
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
            person_landmark_history = {}  # Store recent facial landmarks for each person
            static_image_status = {}  # Track which persons have static images
            
            # Store landmark history as an instance variable for use in _is_static_image
            self.person_landmark_history = person_landmark_history

            logger.info(f"Analyzing {len(frames_data)} extracted frames")

            # Process each frame
            for timestamp in sorted(frames_data.keys()):
                frame = frames_data[timestamp]
                total_samples += 1
                
                # Convert to RGB for MediaPipe (it requires RGB input)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Detect faces using MediaPipe
                face_detection_results = self.face_detection.process(rgb_frame)
                face_mesh_results = self.face_mesh.process(rgb_frame)
                
                # Process face detection results
                faces = []
                face_landmarks = []
                
                if face_detection_results.detections:
                    for detection in face_detection_results.detections:
                        # Get bounding box coordinates
                        bbox = detection.location_data.relative_bounding_box
                        h, w, _ = frame.shape
                        x = int(bbox.xmin * w)
                        y = int(bbox.ymin * h)
                        width = int(bbox.width * w)
                        height = int(bbox.height * h)
                        
                        # Add face to the list in the same format as Haar Cascade for compatibility
                        faces.append((x, y, width, height))
                
                # Store face landmarks for static image detection
                if face_mesh_results.multi_face_landmarks:
                    face_landmarks = face_mesh_results.multi_face_landmarks
                
                camera_on = len(faces) > 0
                if camera_on:
                    face_detected_count += 1
                
                # Log progress every 10 frames or when faces are detected
                if total_samples % 10 == 0 or len(faces) > 0:
                    logger.debug(f"Frame {total_samples}: {len(faces)} faces detected at {timestamp:.1f}s ({'ON' if camera_on else 'OFF'})")
                
                # Assign person IDs to detected faces
                current_person_ids = self._assign_person_ids(faces, last_face_positions, person_ids, next_person_id)
                
                # Store the current person IDs, landmarks, and static status for use in proof frame creation
                self.latest_person_ids = current_person_ids
                self.latest_static_status = static_image_status
                
                # Map face landmarks to person IDs if available
                if face_mesh_results.multi_face_landmarks:
                    for i, face_landmarks in enumerate(face_mesh_results.multi_face_landmarks):
                        if i < len(faces) and f"{i}" in current_person_ids:
                            person_id = current_person_ids[f"{i}"]
                            
                            # Initialize landmark history for this person if needed
                            if person_id not in person_landmark_history:
                                person_landmark_history[person_id] = []
                            
                            # Add current landmarks to history (keep last 5 sets)
                            person_landmark_history[person_id].append(face_landmarks)
                            if len(person_landmark_history[person_id]) > 5:
                                person_landmark_history[person_id].pop(0)
                
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
                
                # Handle proof frame collection
                self._handle_proof_frame_collection(
                    frame, timestamp, camera_on, faces, len(faces),
                    current_off_start, consecutive_off_count, proof_frames
                )
                
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
                        'persons_with_static_images': sum(1 for pid, stats in person_stats.items() if stats.get('using_static_image', False)),
                        'detection_method': 'MediaPipe Face Mesh + SSIM',
                        'ssim_threshold': 0.95,  # SSIM threshold used for detection
                        'landmark_movement_threshold': 0.002  # Threshold for facial landmark movement
                    }
                },
                
                'detailed_results': {
                    'camera_timeline': camera_timeline,
                    'person_timelines': person_timelines,
                    'person_stats': person_stats,
                    'off_periods': off_periods,
                    'person_off_periods': person_off_periods,
                    'proof_frames_count': len(proof_frames),
                    'proof_frames': proof_frames
                },
                
                'analysis_metadata': {
                    'detection_method': 'MediaPipe Face Detection and Face Mesh',
                    'sampling_strategy': f'Every {FRAME_SAMPLING_INTERVAL} seconds',
                    'proof_collection': 'Automated for OFF events + periodic ON samples',
                    'minimum_off_period_for_documentation': MIN_OFF_PERIOD_DURATION,
                    'static_image_detection': 'Enhanced with facial landmark tracking'
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing camera status: {e}", exc_info=True)
            return {
                'error': f'Error analyzing camera status: {e}',
                'success': False
            }

    def _handle_proof_frame_collection(self, frame, timestamp, camera_on, faces, face_count, 
                                 current_off_start, consecutive_off_count, proof_frames):
        # Handle proof frame collection logic
        if not camera_on:
            if current_off_start is None:
                # First OFF frame
                proof_frame_base64 = self._create_proof_frame(frame, timestamp, "CAMERA OFF - START", faces)
                if proof_frame_base64:  # Only add if encoding succeeded
                    proof_frames.append({
                        'timestamp': timestamp,
                        'timestamp_formatted': self._format_timestamp(timestamp),
                        'image_base64': proof_frame_base64,  # 🚀 Now base64 string
                        'status': 'camera_off_start',
                        'face_count': face_count,
                        'description': 'Camera turned off - start of off period'
                    })
            elif consecutive_off_count % 5 == 0:  # Every 5 samples (10 seconds) during OFF
                off_duration = timestamp - current_off_start if current_off_start else 0
                proof_frame_base64 = self._create_proof_frame(
                    frame, timestamp, f"CAMERA OFF - {off_duration:.0f}s", faces
                )
                if proof_frame_base64:  # Only add if encoding succeeded
                    proof_frames.append({
                        'timestamp': timestamp,
                        'timestamp_formatted': self._format_timestamp(timestamp),
                        'image_base64': proof_frame_base64,  # 🚀 Now base64 string
                        'status': 'camera_off_continued',
                        'off_duration': off_duration,
                        'face_count': face_count,
                        'description': f'Camera still off after {off_duration:.0f} seconds'
                    })
        else:  # Camera is ON
            if current_off_start is not None:
                off_duration = timestamp - current_off_start
                if off_duration >= MIN_OFF_PERIOD_DURATION:  # Only document significant OFF periods
                    proof_frame_base64 = self._create_proof_frame(
                        frame, timestamp, f"CAMERA BACK ON (was off {off_duration:.0f}s)", faces
                    )
                    if proof_frame_base64:  # Only add if encoding succeeded
                        proof_frames.append({
                            'timestamp': timestamp,
                            'timestamp_formatted': self._format_timestamp(timestamp),
                            'image_base64': proof_frame_base64,  # 🚀 Now base64 string
                            'status': 'camera_back_on',
                            'off_duration': off_duration,
                            'face_count': face_count,
                            'description': f'Camera back on after {off_duration:.0f} seconds off'
                        })
            
            # Collect periodic ON samples
            elif int(timestamp) % PROOF_FRAME_SAMPLE_INTERVAL == 0 and timestamp > 0:  # Every 5 minutes
                proof_frame_base64 = self._create_proof_frame(frame, timestamp, "CAMERA ON - SAMPLE", faces)
                if proof_frame_base64:  # Only add if encoding succeeded
                    proof_frames.append({
                        'timestamp': timestamp,
                        'timestamp_formatted': self._format_timestamp(timestamp),
                        'image_base64': proof_frame_base64,  # 🚀 Now base64 string
                        'status': 'camera_on_sample',
                        'face_count': face_count,
                        'description': 'Periodic sample showing camera is on'
                    })
            elif int(timestamp) % PROOF_FRAME_VERIFICATION_INTERVAL == 0 and timestamp > 0:  # Every 30 seconds
                proof_frame_base64 = self._create_proof_frame(frame, timestamp, "CAMERA ON - VERIFICATION", faces)
                if proof_frame_base64:  # Only add if encoding succeeded
                    proof_frames.append({
                        'timestamp': timestamp,
                        'timestamp_formatted': self._format_timestamp(timestamp),
                        'image_base64': proof_frame_base64,  # 🚀 Now base64 string
                        'status': 'camera_on_verification',
                        'face_count': face_count,
                        'description': 'Regular verification that camera is on'
                    })
        
        # Collect proof frames more frequently (every 15 seconds)
        if int(timestamp) % PROOF_FRAME_PERIODIC_INTERVAL == 0 and timestamp > 0:
            status_text = "CAMERA ON" if camera_on else "CAMERA OFF"
            proof_frame_base64 = self._create_proof_frame(frame, timestamp, status_text, faces)
            if proof_frame_base64:  # Only add if encoding succeeded
                proof_frames.append({
                    'timestamp': timestamp,
                    'timestamp_formatted': self._format_timestamp(timestamp),
                    'image_base64': proof_frame_base64,  # 🚀 Now base64 string
                    'status': 'periodic_check',
                    'face_count': face_count,
                    'description': f'Periodic check - camera is {"on" if camera_on else "off"}'
                })

    def _create_proof_frame(self, frame, timestamp, status_text, faces):
        """Create proof frame with overlays and return as base64 string"""
        proof_frame = frame.copy()
        height, width = proof_frame.shape[:2]
        
        # Convert timestamp to readable format
        minutes = int(timestamp // 60)
        seconds = int(timestamp % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Create semi-transparent overlay for text background
        overlay = proof_frame.copy()
        text_height = 120 if len(faces) > 0 else 100
        cv2.rectangle(overlay, (10, 10), (500, text_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, proof_frame, 0.3, 0, proof_frame)
        
        # Add timestamp
        cv2.putText(proof_frame, f"Time: {time_str}", (20, 35), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Add status with color coding
        status_color = (0, 255, 0) if "ON" in status_text else (0, 0, 255)
        cv2.putText(proof_frame, f"Status: {status_text}", (20, 65), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Add face detection info and draw boxes
        if len(faces) > 0:
            cv2.putText(proof_frame, f"Faces detected: {len(faces)}", (20, 95), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Define a list of distinct colors for different faces
            colors = [
                (0, 255, 0),    # Green
                (255, 0, 0),    # Blue (in BGR)
                (0, 0, 255),    # Red
                (255, 255, 0),  # Cyan
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Yellow
            ]
            
            # Get person IDs from the latest camera timeline entry if available
            person_ids = {}
            if hasattr(self, 'latest_person_ids') and self.latest_person_ids:
                person_ids = self.latest_person_ids
            
            # Get static image status if available
            static_status = {}
            if hasattr(self, 'latest_static_status') and self.latest_static_status:
                static_status = self.latest_static_status
            
            for i, (x, y, w, h) in enumerate(faces):
                # Use modulo to cycle through colors if there are more faces than colors
                color = colors[i % len(colors)]
                cv2.rectangle(proof_frame, (x, y), (x+w, y+h), color, 2)
                
                # Add person ID label if available
                face_key = f"{i}"
                if face_key in person_ids:
                    person_id = person_ids[face_key]
                    is_static = static_status.get(person_id, False)
                    
                    if is_static:
                        # Add diagonal pattern for static images
                        for j in range(0, w, 10):
                            cv2.line(proof_frame, (x+j, y), (x+min(j+10, w), y+10), color, 1)
                        for j in range(0, h, 10):
                            cv2.line(proof_frame, (x, y+j), (x+10, y+min(j+10, h)), color, 1)
                        
                        cv2.putText(proof_frame, f"PERSON {person_id} [STATIC]", (x, y-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                        # Add MediaPipe landmarks for static image detection visualization
                        if hasattr(self, 'person_landmark_history') and person_id in self.person_landmark_history and self.person_landmark_history[person_id]:
                            # Draw the facial landmarks from MediaPipe
                            landmarks = self.person_landmark_history[person_id][-1]
                            self.mp_drawing.draw_landmarks(
                                image=proof_frame,
                                landmark_list=landmarks,
                                connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                                landmark_drawing_spec=None,
                                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                            )
                    else:
                        cv2.putText(proof_frame, f"PERSON {person_id}", (x, y-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                        # Add MediaPipe landmarks for normal faces too
                        if hasattr(self, 'person_landmark_history') and person_id in self.person_landmark_history and self.person_landmark_history[person_id]:
                            # Draw just the contours for non-static faces (less cluttered)
                            landmarks = self.person_landmark_history[person_id][-1]
                            self.mp_drawing.draw_landmarks(
                                image=proof_frame,
                                landmark_list=landmarks,
                                connections=self.mp_face_mesh.FACEMESH_CONTOURS,
                                landmark_drawing_spec=None,
                                connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_contours_style()
                            )
                else:
                    cv2.putText(proof_frame, f"FACE {i+1}", (x, y-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        else:
            cv2.putText(proof_frame, "No faces detected", (20, 95), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add colored border for emphasis
        cv2.rectangle(proof_frame, (5, 5), (width-5, height-5), status_color, 3)
        
        # 🚀 FIX: Convert numpy array to base64 string before returning
        base64_image = self._encode_frame_to_base64(proof_frame)
        
        if base64_image is None:
            # Fallback: return a simple error indicator
            logger.warning(f"Failed to encode proof frame at {timestamp:.1f}s to base64")
            return None
        
        return base64_image

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

    def _calculate_landmark_movement(self, landmarks1, landmarks2):
        """Calculate movement between facial landmarks in two frames"""
        if not landmarks1 or not landmarks2:
            return 1.0  # Return high movement if landmarks are missing
            
        # Calculate the average movement of key facial landmarks
        # We'll focus on specific landmarks that should move in a live person
        # These include eyes, eyebrows, mouth, and nose
        key_landmark_indices = [
            61, 146, 91, 181, 84, 17, 314, 405,  # Eyes
            0, 267,  # Mouth corners
            13, 14, 33, 133, 362, 386  # Nose and cheeks
        ]
        
        total_movement = 0.0
        count = 0
        
        for idx in key_landmark_indices:
            if idx < len(landmarks1.landmark) and idx < len(landmarks2.landmark):
                lm1 = landmarks1.landmark[idx]
                lm2 = landmarks2.landmark[idx]
                
                # Calculate Euclidean distance between landmarks
                movement = ((lm1.x - lm2.x)**2 + (lm1.y - lm2.y)**2 + (lm1.z - lm2.z)**2)**0.5
                total_movement += movement
                count += 1
        
        if count == 0:
            return 1.0
            
        return total_movement / count
    
    
    def _is_static_image(self, current_frame, person_id, person_frame_history, similarity_threshold=0.95, landmark_threshold=0.002):
        """Determine if a person's image is static (like a profile picture)"""
        if person_id not in person_frame_history or len(person_frame_history[person_id]) < 3:
            return False
        
        # Get the last few frames for this person
        recent_frames = person_frame_history[person_id][-3:]
        
        # First check: Calculate similarity between current frame and recent frames using SSIM
        similarities = [self._calculate_frame_similarity(current_frame, frame) for frame in recent_frames]
        frame_similarity_static = all(sim > similarity_threshold for sim in similarities)
        
        # Second check: If we have facial landmarks, analyze their movement
        landmark_static = False
        
        # If we have stored landmarks for this person
        if hasattr(self, 'person_landmark_history') and person_id in self.person_landmark_history:
            landmarks = self.person_landmark_history[person_id]
            if len(landmarks) >= 3:
                # Calculate movement between consecutive landmark sets
                movements = []
                for i in range(len(landmarks) - 1):
                    movement = self._calculate_landmark_movement(landmarks[i], landmarks[i+1])
                    movements.append(movement)
                
                # If all movements are below threshold, consider it static
                landmark_static = all(move < landmark_threshold for move in movements)
        
        # Combine both checks - if both indicate static or if only SSIM is available and indicates static
        if hasattr(self, 'person_landmark_history') and person_id in self.person_landmark_history:
            return frame_similarity_static and landmark_static
        else:
            return frame_similarity_static  # Fall back to just SSIM if landmarks aren't available
    
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
         
    def _analyze_frames_batch_with_gemini(self, frames, timestamps):
        """Analyze multiple frames in a single batch using Google Gemini 2.0 Flash Vision API
        
        Args:
            frames: List of frames to analyze
            timestamps: List of timestamps corresponding to frames
            
        Returns:
            dict: Combined analysis results for all frames
        """
        try:
            # Configure Gemini (API key already validated in __init__)
            genai.configure(api_key=self.gemini_api_key)
            
            # Create Gemini model
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            # Encode all frames to base64
            encoded_frames = [
                base64_image for frame in frames
                if (base64_image := self._encode_frame_to_base64(frame)) is not None
            ]
            
            if not encoded_frames:
                return {
                    'success': False,
                    'error': 'Failed to encode any frames to base64'
                }
            
            # Prepare combined prompt for attire analysis
            attire_prompt = """Analyze the professional attire in these counseling session images.
            For EACH image, provide a separate analysis considering:
            - Is the clothing appropriate and professional?
            - Does it meet counseling session standards?
            - Any concerns about attire professionalism?
            
            Format your response with numbered sections (1, 2, 3) for each image.
            Keep each analysis brief and professional."""
            
            # Prepare combined prompt for background analysis
            background_prompt = """Analyze the background settings in these counseling session images.
            For EACH image, provide a separate analysis considering:
            - Is the background appropriate and professional?
            - Privacy and confidentiality concerns?
            - Distractions or inappropriate elements?
            - Overall suitability for counseling?
            
            Format your response with numbered sections (1, 2, 3) for each image.
            Keep each analysis brief and professional."""
            
            # Prepare image data for all frames
            image_parts = []
            for base64_image in encoded_frames:
                image_parts.append({
                    "mime_type": "image/jpeg",
                    "data": base64_image
                })
            
            # Make API request for attire analysis
            logger.info(f"Sending batch attire analysis for {len(encoded_frames)} frames to Gemini")
            attire_analyses = []

            try:
                attire_content = [attire_prompt] + image_parts
                attire_response = model.generate_content(
                    attire_content,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=1024,  # Increased for multiple analyses
                        temperature=0.3
                    )
                )
                
                if attire_response and attire_response.text:
                    # Parse the numbered responses
                    attire_text = attire_response.text.strip()
                    attire_results = self._parse_numbered_responses(attire_text, timestamps)
                    attire_analyses = attire_results
                    logger.info(f"Batch attire analysis completed for {len(attire_analyses)} frames")
                else:
                    logger.warning("Gemini API returned empty response for attire analysis")
            except Exception as e:
                logger.error(f"Error in batch attire analysis: {str(e)}")

            # Make API request for background analysis
            logger.info(f"Sending batch background analysis for {len(encoded_frames)} frames to Gemini")
            background_analyses = []
            
            try:
                background_content = [background_prompt] + image_parts
                background_response = model.generate_content(
                    background_content,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=1024,  # Increased for multiple analyses
                        temperature=0.3
                    )
                )
                
                if background_response and background_response.text:
                    # Parse the numbered responses
                    background_text = background_response.text.strip()
                    background_results = self._parse_numbered_responses(background_text, timestamps)
                    background_analyses = background_results
                    logger.info(f"Batch background analysis completed for {len(background_analyses)} frames")
                else:
                    logger.warning("Gemini API returned empty response for background analysis")
            except Exception as e:
                logger.error(f"Error in batch background analysis: {str(e)}")
            
            # Return combined results
            return {
                'success': True,
                'attire_analyses': attire_analyses,
                'background_analyses': background_analyses
            }
                
        except Exception as e:
            error_msg = f"Error in batch analysis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _parse_numbered_responses(self, text, timestamps):
        """Parse numbered responses from Gemini API
        
        Args:
            text: The text response from Gemini API
            timestamps: List of timestamps corresponding to frames
            
        Returns:
            list: List of parsed analyses with timestamps
        """
        analyses = []
        
        # Simple parsing based on numbered sections
        # This is a basic implementation and might need refinement
        import re
        
        # Look for numbered sections (1., 2., etc.)
        sections = re.split(r'\n\s*\d+\.\s*', '\n' + text)
        
        # Remove empty first element if it exists
        if sections and not sections[0].strip():
            sections = sections[1:]
        
        # Match sections with timestamps
        for i, section in enumerate(sections):
            if i < len(timestamps):
                analyses.append({
                    'timestamp': timestamps[i],
                    'analysis': section.strip()
                })
        
        return analyses

    def _select_best_frames_for_analysis(self, camera_timeline, max_frames=3):
        """Select the best frames for visual analysis based on face count"""
        try:
            # Filter frames with faces detected and sort by face count
            frames_with_faces = [
                event for event in camera_timeline 
                if event['face_count'] > 0
            ]
            
            # Sort by face count (descending) and timestamp
            frames_with_faces.sort(
                key=lambda x: (x['face_count'], x['timestamp']), 
                reverse=True
            )
            
            # Select top frames
            selected_frames = frames_with_faces[:max_frames]
            
            logger.info(f"Selected {len(selected_frames)} frames for visual analysis")
            for i, frame in enumerate(selected_frames):
                logger.debug(f"   Frame {i+1}: {frame['face_count']} faces at {frame['timestamp']:.1f}s")
            
            return selected_frames
            
        except Exception as e:
            logger.error(f"Error selecting frames for analysis: {e}")
            return []

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

            # Select best frames for analysis
            selected_frames = self._select_best_frames_for_analysis(camera_timeline, max_frames=3)
            
            if not selected_frames:
                return {
                    'success': False,
                    'error': 'No suitable frames found for visual analysis'
                }
            
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
                return {
                    'success': False,
                    'error': 'No valid frames available for analysis'
                }
            
            # Perform batch analysis for all frames at once
            logger.info(f"Analyzing {len(valid_frames)} frames in a single batch")
            batch_results = self._analyze_frames_batch_with_gemini(valid_frames, valid_timestamps)
            
            if not batch_results['success']:
                return batch_results
            
            # Compile results
            visual_analysis = {
                'success': True,
                'frames_analyzed': len(valid_frames),
                'attire_analysis': {
                    'success': len(batch_results.get('attire_analyses', [])) > 0,
                    'analyses': batch_results.get('attire_analyses', []),
                    'summary': self._summarize_analyses(batch_results.get('attire_analyses', [])) if batch_results.get('attire_analyses') else None
                },
                'background_analysis': {
                    'success': len(batch_results.get('background_analyses', [])) > 0,
                    'analyses': batch_results.get('background_analyses', []),
                    'summary': self._summarize_analyses(batch_results.get('background_analyses', [])) if batch_results.get('background_analyses') else None
                }
            }
            
            logger.info(f"Visual analysis completed: {len(batch_results.get('attire_analyses', []))} attire, {len(batch_results.get('background_analyses', []))} background analyses")

            return visual_analysis

        except Exception as e:
            error_msg = f"Error in visual analysis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }

    def _summarize_analyses(self, analyses):
        """Create a summary of multiple analyses"""
        if not analyses:
            return "No analyses available"
        
        # For now, return the first analysis as summary
        # In the future, this could use Gemini to summarize multiple analyses
        return analyses[0]['analysis']

