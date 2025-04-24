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
BASE_MODEL_PATH = os.getenv("BASE_MODEL_PATH", "yolo11n.pt")
POLICE_MODEL_PATH = os.getenv("POLICE_MODEL_PATH", "police.pt")
WEAPON_MODEL_PATH = os.getenv("WEAPON_MODEL_PATH", "weapon.pt")

# Notification Configuration
NOTIFICATION_ENDPOINT = os.getenv("NOTIFICATION_ENDPOINT", "Unset")
NOTIFICATION_COOLDOWN = int(os.getenv("NOTIFICATION_COOLDOWN", "300"))  # 5 minutes in seconds 
TOKEN = os.getenv("TOKEN", "NOT FOUND")