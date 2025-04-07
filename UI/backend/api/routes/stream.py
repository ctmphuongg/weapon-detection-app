from fastapi import APIRouter, HTTPException
from stream_utils import process_rtsp_frame, StreamManager
from ultralytics import YOLO
from config.settings import RTSP_URL, MODEL_PATH

router = APIRouter()
model = YOLO(MODEL_PATH)
stream_manager = StreamManager(RTSP_URL, model)

@router.get("/process-image")
async def process_image(interval: int = 10):
    """
    Process an image from the RTSP stream, run YOLO detection, save the image,
    and return the detection results.
    
    Args:
        interval: Interval in seconds between captures (default: 10)
        
    Returns:
        Dictionary with detection results and image path
    """
    return await process_rtsp_frame(RTSP_URL, model, interval, stream_manager)

# @router.get("/stream-status")
# async def get_stream_status():
#     """
#     Get the current status of the RTSP stream.
    
#     Returns:
#         Dictionary with stream status information
#     """
#     return {
#         "is_running": stream_manager.is_running,
#         "last_frame_time": stream_manager.last_frame_time,
#         "frame_count": stream_manager.frame_count
#     } 