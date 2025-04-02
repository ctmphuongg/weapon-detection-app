# import the necessary packages
from imutils.video import VideoStream
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import asyncio
import imutils
import time
import cv2
import uvicorn
from multiprocessing import Process, Queue
import subprocess
import numpy as np
import os
from ultralytics import YOLO
from yolo_process import process_frame_with_yolo
from stream_manager import StreamManager
from save_image import process_rtsp_frame

# To think about: How to avoid 3s delay at the beginning when restart client
HTTP_PORT = 6064
lock = threading.Lock()
app = FastAPI()
width = 1280
height = 720
load_dotenv()
url_rtsp = os.getenv("RTSP_URL")
model = YOLO("best.pt")

# Single shared stream manager instance
stream_manager = StreamManager(url_rtsp, model)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def frame_generator():
    try:
        while stream_manager.active:
            try:
                # Use wait_for with timeout to make this cancellable
                encoded_image = await asyncio.wait_for(
                    stream_manager.frame_queue.get(), 
                    timeout=5.0
                )
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                       bytearray(encoded_image) + b'\r\n')
            except asyncio.TimeoutError:
                # No frames available, but stream might still be active
                if stream_manager.active:
                    continue
                break
    except asyncio.CancelledError:
        # Handle client disconnection gracefully
        print("Stream cancelled")
        raise

@app.get("/")
async def video_feed():
    await stream_manager.start_stream()
    return StreamingResponse(
        frame_generator(), 
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

@app.get("/keep-alive")
async def keep_alive(background_tasks: BackgroundTasks):
    stream_manager.keep_alive_counter = 100
    await stream_manager.start_stream()
    return {"status": "ok"}

# Get the list of classes that the model can detect
@app.get("/model-info")
def model_info():
    return {"classes": model.names}

# New endpoint to get latest detections
@app.get("/latest-detections")
async def latest_detections():
    return {"detections": stream_manager.latest_detections}

# New endpoint to process images at intervals and save them
@app.get("/process-image")
async def process_image(interval: int = 10):
    """
    Process an image from the RTSP stream, run YOLO detection, save the image,
    and return the detection results.
    
    Args:
        interval: Interval in seconds between captures (default: 10)
        
    Returns:
        Dictionary with detection results and image path
    """
    return await process_rtsp_frame(url_rtsp, model, interval)

# Shutdown hook
@app.on_event("shutdown")
async def shutdown_event():
    stream_manager.active = False
    if stream_manager.stream_task:
        stream_manager.stream_task.cancel()

# check to see if this is the main thread of execution
if __name__ == '__main__':
    # start app
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT, access_log=False)