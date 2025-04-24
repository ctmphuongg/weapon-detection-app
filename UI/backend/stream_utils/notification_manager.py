import asyncio
import time
import json
import aiohttp
import base64
import cv2
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from config.settings import TOKEN
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
            frame: The current frame with bounding box
            detections: List of detections from YOLO
            
        Returns:
            True if a notification was sent, False otherwise
        """
        print("Get to process_detection")
        current_time = time.time()
        
        # Filter detections to only include weapons with confidence above threshold
        weapon_detections = [
            d for d in detections 
            if d["confidence"] >= self.confidence_threshold
        ]
        
        if not weapon_detections:
            # No weapons detected with sufficient confidence
            print("No weapon detected with sufficient confidence.")
            return False
        
        # Get the highest confidence detection
        highest_conf_detection = max(weapon_detections, key=lambda x: x["confidence"])
        highest_conf = highest_conf_detection["confidence"]
        
        # Count unique weapon types
        weapon_types = set(d["class_name"] for d in weapon_detections)
        weapon_count = len(weapon_types)
        
        print(highest_conf_detection)
        
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
                print("Sending notification")
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
        # print("API", self.api_endpoint, TOKEN)
        if self.best_image is None:
            print("No best image set")
            return False
        
        try:
            # Encode the image as JPEG
            _, buffer = cv2.imencode('.jpg', self.best_image)
            image_bytes = buffer.tobytes()
            
            # Prepare the headers
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer '+ TOKEN
            }

            # Prepare the form data
            form_data = aiohttp.FormData()
            
            # Add the image as a file
            form_data.add_field('photo', 
                            image_bytes, 
                            filename='detection_image.jpg',
                            content_type='image/jpeg')
            
            # Add other parameters as in the example
            form_data.add_field('locationId', '1')
            form_data.add_field('cameraId', '1')
            form_data.add_field('timestamp', datetime.now().isoformat() + 'Z')
            
            print("Best detections: ", self.best_detections)
            # Add detection events
            if self.best_detections:
                for i, detection in enumerate(self.best_detections):
                    print(detection["confidence"], detection["class_name"])
                    i = str(i)
                    form_data.add_field(f'detectionEvent[{i}][confidence]', str(detection["confidence"]))
                    if (detection["class_name"] in ["gun", "knife"]): 
                        form_data.add_field(f'detectionEvent[{i}][classification]', detection["class_name"])
        
            # TODO: Test send notification - delete when done
            else: 
                form_data.add_field(f'detectionEvent[0][confidence]', '0.5')
                form_data.add_field(f'detectionEvent[0][classification]', 'knife')
            
            # TODO: Debug test image - delete when done
            if self.best_image is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(f"debug_image_{timestamp}.jpg", self.best_image)
                print(f"Saved debug image to debug_image_{timestamp}.jpg")
                
            # Send the notification
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_endpoint, data=form_data, headers=headers) as response:
                    print(response)
                    
                    if response.status == 201:
                        response_data = await response.json()
                        print(response_data)
                        
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
            traceback.print_exc()  # Add this to print full exception details
            return False