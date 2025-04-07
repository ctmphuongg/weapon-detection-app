import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RTSP Configuration
RTSP_URL = os.getenv("RTSP_URL", "rtsp://admin:HdJUwQ1E!@172.20.30.21:554/3/profile8/media.smp")

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