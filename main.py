import asyncio
from fastapi import FastAPI, Response, Query
from fastapi.responses import StreamingResponse
import cv2
import threading
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import uvicorn
from typing import Optional, Union

@asynccontextmanager
async def lifespan(app: FastAPI):
  """
  Lifespan context manager for startup and shutdown events.
  """
  try: 
    yield
  except asyncio.exceptions.CancelledError as error:
    print(error.args)
  finally:
    camera.release()
    print("Camera resource released.")

app = FastAPI(lifespan = lifespan)

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
    
  def get_frame(self) -> bytes:
    """
    Capture a frame from the camera.
    
    :return: JPEG encoded image bytes
    """
    with self.lock:
      ret, frame = self.cap.read()
      if not ret:
        return b''
      
      ret, jpeg = cv2.imencode('.jpg', frame)
      if not ret:
        return b''
      
      return jpeg.tobytes()
    
  def release(self) -> None:
    """
    Release the camera resource.
    """
    with self.lock:
      if self.cap.isOpened():
        self.cap.release()
        
        
async def gen_frames() -> AsyncGenerator[bytes, None]:
  """
  An asynchronous generator function that yields camera frames.
  
  :yield: JPEG encoded image bytes
  """
  try:
    while True:
      frame = camera.get_frame()
      if frame:
        yield (b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
      else:
        break
      await asyncio.sleep(0)
  except (asyncio.CancelledError, GeneratorExit):
    print("Frame generation cancelled.")
  finally:
    print("Frame generator exited.")
    

@app.get("/")
def read_root():
  return {"Hello": "World"}