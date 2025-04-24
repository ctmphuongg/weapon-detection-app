from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
from ultralytics import YOLO
from api.routes import stream_manager

router = APIRouter()

async def frame_generator():
    try:
        while stream_manager.active:
            try:
                # Use wait_for with timeout to make this cancellable
                encoded_image = await asyncio.wait_for(
                    stream_manager.frame_queue.get(), 
                    timeout=5.0
                )
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                       bytearray(encoded_image) + b'\r\n')
            except asyncio.TimeoutError:
                # No frames available, but stream might still be active
                if stream_manager.active:
                    continue
                break
    except asyncio.CancelledError:
        # Handle client disconnection gracefully
        print("Stream cancelled")
        raise

@router.get("/")
async def video_feed():
    await stream_manager.start_stream()
    return StreamingResponse(
        frame_generator(), 
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

@router.get("/keep-alive")
async def keep_alive(background_tasks: BackgroundTasks):
    stream_manager.keep_alive_counter = 100
    # await stream_manager.start_stream()
    return {"status": "ok", "is_running": stream_manager.active} 