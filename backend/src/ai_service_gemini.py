"""
AI Service Module

Handles all AI/ML operations using Google Gemini API:
- Image embeddings (for visual search)
- Text embeddings (for query matching)
- Audio transcription with timestamps

Includes retry logic and rate limit handling for production reliability.
"""

import base64
import time
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from .config import get_settings, EMBEDDING_BATCH_SIZE


class AIServiceError(Exception):
    """Raised when AI service operations fail."""
    pass


class AIService:
    """
    Handles AI operations using Google Gemini API.
    
    Features:
    - Automatic retry with exponential backoff
    - Batch processing to avoid rate limits
    - Graceful error handling
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._configure_gemini()
        
    def _configure_gemini(self) -> None:
        """Configure Gemini API client."""
        genai.configure(api_key=self.settings.gemini_api_key)
        
        # Initialize models
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash')
        self.embedding_model = 'models/gemini-embedding-001'
        
        logger.info("Gemini API configured successfully")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable))
    )
    def get_image_embedding(self, image_path: str) -> List[float]:
        """
        Generate embedding for an image using Gemini.
        
        Gemini doesn't have direct image embeddings, so we:
        1. Generate a detailed description of the image
        2. Embed that description
        
        This approach enables semantic search on visual content.
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of floats representing the embedding
        """
        path = Path(image_path)
        if not path.exists():
            raise AIServiceError(f"Image not found: {image_path}")
        
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Create image part for Gemini
            image_part = {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_data).decode()
            }
            
            # Generate detailed description
            prompt = """Describe this image in detail. Include:
            - Main subjects/objects visible
            - Actions or activities happening
            - Colors, lighting, environment
            - Any text visible
            - Overall scene/context
            
            Be specific and descriptive. Output only the description, no preamble."""
            
            response = self.vision_model.generate_content([prompt, image_part])
            description = response.text.strip()
            
            # Now embed the description
            embedding = self.get_text_embedding(description)
            
            return embedding
            
        except google_exceptions.InvalidArgument as e:
            raise AIServiceError(f"Invalid image: {e}")
        except Exception as e:
            logger.error(f"Image embedding failed for {image_path}: {e}")
            raise AIServiceError(f"Failed to generate image embedding: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable))
    )
    def get_text_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            raise AIServiceError("Cannot embed empty text")
        
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Text embedding failed: {e}")
            raise AIServiceError(f"Failed to generate text embedding: {e}")
    
    def get_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Uses retrieval_query task type for better search matching.
        
        Args:
            query: Search query text
            
        Returns:
            List of floats representing the embedding
        """
        if not query or not query.strip():
            raise AIServiceError("Cannot embed empty query")
        
        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Query embedding failed: {e}")
            raise AIServiceError(f"Failed to generate query embedding: {e}")
    
    def get_batch_image_embeddings(
        self,
        image_paths: List[str],
        on_progress: Optional[callable] = None
    ) -> List[Tuple[str, List[float]]]:
        """
        Generate embeddings for multiple images with progress tracking.
        
        Processes in batches to avoid rate limits.
        
        Args:
            image_paths: List of image file paths
            on_progress: Optional callback(processed, total) for progress updates
            
        Returns:
            List of (image_path, embedding) tuples
        """
        results = []
        total = len(image_paths)
        
        for i, path in enumerate(image_paths):
            try:
                embedding = self.get_image_embedding(path)
                results.append((path, embedding))
            except AIServiceError as e:
                logger.warning(f"Skipping image {path}: {e}")
                continue
            
            # Progress callback
            if on_progress:
                on_progress(i + 1, total)
            
            # Rate limiting: pause between batches
            if (i + 1) % EMBEDDING_BATCH_SIZE == 0:
                logger.debug(f"Processed {i + 1}/{total} images, pausing...")
                time.sleep(1)  # Respect rate limits
        
        return results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable))
    )
    def transcribe_audio(self, audio_path: str) -> List[dict]:
        """
        Transcribe audio file with timestamps.
        
        Args:
            audio_path: Path to audio file (WAV format)
            
        Returns:
            List of transcript segments with timestamps:
            [{"start": 0.0, "end": 5.0, "text": "Hello world"}, ...]
        """
        path = Path(audio_path)
        if not path.exists():
            raise AIServiceError(f"Audio file not found: {audio_path}")
        
        try:
            # Upload audio file to Gemini
            audio_file = genai.upload_file(audio_path)
            
            # Wait for file to be processed
            while audio_file.state.name == "PROCESSING":
                time.sleep(1)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                raise AIServiceError("Audio file processing failed")
            
            # Transcribe with timestamp request
            prompt = """Transcribe this audio with timestamps.
            
            Output format (one segment per line):
            [START_TIME - END_TIME] Transcribed text here
            
            Example:
            [0.0 - 3.5] Hello, welcome to the presentation.
            [3.5 - 7.2] Today we'll discuss our quarterly results.
            
            Be accurate with timestamps and transcription."""
            
            response = self.vision_model.generate_content([prompt, audio_file])
            
            # Parse response into segments
            segments = self._parse_transcript_response(response.text)
            
            # Clean up uploaded file
            genai.delete_file(audio_file.name)
            
            return segments
            
        except Exception as e:
            logger.error(f"Transcription failed for {audio_path}: {e}")
            raise AIServiceError(f"Failed to transcribe audio: {e}")
    
    def _parse_transcript_response(self, response_text: str) -> List[dict]:
        """Parse Gemini's transcript response into structured segments."""
        segments = []
        
        for line in response_text.strip().split("\n"):
            line = line.strip()
            if not line or not line.startswith("["):
                continue
            
            try:
                # Parse [START - END] text format
                bracket_end = line.find("]")
                if bracket_end == -1:
                    continue
                
                time_part = line[1:bracket_end]
                text_part = line[bracket_end + 1:].strip()
                
                if " - " in time_part:
                    start_str, end_str = time_part.split(" - ")
                    start_time = float(start_str.strip())
                    end_time = float(end_str.strip())
                    
                    if text_part:
                        segments.append({
                            "start": start_time,
                            "end": end_time,
                            "text": text_part
                        })
            except (ValueError, IndexError) as e:
                logger.debug(f"Could not parse transcript line: {line}")
                continue
        
        return segments


# Singleton instance
_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create AIService instance."""
    global _service
    if _service is None:
        _service = AIService()
    return _service
