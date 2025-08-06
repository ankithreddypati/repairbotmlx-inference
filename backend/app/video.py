# app/video.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
from app.mlx_service import get_mlx_service
import io
from PIL import Image

router = APIRouter()

# Store multiple camera instances
cameras = {}

def get_camera(camera_index: int = 0):
    """Get or create camera instance for given index"""
    if camera_index not in cameras:
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Changed to 1280
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Changed to 720
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cameras[camera_index] = cap
            print(f" Camera {camera_index} initialized")
        else:
            print(f" Camera {camera_index} not available")
            return None
    
    return cameras[camera_index]

@router.get("/stream")
async def video_stream(camera_index: int = Query(0, description="Camera index (0, 1, 2, etc.)")):
    """Stream webcam video feed from specified camera"""
    
    camera = get_camera(camera_index)
    if not camera or not camera.isOpened():
        raise HTTPException(status_code=503, detail=f"Camera {camera_index} not available")
    
    def generate_frames():
        while True:
            try:
                ret, frame = camera.read()
                if not ret:
                    break
                
                # Convert frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                       
            except Exception as e:
                print(f"Error generating frame from camera {camera_index}: {e}")
                break
    
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/capture")
async def capture_frame(camera_index: int = Query(0, description="Camera index")):
    """Capture a single frame from specified camera"""
    
    camera = get_camera(camera_index)
    if not camera or not camera.isOpened():
        raise HTTPException(status_code=503, detail=f"Camera {camera_index} not available")
    
    try:
        ret, frame = camera.read()
        if not ret:
            raise HTTPException(status_code=500, detail=f"Failed to capture frame from camera {camera_index}")
        
        # Convert frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        frame_bytes = buffer.tobytes()
        
        return StreamingResponse(
            io.BytesIO(frame_bytes),
            media_type="image/jpeg"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error capturing frame from camera {camera_index}: {str(e)}")

@router.get("/status")
async def video_status():
    """Get status of all cameras"""
    camera_status = {}
    
    # Check cameras 0-3
    for i in range(4):
        camera = get_camera(i)
        if camera and camera.isOpened():
            camera_status[f"camera_{i}"] = {
                "available": True,
                "width": int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": int(camera.get(cv2.CAP_PROP_FPS))
            }
        else:
            camera_status[f"camera_{i}"] = {
                "available": False
            }
    
    return camera_status

@router.on_event("shutdown")
async def cleanup_cameras():
    """Cleanup camera resources on shutdown"""
    for camera_index, camera in cameras.items():
        if camera:
            camera.release()
            print(f"🧹 Camera {camera_index} released")