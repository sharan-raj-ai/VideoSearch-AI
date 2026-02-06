"""
AI Service Module (Free Tier Stack - Groq Vision Update)

Handles AI/ML operations using free tier APIs:
- Vision: Groq API (meta-llama/llama-4-scout-17b-16e-instruct)
- Embeddings: Jina AI API (jina-embeddings-v3)
- Audio: Groq API (whisper-large-v3)

Includes retry logic and graceful error handling.
"""

import base64
import time
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import get_settings, EMBEDDING_BATCH_SIZE


class AIServiceError(Exception):
    """Raised when AI service operations fail."""
    pass


class AIService:
    """
    Handles AI operations using free tier cloud APIs.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.http_client = httpx.Client(timeout=60.0)
        logger.info("AI Service initialized with Free Tier Stack (Groq Vision/Audio + Jina)")
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    def get_image_embedding(self, image_path: str) -> List[float]:
        """
        Generate embedding for an image.
        1. Get detailed description using Groq Llama 4 Scout (Vision)
        2. Embed description using Jina AI
        """
        path = Path(image_path)
        if not path.exists():
            raise AIServiceError(f"Image not found: {image_path}")
            
        try:
            # Step 1: Get Description from Groq Vision
            description = self._get_image_description_groq(image_path)
            
            # Step 2: Embed Description with Jina
            return self.get_text_embedding(description)
            
        except Exception as e:
            logger.error(f"Image processed failed for {image_path}: {e}")
            raise AIServiceError(f"Failed to process image: {e}")

    def _get_image_description_groq(self, image_path: str) -> str:
        """Get image description using Groq Vision (Llama 4 Scout)."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        
        payload = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail, focusing on the main subjects, actions, and environment."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            "max_tokens": 300
        }
        
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.http_client.post(url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Groq Vision failed: {e}")
            # Fallback to Jina embedding of empty string or generic placeholder is bad.
            # But better to fail here so we know vision is broken.
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    def get_text_embedding(self, text: str) -> List[float]:
        """Generate embedding using Jina AI."""
        if not text or not text.strip():
            raise AIServiceError("Cannot embed empty text")
            
        url = "https://api.jina.ai/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.settings.jina_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "jina-embeddings-v3",
            "task": "retrieval.passage",
            "dimensions": 1024,
            "late_chunking": False,
            "embedding_type": "float",
            "input": [text]
        }
        
        try:
            response = self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Jina embedding failed: {e}")
            raise AIServiceError(f"Failed to generate embedding: {e}")

    def get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query (optimized for retrieval)."""
        if not query or not query.strip():
            raise AIServiceError("Cannot embed empty query")
            
        url = "https://api.jina.ai/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.settings.jina_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "jina-embeddings-v3",
            "task": "retrieval.query", # Optimized task for queries
            "dimensions": 1024,
            "embedding_type": "float",
            "input": [query]
        }
        
        try:
            response = self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise AIServiceError(f"Failed to generate query embedding: {e}")

    def get_batch_image_embeddings(
        self,
        image_paths: List[str],
        on_progress: Optional[callable] = None
    ) -> List[Tuple[str, List[float]]]:
        """Generate embeddings for multiple images with progress tracking."""
        results = []
        total = len(image_paths)
        
        for i, path in enumerate(image_paths):
            try:
                embedding = self.get_image_embedding(path)
                results.append((path, embedding))
            except Exception as e:
                logger.warning(f"Skipping image {path}: {e}")
                continue
            
            if on_progress:
                on_progress(i + 1, total)
            
            # Gentle rate limiting
            time.sleep(0.5) 
            
        return results

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    def transcribe_audio(self, audio_path: str) -> List[dict]:
        """Transcribe audio using Groq Whisper."""
        path = Path(audio_path)
        if not path.exists():
            raise AIServiceError(f"Audio file not found: {audio_path}")
            
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key}"
        }
        
        try:
            with open(path, "rb") as f:
                files = {"file": (path.name, f, "audio/wav")}
                data = {
                    "model": "whisper-large-v3",
                    "response_format": "verbose_json", # Needed for timestamps
                    "temperature": 0.0
                }
                
                # Note: httpx.post with files doesn't need content-type header, it sets it up
                response = self.http_client.post(url, headers=headers, files=files, data=data)
                response.raise_for_status()
                result = response.json()
                
                # Parse Groq/Whisper verbose_json output to segments
                segments = []
                for seg in result.get("segments", []):
                    segments.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": seg["text"].strip()
                    })
                    
                return segments
                
        except Exception as e:
            logger.error(f"Transcription failed for {audio_path}: {e}")
            raise AIServiceError(f"Failed to transcribe audio: {e}")


# Singleton instance
_service: Optional[AIService] = None

def get_ai_service() -> AIService:
    """Get or create AIService instance."""
    global _service
    if _service is None:
        _service = AIService()
    return _service
