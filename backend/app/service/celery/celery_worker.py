from celery import Celery

# Configure Celery (Redis as broker & backend)
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",  # Broker = queue
    backend="redis://localhost:6379/1",  # Backend = results
)


@celery_app.task
def process_video(video_path: str):
    # 🔽 Place your video processing logic here
    # e.g., compress, transcode, generate transcript, etc.
    return f"Video processed: {video_path}"
