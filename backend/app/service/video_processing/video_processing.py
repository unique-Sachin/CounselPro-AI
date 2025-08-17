from .video_extraction import VideoExtractor
import cv2
import numpy as np
import tempfile
import shutil
import os
import base64
import google.generativeai as genai
from datetime import datetime

# Gemini API Configuration
GEMINI_MODEL = "gemini-2.0-flash"  # Using Gemini 2.0 Flash experimental

class VideoProcessor:
    """
    Optimized video processor for analyzing counseling session videos.
    Uses frame-based processing instead of saving temporary video files.
    """
    
    def __init__(self):
        """Initialize the video processor"""
        self.extractor = VideoExtractor()

    async def analyze_video(self, video_url: str):
        """
        Main function to analyze a private video from Google Drive.
        Optimized to work with frames directly without temporary video files.
        
        Args:
            video_url (str): The Google Drive shareable link of the video.
            
        Returns:
            dict: A dictionary with the analysis results.
        """
        print(f"🚀 Starting video analysis for URL: {video_url}")
        
        try:
            # Extract file ID from Google Drive URL
            result = self.extractor.get_video_frames_and_audio_paths(video_url)
            frames_data = result['frames']
            audio_path = result['audio_path'] 
            metadata = result['metadata']
            print(f"📹 Audio path: {audio_path}")

            fps = metadata['fps']
            duration = metadata['duration']
            frame_count = metadata['total_frames']
            
            print(f"📹 Video metadata: {duration:.1f}s, {fps:.1f} fps, {frame_count} frames")
            
            # Analyze camera status using extracted frames
            print("🎥 Starting camera status analysis...")
            camera_analysis = self.analyze_camera_status_from_frames(frames_data, duration, fps)
            
            # Check if camera analysis was successful
            if not camera_analysis.get('success', False):
                raise Exception(f"Camera analysis failed: {camera_analysis.get('error', 'Unknown error')}")
            
            print("✅ Camera analysis completed successfully")
            
            # Perform visual intelligence analysis
            print("🎨 Starting visual intelligence analysis...")
            visual_analysis = self._perform_visual_analysis_from_frames(frames_data, camera_analysis['detailed_results']['camera_timeline'])
            
            
            # Construct the structured response for frontend
            print("📋 Constructing final results...")
            results = {
                # Basic video information
                "video_info": {
                    "duration_seconds": round(duration, 2),
                    "frame_count": frame_count,
                    "fps": round(fps, 2),
                    "audio_path": audio_path,
                    "width": metadata['width'],
                    "height": metadata['height']
                },
                
                # Camera analysis results
                "camera_analysis": {
                    "status": "On" if camera_analysis['summary']['camera_on_overall'] else "Off",
                    "on_percentage": camera_analysis['summary']['camera_on_percentage'],
                    "total_samples": camera_analysis['summary']['total_samples_analyzed'],
                    "samples_with_faces": camera_analysis['summary']['samples_with_faces'],
                    "significant_off_periods": camera_analysis['summary']['significant_off_periods'],
                    "total_off_duration": camera_analysis['summary']['total_off_duration'],
                    "off_periods": camera_analysis['detailed_results']['off_periods'],
                    "proof_frames_count": camera_analysis['detailed_results']['proof_frames_count'],
                    "proof_frames": camera_analysis['detailed_results']['proof_frames'],
                    # Detailed frame-by-frame timeline for UI
                    "frame_timeline": [
                        {
                            "timestamp": frame['timestamp'],
                            "timestamp_formatted": f"{int(frame['timestamp']//60):02d}:{int(frame['timestamp']%60):02d}",
                            "camera_on": frame['camera_on'],
                            "face_count": frame['face_count'],
                            "face_positions": frame['face_positions']
                        }
                        for frame in camera_analysis['detailed_results']['camera_timeline']
                    ]
                },
                
                # Visual intelligence results
                "visual_intelligence": {
                    "attire_analysis": {
                        "success": visual_analysis.get('attire_analysis', {}).get('success', False),
                        "summary": visual_analysis.get('attire_analysis', {}).get('summary', 'Analysis not available'),
                        "frames_analyzed": len(visual_analysis.get('attire_analysis', {}).get('analyses', [])),
                        "error": visual_analysis.get('attire_analysis', {}).get('error', None)
                    },
                    "background_analysis": {
                        "success": visual_analysis.get('background_analysis', {}).get('success', False),
                        "summary": visual_analysis.get('background_analysis', {}).get('summary', 'Analysis not available'),
                        "frames_analyzed": len(visual_analysis.get('background_analysis', {}).get('analyses', [])),
                        "error": visual_analysis.get('background_analysis', {}).get('error', None)
                    },
                    "total_frames_analyzed": visual_analysis.get('frames_analyzed', 0),
                    "error": visual_analysis.get('error', None)
                },
                
                # Analysis metadata
                "analysis_metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "camera_detection_method": "Haar Cascade Face Detection",
                    "visual_analysis_model": GEMINI_MODEL,
                    "sampling_strategy": f"Every 2 seconds",
                    "extraction_method": "Direct frame extraction (no temporary video files)"
                }
            }
            
            # Print comprehensive results
            self._print_comprehensive_results(results)
            
            return results
            
        except Exception as e:
            print(f"❌ An error occurred during video analysis: {e}")
            raise e
            
        finally:
            # Cleanup
            self.extractor.cleanup()

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
        
        # Load the pre-trained Haar Cascade for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        if face_cascade.empty():
            return {
                'error': 'Error loading face cascade XML file',
                'success': False
            }
        
        try:
            # Analysis tracking variables
            camera_timeline = []
            proof_frames = []
            face_detected_count = 0
            total_samples = 0
            
            # Camera OFF period tracking
            current_off_start = None
            consecutive_off_count = 0
            
            print(f"Analyzing {len(frames_data)} extracted frames...")
            
            # Process each frame
            for timestamp in sorted(frames_data.keys()):
                frame = frames_data[timestamp]
                total_samples += 1
                
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5, 
                    minSize=(30, 30)
                )
                
                camera_on = len(faces) > 0
                if camera_on:
                    face_detected_count += 1
                
                # Print progress every 10 frames or when faces are detected
                if total_samples % 10 == 0 or len(faces) > 0:
                    print(f"📸 Frame {total_samples}: {len(faces)} faces detected at {timestamp:.1f}s ({'ON' if camera_on else 'OFF'})")
                
                # Add to timeline
                camera_timeline.append({
                    'timestamp': timestamp,
                    'camera_on': camera_on,
                    'face_count': len(faces),
                    'face_positions': faces.tolist() if len(faces) > 0 else []
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
            
            # Detect significant OFF periods
            off_periods = self._detect_off_periods(camera_timeline)
            
            print(f"Analysis complete: {face_detected_count}/{total_samples} samples with faces detected")
            
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
                    'sampling_interval_seconds': 2.0,
                    'significant_off_periods': len(off_periods),
                    'total_off_duration': sum(p['duration'] for p in off_periods)
                },
                
                'detailed_results': {
                    'camera_timeline': camera_timeline,
                    'off_periods': off_periods,
                    'proof_frames_count': len(proof_frames),
                    'proof_frames': proof_frames
                },
                
                'analysis_metadata': {
                    'detection_method': 'Haar Cascade Face Detection',
                    'sampling_strategy': 'Every 2 seconds',
                    'proof_collection': 'Automated for OFF events + periodic ON samples',
                    'minimum_off_period_for_documentation': 6
                }
            }
            
        except Exception as e:
            print(f"Error analyzing camera status: {e}")
            return {
                'error': f'Error analyzing camera status: {e}',
                'success': False
            }

    def _handle_proof_frame_collection(self, frame, timestamp, camera_on, faces, face_count, 
                                     current_off_start, consecutive_off_count, proof_frames):
        """Handle proof frame collection logic"""
        if not camera_on:
            if current_off_start is None:
                # First OFF frame
                proof_frame = self._create_proof_frame(frame, timestamp, "CAMERA OFF - START", faces)
                proof_frames.append({
                    'timestamp': timestamp,
                    'frame': proof_frame,
                    'status': 'camera_off_start',
                    'face_count': face_count
                })
            elif consecutive_off_count % 5 == 0:  # Every 10 seconds during OFF
                off_duration = timestamp - current_off_start if current_off_start else 0
                proof_frame = self._create_proof_frame(
                    frame, timestamp, f"CAMERA OFF - {off_duration:.0f}s", faces
                )
                proof_frames.append({
                    'timestamp': timestamp,
                    'frame': proof_frame,
                    'status': 'camera_off_continued',
                    'off_duration': off_duration,
                    'face_count': face_count
                })
        else:  # Camera is ON
            if current_off_start is not None:
                off_duration = timestamp - current_off_start
                if off_duration >= 6:  # Only document significant OFF periods
                    proof_frame = self._create_proof_frame(
                        frame, timestamp, f"CAMERA BACK ON (was off {off_duration:.0f}s)", faces
                    )
                    proof_frames.append({
                        'timestamp': timestamp,
                        'frame': proof_frame,
                        'status': 'camera_back_on',
                        'off_duration': off_duration,
                        'face_count': face_count
                    })
            
            # Collect periodic ON samples
            elif int(timestamp) % 300 == 0 and timestamp > 0:  # Every 5 minutes
                proof_frame = self._create_proof_frame(frame, timestamp, "CAMERA ON - SAMPLE", faces)
                proof_frames.append({
                    'timestamp': timestamp,
                    'frame': proof_frame,
                    'status': 'camera_on_sample',
                    'face_count': face_count
                })
            elif int(timestamp) % 30 == 0 and timestamp > 0:  # Every 30 seconds
                proof_frame = self._create_proof_frame(frame, timestamp, "CAMERA ON - VERIFICATION", faces)
                proof_frames.append({
                    'timestamp': timestamp,
                    'frame': proof_frame,
                    'status': 'camera_on_verification',
                    'face_count': face_count
                })
        
        # Collect proof frames more frequently (every 15 seconds)
        if int(timestamp) % 15 == 0 and timestamp > 0:
            status_text = "CAMERA ON" if camera_on else "CAMERA OFF"
            proof_frame = self._create_proof_frame(frame, timestamp, status_text, faces)
            proof_frames.append({
                'timestamp': timestamp,
                'frame': proof_frame,
                'status': 'periodic_check',
                'face_count': face_count
            })

    def _create_proof_frame(self, frame, timestamp, status_text, faces):
        """Create proof frame with overlays"""
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
            
            for i, (x, y, w, h) in enumerate(faces):
                # Use modulo to cycle through colors if there are more faces than colors
                color = colors[i % len(colors)]
                cv2.rectangle(proof_frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(proof_frame, f"FACE {i+1}", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        else:
            cv2.putText(proof_frame, "No faces detected", (20, 95), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add colored border for emphasis
        cv2.rectangle(proof_frame, (5, 5), (width-5, height-5), status_color, 3)
        
        return proof_frame

    def _detect_off_periods(self, camera_timeline):
        """Detect significant camera OFF periods from timeline"""
        off_periods = []
        current_off_start = None
        
        for event in camera_timeline:
            if not event['camera_on'] and current_off_start is None:
                current_off_start = event['timestamp']
            elif event['camera_on'] and current_off_start is not None:
                duration = event['timestamp'] - current_off_start
                
                # Only include significant OFF periods (6+ seconds)
                if duration >= 6:
                    off_periods.append({
                        'start_time': current_off_start,
                        'end_time': event['timestamp'],
                        'duration': duration,
                        'start_formatted': f"{int(current_off_start//60):02d}:{int(current_off_start%60):02d}",
                        'end_formatted': f"{int(event['timestamp']//60):02d}:{int(event['timestamp']%60):02d}"
                    })
                
                current_off_start = None
        
        # Handle case where video ends during OFF period
        if current_off_start is not None and camera_timeline:
            last_timestamp = camera_timeline[-1]['timestamp']
            duration = last_timestamp - current_off_start
            
            if duration >= 6:
                off_periods.append({
                    'start_time': current_off_start,
                    'end_time': last_timestamp,
                    'duration': duration,
                    'start_formatted': f"{int(current_off_start//60):02d}:{int(current_off_start%60):02d}",
                    'end_formatted': f"{int(last_timestamp//60):02d}:{int(last_timestamp%60):02d}"
                })
        
        return off_periods

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
            print(f"❌ Error encoding frame to base64: {e}")
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
            # Get Gemini API key from environment
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                return {
                    'success': False,
                    'error': 'Gemini API key not found. Please set GEMINI_API_KEY environment variable.'
                }
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Create Gemini model
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            # Encode all frames to base64
            encoded_frames = []
            for frame in frames:
                base64_image = self._encode_frame_to_base64(frame)
                if base64_image:
                    encoded_frames.append(base64_image)
                else:
                    print("⚠️ Failed to encode a frame to base64, skipping")
            
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
            print(f"🤖 Sending batch attire analysis for {len(encoded_frames)} frames to Gemini 2.0 Flash...")
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
                    print(f"✅ Batch attire analysis completed for {len(attire_analyses)} frames")
                else:
                    print("❌ Gemini API returned empty response for attire analysis")
            except Exception as e:
                print(f"❌ Error in batch attire analysis: {str(e)}")
            
            # Make API request for background analysis
            print(f"🤖 Sending batch background analysis for {len(encoded_frames)} frames to Gemini 2.0 Flash...")
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
                    print(f"✅ Batch background analysis completed for {len(background_analyses)} frames")
                else:
                    print("❌ Gemini API returned empty response for background analysis")
            except Exception as e:
                print(f"❌ Error in batch background analysis: {str(e)}")
            
            # Return combined results
            return {
                'success': True,
                'attire_analyses': attire_analyses,
                'background_analyses': background_analyses
            }
                
        except Exception as e:
            error_msg = f"Error in batch analysis: {str(e)}"
            print(f"❌ {error_msg}")
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
            
            print(f"📸 Selected {len(selected_frames)} frames for visual analysis")
            for i, frame in enumerate(selected_frames):
                print(f"   Frame {i+1}: {frame['face_count']} faces at {frame['timestamp']:.1f}s")
            
            return selected_frames
            
        except Exception as e:
            print(f"❌ Error selecting frames for analysis: {e}")
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
            print("🎨 Starting visual intelligence analysis from extracted frames...")
            
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
                print(f"🔍 Preparing frame {i+1} at {timestamp:.1f}s...")
                
                # Get frame from pre-extracted data
                frame = frames_data.get(timestamp)
                if frame is None:
                    print(f"⚠️ Frame not available at {timestamp:.1f}s")
                    continue
                
                valid_frames.append(frame)
                valid_timestamps.append(timestamp)
            
            if not valid_frames:
                return {
                    'success': False,
                    'error': 'No valid frames available for analysis'
                }
            
            # Perform batch analysis for all frames at once
            print(f"🤖 Analyzing {len(valid_frames)} frames in a single batch...")
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
            
            print(f"✅ Visual analysis completed: {len(batch_results.get('attire_analyses', []))} attire, {len(batch_results.get('background_analyses', []))} background analyses")
            
            return visual_analysis
            
        except Exception as e:
            error_msg = f"Error in visual analysis: {str(e)}"
            print(f"❌ {error_msg}")
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

    def _print_comprehensive_results(self, results):
        """Print comprehensive analysis results"""
        print("\n" + "="*60)
        print("📊 COMPLETE ANALYSIS RESULTS")
        print("="*60)
        
        # Video info
        print(f"\n📹 VIDEO INFORMATION:")
        print(f"   Duration: {results['video_info']['duration_seconds']} seconds")
        print(f"   Frame Count: {results['video_info']['frame_count']}")
        print(f"   FPS: {results['video_info']['fps']}")
        print(f"   Dimensions: {results['video_info']['width']}x{results['video_info']['height']}")
        print(f"   Audio Path: {results['video_info']['audio_path']}")
        
        # Camera analysis
        print(f"\n🎥 CAMERA ANALYSIS:")
        print(f"   Overall Status: {results['camera_analysis']['status']}")
        print(f"   On Percentage: {results['camera_analysis']['on_percentage']}%")
        print(f"   Total Samples: {results['camera_analysis']['total_samples']}")
        print(f"   Samples with Faces: {results['camera_analysis']['samples_with_faces']}")
        print(f"   Significant Off Periods: {results['camera_analysis']['significant_off_periods']}")
        print(f"   Total Off Duration: {results['camera_analysis']['total_off_duration']} seconds")
        print(f"   Proof Frames Count: {results['camera_analysis']['proof_frames_count']}")
        print(f"   Timeline Entries: {len(results['camera_analysis']['frame_timeline'])}")
        
        # Off periods details
        print(f"\n📅 OFF PERIODS DETAILS:")
        off_periods = results['camera_analysis']['off_periods']
        for i, period in enumerate(off_periods):
            print(f"   Period {i+1}: {period['start_formatted']} - {period['end_formatted']} ({period['duration']:.1f}s)")
        
        # Frame timeline preview
        print(f"\n📅 FRAME TIMELINE PREVIEW (first 10 frames):")
        timeline = results['camera_analysis']['frame_timeline']
        for i, frame in enumerate(timeline[:10]):
            status = "🟢 ON" if frame['camera_on'] else "🔴 OFF"
            face_positions = f"{len(frame['face_positions'])} positions" if frame['face_positions'] else "no positions"
            print(f"   {frame['timestamp_formatted']} - {status} - {frame['face_count']} faces - {face_positions}")
        
        if len(timeline) > 10:
            print(f"   ... and {len(timeline) - 10} more frames")
        
        # Proof frames details
        print(f"\n📷 PROOF FRAMES DETAILS:")
        proof_frames = results['camera_analysis']['proof_frames']
        for i, proof in enumerate(proof_frames):
            off_duration = f" (off for {proof.get('off_duration', 0):.1f}s)" if 'off_duration' in proof else ""
            print(f"   Proof {i+1}: {proof['status']} at {proof['timestamp']:.1f}s - {proof['face_count']} faces{off_duration}")
            if 'frame' in proof and proof['frame'] is not None:
                frame_shape = proof['frame'].shape if hasattr(proof['frame'], 'shape') else "numpy_array"
                print(f"      Frame data: {frame_shape}")
        
        # Visual intelligence
        print(f"\n🎨 VISUAL INTELLIGENCE:")
        print(f"   Total Frames Analyzed: {results['visual_intelligence']['total_frames_analyzed']}")
        
        # Attire analysis
        attire = results['visual_intelligence']['attire_analysis']
        print(f"   👔 Attire Analysis: {'✅' if attire['success'] else '❌'}")
        if attire['success']:
            print(f"      Summary: {attire['summary']}")
            print(f"      Frames Analyzed: {attire['frames_analyzed']}")
        else:
            print(f"      Error: {attire['error']}")
        
        # Background analysis
        background = results['visual_intelligence']['background_analysis']
        print(f"   🏠 Background Analysis: {'✅' if background['success'] else '❌'}")
        if background['success']:
            print(f"      Summary: {background['summary']}")
            print(f"      Frames Analyzed: {background['frames_analyzed']}")
        else:
            print(f"      Error: {background['error']}")
        
        # Visual intelligence error
        if results['visual_intelligence']['error']:
            print(f"   Overall Error: {results['visual_intelligence']['error']}")
        
        # Metadata
        print(f"\n📋 ANALYSIS METADATA:")
        print(f"   Timestamp: {results['analysis_metadata']['analysis_timestamp']}")
        print(f"   Camera Method: {results['analysis_metadata']['camera_detection_method']}")
        print(f"   Visual Model: {results['analysis_metadata']['visual_analysis_model']}")
        print(f"   Sampling Strategy: {results['analysis_metadata']['sampling_strategy']}")
        print(f"   Extraction Method: {results['analysis_metadata']['extraction_method']}")
        
        # Complete structure summary
        print(f"\n🔍 COMPLETE OUTPUT STRUCTURE SUMMARY:")
        print(f"   📁 video_info: {len(results['video_info'])} fields")
        print(f"   📁 camera_analysis: {len(results['camera_analysis'])} fields")
        print(f"   📁 visual_intelligence: {len(results['visual_intelligence'])} fields")
        print(f"   📁 analysis_metadata: {len(results['analysis_metadata'])} fields")
        
        print(f"\n🎯 Final camera status: {results['camera_analysis']['status']}")
        print(f"⏱️ Video duration: {results['video_info']['duration_seconds']} seconds")
        print(f"🎵 Audio path: {results['video_info']['audio_path']}")
        print(f"👔 Attire analysis: {'✅' if results['visual_intelligence']['attire_analysis']['success'] else '❌'}")
        print(f"🏠 Background analysis: {'✅' if results['visual_intelligence']['background_analysis']['success'] else '❌'}")
        print("✅ Video analysis completed successfully!")
        print("="*60)