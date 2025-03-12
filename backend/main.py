import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, Response, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import threading
import os
from typing import AsyncGenerator, Optional, Union, List, Dict, Any
from contextlib import asynccontextmanager
import uvicorn
import numpy as np
import time
from ultralytics import YOLO

load_dotenv()
rtsp_url = os.getenv("RTSP_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  Lifespan context manager for startup and shutdown events.
  """
  global camera
  global detector
  camera = Camera(rtsp_url)
  detector = YOLODetector(model_path='yolo11n.pt', conf_threshold=0.25)
  try: 
    yield
  except asyncio.exceptions.CancelledError as error:
    print(error.args)
  finally:
    camera.release()
    print("Camera resource released.")

app = FastAPI(lifespan = lifespan)

# Add CORS middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. In production, specify your React app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class YOLODetector:
  """
  A class to handle YOLO object detection using ultralytics.
  """
  def __init__(self, model_path: str, conf_threshold: float=0.25):
    """
    Initialize the YOLO detector.
        
    :param model_path: Path to the YOLO model weights
    :param conf_threshold: Confidence threshold for detections
    """
    self.conf_threshold = conf_threshold
    self.lock = threading.Lock()
        
    # Load YOLO model using ultralytics
    with self.lock:
      self.model = YOLO(model_path)
      
  def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
    """
    Perform object detection on a frame.
    
    :param frame: Input image frame
    :return: List of detection results containing bounding boxes, class names, and confidence scores
    """
    with self.lock:
      # Run inference with the specified confidence threshold
      results = self.model(frame, conf=self.conf_threshold)
      
      # Process results
      detections = []
      for result in results:
        boxes = result.boxes
        
        for box in boxes:
          # Get box coordinates
          x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
          
          # Get class name and confidence
          class_id = int(box.cls[0])
          class_name = result.names[class_id]
          conf = float(box.conf[0])
          
          detections.append({
            'bbox': [float(x1), float(y1), float(x2), float(y2)],
            'class': class_name,
            'confidence': conf
          })
    
      return detections
    
  def visualize(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
    """
    Draw bounding boxes and labels on the frame.
    
    :param frame: Input frame
    :param detections: Detection results
    :return: Frame with visualizations
    """
    vis_frame = frame.copy()
    
    for det in detections:
      x1, y1, x2, y2 = map(int, det['bbox'])
      class_name = det['class']
      conf = det['confidence']
      
      # Generate color based on class name (same as your original code)
      color = (hash(class_name) % 256, hash(class_name * 2) % 256, hash(class_name * 3) % 256)
      
      # Draw bounding box
      cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 2)
      
      # Add label with class name and confidence
      label = f"{class_name}: {conf:.2f}"
      cv2.putText(vis_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return vis_frame


class Camera:
  """
  A class to handle video capture from a camera.
  """
  def __init__(self, url: Optional[Union[str, int]] = 0) -> None:
    """
    Initialize the camera
    """
    self.cap = cv2.VideoCapture(url)
    self.lock = threading.Lock()
    
    # Frame caching to avoid duplicates
    self.last_frame = None
    self.last_frame_time = 0
    self.frame_cache_duration = 0.03 #~30fps
    
    # Detection results cache
    self.last_detections = []
    self.detection_cache_duration = 0.1 # Process detections at 10fps to reduce CPU load
    self.last_detection_time = 0
    
  def get_frame(self, apply_detection=True) -> tuple:
    """
    Capture a frame from the camera.
    
    :return: JPEG encoded image bytes
    """
    current_time = time.time()
    detections = []
    
    with self.lock:
      if self.last_frame is None or (current_time - self.last_frame_time) > self.frame_cache_duration:
        ret, frame = self.cap.read()
        if not ret:
          return b'', None, []
        
        self.last_frame = frame
        self.last_frame_time = current_time
      else:
        frame = self.last_frame.copy()
      
      if apply_detection:
        if (current_time - self.last_detection_time) > self.detection_cache_duration:
          self.last_detections = detector.detect(frame)
          self.last_detection_time = current_time
        
        detections = self.last_detections
      
      # Apply visualization with bounding boxes
      if apply_detection:
        frame = detector.visualize(frame, detections)
      
      # Encode the frame to JPEG
      ret, jpeg = cv2.imencode('.jpg', frame)
      if not ret:
          return b'', None, []
          
      return jpeg.tobytes(), frame, detections

    
  def release(self) -> None:
    """
    Release the camera resource.
    """
    with self.lock:
      if self.cap.isOpened():
        self.cap.release()
        
        
async def gen_frames(detection=False) -> AsyncGenerator[bytes, None]:
  """
  An asynchronous generator function that yields camera frames.
  
  :yield: JPEG encoded image bytes
  """
  # try:
  #   while True:
  #     frame, _, _ = camera.get_frame(apply_detection=detection)
  #     if frame:
  #       yield (b'--frame\r\n'
  #             b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
  #     else:
  #       break
  #     await asyncio.sleep(0)
  # except (asyncio.CancelledError, GeneratorExit):
  #   print("Frame generation cancelled.")
  # finally:
  #   print("Frame generator exited.")
  try:
      while True:
          frame, _, _ = camera.get_frame(apply_detection=detection)
          if frame:
              yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
          else:
              # If no frame, wait a bit and try again instead of breaking
              await asyncio.sleep(0.1)
              continue
              
          # Make sure to yield control back to the event loop
          await asyncio.sleep(0.03)  # ~30fps, but adjust as needed
  except (asyncio.CancelledError, GeneratorExit):
      print("Frame generation cancelled.")
  finally:
      print("Frame generator exited.")

@app.get("/video")
async def video_feed(detection: bool = Query(False)) -> StreamingResponse:
  """
  Video streaming route
  
  :return: StreamingResponse with multipart JPEG frames.
  """
  return StreamingResponse(
    gen_frames(detection=detection),
    media_type='multipart/x-mixed-replaced; boundary=frame'
  )
  

@app.get("/snapshot")
async def snapshot(detection: bool = Query(False)) -> Response:
  """
  Snapshot route to get a single frame
  
  :return: Response with JPEG image.
  """
  frame, _, _ = camera.get_frame(apply_detection=False)
  if frame:
    return Response(content=frame, media_type="image/jpeg")
  else:
    return Response(status_code=404, content="Camera frame not available.")
  
@app.get("/detections")
async def get_detections() -> Dict:
  """
  Get the latest detection results as JSON.
  
  :return: Dictionary with detection results
  """
  _, _, detections = camera.get_frame(apply_detection=True)
  return {"detections": detections}
  
# @app.get("/", response_class=HTMLResponse)
# async def index() -> str:
#     """
#     Serve a simple HTML page for visualization.
    
#     :return: HTML content
#     """
#     html_content = """
#     <!DOCTYPE html>
#     <html>
#         <head>
#             <title>Camera Stream with YOLO Detection</title>
#             <style>
#                 body { font-family: Arial, sans-serif; margin: 20px; }
#                 .container { display: flex; flex-wrap: wrap; gap: 20px; }
#                 .stream-container { margin-bottom: 20px; }
#                 button { padding: 10px; margin: 5px; cursor: pointer; }
#                 pre { background: #f5f5f5; padding: 10px; border-radius: 5px; max-height: 300px; overflow-y: auto; }
#             </style>
#         </head>
#         <body>
#             <h1>Camera Stream with YOLO Detection</h1>
#             <div class="container">
#                 <div class="stream-container">
#                     <h2>Raw Video</h2>
#                     <img src="/video?detection=false" width="640" height="480" />
#                     <div>
#                         <button onclick="takeSnapshot(false)">Take Snapshot</button>
#                     </div>
#                 </div>
#                 <div class="stream-container">
#                     <h2>Video with Detection</h2>
#                     <img src="/video?detection=true" width="640" height="480" />
#                     <div>
#                         <button onclick="takeSnapshot(true)">Take Snapshot with Detection</button>
#                     </div>
#                 </div>
#             </div>
#             <h3>Latest Detections:</h3>
#             <div id="detections">
#                 <pre>No detections yet</pre>
#             </div>
            
#             <script>
#                 function takeSnapshot(withDetection) {
#                     window.open(`/snapshot?detection=${withDetection}`, '_blank');
#                 }
                
#                 // Fetch detection data periodically
#                 setInterval(async () => {
#                     try {
#                         const response = await fetch('/detections');
#                         const data = await response.json();
#                         document.getElementById('detections').innerHTML = 
#                             '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
#                     } catch (error) {
#                         console.error("Error fetching detections:", error);
#                     }
#                 }, 1000);
#             </script>
#         </body>
#     </html>
#     """
#     return html_content

async def main():
  """
  Main entry point to run the Uvicorn server.
  """
  config = uvicorn.Config(app, host="0.0.0.0", port="8000")
  server = uvicorn.Server(config)
  
  # Run the server
  await server.serve()
  
if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("Server stopped by user.")
    
  
    