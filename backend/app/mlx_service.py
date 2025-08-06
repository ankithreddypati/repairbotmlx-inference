# app/mlx_service.py
import cv2
import os
import base64
import asyncio
import concurrent.futures
from typing import Optional, List, AsyncGenerator
from PIL import Image
import numpy as np
import uuid
import tempfile
import time
import re
import aiohttp
from dotenv import load_dotenv

load_dotenv()

class MLXService:
    def __init__(self):
        self.vlm_model = None
        self.vlm_processor = None
        self.vlm_config = None
        self.webcam = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        # Simple robot integration (optional)
        self.robot_ip = os.getenv("ROBOT_IP")  
        self.robot_port = os.getenv("ROBOT_PORT")      
        self.available_actions = ["pass_screwdriver"]
        
        self.load_models()
        self.init_webcam()
    
    def load_models(self):
        """Load MLX models"""
        try:
            from mlx_vlm import load, generate
            from mlx_vlm.prompt_utils import apply_chat_template
            from mlx_vlm.utils import load_config
            from mlx_audio.tts.generate import generate_audio
            
            print("🔄 Loading MLX models...")
            
            model_path = "mlx-community/gemma-3n-E2B-it-4bit"
            self.vlm_model, self.vlm_processor = load(model_path)
            self.vlm_config = load_config(model_path)
            
            self.generate_vlm = generate
            self.apply_chat_template = apply_chat_template
            self.generate_audio_fn = generate_audio
            
            print(" MLX models loaded successfully")
            
        except Exception as e:
            print(f" Failed to load MLX models: {e}")
            raise e
    
    def init_webcam(self):
        """Initialize webcam - Camera 1 for AI"""
        try:
            # Use camera index 1 for AI processing (backend) - CORRECT
            self.webcam = cv2.VideoCapture(1)
            if self.webcam.isOpened():
                self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.webcam.set(cv2.CAP_PROP_FPS, 30)
                self.webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                print(" Webcam initialized at index 1 (AI processing)")
            else:
                print("⚠️ Camera index 1 not available, trying index 0")
                self.webcam = cv2.VideoCapture(0)
                if self.webcam.isOpened():
                    self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    self.webcam.set(cv2.CAP_PROP_FPS, 30)
                    self.webcam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    print(" Webcam initialized at index 0 (fallback)")
                else:
                    print(" No webcam available")
                    self.webcam = None
        except Exception as e:
            print(f"⚠️ Webcam initialization failed: {e}")
            self.webcam = None
    
    def clean_response_text(self, text: str) -> str:
        """Clean response text - remove asterisks and formatting"""
        text = re.sub(r'\*+', '', text)  # Remove asterisks
        text = re.sub(r'#+', '', text)   # Remove hashtags
        text = re.sub(r'_+', '', text)   # Remove underscores
        text = re.sub(r'\s+', ' ', text) # Remove extra whitespace
        text = text.strip()
        
        # Remove robot commands from user text
        text = re.sub(r'ROBOT_ACTION:.*', '', text).strip()
        
        # Keep first sentence only
        sentences = re.split(r'[.!?]+', text)
        if sentences and sentences[0].strip():
            clean_text = sentences[0].strip()
            if not clean_text.endswith(('.', '!', '?')):
                clean_text += '.'
            return clean_text
        
        return text
    
    def extract_robot_action(self, ai_response: str) -> Optional[str]:
        """Extract robot action from AI response - LLM decides"""
        if "ROBOT_ACTION:" in ai_response:
            match = re.search(r'ROBOT_ACTION:\s*(\w+)', ai_response)
            if match:
                action = match.group(1)
                if action in self.available_actions:
                    return action
        return None
    
    async def send_robot_task(self, task_name: str) -> dict:
        """Send task to robot machine over WiFi - only if robot configured"""
        if not self.robot_ip or not self.robot_port:
            print("🤖 Robot not configured (no IP/port)")
            return {"success": False, "error": "Robot not configured"}
            
        try:
            payload = {"task": task_name}
            robot_url = f"http://{self.robot_ip}:{self.robot_port}/trigger"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(robot_url, json=payload, timeout=5) as response:
                    if response.status == 200:
                        print(f"🤖 Robot task sent to {self.robot_ip}: {task_name}")
                        return {"success": True, "task": task_name}
                    else:
                        print(f" Robot failed: HTTP {response.status}")
                        return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f" Robot unreachable at {self.robot_ip}: {e}")
            return {"success": False, "error": str(e)}
    
    async def async_webcam_capture(self) -> Optional[Image.Image]:
        """Async webcam capture"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self.capture_current_frame)
    
    def capture_current_frame(self) -> Optional[Image.Image]:
        """Capture webcam frame"""
        if not self.webcam or not self.webcam.isOpened():
            return None
        
        for _ in range(3):  # Get latest frame
            ret, frame = self.webcam.read()
            if not ret:
                return None
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
    
    async def async_multimodal_chat_streaming(self, image: Image.Image, prompt: str, max_tokens: int = 50) -> AsyncGenerator[str, None]:
        """Stream multimodal response"""
        try:
            print(f"👤 User prompt: '{prompt}'")
            
            loop = asyncio.get_event_loop()
            
            def process_vlm():
                formatted_prompt = self.apply_chat_template(
                    self.vlm_processor, 
                    self.vlm_config, 
                    prompt,  # USER'S TEXT
                    num_images=1
                )
                
                response = self.generate_vlm(
                    self.vlm_model, 
                    self.vlm_processor, 
                    formatted_prompt, 
                    [image],  # Webcam image
                    verbose=False,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                return response
            
            response = await loop.run_in_executor(self.executor, process_vlm)
            
            # Get and clean text
            if hasattr(response, 'text'):
                full_text = response.text
            elif isinstance(response, str):
                full_text = response
            else:
                full_text = str(response)
            
            clean_text = self.clean_response_text(full_text)
            print(f"🤖 Original: {full_text}")
            print(f"🧹 Cleaned: {clean_text}")
            
            # Stream clean text
            words = clean_text.split(' ')
            for word in words:
                yield word + ' '
                await asyncio.sleep(0.02)
                    
        except Exception as e:
            print(f" Multimodal error: {e}")
            yield f"Error: {str(e)}"
    
    async def async_text_to_speech_streaming(self, text: str, voice: str = "am_michael") -> AsyncGenerator[dict, None]:
        """Generate TTS"""
        try:
            print(f"🔊 TTS input: '{text}'")
            
            loop = asyncio.get_event_loop()
            
            chunk_result = await loop.run_in_executor(
                self.executor, 
                self._generate_tts, 
                text, voice
            )
            
            if chunk_result["success"]:
                yield {
                    "audio_data": chunk_result["audio_data"],
                    "chunk_index": 0,
                    "is_final": True,
                    "text": text,
                    "duration": chunk_result.get("duration", 0)
                }
            else:
                print(f" TTS failed: {chunk_result.get('error')}")
                
        except Exception as e:
            print(f" TTS error: {e}")
    
    def _generate_tts(self, text: str, voice: str) -> dict:
        """Generate TTS"""
        try:
            chunk_id = f"tts_{uuid.uuid4().hex[:8]}"
            
            result = self.generate_audio_fn(
                text=text,
                model_path="prince-canuma/Kokoro-82M",
                voice=voice,
                speed=1.2,
                lang_code="a",
                file_prefix=chunk_id,
                audio_format="wav",
                sample_rate=22050,
                join_audio=True,
                verbose=False
            )
            
            # Find file
            possible_paths = [
                f"{chunk_id}.wav",
                f"./{chunk_id}.wav", 
                os.path.expanduser(f"~/.mlx_audio/outputs/{chunk_id}.wav")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        audio_data = f.read()
                        audio_b64 = base64.b64encode(audio_data).decode()
                    
                    try:
                        import wave
                        with wave.open(path, 'rb') as wav:
                            duration = wav.getnframes() / wav.getframerate()
                    except:
                        duration = len(text) * 0.1
                    
                    try:
                        os.remove(path)
                    except:
                        pass
                    
                    print(f" TTS generated: {len(audio_data)} bytes, {duration:.1f}s")
                    
                    return {
                        "success": True,
                        "audio_data": audio_b64,
                        "duration": duration,
                        "text": text
                    }
            
            return {"success": False, "error": "Audio file not found"}
            
        except Exception as e:
            print(f" TTS error: {e}")
            return {"success": False, "error": str(e)}
    
    async def webcam_chat(self, prompt: str, enable_tts: bool = True, max_tokens: int = 50) -> dict:
        """Webcam chat - Gemma 3n format with instructions in user prompt"""
        image = self.capture_current_frame()
        if not image:
            return {"error": "Failed to capture webcam frame"}
        
        try:
            print(f"👤 User: '{prompt}'")
            
            # Gemma 3n format: system instructions at the start of user prompt
            gemma_prompt = f"""You are LeRepairBot, a professional repair assistant. You can see through cameras and help with electronics repair. Be concise and practical use the image only if its useful according to user commamd.

{prompt}"""
            
            formatted_prompt = self.apply_chat_template(
                self.vlm_processor, 
                self.vlm_config, 
                gemma_prompt,  # Instructions + user question in one prompt
                num_images=1
            )
            
            response = self.generate_vlm(
                self.vlm_model, 
                self.vlm_processor, 
                formatted_prompt, 
                [image],
                verbose=False,  
                max_tokens=max_tokens,
                temperature=0.6
            )
            
            if hasattr(response, 'text'):
                ai_response = response.text
            elif isinstance(response, str):
                ai_response = response
            else:
                ai_response = str(response)
            
            # Clean response for user
            clean_response = self.clean_response_text(ai_response)
            print(f"🤖 AI: '{clean_response}'")
            
            result = {
                "ai_response": clean_response,
                "prompt": prompt,
                "has_webcam": True
            }
            
            # Generate TTS
            if enable_tts and clean_response:
                tts_result = self._generate_tts(clean_response, "am_michael")
                result["audio"] = tts_result
            
            return result
            
        except Exception as e:
            print(f" Chat error: {e}")
            return {"error": str(e)}
    
    def process_image_chat(self, image: Image.Image, prompt: str, max_tokens: int = 50) -> str:
        """Process image + text with VLM"""
        try:
            formatted_prompt = self.apply_chat_template(
                self.vlm_processor, 
                self.vlm_config, 
                prompt,
                num_images=1
            )
            
            response = self.generate_vlm(
                self.vlm_model, 
                self.vlm_processor, 
                formatted_prompt, 
                [image],
                verbose=False,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if hasattr(response, 'text'):
                return self.clean_response_text(response.text)
            else:
                return self.clean_response_text(str(response))
                
        except Exception as e:
            print(f" Image chat error: {e}")
            return f"Error processing image: {str(e)}"

    def process_audio_chat(self, audio_paths: List[str], prompt: str, max_tokens: int = 50) -> str:
        """Process audio files - placeholder"""
        return f"Audio processing not implemented. Text prompt: {prompt}"

    def process_multimodal_chat(self, image: Image.Image, audio_paths: List[str], prompt: str, max_tokens: int = 50) -> str:
        """Process image + audio + text"""
        return self.process_image_chat(image, prompt, max_tokens)
    
    def cleanup(self):
        """Cleanup"""
        if self.webcam:
            self.webcam.release()
            print("🧹 Webcam released")
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
            print("🧹 Thread pool cleaned up")

    def get_camera_info(self):
        """Get info about available cameras"""
        cameras = []
        for i in range(4):  # Check first 4 camera indices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                cameras.append({
                    "index": i,
                    "width": int(width),
                    "height": int(height)
                })
                cap.release()
        return cameras

# Global service
mlx_service = None

def get_mlx_service() -> MLXService:
    global mlx_service
    if mlx_service is None:
        mlx_service = MLXService()
    return mlx_service