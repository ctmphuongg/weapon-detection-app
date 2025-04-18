import os
import cv2
import time
import asyncio
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging
from .stream_manager import StreamManager

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# S3 configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
SAVE_MODE = os.getenv("SAVE_MODE", "local")  # "local" or "s3"
LOCAL_SAVE_DIR = os.getenv("LOCAL_SAVE_DIR", "saved_images")

# Ensure local save directory exists
if SAVE_MODE == "local" and not os.path.exists(LOCAL_SAVE_DIR):
    os.makedirs(LOCAL_SAVE_DIR)

def save_image_local(image: np.ndarray, filename: str) -> str:
    """
    Save image to local filesystem
    
    Args:
        image: The image to save
        filename: The filename to save as
        
    Returns:
        The path where the image was saved
    """
    filepath = os.path.join(LOCAL_SAVE_DIR, filename)
    cv2.imwrite(filepath, image)
    return filepath

def save_image_s3(image: np.ndarray, filename: str) -> str:
    """
    Save image to S3 bucket with hierarchical path structure
    
    Args:
        image: The image to save
        filename: The filename to save as
        
    Returns:
        The S3 URL where the image was saved
    """
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name=S3_REGION)
    
    # Create hierarchical path structure for S3
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    
    # Create S3 key with hierarchical path
    s3_key = f"detections/{year}/{month}/{day}/{filename}"
    
    # Save image to temporary file
    temp_filepath = f"/tmp/{filename}"
    cv2.imwrite(temp_filepath, image)
    
    # Upload to S3
    try:
        s3_client.upload_file(temp_filepath, S3_BUCKET_NAME, s3_key)
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        
        # Clean up temporary file
        os.remove(temp_filepath)
        
        return s3_url
    except ClientError as e:
        logger.error(f"Error uploading to S3: {e}")
        # If S3 upload fails, fall back to local save
        return save_image_local(image, filename)

def save_image(image: np.ndarray, filename: Optional[str] = None) -> str:
    """
    Save image based on configured mode (local or S3)
    
    Args:
        image: The image to save
        filename: Optional filename, will generate one if not provided
        
    Returns:
        The path or URL where the image was saved
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detection_{timestamp}.jpg"
    
    if SAVE_MODE == "s3":
        return save_image_s3(image, filename)
    else:
        return save_image_local(image, filename)

def get_detections(frame: np.ndarray, model: Any) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Run YOLO detection on a frame and return the annotated frame and detections
    
    Args:
        frame: The image frame to process
        model: The YOLO model
        
    Returns:
        Tuple of (annotated_frame, detections)
    """
    if frame is None:
        return None, []
    
    # Run inference on the frame
    results = model(frame)
    
    # Store detections
    detection_list = []
    
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
            
            # Add to detection list
            detection_list.append({
                "class_name": class_name,
                "confidence": conf,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2
            })
    
    return frame, detection_list

async def process_rtsp_frame(url_rtsp: str, model: Any, interval: int = 10, stream_manager: Optional[StreamManager] = None) -> Dict[str, Any]:
    """
    Process a frame from RTSP URL at specified intervals
    
    Args:
        url_rtsp: The RTSP URL
        model: The YOLO model
        interval: Interval in seconds between captures
        stream_manager: Optional StreamManager instance to get the latest processed frame
        
    Returns:
        Dictionary with detection results and image path
    """
    try:
        # If stream_manager is provided, use its latest processed frame
        if stream_manager is not None:
            frame, detections = await stream_manager.get_latest_processed_frame()
            if frame is None:
                logger.error("No processed frame available from stream manager")
                return {
                    "error": "No processed frame available",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Save the annotated image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detection_{timestamp}.jpg"
            image_path = save_image(frame, filename)
            
            # Format detections for API response
            formatted_detections = []
            for detection in detections:
                formatted_detections.append({
                    "confidence": detection["confidence"],
                    "classification": detection["class_name"]
                })
            
            # Prepare API response
            response = {
                "picture": image_path,
                "detection_event": formatted_detections,
                "location_id": 1,  # Default as specified
                "camera_id": 1,    # Same as location_id as specified
                "timestamp": datetime.now().isoformat()
            }
            
            return response
        
        # Fallback to direct RTSP capture if no stream_manager is provided
        # Initialize video capture with a timeout
        cap = cv2.VideoCapture(url_rtsp)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5 second timeout
        
        if not cap.isOpened():
            logger.error("Failed to open RTSP stream")
            return {
                "error": "Failed to open RTSP stream",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Try to read a frame with a timeout
            start_time = time.time()
            ret = False
            frame = None
            
            while time.time() - start_time < 5.0:  # 5 second timeout
                ret, frame = cap.read()
                if ret and frame is not None:
                    break
                await asyncio.sleep(0.1)  # Small sleep to yield control
            
            if not ret or frame is None:
                logger.error("Failed to read frame from RTSP stream")
                return {
                    "error": "Failed to read frame from RTSP stream",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Process frame with YOLO
            annotated_frame, detections = get_detections(frame, model)
            
            if annotated_frame is None:
                logger.error("Failed to process frame with YOLO")
                return {
                    "error": "Failed to process frame with YOLO",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Save the annotated image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"detection_{timestamp}.jpg"
            image_path = save_image(annotated_frame, filename)
            
            # Format detections for API response
            formatted_detections = []
            for detection in detections:
                formatted_detections.append({
                    "confidence": detection["confidence"],
                    "classification": detection["class_name"]
                })
            
            # Prepare API response
            response = {
                "picture": image_path,
                "detection_event": formatted_detections,
                "location_id": 1,  # Default as specified
                "camera_id": 1,    # Same as location_id as specified
                "timestamp": datetime.now().isoformat()
            }
            
            return response
        
        finally:
            # Always release the capture
            try:
                cap.release()
            except Exception as e:
                logger.error(f"Error releasing video capture: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error processing RTSP frame: {str(e)}")
        return {
            "error": f"Error processing frame: {str(e)}",
            "timestamp": datetime.now().isoformat()
        } 