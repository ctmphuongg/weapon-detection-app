from fastapi import APIRouter, HTTPException, BackgroundTasks
import numpy as np
import cv2
import base64
from datetime import datetime
import aiohttp
from api.models import NotificationConfig, NotificationPayload
from stream_utils import save_image, NotificationManager
from config.settings import NOTIFICATION_ENDPOINT, NOTIFICATION_COOLDOWN
from api.routes.stream import stream_manager

router = APIRouter()
notification_manager = NotificationManager(NOTIFICATION_ENDPOINT)

@router.post("/configure")
async def configure_notifications(
    config: NotificationConfig
):
    """
    Configure the notification settings
    
    Args:
        config: The notification configuration
        
    Returns:
        Dictionary with the updated configuration
    """
    try:
        # Update the notification manager with the new configuration
        stream_manager.notification_manager.confidence_threshold = config.confidence_threshold
        stream_manager.notification_manager.cooldown_period = config.cooldown_period
        stream_manager.notification_manager.confidence_increase_threshold = config.confidence_increase_threshold
        stream_manager.notification_manager.best_image_window = config.best_image_window
        stream_manager.notification_manager.api_endpoint = config.api_endpoint
        
        return {
            "status": "success",
            "message": "Notification settings updated",
            "config": {
                "confidence_threshold": config.confidence_threshold,
                "cooldown_period": config.cooldown_period,
                "confidence_increase_threshold": config.confidence_increase_threshold,
                "best_image_window": config.best_image_window,
                "api_endpoint": config.api_endpoint
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/config")
async def get_notification_config():
    """
    Get the current notification settings
    
    Returns:
        Dictionary with the current configuration
    """
    return {
        "confidence_threshold": stream_manager.notification_manager.confidence_threshold,
        "cooldown_period": stream_manager.notification_manager.cooldown_period,
        "confidence_increase_threshold": stream_manager.notification_manager.confidence_increase_threshold,
        "best_image_window": stream_manager.notification_manager.best_image_window,
        "api_endpoint": stream_manager.notification_manager.api_endpoint
    }

@router.post("/trigger")
async def trigger_notification(payload: NotificationPayload):
    """
    Manually trigger a notification with the provided payload
    
    Args:
        payload: The notification payload
        
    Returns:
        Dictionary with the result
    """
    try:
        # Send the notification
        async with aiohttp.ClientSession() as session:
            async with session.post(
                stream_manager.notification_manager.api_endpoint, 
                json=payload.dict()
            ) as response:
                if response.status == 200:
                    return {"status": "success", "message": "Notification sent successfully"}
                else:
                    return {"status": "error", "message": f"Failed to send notification: {response.status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")

@router.post("/mock-notification")
async def mock_notification(payload: NotificationPayload):
    try:
        # Decode the base64 image
        image_bytes = base64.b64decode(payload.picture)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Save the image with detection information
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mock_notification_{timestamp}.jpg"
        image_path = save_image(image, filename)
        
        # Log the detection information
        print(f"Mock notification received:")
        print(f"Image saved at: {image_path}")
        print(f"Detections: {payload.detection_event}")
        print(f"Location ID: {payload.location_id}")
        print(f"Camera ID: {payload.camera_id}")
        print(f"Timestamp: {payload.timestamp}")
        
        return {
            "status": "success",
            "message": "Mock notification processed successfully",
            "image_path": image_path,
            "detections": payload.detection_event
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing mock notification: {str(e)}")