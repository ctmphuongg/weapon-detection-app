import asyncio
import cv2
import imutils
from imutils.video import VideoStream
from yolo_process import process_frame_with_yolo

# Shared state management
class StreamManager:
    def __init__(self, url_rtsp, model):
        self.active = False
        self.url_rtsp = url_rtsp
        self.model = model
        self.frame_queue = asyncio.Queue(maxsize=1000)
        self.keep_alive_counter = 0
        self.stream_task = None
        self.latest_detections = []
        
    async def start_stream(self):
        if not self.active:
            self.active = True
            self.stream_task = asyncio.create_task(self.process_stream())
            asyncio.create_task(self.monitor_activity())
    
    async def process_stream(self):
        # Start video stream in a thread pool to not block the event loop
        loop = asyncio.get_running_loop()
        vs = VideoStream(self.url_rtsp).start()
        await asyncio.sleep(1)  # Give time for camera to initialize
        
        try:
            while self.active:
                # Get frame in thread pool executor
                frame = await loop.run_in_executor(None, vs.read)
                if frame is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # Resize frame
                frame = imutils.resize(frame, width=680)
                
                # Process with YOLO in thread pool executor
                processed_frame, detections = await loop.run_in_executor(
                    None, 
                    lambda f: process_frame_with_yolo(f, self.model, return_detections=True), 
                    frame.copy()
                )
                
                if processed_frame is None:
                    await asyncio.sleep(0.1)
                    continue
                
                # Update latest detections if any were found
                if detections:
                    self.latest_detections = detections
                
                # Encode frame in thread pool executor
                encode_result = await loop.run_in_executor(
                    None, cv2.imencode, ".jpg", processed_frame
                )
                
                flag, encoded_image = encode_result
                if not flag:
                    await asyncio.sleep(0.1)
                    continue
                
                # If queue is full, remove oldest frame to prevent backlog
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                
                # Add new frame to queue
                await self.frame_queue.put(encoded_image)
                await asyncio.sleep(0.01)  # Small sleep to yield control
        finally:
            vs.stop()
    
    async def monitor_activity(self):
        while self.active:
            await asyncio.sleep(1)
            self.keep_alive_counter -= 1
            if self.keep_alive_counter <= 0:
                self.active = False
                if self.stream_task:
                    self.stream_task.cancel()
                    try:
                        await self.stream_task
                    except asyncio.CancelledError:
                        pass
                    self.stream_task = None
                break