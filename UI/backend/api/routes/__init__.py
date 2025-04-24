# api/__init__.py
from stream_utils import StreamManager, NotificationManager
from config.settings import RTSP_URL, BASE_MODEL_PATH, POLICE_MODEL_PATH, WEAPON_MODEL_PATH, NOTIFICATION_ENDPOINT
from ultralytics import YOLO

# Create shared instances that will be used across the API
base_model = YOLO(BASE_MODEL_PATH)
police_model = YOLO(POLICE_MODEL_PATH)
weapon_model = YOLO(WEAPON_MODEL_PATH)
stream_manager = StreamManager(RTSP_URL, base_model=base_model, police_model=police_model, weapon_model=weapon_model)
notification_manager = NotificationManager(NOTIFICATION_ENDPOINT)