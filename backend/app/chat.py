# app/chat.py - FIXED VERSION
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional, List
import json
import asyncio
import base64
import os
from io import BytesIO
from PIL import Image
import time
import uuid
from app.vercel import VercelStreamResponse
from app.mlx_service import get_mlx_service

router = APIRouter(prefix="/chat")

@router.post("/")
async def chat(request: Request) -> StreamingResponse:
    """Original chat endpoint with MLX integration"""
    data = await request.json()
    messages = data.get("messages", [])
    last_message = messages[-1] if messages else {"content": ""}
    
    user_prompt = last_message.get("content", "")
    
    # Get MLX service
    mlx_service = get_mlx_service()
    
    # Process with webcam + MLX
    try:
        result = await mlx_service.webcam_chat(user_prompt, enable_tts=True, max_tokens=50)
        ai_response = result.get("ai_response", "No response generated")
        
        # Create streaming events
        events = []
        
        # Add query context
        events.append(f'User query: "{user_prompt}"\n\n')
        
        # Stream AI response word by word
        response_tokens = ai_response.split(' ')
        events.extend([f"{token} " for token in response_tokens])
        
        # Add audio annotation if available
        if result.get("audio") and result["audio"].get("success"):
            audio_annotation = {
                "type": "audio_response",
                "data": {
                    "audio_data": result["audio"]["audio_data"],
                    "text": ai_response,
                    "voice": "am_michael",
                    "duration": result["audio"].get("duration", 0)
                }
            }
            events.append(audio_annotation)
        
        # Add webcam annotation
        webcam_annotation = {
            "type": "webcam_capture",
            "data": {
                "captured": result.get("has_webcam", False),
                "timestamp": asyncio.get_event_loop().time()
            }
        }
        events.append(webcam_annotation)
        
    except Exception as e:
        print(f" MLX processing error: {e}")
        # Fallback to original sample response
        events = [
            f'User query: "{user_prompt}"\n\n',
            f"Sorry, I encountered an error: {str(e)}\n\n",
            "Please try again or check the MLX service status."
        ]
    
    async def event_stream():
        for event in events:
            await asyncio.sleep(0.05)
            if isinstance(event, str):
                yield f"data: {json.dumps({'type': 'text', 'content': event})}\n\n"
            elif isinstance(event, dict):
                yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# Add this simple test endpoint to your app/chat.py

@router.post("/test")
async def test_endpoint(request: Request):
    """Simple test endpoint"""
    try:
        data = await request.json()
        messages = data.get("messages", [])
        last_message = messages[-1] if messages else {"content": "test"}
        prompt = last_message.get("content", "test")
        
        print(f"🧪 Test request received: {prompt}")
        
        # Simple response
        async def test_stream():
            yield f"data: {json.dumps({'content': f'Echo: {prompt}', 'role': 'assistant'})}\n\n"
            yield f"data: [DONE]\n\n"
        
        return StreamingResponse(
            test_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive", 
                "Access-Control-Allow-Origin": "*",
            }
        )
        
    except Exception as e:
        print(f" Test error: {e}")
        return {"error": str(e)}


# @router.post("/realtime")
# async def realtime_chat(request: Request) -> StreamingResponse:
    """FIXED: Real-time chat that accepts JSON from frontend"""
    data = await request.json()
    messages = data.get("messages", [])
    last_message = messages[-1] if messages else {"content": ""}
    
    prompt = last_message.get("content", "")
    max_tokens = 50
    enable_tts = True
    
    mlx_service = get_mlx_service()
    
    async def stream_realtime_response():
        try:
            yield f'data: {json.dumps({"type": "start", "prompt": prompt})}\n\n'
            
            # Start webcam capture
            webcam_task = asyncio.create_task(mlx_service.async_webcam_capture())
            
            # Wait for webcam image
            image = await webcam_task
            if not image:
                yield f'data: {json.dumps({"type": "error", "error": "Could not capture webcam"})}\n\n'
                return
            
            # Process multimodal (image + text) with VLM
            full_response = ""
            async for text_chunk in mlx_service.async_multimodal_chat_streaming(image, prompt, max_tokens):
                full_response += text_chunk
                yield f'data: {json.dumps({"type": "text", "content": text_chunk})}\n\n'
                await asyncio.sleep(0.02)  # Faster streaming
            
            # Clean response - remove asterisks and extra formatting
            clean_response = mlx_service.clean_response_text(full_response)
            
            # Wait for complete text before starting TTS
            yield f'data: {json.dumps({"type": "text_complete", "full_text": clean_response})}\n\n'
            await asyncio.sleep(0.2)  # Small pause before audio starts
            
            # Start TTS with cleaned text
            if enable_tts and clean_response:
                async for audio_chunk in mlx_service.async_text_to_speech_streaming(clean_response):
                    if not audio_chunk.get("error"):
                        chunk_data = {
                            "type": "audio_chunk",
                            "audio_data": audio_chunk["audio_data"],
                            "chunk_index": audio_chunk.get("chunk_index", 0),
                            "total_chunks": 1,
                            "is_final": audio_chunk["is_final"],
                            "text": audio_chunk["text"],
                            "duration": audio_chunk["duration"]
                        }
                        yield f'data: {json.dumps(chunk_data)}\n\n'
                        await asyncio.sleep(0.1)
                    else:
                        yield f'data: {json.dumps({"type": "error", "error": audio_chunk["error"]})}\n\n'
            
            yield f'data: {json.dumps({"type": "complete", "full_response": clean_response})}\n\n'
            
        except Exception as e:
            print(f" Realtime chat error: {e}")
            yield f'data: {json.dumps({"type": "error", "error": str(e)})}\n\n'
    
    return StreamingResponse(
        stream_realtime_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

# Replace your /realtime endpoint in app/chat.py with this AI SDK compatible version

# Replace your /realtime endpoint with this EXACT format for AI SDK

# Update your /realtime endpoint to handle audio properly

# @router.post("/realtime")
# async def realtime_chat(request: Request) -> StreamingResponse:
    """Fixed with proper audio handling"""
    data = await request.json()
    messages = data.get("messages", [])
    prompt = messages[-1]["content"] if messages else "hello"
    
    print(f"🎯 Request: {prompt}")
    
    mlx_service = get_mlx_service()
    
    async def ai_sdk_stream():
        try:
            # Get response from MLX
            result = await mlx_service.webcam_chat(prompt, enable_tts=True, max_tokens=50)
            
            if "error" in result:
                yield f'data: {json.dumps({"error": result["error"]})}\n\n'
                return
            
            response_text = result.get("ai_response", "No response")
            print(f" Response: {response_text}")
            
            # Stream text first
            words = response_text.split()
            for word in words:
                chunk = f'0:"{word} "\n'
                yield chunk
                await asyncio.sleep(0.1)
            
            # Send complete message
            yield f'0:""\n'  # End text stream
            
            # Send audio data if available - in the format frontend expects
            if result.get("audio") and result["audio"].get("success"):
                audio_data = result["audio"]["audio_data"]
                duration = result["audio"].get("duration", 3)
                
                # Send audio in format your frontend StreamingAudioHandler expects
                audio_chunk = {
                    "audio_data": audio_data,
                    "text": response_text,
                    "duration": duration,
                    "is_final": True
                }
                
                # Send as a separate data stream
                yield f'data: {json.dumps({"type": "audio", "data": audio_chunk})}\n\n'
            
        except Exception as e:
            print(f" Error: {e}")
            yield f'0:"Error: {str(e)}"\n'
    
    return StreamingResponse(
        ai_sdk_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        }
    )
    """AI SDK compatible format - this will work"""
    data = await request.json()
    messages = data.get("messages", [])
    prompt = messages[-1]["content"] if messages else "hello"
    
    print(f"🎯 Request: {prompt}")
    
    mlx_service = get_mlx_service()
    
    async def ai_sdk_stream():
        try:
            # Get response from MLX
            result = await mlx_service.webcam_chat(prompt, enable_tts=True, max_tokens=50)
            
            if "error" in result:
                yield f'data: {json.dumps({"error": result["error"]})}\n\n'
                return
            
            response_text = result.get("ai_response", "No response")
            print(f" Response: {response_text}")
            
            # Stream in chunks that AI SDK understands
            words = response_text.split()
            
            for word in words:
                # This is the EXACT format useChat expects
                chunk = f'0:"{word} "\n'
                yield chunk
                await asyncio.sleep(0.1)
            
            # End with newline
            yield '\n'
                
        except Exception as e:
            print(f" Error: {e}")
            yield f'0:"Error: {str(e)}"\n'
    
    return StreamingResponse(
        ai_sdk_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        }
    )
    """AI SDK compatible realtime endpoint"""
    try:
        data = await request.json()
        messages = data.get("messages", [])
        last_message = messages[-1] if messages else {"content": ""}
        prompt = last_message.get("content", "")
        
        print(f"🎯 Realtime request: {prompt}")
        
        mlx_service = get_mlx_service()
        
        async def ai_sdk_stream():
            try:
                # Call your working webcam_chat method
                result = await mlx_service.webcam_chat(prompt, enable_tts=True, max_tokens=50)
                
                if "error" in result:
                    # Send error in AI SDK format
                    yield f'data: {json.dumps({"error": result["error"]})}\n\n'
                    return
                
                # Get the response
                ai_response = result.get("ai_response", "No response")
                print(f" Got response: {ai_response}")
                
                # Stream word by word in AI SDK format
                words = ai_response.split()
                accumulated_text = ""
                
                for word in words:
                    accumulated_text += word + " "
                    
                    # AI SDK expects this exact format
                    chunk_data = {
                        "id": f"msg_{uuid.uuid4().hex[:8]}",
                        "object": "chat.completion.chunk", 
                        "created": int(time.time()),
                        "model": "mlx-gemma",
                        "choices": [{
                            "index": 0,
                            "delta": {"content": word + " "},
                            "finish_reason": None
                        }]
                    }
                    
                    yield f'data: {json.dumps(chunk_data)}\n\n'
                    await asyncio.sleep(0.05)  # Smooth streaming
                
                # Send final chunk with finish_reason
                final_chunk = {
                    "id": f"msg_{uuid.uuid4().hex[:8]}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "mlx-gemma", 
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                
                yield f'data: {json.dumps(final_chunk)}\n\n'
                yield f'data: [DONE]\n\n'
                
            except Exception as e:
                print(f" Stream error: {e}")
                error_chunk = {
                    "error": {
                        "message": str(e),
                        "type": "server_error"
                    }
                }
                yield f'data: {json.dumps(error_chunk)}\n\n'
        
        return StreamingResponse(
            ai_sdk_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        print(f" Realtime endpoint error: {e}")
        return StreamingResponse(
            iter([f'data: {json.dumps({"error": str(e)})}\n\n']),
            media_type="text/plain"
        )

# Fix your /realtime endpoint to actually USE the audio you generated

@router.post("/realtime")
async def realtime_chat(request: Request) -> StreamingResponse:
    """Use the audio we already generated!"""
    data = await request.json()
    messages = data.get("messages", [])
    prompt = messages[-1]["content"] if messages else "hello"
    
    print(f"🎯 Request: {prompt}")
    
    mlx_service = get_mlx_service()
    
    async def ai_sdk_stream():
        try:
            # Get response from MLX (which INCLUDES audio!)
            result = await mlx_service.webcam_chat(prompt, enable_tts=True, max_tokens=50)
            
            if "error" in result:
                yield f'0:"Error: {result["error"]}"\n'
                return
            
            response_text = result.get("ai_response", "No response")
            print(f" Response: {response_text}")
            
            # Stream text first
            words = response_text.split()
            for word in words:
                chunk = f'0:"{word} "\n'
                yield chunk
                await asyncio.sleep(0.1)
            
            yield f'0:""\n'  # End text
            
            # NOW SEND THE AUDIO THAT'S ALREADY GENERATED!
            if result.get("audio") and result["audio"].get("success"):
                audio_b64 = result["audio"]["audio_data"]
                
                # Send audio command that frontend can catch
                audio_cmd = f'AUDIO:{audio_b64}\n'
                yield audio_cmd
                print(f"🔊 Sent audio: {len(audio_b64)} chars")
                
        except Exception as e:
            print(f" Error: {e}")
            yield f'0:"Error: {str(e)}"\n'
    
    return StreamingResponse(
        ai_sdk_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        }
    )

@router.post("/webcam")
async def webcam_chat(
    prompt: str = Form(...),
    max_tokens: int = Form(50),
    enable_tts: bool = Form(True)
) -> dict:
    """Direct webcam chat endpoint"""
    mlx_service = get_mlx_service()
    
    try:
        result = await mlx_service.webcam_chat(prompt, enable_tts, max_tokens)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image")
async def image_chat(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    max_tokens: int = Form(50),
    enable_tts: bool = Form(True)
) -> dict:
    """Chat with uploaded image"""
    mlx_service = get_mlx_service()
    
    try:
        # Read and process uploaded image
        image_data = await image.read()
        pil_image = Image.open(BytesIO(image_data))
        
        # Process with MLX-VLM
        ai_response = mlx_service.process_image_chat(pil_image, prompt, max_tokens)
        
        result = {
            "ai_response": ai_response,
            "prompt": prompt,
            "image_filename": image.filename
        }
        
        # Generate TTS if enabled
        if enable_tts and ai_response and not ai_response.startswith("Error"):
            tts_result = mlx_service._generate_tts(ai_response, "am_michael")
            result["audio"] = tts_result
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audio")
async def audio_chat(
    audio_files: List[UploadFile] = File(...),
    prompt: str = Form(...),
    max_tokens: int = Form(50),
    enable_tts: bool = Form(True)
) -> dict:
    """Chat with uploaded audio files"""
    mlx_service = get_mlx_service()
    
    try:
        # Save uploaded audio files temporarily
        audio_paths = []
        for audio_file in audio_files:
            temp_path = f"temp_{audio_file.filename}"
            with open(temp_path, "wb") as f:
                content = await audio_file.read()
                f.write(content)
            audio_paths.append(temp_path)
        
        # Process with MLX-VLM audio support
        ai_response = mlx_service.process_audio_chat(audio_paths, prompt, max_tokens)
        
        result = {
            "ai_response": ai_response,
            "prompt": prompt,
            "audio_files": [f.filename for f in audio_files]
        }
        
        # Generate TTS if enabled
        if enable_tts and ai_response and not ai_response.startswith("Error"):
            tts_result = mlx_service._generate_tts(ai_response, "am_michael")
            result["audio"] = tts_result
        
        # Cleanup temp files
        for path in audio_paths:
            if os.path.exists(path):
                os.remove(path)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/multimodal")
async def multimodal_chat(
    image: UploadFile = File(...),
    audio_files: List[UploadFile] = File(...),
    prompt: str = Form(...),
    max_tokens: int = Form(50),
    enable_tts: bool = Form(True)
) -> dict:
    """Chat with both image and audio"""
    mlx_service = get_mlx_service()
    
    try:
        # Process image
        image_data = await image.read()
        pil_image = Image.open(BytesIO(image_data))
        
        # Process audio files
        audio_paths = []
        for audio_file in audio_files:
            temp_path = f"temp_{audio_file.filename}"
            with open(temp_path, "wb") as f:
                content = await audio_file.read()
                f.write(content)
            audio_paths.append(temp_path)
        
        # Process with multimodal MLX
        ai_response = mlx_service.process_multimodal_chat(pil_image, audio_paths, prompt, max_tokens)
        
        result = {
            "ai_response": ai_response,
            "prompt": prompt,
            "image_filename": image.filename,
            "audio_files": [f.filename for f in audio_files]
        }
        
        # Generate TTS if enabled
        if enable_tts and ai_response and not ai_response.startswith("Error"):
            tts_result = mlx_service._generate_tts(ai_response, "am_michael")
            result["audio"] = tts_result
        
        # Cleanup
        for path in audio_paths:
            if os.path.exists(path):
                os.remove(path)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    voice: str = Form("am_michael"),
    speed: float = Form(1.2)
) -> dict:
    """Generate speech from text"""
    mlx_service = get_mlx_service()
    
    try:
        result = mlx_service._generate_tts(text, voice)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cameras")
async def get_available_cameras():
    """Get info about available cameras"""
    try:
        mlx_service = get_mlx_service()
        cameras = mlx_service.get_camera_info()
        return {"cameras": cameras}
    except Exception as e:
        return {"error": str(e), "cameras": []}

@router.get("/health")
async def health_check():
    """Check MLX service health"""
    try:
        mlx_service = get_mlx_service()
        return {
            "status": "healthy",
            "vlm_loaded": mlx_service.vlm_model is not None,
            "webcam_available": mlx_service.webcam is not None
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve generated audio files"""
    import os
    
    # Security: only allow .wav files
    if not filename.endswith('.wav'):
        raise HTTPException(status_code=400, detail="Only .wav files allowed")
    
    # Look for the file in common locations
    possible_paths = [
        filename,
        f"./{filename}",
        f"backend/{filename}",
        f"backend/app/{filename}",
        os.path.expanduser(f"~/.mlx_audio/outputs/{filename}"),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.getcwd(), "app", filename)
    ]
    
    for file_path in possible_paths:
        if os.path.exists(file_path):
            print(f" Serving audio file from: {file_path}")
            return FileResponse(
                file_path,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f"inline; filename={filename}",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
    
    # Debug: list files in current directory
    print(f" Audio file {filename} not found. Available .wav files:")
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith('.wav'):
                print(f"  - {os.path.join(root, file)}")
    
    raise HTTPException(status_code=404, detail=f"Audio file {filename} not found")