import os
import io
import ffmpeg
import tempfile
import numpy as np
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Configure logging
logger = logging.getLogger(__name__)

# Define the scopes for Google Drive API access.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class VideoExtractor:
    """
    Simplified video extractor with just two methods: auth and processing.
    """
    
    def __init__(self):
        """Initialize the video extractor"""
        logger.info("Initializing VideoExtractor")
        self.service = None
        self.temp_dir = tempfile.mkdtemp()
        logger.debug(f"Created temporary directory: {self.temp_dir}")
        
    def get_drive_service(self):
        """
        Handles the Google Drive API authentication using service account.
        
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
                logger.info("Successfully loaded service account credentials")
            else:
                error_msg = "Service account key file 'credentials.json' not found"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)

            # Build the Drive service
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully built Google Drive service")
            return self.service

        except Exception as e:
            logger.error(f"Error setting up Google Drive service: {e}")
            raise Exception(f"Failed to authenticate with Google Drive: {str(e)}")

    def get_video_frames_and_audio_paths(self, video_url: str):
        """
        Main processing method that downloads video once and extracts frames and audio.
        
        Args:
            video_url (str): Google Drive shareable link
            
        Returns:
            dict: {
                'frames': dict mapping timestamp to frame (numpy array),
                'audio_path': str path to extracted audio file,
                'metadata': dict with video info
            }
        """
        try:
            # Authenticate if not already done
            if not self.service:
                self.get_drive_service()
            
            # Extract file ID from URL
            if '/file/d/' in video_url:
                file_id = video_url.split('/file/d/')[1].split('/')[0]
            elif '/id=' in video_url:
                file_id = video_url.split('/id=')[1].split('&')[0]
            else:
                error_msg = "Invalid Google Drive URL format. URL must contain '/file/d/' or '/id='"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"Starting video download and processing for file ID: {file_id}")
            
            # Download video to temporary file ONCE
            temp_video = os.path.join(self.temp_dir, 'temp_video.mp4')
            
            request = self.service.files().get_media(fileId=file_id, acknowledgeAbuse=True)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
                if not done:
                    progress = int(status.progress() * 100)
                    if progress % 20 == 0:  # Log every 20% to reduce noise
                        logger.info(f"Download progress: {progress}%")

            file_content.seek(0)
            with open(temp_video, 'wb') as f:
                f.write(file_content.getvalue())

            logger.info("Video downloaded successfully, starting processing")
            
            # Get video metadata
            probe = ffmpeg.probe(temp_video)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            fps = float(video_info['r_frame_rate'].split('/')[0]) / float(video_info['r_frame_rate'].split('/')[1])
            duration = float(probe['format']['duration'])
            width = int(video_info['width'])
            height = int(video_info['height'])
            
            metadata = {
                'duration': duration,
                'fps': fps,
                'width': width,
                'height': height,
                'total_frames': int(duration * fps)
            }
            
            logger.info(f"Video metadata: {duration:.1f}s, {fps:.1f} fps, {width}x{height}")
            
            # Extract frames if timestamps provided
            frames = {}
            # Get frame sampling interval from environment or default to 2 seconds
            sampling_interval = int(os.getenv("FRAME_SAMPLING_INTERVAL", "2"))
            timestamps = list(range(0, int(duration), sampling_interval))

            if timestamps:
                logger.info(f"Extracting {len(timestamps)} frames")

                for i, timestamp in enumerate(timestamps):
                    try:
                        frame_data, _ = (
                            ffmpeg
                            .input(temp_video, ss=timestamp)
                            .output('pipe:', format='rawvideo', pix_fmt='bgr24', vframes=1, s=f'{width}x{height}')
                            .run(capture_stdout=True, quiet=True)
                        )

                        if frame_data:
                            frame_array = np.frombuffer(frame_data, np.uint8)
                            frame = frame_array.reshape((height, width, 3))
                            frames[timestamp] = frame

                            if (i + 1) % 10 == 0:
                                logger.debug(f"Extracted {i + 1}/{len(timestamps)} frames")

                    except Exception as e:
                        logger.warning(f"Failed to extract frame at {timestamp}s: {e}")
                        frames[timestamp] = None

                successful_frames = len([f for f in frames.values() if f is not None])
                logger.info(f"Frame extraction completed: {successful_frames}/{len(timestamps)} successful")
            
            # Extract audio
            logger.info("Extracting audio")
            audio_path = os.path.join(self.temp_dir, 'extracted_audio.wav')

            stream = ffmpeg.input(temp_video)
            stream = ffmpeg.output(stream, audio_path,
                                 acodec='pcm_s16le',  # 16-bit PCM
                                 ar='16000',           # 16kHz sample rate
                                 ac='1')               # mono channel

            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            logger.info(f"Audio extracted to: {audio_path}")
            
            # Clean up video file (keep audio file)
            if os.path.exists(temp_video):
                os.unlink(temp_video)
            
            return {
                'frames': frames,
                'audio_path': audio_path,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error in video processing: {e}", exc_info=True)
            raise Exception(f"Failed to process video: {str(e)}")

    def cleanup(self):
        """Clean up temporary directory and files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            logger.info(f"Cleaning up temporary directory: {self.temp_dir}")
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.temp_dir = None
                logger.info("Cleanup completed successfully")
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup()

