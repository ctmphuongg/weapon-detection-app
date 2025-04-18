import asyncio
import cv2
import imutils
from imutils.video import VideoStream
from stream_utils.yolo_process import process_frame_with_yolo
import time
from stream_utils.notification_manager import NotificationManager
import os
from dotenv import load_dotenv
import logging
import numpy as np
from typing import Tuple, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
        self.last_detection_time = None
        self.detection_timeout = 2.0  # Seconds to wait before considering a detection as disappeared
        self.detection_history = []  # List to store detection history
        self.history_timeout = 3600  # 1 hour in seconds
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        # Store the latest processed frame and detections
        self.latest_processed_frame = None
        self.latest_processed_detections = []
        self.frame_lock = asyncio.Lock()
        
        # Initialize notification manager
        api_endpoint = os.getenv("NOTIFICATION_API_ENDPOINT", "https://learnsecure-api.d.vaultinnovation.com/api/v1/public/threats")
        self.notification_manager = NotificationManager(api_endpoint)
    
    async def get_latest_processed_frame(self) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Get the latest processed frame and its detections
        
        Returns:
            Tuple of (frame, detections) or (None, []) if no frame is available
        """
        async with self.frame_lock:
            if self.latest_processed_frame is None:
                return None, []
            return self.latest_processed_frame.copy(), self.latest_processed_detections.copy()
    
    async def start_stream(self):
        if not self.active:
            logger.info("Starting stream...")
            self.active = True
            self.stream_task = asyncio.create_task(self.process_stream())
            asyncio.create_task(self.monitor_activity())
    
    async def process_stream(self):
        while self.active:
            try:
                # Start video stream in a thread pool to not block the event loop
                loop = asyncio.get_running_loop()
                logger.info(f"Connecting to RTSP stream: {self.url_rtsp}")
                vs = VideoStream(self.url_rtsp).start()
                await asyncio.sleep(1)  # Give time for camera to initialize
                
                self.reconnect_attempts = 0  # Reset reconnect attempts on successful connection
                
                while self.active:
                    try:
                        # Get frame in thread pool executor
                        frame = await loop.run_in_executor(None, vs.read)
                        if frame is None:
                            logger.warning("Received empty frame, retrying...")
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
                        
                        # print("Detections: ", detections)
                        if processed_frame is None:
                            logger.warning("Failed to process frame, retrying...")
                            await asyncio.sleep(0.1)
                            continue
                        
                        # Store the latest processed frame and detections
                        async with self.frame_lock:
                            self.latest_processed_frame = processed_frame
                            self.latest_processed_detections = detections
                        
                        current_time = time.time()
                        
                        # Update latest detections if any were found
                        if detections:
                            self.latest_detections = detections
                            self.last_detection_time = current_time
                            
                            # Add to history if these are new detections
                            if not self.detection_history or (current_time - self.detection_history[-1]['time']) > self.detection_timeout:
                                self.detection_history.append({
                                    'time': current_time,
                                    'count': len(detections),
                                    'detections': detections
                                })
                            
                            print("Sent to process detection")
                            # Process detections for notification
                            await self.notification_manager.process_detection(processed_frame, detections)
                        else:
                            # Check if detections have disappeared for too long
                            if self.last_detection_time and (current_time - self.last_detection_time) > self.detection_timeout:
                                self.latest_detections = []
                                self.last_detection_time = None
                        
                        # Clean up old history entries
                        self.detection_history = [
                            entry for entry in self.detection_history 
                            if current_time - entry['time'] <= self.history_timeout
                        ]
                        
                        # Encode frame in thread pool executor
                        encode_result = await loop.run_in_executor(
                            None, cv2.imencode, ".jpg", processed_frame
                        )
                        
                        flag, encoded_image = encode_result
                        if not flag:
                            logger.warning("Failed to encode frame, retrying...")
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
                        
                    except Exception as e:
                        logger.error(f"Error processing frame: {str(e)}")
                        await asyncio.sleep(0.1)
                        continue
                
            except Exception as e:
                logger.error(f"Stream error: {str(e)}")
                vs.stop()
                
                # Handle reconnection
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    logger.info(f"Attempting to reconnect (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})...")
                    await asyncio.sleep(self.reconnect_delay)
                    continue
                else:
                    logger.error("Max reconnection attempts reached. Stopping stream.")
                    self.active = False
                    break
    
    async def monitor_activity(self):
        while self.active:
            await asyncio.sleep(1)
            self.keep_alive_counter -= 1
            if self.keep_alive_counter <= 0:
                logger.info("Keep-alive counter expired, stopping stream")
                self.active = False
                if self.stream_task:
                    self.stream_task.cancel()
                    try:
                        await self.stream_task
                    except asyncio.CancelledError:
                        pass
                    self.stream_task = None
                break