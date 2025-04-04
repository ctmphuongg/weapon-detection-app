from fastapi import APIRouter, HTTPException
from stream_utils import NotificationManager
from config.settings import NOTIFICATION_ENDPOINT, NOTIFICATION_COOLDOWN

router = APIRouter()
notification_manager = NotificationManager(NOTIFICATION_ENDPOINT)

@router.post("/configure")
async def configure_notifications(
    endpoint: str,
    cooldown: int = NOTIFICATION_COOLDOWN,
    threat_categories: list = None
):
    """
    Configure notification settings.
    
    Args:
        endpoint: The notification endpoint URL
        cooldown: Cooldown period in seconds between notifications
        threat_categories: List of threat categories to notify about
        
    Returns:
        Dictionary with configuration status
    """
    try:
        notification_manager.configure(endpoint, cooldown, threat_categories)
        return {"status": "success", "message": "Notification settings updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/test")
async def test_notifications():
    """
    Test the notification system with a mock detection.
    
    Returns:
        Dictionary with test results
    """
    try:
        result = await notification_manager.send_notification(
            "test_image.jpg",
            [{"confidence": 0.95, "classification": "gun"}],
            1,
            1
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 