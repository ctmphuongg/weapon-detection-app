from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from api.routes import notifications, stream, video
from config.settings import API_HOST, API_PORT


# Disable YOLO inference logs
logging.getLogger('ultralytics').setLevel(logging.WARNING)

# Initialize FastAPI app
app = FastAPI(title="Weapon Detection API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(video.router, prefix="/video", tags=["Video Processing"])
app.include_router(stream.router, prefix="/stream", tags=["Stream Management"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

# Root endpoint for model information
@app.get("/model-info")
def model_info():
    return {"classes": stream.weapon_model.names}

# Latest detections endpoint
@app.get("/latest-detections")
async def latest_detections():
    return {"detections": stream.stream_manager.latest_detections}

# Startup event handler
@app.on_event("startup")
async def startup_event():
    """
    Start the stream automatically when the server starts
    """
    print("Starting stream on server startup...")
    await stream.stream_manager.start_stream()
    # Set a high keep-alive counter to keep the stream running
    stream.stream_manager.keep_alive_counter = 1000000  # A very large number

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    stream.stream_manager.active = False
    if stream.stream_manager.stream_task:
        stream.stream_manager.stream_task.cancel()

if __name__ == "__main__":
    uvicorn.run(app, host=API_HOST, port=API_PORT)