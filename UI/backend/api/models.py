from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DetectionEvent(BaseModel):
    confidence: float
    classification: str

class NotificationPayload(BaseModel):
    picture: str  # Base64 encoded image
    detection_event: List[DetectionEvent]
    location_id: int = 1
    camera_id: int = 1
    timestamp: str = datetime.now().isoformat()

class NotificationConfig(BaseModel):
    confidence_threshold: float = 0.60
    cooldown_period: int = 300  # 5 minutes in seconds
    confidence_increase_threshold: float = 0.10
    best_image_window: int = 3  # 3 seconds window
    api_endpoint: str = "http://localhost:8000/api/notifications" 