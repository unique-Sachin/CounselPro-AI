import cv2
import numpy as np
import tempfile
import shutil
import os
import io
import ffmpeg
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from datetime import datetime

# Define the scopes for Google Drive API access.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class VideoProcessor:
    """
    Simple video processor for analyzing counseling session videos.
    Handles Google Drive authentication, video download, and basic analysis.
    """
    
    def __init__(self):
        """Initialize the video processor"""
        pass

    # --- Google Drive API Authentication and Service Creation ---
    def get_drive_service(self):
        """
        Handles the Google Drive API authentication using service account.
        
        This function loads service account credentials from 'credentials.json'.
        Service accounts are suitable for server-to-server authentication.
        
        Returns:
            googleapiclient.discovery.Resource: An authenticated Google Drive service object.
        """
        try:
            # Load service account credentials
            if os.path.exists('credentials.json'):
                creds = service_account.Credentials.from_service_account_file(
                    'credentials.json', 
                    scopes=SCOPES
                )
                print("Successfully loaded service account credentials")
            else:
                raise FileNotFoundError("Service account key file 'credentials.json' not found")
            
            # Build the Drive service
            service = build('drive', 'v3', credentials=creds)
            print("Successfully built Google Drive service")
            return service
            
        except Exception as e:
            print(f"Error setting up Google Drive service: {e}")
            raise Exception(f"Failed to authenticate with Google Drive: {str(e)}")

    # --- Video Processing Functions ---

    def download_video_by_id(self, service, file_id, destination_path):
        """
        Downloads a video file from Google Drive using the Drive API.
        
        Args:
            service (googleapiclient.discovery.Resource): Authenticated Drive service object.
            file_id (str): The ID of the file to download.
            destination_path (str): The local path to save the downloaded video.
        
        Raises:
            Exception: If the file cannot be downloaded.
        """
        try:
            request = service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download progress: {int(status.progress() * 100)}%")

            file_content.seek(0)
            with open(destination_path, 'wb') as f:
                f.write(file_content.getvalue())
            
            print(f"File '{file_id}' downloaded successfully to '{destination_path}'.")

        except Exception as e:
            print(f"Error downloading private file: {e}")
            raise Exception(f"Failed to download private video from Google Drive: {str(e)}")


    def extract_audio(self, video_path: str, temp_dir: str):
        """
        Extracts audio from a video file using ffmpeg.
        
        This function extracts audio in WAV format (16-bit, 16kHz) which is
        optimal for Whisper models and other speech recognition systems.
        
        Args:
            video_path (str): Path to the input video file.
            temp_dir (str): Temporary directory to store the extracted audio.
            
        Returns:
            str: Path to the extracted audio file.
            
        Raises:
            Exception: If audio extraction fails.
        """
        try:
            print(f"🎵 Starting audio extraction from: {os.path.basename(video_path)}")
            
            # Generate output audio filename
            audio_filename = 'extracted_audio.wav'
            audio_path = os.path.join(temp_dir, audio_filename)
            
            print(f"🎵 Audio will be saved to: {audio_path}")
            
            # Extract audio using ffmpeg with optimal settings for Whisper
            # 16-bit, 16kHz, mono - these are the recommended settings
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, audio_path,
                                 acodec='pcm_s16le',  # 16-bit PCM
                                 ar='16000',           # 16kHz sample rate
                                 ac='1')               # mono channel
            
            print("🎵 Running ffmpeg audio extraction...")
            # Run the ffmpeg command
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            print(f"✅ Audio extracted successfully to: {audio_path}")
            return audio_path
            
        except Exception as e:
            print(f"❌ Error extracting audio: {e}")
            raise Exception(f"Failed to extract audio from video: {str(e)}")



    async def analyze_video(self, video_url: str):
        """
        Main function to analyze a private video from Google Drive.
        
        Args:
            video_url (str): The Google Drive shareable link of the video.
            
        Returns:
            dict: A dictionary with the analysis results.
        """
        print(f"🚀 Starting video analysis for URL: {video_url}")
        
        # Create a temporary directory to store the video file
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, 'input_video.mp4')
        print(f"📁 Created temporary directory: {temp_dir}")
        
        try:
            # Extract file ID from Google Drive URL
            if '/file/d/' in video_url:
                file_id = video_url.split('/file/d/')[1].split('/')[0]
            elif '/id=' in video_url:
                file_id = video_url.split('/id=')[1].split('&')[0]
            else:
                raise ValueError("Invalid Google Drive URL format")
            
            print(f"🔍 Extracted file ID: {file_id}")

            # Download the private video using authenticated API
            print("🔐 Authenticating with Google Drive...")
            service = self.get_drive_service()
            print("⬇️ Downloading video from Google Drive...")
            self.download_video_by_id(service, file_id, video_path)
            print("✅ Successfully downloaded private video using authenticated API")

            # Get video metadata using ffmpeg
            print("📊 Extracting video metadata...")
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            fps = float(video_info['r_frame_rate'].split('/')[0]) / float(video_info['r_frame_rate'].split('/')[1])
            duration = float(probe['format']['duration'])
            frame_count = int(duration * fps)
            
            print(f"📹 Video metadata: {duration:.1f}s, {fps:.1f} fps, {frame_count} frames")
            
            # Analyze camera status using ffmpeg frame extraction
            print("🎥 Starting camera status analysis...")
            camera_analysis = self.analyze_camera_status(video_path)
            
            # Check if camera analysis was successful
            if not camera_analysis.get('success', False):
                raise Exception(f"Camera analysis failed: {camera_analysis.get('error', 'Unknown error')}")
            
            print("✅ Camera analysis completed successfully")
            
            # Extract audio for Whisper processing
            print("🎵 Extracting audio from video...")
            audio_path = self.extract_audio(video_path, temp_dir)
            print(f"🎵 Audio extraction completed")
            
            # Construct the response with all camera analysis data
            print("📋 Constructing final results...")
            results = {
                "camera_status": "On" if camera_analysis['summary']['camera_on_overall'] else "Off",
                "video_duration": round(duration, 2),
                "frame_count": frame_count,
                "fps": round(fps, 2),
                "audio_path": audio_path,
                # Include all detailed camera analysis data
                "camera_analysis": camera_analysis
            }
            
            print(f"🎯 Final camera status: {results['camera_status']}")
            print(f"⏱️ Video duration: {results['video_duration']} seconds")
            print(f"🎵 Audio path: {results['audio_path']}")
            print("✅ Video analysis completed successfully!")
            
            return results
            
        except Exception as e:
            print(f"❌ An error occurred during video analysis: {e}")
            raise e
            
        finally:
            # Cleanup: remove the temporary directory and its contents
            print(f"🧹 Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("✅ Cleanup completed")


    def analyze_camera_status(self, video_path: str):
        """
        Analyzes a video to determine camera on/off status with proof generation.
        
        Enhanced version with:
        - Smart sampling (every 2 seconds instead of every frame)
        - Proof frame collection for camera OFF events
        - Timeline tracking with timestamps
        - Visual proof generation with overlays
        - Uses ffmpeg for frame extraction (memory efficient)
        
        Args:
            video_path (str): The local path to the video file.
            
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
            # Get video metadata using ffmpeg
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            fps = float(video_info['r_frame_rate'].split('/')[0]) / float(video_info['r_frame_rate'].split('/')[1])
            duration = float(probe['format']['duration'])
            total_frames = int(duration * fps)
            
            # Sampling optimization: every 2 seconds instead of every frame
            sampling_interval = int(fps * 2) if fps > 0 else 60
            
            # Analysis tracking variables
            camera_timeline = []
            proof_frames = []
            face_detected_count = 0
            total_samples = 0
            
            # Camera OFF period tracking for proof collection
            current_off_start = None
            consecutive_off_count = 0
            
            print(f"Analyzing video: {os.path.basename(video_path)}")
            print(f"Duration: {duration:.1f}s, FPS: {fps:.1f}, Sampling every {sampling_interval} frames")
            print(f"📊 Will analyze {total_frames // sampling_interval} frames (every {sampling_interval} frames)")
            
            # Process video with smart sampling using ffmpeg
            for frame_num in range(0, total_frames, sampling_interval):
                timestamp = frame_num / fps
                
                # Extract single frame using ffmpeg
                frame_data = self._extract_frame_with_ffmpeg(video_path, timestamp)
                if frame_data is None:
                    print(f"⚠️ Failed to extract frame at {timestamp:.1f}s")
                    continue
                
                total_samples += 1
                
                # Convert frame data to OpenCV format
                frame_array = np.frombuffer(frame_data, np.uint8)
                
                # Get video dimensions for proper reshaping
                probe = ffmpeg.probe(video_path)
                video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
                width = int(video_info['width'])
                height = int(video_info['height'])
                
                # Reshape the frame data to proper dimensions (BGR format)
                frame = frame_array.reshape((height, width, 3))
                
                if frame is None:
                    print(f"⚠️ Failed to decode frame at {timestamp:.1f}s (frame_data size: {len(frame_data)})")
                    continue
                
                # Check frame dimensions
                if frame.size == 0:
                    print(f"⚠️ Empty frame at {timestamp:.1f}s")
                    continue
                
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
                
                # Handle camera OFF period detection and proof collection
                if not camera_on:
                    if current_off_start is None:
                        current_off_start = timestamp
                        consecutive_off_count = 1
                        
                        # Collect first OFF proof frame
                        proof_frame = self._create_proof_frame(frame, timestamp, "CAMERA OFF - START", faces)
                        proof_frames.append({
                            'timestamp': timestamp,
                            'frame': proof_frame,
                            'status': 'camera_off_start',
                            'face_count': len(faces)
                        })
                        
                    else:
                        consecutive_off_count += 1
                        
                        # Collect additional proof frames during extended OFF period
                        if consecutive_off_count % 5 == 0:  # Every 10 seconds during OFF
                            off_duration = timestamp - current_off_start
                            proof_frame = self._create_proof_frame(
                                frame, timestamp, f"CAMERA OFF - {off_duration:.0f}s", faces
                            )
                            proof_frames.append({
                                'timestamp': timestamp,
                                'frame': proof_frame,
                                'status': 'camera_off_continued',
                                'off_duration': off_duration,
                                'face_count': len(faces)
                            })
                
                else:  # Camera is ON
                    # Check if camera just turned back ON after OFF period
                    if current_off_start is not None:
                        off_duration = timestamp - current_off_start
                        
                        # Only document significant OFF periods (6+ seconds)
                        if off_duration >= 6:
                            proof_frame = self._create_proof_frame(
                                frame, timestamp, f"CAMERA BACK ON (was off {off_duration:.0f}s)", faces
                            )
                            proof_frames.append({
                                'timestamp': timestamp,
                                'frame': proof_frame,
                                'status': 'camera_back_on',
                                'off_duration': off_duration,
                                'face_count': len(faces)
                            })
                        
                        # Reset OFF period tracking
                        current_off_start = None
                        consecutive_off_count = 0
                    
                    # Collect periodic ON samples for verification (every 5 minutes)
                    elif int(timestamp) % 300 == 0 and timestamp > 0:  # Every 5 minutes, skip t=0
                        proof_frame = self._create_proof_frame(frame, timestamp, "CAMERA ON - SAMPLE", faces)
                        proof_frames.append({
                            'timestamp': timestamp,
                            'frame': proof_frame,
                            'status': 'camera_on_sample',
                            'face_count': len(faces)
                        })
                    
                    # Also collect ON proof frames periodically (every 30 seconds) to show camera is working
                    elif int(timestamp) % 30 == 0 and timestamp > 0:  # Every 30 seconds, skip t=0
                        proof_frame = self._create_proof_frame(frame, timestamp, "CAMERA ON - VERIFICATION", faces)
                        proof_frames.append({
                            'timestamp': timestamp,
                            'frame': proof_frame,
                            'status': 'camera_on_verification',
                            'face_count': len(faces)
                        })
                
                # Collect proof frames more frequently for better coverage (every 15 seconds)
                if int(timestamp) % 15 == 0 and timestamp > 0:  # Every 15 seconds, skip t=0
                    status_text = "CAMERA ON" if camera_on else "CAMERA OFF"
                    proof_frame = self._create_proof_frame(frame, timestamp, status_text, faces)
                    proof_frames.append({
                        'timestamp': timestamp,
                        'frame': proof_frame,
                        'status': 'periodic_check',
                        'face_count': len(faces)
                    })
            
            # Calculate final statistics
            face_detection_ratio = face_detected_count / total_samples if total_samples > 0 else 0
            camera_on_overall = face_detection_ratio > 0.1
            
            # Detect significant OFF periods
            off_periods = self._detect_off_periods(camera_timeline)
            
            print(f"Analysis complete: {face_detected_count}/{total_samples} samples with faces detected")
            print(f"Face detection ratio: {face_detection_ratio:.2f}")
            print(f"Total OFF periods (6+ seconds): {len(off_periods)}")
            print(f"Proof frames collected: {len(proof_frames)}")


            return {
                'success': True,
                'video_info': {
                    'filename': os.path.basename(video_path),
                    'duration_seconds': duration,
                    'fps': fps,
                    'total_frames': total_frames,
                    'analysis_timestamp': datetime.now().isoformat()
                },
                
                'summary': {
                    'camera_on_overall': camera_on_overall,
                    'camera_on_percentage': round(face_detection_ratio * 100, 2),
                    'total_samples_analyzed': total_samples,
                    'samples_with_faces': face_detected_count,
                    'sampling_interval_seconds': sampling_interval / fps if fps > 0 else 2,
                    'significant_off_periods': len(off_periods),
                    'total_off_duration': sum(p['duration'] for p in off_periods)
                },
                
                'detailed_results': {
                    'camera_timeline': camera_timeline,
                    'off_periods': off_periods,
                    'proof_frames_count': len(proof_frames),
                    'proof_frames': proof_frames  # Contains actual image data
                },
                
                'analysis_metadata': {
                    'detection_method': 'Haar Cascade Face Detection',
                    'sampling_strategy': 'Every 2 seconds',
                    'proof_collection': 'Automated for OFF events + periodic ON samples',
                    'minimum_off_period_for_documentation': 6  # seconds
                }
            }
            
        except Exception as e:
            print(f"Error analyzing camera status: {e}")
            return {
                'error': f'Error analyzing camera status: {e}',
                'success': False
            }

    def _create_proof_frame(self, frame, timestamp, status_text, faces):
        """
        Create proof frame with timestamp, status, and face detection overlays
        
        Args:
            frame: Original video frame
            timestamp: Time in seconds from video start
            status_text: Status description to overlay
            faces: Face detection results from Haar cascade
            
        Returns:
            numpy.ndarray: Frame with proof overlays added
        """
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
        status_color = (0, 255, 0) if "ON" in status_text else (0, 0, 255)  # Green for ON, Red for OFF
        cv2.putText(proof_frame, f"Status: {status_text}", (20, 65), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Add face detection info and draw boxes
        if len(faces) > 0:
            cv2.putText(proof_frame, f"Faces detected: {len(faces)}", (20, 95), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Draw face detection rectangles
            for (x, y, w, h) in faces:
                cv2.rectangle(proof_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(proof_frame, "FACE", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            cv2.putText(proof_frame, "No faces detected", (20, 95), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add colored border for emphasis
        cv2.rectangle(proof_frame, (5, 5), (width-5, height-5), status_color, 3)
        
        return proof_frame

    def _detect_off_periods(self, camera_timeline):
        """
        Detect significant camera OFF periods from timeline
        
        Args:
            camera_timeline: List of timeline events with timestamp and camera_on status
            
        Returns:
            list: List of significant OFF periods with start, end, and duration
        """
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

    def _extract_frame_with_ffmpeg(self, video_path: str, timestamp: float):
        """
        Extract a single frame from video at specified timestamp using ffmpeg.
        
        Args:
            video_path (str): Path to the video file
            timestamp (float): Timestamp in seconds
            
        Returns:
            bytes: Frame data as bytes, or None if extraction fails
        """
        try:
            # First get video dimensions
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            width = int(video_info['width'])
            height = int(video_info['height'])
            
            # Extract frame at specific timestamp with proper format and dimensions
            frame_data, _ = (
                ffmpeg
                .input(video_path, ss=timestamp)
                .output('pipe:', format='rawvideo', pix_fmt='bgr24', vframes=1, s=f'{width}x{height}')
                .run(capture_stdout=True, quiet=True)
            )
            
            # Check if we got any data
            if not frame_data:
                print(f"⚠️ No frame data extracted at {timestamp}s")
                return None
                
            return frame_data
            
        except Exception as e:
            print(f"❌ Error extracting frame at {timestamp}s: {e}")
            return None