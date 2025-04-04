import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RTSP Configuration
RTSP_URL = os.getenv("RTSP_URL", "rtsp://admin:admin@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0")

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000

# API Configuration
API_PREFIX = "/api/v1"

# Model Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "best.pt")

# Notification Configuration
NOTIFICATION_ENDPOINT = os.getenv("NOTIFICATION_ENDPOINT", "http://localhost:8000/api/notifications")
NOTIFICATION_COOLDOWN = int(os.getenv("NOTIFICATION_COOLDOWN", "300"))  # 5 minutes in seconds 