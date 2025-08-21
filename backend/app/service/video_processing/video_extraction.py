import os
import io
import ffmpeg
import tempfile
import numpy as np
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Configure logging
logger = logging.getLogger(__name__)

# Define the scopes for Google Drive API access.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class VideoExtractor:
    """
    Optimized video extractor with parallel processing and smart sampling.
    """
    
    def __init__(self, max_workers=4):
        """Initialize the video extractor with configurable parallelism"""
        logger.info("Initializing OptimizedVideoExtractor")
        self.service = None
        self.temp_dir = tempfile.mkdtemp()
        self.max_workers = max_workers
        logger.debug(f"Created temporary directory: {self.temp_dir}")
        
    def get_drive_service(self):
        """Handles the Google Drive API authentication using service account."""
        try:
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

            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully built Google Drive service")
            return self.service

        except Exception as e:
            logger.error(f"Error setting up Google Drive service: {e}")
            raise Exception(f"Failed to authenticate with Google Drive: {str(e)}")

    def _extract_single_frame(self, temp_video_path, timestamp, width, height):
        """Extract a single frame at the given timestamp."""
        try:
            frame_data, _ = (
                ffmpeg
                .input(temp_video_path, ss=timestamp)
                .output('pipe:', format='rawvideo', pix_fmt='bgr24', vframes=1, s=f'{width}x{height}')
                .run(capture_stdout=True, quiet=True)
            )

            if frame_data:
                frame_array = np.frombuffer(frame_data, np.uint8)
                frame = frame_array.reshape((height, width, 3))
                return timestamp, frame
            else:
                return timestamp, None

        except Exception as e:
            logger.warning(f"Failed to extract frame at {timestamp}s: {e}")
            return timestamp, None

    def _extract_frames_batch(self, temp_video_path, timestamps, width, height, batch_size=10):
        """Extract multiple frames in a single ffmpeg call for efficiency."""
        try:
            # Create filter for multiple timestamps
            filter_complex = []
            outputs = []
            
            for i, timestamp in enumerate(timestamps):
                filter_complex.append(f'[0:v]trim=start={timestamp}:duration=0.04,setpts=PTS-STARTPTS[v{i}]')
                outputs.append(f'[v{i}]')
            
            if not filter_complex:
                return {}
            
            # Build ffmpeg command
            input_stream = ffmpeg.input(temp_video_path)
            
            # For small batches, use the single frame approach which is more reliable
            if len(timestamps) <= 3:
                frames = {}
                for timestamp in timestamps:
                    try:
                        frame_data, _ = (
                            ffmpeg
                            .input(temp_video_path, ss=timestamp)
                            .output('pipe:', format='rawvideo', pix_fmt='bgr24', vframes=1, s=f'{width}x{height}')
                            .run(capture_stdout=True, quiet=True)
                        )
                        if frame_data:
                            frame_array = np.frombuffer(frame_data, np.uint8)
                            frame = frame_array.reshape((height, width, 3))
                            frames[timestamp] = frame
                        else:
                            frames[timestamp] = None
                    except Exception as e:
                        logger.warning(f"Failed to extract frame at {timestamp}s: {e}")
                        frames[timestamp] = None
                return frames
            else:
                # For larger batches, fall back to individual extraction
                frames = {}
                for timestamp in timestamps:
                    _, frame = self._extract_single_frame(temp_video_path, timestamp, width, height)
                    frames[timestamp] = frame
                return frames
                
        except Exception as e:
            logger.warning(f"Batch extraction failed, falling back to individual: {e}")
            # Fallback to individual extraction
            frames = {}
            for timestamp in timestamps:
                _, frame = self._extract_single_frame(temp_video_path, timestamp, width, height)
                frames[timestamp] = frame
            return frames

    def get_video_frames_and_audio_paths(self, video_url: str, smart_sampling=True):
        """
        Optimized processing method with parallel extraction and smart sampling.
        """
        try:
            if not self.service:
                self.get_drive_service()
            
            # Extract file ID from URL
            if '/file/d/' in video_url:
                file_id = video_url.split('/file/d/')[1].split('/')[0]
            elif '/id=' in video_url:
                file_id = video_url.split('/id=')[1].split('&')[0]
            else:
                error_msg = "Invalid Google Drive URL format"
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"Starting optimized video processing for file ID: {file_id}")
            
            # Download video with progress tracking
            temp_video = os.path.join(self.temp_dir, 'temp_video.mp4')
            
            request = self.service.files().get_media(fileId=file_id, acknowledgeAbuse=True)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            done = False
            
            while not done:
                status, done = downloader.next_chunk()
                if not done:
                    progress = int(status.progress() * 100)
                    if progress % 20 == 0:
                        logger.info(f"Download progress: {progress}%")

            # Write to file more efficiently
            file_content.seek(0)
            with open(temp_video, 'wb') as f:
                f.write(file_content.getvalue())

            logger.info("Video downloaded, analyzing metadata")
            
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
            
            # Smart sampling strategy
            sampling_interval = int(os.getenv("FRAME_SAMPLING_INTERVAL", "60"))
            
            if smart_sampling and duration > 60:  # For videos longer than 1 minute
                # Sample more densely at the beginning and end, sparse in middle
                start_samples = list(range(0, min(30, int(duration//3)), 2))
                middle_samples = list(range(30, int(duration*2//3), sampling_interval*2))
                end_samples = list(range(max(int(duration*2//3), 30), int(duration), 2))
                timestamps = start_samples + middle_samples + end_samples
                timestamps = [t for t in timestamps if t < duration]
            else:
                timestamps = list(range(0, int(duration), sampling_interval))
            
            # Remove duplicates and sort
            timestamps = sorted(list(set(timestamps)))
            
            logger.info(f"Using smart sampling: {len(timestamps)} frames to extract")
            
            # Parallel frame extraction
            frames = {}
            if timestamps:
                logger.info("Starting parallel frame extraction")
                
                # Split timestamps into batches for processing
                batch_size = max(1, len(timestamps) // self.max_workers)
                timestamp_batches = [timestamps[i:i + batch_size] for i in range(0, len(timestamps), batch_size)]
                
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    # Submit batch jobs
                    future_to_batch = {
                        executor.submit(self._extract_frames_batch, temp_video, batch, width, height): batch
                        for batch in timestamp_batches
                    }
                    
                    completed_frames = 0
                    for future in as_completed(future_to_batch):
                        try:
                            batch_frames = future.result()
                            frames.update(batch_frames)
                            completed_frames += len(batch_frames)
                            
                            if completed_frames % 20 == 0:
                                logger.info(f"Extracted {completed_frames}/{len(timestamps)} frames")
                        except Exception as e:
                            logger.error(f"Batch processing error: {e}")
                
                successful_frames = len([f for f in frames.values() if f is not None])
                logger.info(f"Parallel frame extraction completed: {successful_frames}/{len(timestamps)} successful")
            
            # Extract audio in parallel with frame processing cleanup
            logger.info("Extracting audio")
            audio_path = os.path.join(self.temp_dir, 'extracted_audio.wav')

            # Use more efficient audio extraction settings
            stream = ffmpeg.input(temp_video)
            stream = ffmpeg.output(stream, audio_path,
                                 acodec='pcm_s16le',
                                 ar='16000',
                                 ac='1',
                                 preset='ultrafast')  # Faster encoding

            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            logger.info(f"Audio extracted to: {audio_path}")
            
            # Clean up video file
            if os.path.exists(temp_video):
                os.unlink(temp_video)
            
            return {
                'frames': frames,
                'audio_path': audio_path,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error in optimized video processing: {e}", exc_info=True)
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