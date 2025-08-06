# LE_REPAIRBOT - MLX-Powered AI Repair Assistant

A sophisticated AI-powered repair assistant that combines computer vision, natural language processing, and real-time video streaming to help with repair tasks. Built with MLX for efficient AI inference, FastAPI for the backend, and Next.js with ChatUI for the frontend.

##  Features

- **AI-Powered Chat**: Real-time conversation with an MLX-powered AI assistant
- **Multi-Camera Support**: Live video streaming from multiple camera angles (wrist view and global top view)
- **Text-to-Speech**: Natural voice responses using Kokoro-82M TTS model
- **Computer Vision**: Visual understanding using Gemma-3n-E2B-it-4bit model
- **LE Robot Integration**: Trigger physical robot actions via WiFi (pass_screwdriver, etc.)
- **Real-time Processing**: Low-latency AI inference optimized with MLX
- **Modern UI**: Beautiful, responsive interface with Framer Motion animations

##  Architecture

- **Backend**: FastAPI with MLX for AI inference
- **Frontend**: Next.js 15 
- **AI Models**: 
  - Vision Language Model: `mlx-community/gemma-3n-E2B-it-4bit`
  - Text-to-Speech: `prince-canuma/Kokoro-82M`
- **Video Streaming**: Real-time camera feeds with WebRTC support
- **Audio Processing**: Advanced audio handling with sounddevice and soundfile

##  Prerequisites

- **Python 3.10+** with uv package manager
- **Node.js 18+** with pnpm package manager
- **macOS** (MLX is optimized for Apple Silicon)
- **Webcam access** for video streaming functionality

##  Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd repairbotmlx-inference
```

### 2. Backend Setup

Navigate to the backend directory and set up the Python environment:

```bash
cd backend

# Install dependencies using uv (recommended)
uv sync

# Start the FastAPI development server
uv run fastapi dev
```

The backend API will be available at:
- **API**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

### 3. Frontend Setup

In a new terminal, navigate to the frontend directory:

```bash
cd frontend

# Install dependencies
pnpm install

# Start the development server
pnpm dev
```

The frontend will be available at `http://localhost:3000`

##  Usage

1. **Start both servers** (backend and frontend)
2. **Allow camera access** when prompted
3. **Begin chatting** with the AI assistant
4. **View live camera feeds** on the right side of the interface
5. **Listen to AI responses** with natural text-to-speech
6. **Trigger robot actions** by asking the AI to perform tasks (e.g., "pass me the screwdriver")

###  LE Robot Integration

The AI can trigger physical robot actions when configured:

- **Setup**: Configure `ROBOT_IP` and `ROBOT_PORT` in your `.env` file
- **Robot Server**: Ensure your LE Robot server is running and accessible via HTTP
- **Available Actions**: Currently supports `pass_screwdriver` and can be extended
- **AI Decision**: The AI automatically decides when to trigger robot actions based on conversation context
- **WiFi Communication**: Robot commands are sent via HTTP POST to `http://{ROBOT_IP}:{ROBOT_PORT}/trigger`

**Note**: The LE Robot policy server should be run simultaneously with this application.

**Learn More**: For detailed information about the LE Robot integration, visit 

**Example Robot Server Endpoint:**
```python
# Your robot server should implement this endpoint
@app.post("/trigger")
async def trigger_robot_action(request: dict):
    task = request.get("task")
    if task == "pass_screwdriver":
        # Execute robot action
        return {"success": True, "action": task}
    return {"success": False, "error": "Unknown task"}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Backend environment variables
MODEL_CACHE_DIR=./models
AUDIO_OUTPUT_DIR=./audio_output
CAMERA_INDEX_0=0
CAMERA_INDEX_1=1

# LE Robot Integration (Optional)
ROBOT_IP=192.168.1.100
ROBOT_PORT=8080
```

### Model Configuration

The application uses pre-configured models, but you can modify the model paths in `backend/app/mlx_service.py`:

- **VLM Model**: `mlx-community/gemma-3n-E2B-it-4bit`
- **TTS Model**: `prince-canuma/Kokoro-82M`

## 📁 Project Structure

```
repairbotmlx-inference/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── chat.py          # Chat API endpoints
│   │   ├── video.py         # Video streaming endpoints
│   │   ├── mlx_service.py   # MLX AI service
│   │   └── vercel.py        # Vercel deployment config
│   ├── pyproject.toml       # Python dependencies
│   └── uv.lock             # Locked dependencies
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main application page
│   │   ├── layout.tsx       # App layout
│   │   └── globals.css      # Global styles
│   ├── components/
│   │   ├── VideoChatCanvas.tsx    # Video chat interface
│   │   ├── VideoFeed.tsx          # Video streaming component
│   │   ├── BackendVideoFeed.tsx   # Backend video integration
│   │   └── HiddenAudioPlayer.tsx  # Audio playback component
│   ├── package.json         # Node.js dependencies
│   └── pnpm-lock.yaml      # Locked dependencies
└── README.md               # This file
```

## 🛠️ Development

### Backend Development

```bash
cd backend

# Run with auto-reload
uv run fastapi dev

# Run tests
uv run pytest

# Check health
curl http://localhost:8000/health

# Test robot integration (if configured)
curl -X POST http://localhost:8000/api/chat/realtime \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Please pass me the screwdriver"}]}'
```

### Frontend Development

```bash
cd frontend

# Development server
pnpm dev

# Build for production
pnpm build

# Type checking
pnpm type-check

# Linting
pnpm lint
```

## 🚀 Deployment

### Backend Deployment

The backend is configured for Vercel deployment with the `vercel.py` configuration file.

### Frontend Deployment

```bash
cd frontend
pnpm build
pnpm dev
```



## 🙏 Acknowledgments

- **MLX Team** for the efficient ML framework and multimodal day0 support for gemma3n models
- **LlamaIndex** for the ChatUI components
- **LE Robot Team** for the physical robot integration capabilities

