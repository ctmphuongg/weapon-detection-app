import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RTSP Configuration
RTSP_URL = os.getenv("RTSP_URL", "Unset")

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000

# Model Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "best.pt")

# Notification Configuration
NOTIFICATION_ENDPOINT = os.getenv("NOTIFICATION_ENDPOINT", "Unset")
NOTIFICATION_COOLDOWN = int(os.getenv("NOTIFICATION_COOLDOWN", "300"))  # 5 minutes in seconds 
TOKEN = os.getenv("TOKEN", "NOT FOUND")