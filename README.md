# Senior Design

....

# Weapon Detection App

A real-time weapon detection system that uses computer vision to detect weapons in video streams. The system consists of a FastAPI backend that processes RTSP video streams and a React frontend that displays the video feed and detection results.

## Features

- Real-time video streaming from RTSP cameras
- YOLO-based weapon detection
- Live detection alerts and statistics
- Detection history tracking
- Modern, responsive UI with Tailwind CSS

## Tech Stack

### Backend
- FastAPI (Python web framework)
- OpenCV for video processing
- YOLO (You Only Look Once) for object detection
- RTSP streaming support
- Multiprocessing for efficient video processing

### Frontend
- React.js
- Tailwind CSS for styling
- Real-time video streaming via MJPEG
- WebSocket-like polling for detection updates

## How It Works

### Video Streaming
1. The backend connects to an RTSP camera stream using OpenCV
2. Frames are processed in real-time using YOLO for weapon detection
3. Processed frames are encoded as JPEG images
4. The frontend receives a continuous stream of JPEG images via MJPEG streaming
5. The frontend displays the video feed and updates detection information

### Detection System
1. Each frame is processed by the YOLO model
2. Detected objects are filtered for weapons
3. Detection results include:
   - Object class (weapon type)
   - Confidence score
   - Bounding box coordinates
4. Results are sent to the frontend via a REST API endpoint

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 14+
- RTSP camera or video source

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your RTSP URL:
   ```
   RTSP_URL=rtsp://your-camera-url
   ```

5. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend/weapon
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open your browser and navigate to `http://localhost:3000`

## API Endpoints

### Backend
- `GET /`: Main video stream endpoint (MJPEG)
- `GET /keep-alive`: Keep the stream active
- `GET /latest-detections`: Get the latest detection results
- `GET /model-info`: Get information about the YOLO model classes

## Architecture Details

### RTSP Stream Processing
The system uses OpenCV's VideoStream to connect to RTSP cameras. The video stream is processed in a separate thread to prevent blocking the main application. Each frame is:
1. Captured from the RTSP stream
2. Resized for optimal processing
3. Processed by the YOLO model
4. Encoded as JPEG
5. Sent to connected clients

### Frontend Video Display
The frontend uses a simple but effective approach to display the video stream:
1. Connects to the MJPEG stream endpoint
2. Displays frames using an HTML img element
3. Polls for new detections every second
4. Updates the UI with detection results and statistics
