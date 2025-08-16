import cv2
import numpy as np
import tempfile
import shutil
import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

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



    def analyze_camera_status(self, video_path: str):
        """
        Analyzes a video to determine if a person's camera is on or off.
        
        This function checks for the presence of a face in the video frames.
        It returns a boolean indicating if a face was detected for a significant
        portion of the video.
        
        Args:
            video_path (str): The local path to the video file.
            
        Returns:
            bool: True if a face is detected (camera is on), False otherwise.
        """
        # Load the pre-trained Haar Cascade for face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        if face_cascade.empty():
            print("Error loading face cascade XML file.")
            return False
            
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error opening video file at {video_path}")
            return False

        frame_count = 0
        face_detected_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            faces = face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                face_detected_frames += 1
                
        cap.release()

        face_detection_ratio = face_detected_frames / frame_count if frame_count > 0 else 0
        print(f"Face detected in {face_detected_frames}/{frame_count} frames. Ratio: {face_detection_ratio:.2f}")

        return face_detection_ratio > 0.1

    def analyze_attire(self, frame):
        """
        (Placeholder) Analyzes attire for professionalism.
        
        This is a placeholder that you would replace with a pre-trained model
        for clothing classification.
        
        Args:
            frame (np.ndarray): The video frame to analyze.
            
        Returns:
            str: A string indicating the attire status.
        """
        return "Professional"



    async def analyze_video(self, video_url: str):
        """
        Main function to analyze a private video from Google Drive.
        
        Args:
            video_url (str): The Google Drive shareable link of the video.
            
        Returns:
            dict: A dictionary with the analysis results.
        """
        # Create a temporary directory to store the video file
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, 'input_video.mp4')
        
        try:
            # Extract file ID from Google Drive URL
            if '/file/d/' in video_url:
                file_id = video_url.split('/file/d/')[1].split('/')[0]
            elif '/id=' in video_url:
                file_id = video_url.split('/id=')[1].split('&')[0]
            else:
                raise ValueError("Invalid Google Drive URL format")

            # Download the private video using authenticated API
            service = self.get_drive_service()
            self.download_video_by_id(service, file_id, video_path)
            print("Successfully downloaded private video using authenticated API")

            # Perform the analysis
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Failed to open video file for analysis")
                
            ret, first_frame = cap.read()
            cap.release()
            
            if not ret:
                raise Exception("Failed to read video frames")
            
            # Analyze camera status
            camera_on = self.analyze_camera_status(video_path)
            
            # Analyze attire if camera is on
            if camera_on:
                attire_status = self.analyze_attire(first_frame)
            else:
                attire_status = "Not applicable (camera off)"
            
            # Get video metadata
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
            
            # Construct the response
            results = {
                "camera_status": "On" if camera_on else "Off",
                "attire_status": attire_status,
                "video_duration": round(duration, 2),
                "frame_count": frame_count,
                "fps": round(fps, 2)
            }
            
            return results
            
        except Exception as e:
            print(f"An error occurred: {e}")
            raise e
            
        finally:
            # Cleanup: remove the temporary directory and its contents
            shutil.rmtree(temp_dir, ignore_errors=True)

