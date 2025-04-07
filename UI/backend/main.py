# # import the necessary packages
# from imutils.video import VideoStream
# from dotenv import load_dotenv
# from fastapi import FastAPI, BackgroundTasks, HTTPException
# from fastapi.responses import StreamingResponse
# from fastapi.middleware.cors import CORSMiddleware
# import threading
# import asyncio
# import imutils
# import time
# import cv2
# import uvicorn
# from multiprocessing import Process, Queue
# import subprocess
# import numpy as np
# import os
# from ultralytics import YOLO
# from stream_utils import (
#     process_frame_with_yolo,
#     StreamManager,
#     process_rtsp_frame,
#     save_image
# )
# from pydantic import BaseModel
# from typing import List, Dict, Any, Optional
# import aiohttp
# import base64
# from datetime import datetime
# from config.settings import API_HOST, API_PORT, RTSP_URL
# import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from api.routes import notifications, stream, video
from config.settings import API_HOST, API_PORT


# Disable YOLO inference logs
logging.getLogger('ultralytics').setLevel(logging.WARNING)

# Initialize FastAPI app
app = FastAPI(title="Weapon Detection API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model and stream manager
# model = YOLO("best.pt")
# stream_manager = StreamManager(RTSP_URL, model)

# Include routers
app.include_router(video.router, prefix="/video", tags=["Video Processing"])
app.include_router(stream.router, prefix="/stream", tags=["Stream Management"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

# Pydantic models for API requests
# class NotificationConfig(BaseModel):
#     confidence_threshold: float = 0.60
#     cooldown_period: int = 300  # 5 minutes in seconds
#     confidence_increase_threshold: float = 0.10
#     best_image_window: int = 3  # 3 seconds window
#     api_endpoint: str = os.getenv("NOTIFICATION_API_ENDPOINT", "http://localhost:8000/api/notifications")

# class DetectionEvent(BaseModel):
#     confidence: float
#     classification: str

# class NotificationPayload(BaseModel):
#     picture: str  # Base64 encoded image
#     detection_event: List[DetectionEvent]
#     location_id: int = 1
#     camera_id: int = 1
#     timestamp: str

# Mock notification endpoint for testing
# @app.post("/mock-notification")
# async def mock_notification(payload: NotificationPayload):
#     try:
#         # Decode the base64 image
#         image_bytes = base64.b64decode(payload.picture)
#         nparr = np.frombuffer(image_bytes, np.uint8)
#         image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
#         # Save the image with detection information
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"mock_notification_{timestamp}.jpg"
#         image_path = save_image(image, filename)
        
#         # Log the detection information
#         print(f"Mock notification received:")
#         print(f"Image saved at: {image_path}")
#         print(f"Detections: {payload.detection_event}")
#         print(f"Location ID: {payload.location_id}")
#         print(f"Camera ID: {payload.camera_id}")
#         print(f"Timestamp: {payload.timestamp}")
        
#         return {
#             "status": "success",
#             "message": "Mock notification processed successfully",
#             "image_path": image_path,
#             "detections": payload.detection_event
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing mock notification: {str(e)}")

# async def frame_generator():
#     try:
#         while stream_manager.active:
#             try:
#                 # Use wait_for with timeout to make this cancellable
#                 encoded_image = await asyncio.wait_for(
#                     stream_manager.frame_queue.get(), 
#                     timeout=5.0
#                 )
#                 yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
#                        bytearray(encoded_image) + b'\r\n')
#             except asyncio.TimeoutError:
#                 # No frames available, but stream might still be active
#                 if stream_manager.active:
#                     continue
#                 break
#     except asyncio.CancelledError:
#         # Handle client disconnection gracefully
#         print("Stream cancelled")
#         raise

# @app.get("/")
# async def video_feed():
#     await stream_manager.start_stream()
#     return StreamingResponse(
#         frame_generator(), 
#         media_type="multipart/x-mixed-replace;boundary=frame"
#     )

# @app.get("/keep-alive")
# async def keep_alive(background_tasks: BackgroundTasks):
#     stream_manager.keep_alive_counter = 100
#     await stream_manager.start_stream()
#     return {"status": "ok"}

# Get the list of classes that the model can detect
# @app.get("/model-info")
# def model_info():
#     return {"classes": model.names}

# # New endpoint to get latest detections
# @app.get("/latest-detections")
# async def latest_detections():
#     return {"detections": stream_manager.latest_detections}

# # New endpoint to process images at intervals and save them
# @app.get("/process-image")
# async def process_image(interval: int = 10):
#     """
#     Process an image from the RTSP stream, run YOLO detection, save the image,
#     and return the detection results.
    
#     Args:
#         interval: Interval in seconds between captures (default: 10)
        
#     Returns:
#         Dictionary with detection results and image path
#     """
#     return await process_rtsp_frame(RTSP_URL, model, interval, stream_manager)

# # New endpoint to configure notification settings
# @app.post("/notification-config")
# async def configure_notifications(config: NotificationConfig):
#     """
#     Configure the notification settings
    
#     Args:
#         config: The notification configuration
        
#     Returns:
#         Dictionary with the updated configuration
#     """
#     # Update the notification manager with the new configuration
#     stream_manager.notification_manager.confidence_threshold = config.confidence_threshold
#     stream_manager.notification_manager.cooldown_period = config.cooldown_period
#     stream_manager.notification_manager.confidence_increase_threshold = config.confidence_increase_threshold
#     stream_manager.notification_manager.best_image_window = config.best_image_window
#     stream_manager.notification_manager.api_endpoint = config.api_endpoint
    
#     return {
#         "status": "success",
#         "message": "Notification settings updated",
#         "config": {
#             "confidence_threshold": config.confidence_threshold,
#             "cooldown_period": config.cooldown_period,
#             "confidence_increase_threshold": config.confidence_increase_threshold,
#             "best_image_window": config.best_image_window,
#             "api_endpoint": config.api_endpoint
#         }
#     }

# # New endpoint to get current notification settings
# @app.get("/notification-config")
# async def get_notification_config():
#     """
#     Get the current notification settings
    
#     Returns:
#         Dictionary with the current configuration
#     """
#     return {
#         "confidence_threshold": stream_manager.notification_manager.confidence_threshold,
#         "cooldown_period": stream_manager.notification_manager.cooldown_period,
#         "confidence_increase_threshold": stream_manager.notification_manager.confidence_increase_threshold,
#         "best_image_window": stream_manager.notification_manager.best_image_window,
#         "api_endpoint": stream_manager.notification_manager.api_endpoint
#     }

# # New endpoint to manually trigger a notification
# @app.post("/trigger-notification")
# async def trigger_notification(payload: NotificationPayload):
#     """
#     Manually trigger a notification with the provided payload
    
#     Args:
#         payload: The notification payload
        
#     Returns:
#         Dictionary with the result
#     """
#     try:
#         # Send the notification
#         async with aiohttp.ClientSession() as session:
#             async with session.post(
#                 stream_manager.notification_manager.api_endpoint, 
#                 json=payload.dict()
#             ) as response:
#                 if response.status == 200:
#                     return {"status": "success", "message": "Notification sent successfully"}
#                 else:
#                     return {"status": "error", "message": f"Failed to send notification: {response.status}"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")

# Startup event handler
# @app.on_event("startup")
# async def startup_event():
#     """
#     Start the stream automatically when the server starts
#     """
#     print("Starting stream on server startup...")
#     await stream_manager.start_stream()
#     # Set a high keep-alive counter to keep the stream running
#     stream_manager.keep_alive_counter = 1000000  # A very large number

# # Shutdown event handler
# @app.on_event("shutdown")
# async def shutdown_event():
#     stream_manager.active = False
#     if stream_manager.stream_task:
#         stream_manager.stream_task.cancel()
# Root endpoint for model information

@app.get("/model-info")
def model_info():
    return {"classes": video.model.names}

# Latest detections endpoint
@app.get("/latest-detections")
async def latest_detections():
    return {"detections": stream.stream_manager.latest_detections}

# Startup event handler
@app.on_event("startup")
async def startup_event():
    """
    Start the stream automatically when the server starts
    """
    print("Starting stream on server startup...")
    await stream.stream_manager.start_stream()
    # Set a high keep-alive counter to keep the stream running
    stream.stream_manager.keep_alive_counter = 1000000  # A very large number

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    stream.stream_manager.active = False
    if stream.stream_manager.stream_task:
        stream.stream_manager.stream_task.cancel()

if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)