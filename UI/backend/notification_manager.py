import asyncio
import time
import json
import aiohttp
import base64
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class NotificationManager:
    def __init__(self, api_endpoint: str):
        """
        Initialize the notification manager
        
        Args:
            api_endpoint: The endpoint URL to send notifications to
        """
        self.api_endpoint = api_endpoint
        self.last_notification_time = 0
        self.cooldown_period = 300  # 5 minutes in seconds
        self.confidence_threshold = 0.60  # 60% confidence threshold
        self.confidence_increase_threshold = 0.10  # 10% confidence increase threshold
        self.best_image_window = 3  # 3 seconds window to find best image
        self.best_image = None
        self.best_image_time = 0
        self.best_detections = []
        self.is_capturing_best_image = False
        self.capture_start_time = 0
        self.last_detection_category = None
        self.last_detection_count = 0
        self.last_detection_confidence = 0.0
        
    async def process_detection(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> bool:
        """
        Process a detection and determine if a notification should be sent
        
        Args:
            frame: The current frame
            detections: List of detections from YOLO
            
        Returns:
            True if a notification was sent, False otherwise
        """
        current_time = time.time()
        
        # Filter detections to only include weapons with confidence above threshold
        weapon_detections = [
            d for d in detections 
            if d["confidence"] >= self.confidence_threshold
        ]
        
        if not weapon_detections:
            # No weapons detected with sufficient confidence
            return False
        
        # Get the highest confidence detection
        highest_conf_detection = max(weapon_detections, key=lambda x: x["confidence"])
        highest_conf = highest_conf_detection["confidence"]
        
        # Count unique weapon types
        weapon_types = set(d["class_name"] for d in weapon_detections)
        weapon_count = len(weapon_types)
        
        # Check if we should start capturing the best image
        if not self.is_capturing_best_image and self._should_start_capture(
            highest_conf, weapon_types, weapon_count
        ):
            self.is_capturing_best_image = True
            self.capture_start_time = current_time
            self.best_image = frame.copy()
            self.best_image_time = current_time
            self.best_detections = weapon_detections
            return False
        
        # If we're in the capture window, update the best image if this one is better
        if self.is_capturing_best_image:
            elapsed_time = current_time - self.capture_start_time
            
            # Check if this is a better image
            if self._is_better_image(highest_conf, weapon_types, weapon_count):
                self.best_image = frame.copy()
                self.best_image_time = current_time
                self.best_detections = weapon_detections
            
            # If we've reached the end of the capture window, send the notification
            if elapsed_time >= self.best_image_window:
                self.is_capturing_best_image = False
                await self._send_notification()
                return True
        
        return False
    
    def _should_start_capture(self, confidence: float, weapon_types: set, weapon_count: int) -> bool:
        """
        Determine if we should start capturing the best image
        
        Args:
            confidence: The highest confidence of current detections
            weapon_types: Set of weapon types detected
            weapon_count: Number of unique weapon types
            
        Returns:
            True if we should start capturing, False otherwise
        """
        current_time = time.time()
        
        # If we're in cooldown period, check for exceptions
        if current_time - self.last_notification_time < self.cooldown_period:
            # Exception 1: Threat category changed
            if self.last_detection_category != list(weapon_types)[0]:
                return True
            
            # Exception 2: Number of weapons changed
            if self.last_detection_count != weapon_count:
                return True
            
            # Exception 3: Confidence increased by threshold
            if confidence - self.last_detection_confidence >= self.confidence_increase_threshold:
                return True
            
            # No exceptions met, don't start capture
            return False
        
        # Not in cooldown period, start capture if confidence is above threshold
        return confidence >= self.confidence_threshold
    
    def _is_better_image(self, confidence: float, weapon_types: set, weapon_count: int) -> bool:
        """
        Determine if the current image is better than the best image so far
        
        Args:
            confidence: The highest confidence of current detections
            weapon_types: Set of weapon types detected
            weapon_count: Number of unique weapon types
            
        Returns:
            True if current image is better, False otherwise
        """
        # If we don't have a best image yet, this is better
        if self.best_image is None:
            return True
        
        # Get the highest confidence from the best detections
        best_conf = max(d["confidence"] for d in self.best_detections) if self.best_detections else 0
        
        # If confidence is higher, this is better
        if confidence > best_conf:
            return True
        
        # If confidence is the same but more weapon types, this is better
        if confidence == best_conf and weapon_count > len(self.best_detections):
            return True
        
        return False
    
    async def _send_notification(self) -> bool:
        """
        Send the notification with the best image to the API endpoint
        
        Returns:
            True if notification was sent successfully, False otherwise
        """
        if self.best_image is None:
            return False
        
        try:
            # Encode the image as JPEG
            _, buffer = cv2.imencode('.jpg', self.best_image)
            image_bytes = buffer.tobytes()
            
            # Convert to base64 for JSON serialization
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare the payload
            payload = {
                "picture": image_base64,
                "detection_event": [
                    {
                        "confidence": d["confidence"],
                        "classification": d["class_name"]
                    } for d in self.best_detections
                ],
                "location_id": 1,  # Default as specified
                "camera_id": 1,    # Same as location_id as specified
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the notification
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_endpoint, json=payload) as response:
                    if response.status == 200:
                        # Update state after successful notification
                        self.last_notification_time = time.time()
                        self.last_detection_category = self.best_detections[0]["class_name"] if self.best_detections else None
                        self.last_detection_count = len(self.best_detections)
                        self.last_detection_confidence = max(d["confidence"] for d in self.best_detections) if self.best_detections else 0
                        
                        # Clear the best image
                        self.best_image = None
                        self.best_detections = []
                        
                        return True
                    else:
                        print(f"Failed to send notification: {response.status}")
                        return False
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False 