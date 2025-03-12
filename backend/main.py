# import the necessary packages
from imutils.video import VideoStream
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import imutils
import time
import cv2
import uvicorn
from multiprocessing import Process, Queue
import subprocess
import numpy as np
import os
from ultralytics import YOLO

HTTP_PORT = 6064
lock = threading.Lock()
app = FastAPI()
manager = None
count_keep_alive = 0
width = 1280
height = 720
load_dotenv()
url_rtsp = os.getenv("RTSP_URL")
model = YOLO("yolo11n.pt")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_frame_with_yolo(frame):
    """Apply YOLO detection to a frame and return the annotated frame"""
    if frame is None:
        return None
    
    # Run inference on the frame
    results = model(frame)
    
    # Process each detection
    for result in results:
        boxes = result.boxes
        
        # Draw each bounding box
        for box in boxes:
            # Get box coordinates
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Get class name and confidence
            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            conf = float(box.conf[0])
            
            # Generate color for class
            color = (hash(class_name) % 256, hash(class_name * 2) % 256, hash(class_name * 3) % 256)
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Add label with class name and confidence
            label = f"{class_name}: {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return frame

def start_stream(url_rtsp, manager):
    global width
    global height

    vs = VideoStream(url_rtsp).start()
    while True:
        time.sleep(0.2)

        frame = vs.read()
        frame = imutils.resize(frame, width=680)
        output_frame = process_frame_with_yolo(frame.copy())

        if output_frame is None:
            continue
        
        (flag, encodedImage) = cv2.imencode(".jpg", output_frame)
        if not flag:
            continue
        
        manager.put(encodedImage)


def streamer():
    try:
        while manager:
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                   bytearray(manager.get()) + b'\r\n')
    except GeneratorExit:
        print("cancelled")


def manager_keep_alive(p):
    global count_keep_alive
    global manager
    while count_keep_alive:
        time.sleep(1)
        print(count_keep_alive)
        count_keep_alive -= 1
    p.kill()
    time.sleep(.5)
    p.close()
    manager.close()
    manager = None

@app.get("/")
async def video_feed():
    return StreamingResponse(streamer(), media_type="multipart/x-mixed-replace;boundary=frame")


@app.get("/keep-alive")
def keep_alive():
    global manager
    global count_keep_alive
    count_keep_alive = 100
    if not manager:
        manager = Queue()
        p = Process(target=start_stream, args=(url_rtsp, manager,))
        p.start()
        threading.Thread(target=manager_keep_alive, args=(p,)).start()

# Get the list of classes that the model can detect
@app.get("/model-info")
def model_info():
    return {"classes": model.names}

# check to see if this is the main thread of execution
if __name__ == '__main__':
    # start app
    uvicorn.run(app, host="0.0.0.0", port=HTTP_PORT, access_log=False)