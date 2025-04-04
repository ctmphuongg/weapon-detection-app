import cv2
from ultralytics import YOLO

def process_frame_with_yolo(frame, model, return_detections=False):
    """Apply YOLO detection to a frame and return the annotated frame"""
    if frame is None:
        return None if not return_detections else (None, [])
    
    # Run inference on the frame
    results = model(frame)
    
    # Store detections if requested
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
            
            # Add to detection list if requested
            if return_detections:
                detection_list.append({
                    "class_name": class_name,
                    "confidence": conf,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                })
    
    if return_detections:
        return frame, detection_list
    return frame