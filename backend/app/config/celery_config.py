from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/")


celery_app = Celery(
    "counselpro",
    broker="{REDIS_URL}0",
    backend="{REDIS_URL}1",
    include=[
        "app.tasks.video_processing",
        "app.tasks.audio_processing",
        "app.tasks.analysis",
    ],
)

# Configure Celery settings
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)
