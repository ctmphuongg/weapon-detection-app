from fastapi import APIRouter, HTTPException, BackgroundTasks
import numpy as np
import cv2
import base64
from datetime import datetime
import aiohttp
from api.models import NotificationConfig, NotificationPayload
from stream_utils import save_image, NotificationManager
from config.settings import NOTIFICATION_ENDPOINT, NOTIFICATION_COOLDOWN
from api.routes import stream_manager, notification_manager

router = APIRouter()

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
    
@router.post("/trigger-stream-notification")
async def trigger_stream_notification():
    """
    Trigger a notification with the current frame from the running stream
    
    Returns:
        Dictionary with the result of the notification attempt
    """
    try:
        # Check if stream is active
        if not stream_manager.active:
            raise HTTPException(status_code=400, detail="Stream is not active")
            
        # Get the latest processed frame and detections from the stream manager
        frame, detections = await stream_manager.get_latest_processed_frame()
        
        if frame is None:
            raise HTTPException(status_code=404, detail="No frames available from stream")
        
        # Check if we have valid detections, otherwise use the latest stored detections
        if not detections and stream_manager.latest_detections:
            detections = stream_manager.latest_detections
        
        # Skip sending if no detections are available
        # if not detections:
        #     return {"status": "warning", "message": "No detections available to send"}
        
        # print("Detections:", detections)
        
        # Temporarily store the frame and detections in the notification manager
        notification_manager = stream_manager.notification_manager
        notification_manager.best_image = frame.copy()
        notification_manager.best_detections = detections
        
        # Use the internal notification method
        # print("Sending notification")
        success = await notification_manager._send_notification()
        
        if success:
            return {"status": "success", "message": "Notification sent successfully"}
        else:
            return {"status": "error", "message": "Failed to send notification"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")