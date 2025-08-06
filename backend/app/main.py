# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.chat import router as chat_router
from app.video import router as video_router
from app.mlx_service import get_mlx_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MLX service
    print("Starting MLX service...")
    try:
        mlx_service = get_mlx_service()
        print(" MLX service initialized successfully")
        yield
    except Exception as e:
        print(f" Failed to initialize MLX service: {e}")
        raise e
    finally:
        # Shutdown: Cleanup resources
        print(" Cleaning up MLX service...")
        mlx_service = get_mlx_service()
        mlx_service.cleanup()
        print(" Cleanup completed")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify allowed origins here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(video_router, prefix="/api/video")

@app.get("/")
async def root():
    return {
        "message": "MLX-powered FastAPI Chat Backend", 
        "status": "running",
        "models": "gemma-3n-E2B-it-4bit + Kokoro-82M"
    }

@app.get("/health")
async def health():
    """Global health check"""
    try:
        mlx_service = get_mlx_service()
        return {
            "fastapi": "healthy",
            "mlx_vlm": mlx_service.vlm_model is not None,
            "webcam": mlx_service.webcam is not None,
            "models": {
                "vlm": "mlx-community/gemma-3n-E2B-it-4bit",
                "tts": "prince-canuma/Kokoro-82M"
            }
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)