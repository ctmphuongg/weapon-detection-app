# api/__init__.py
from stream_utils import StreamManager, NotificationManager
from config.settings import RTSP_URL, MODEL_PATH, NOTIFICATION_ENDPOINT
from ultralytics import YOLO

# Create shared instances that will be used across the API
model = YOLO(MODEL_PATH)
stream_manager = StreamManager(RTSP_URL, model)
notification_manager = NotificationManager(NOTIFICATION_ENDPOINT)