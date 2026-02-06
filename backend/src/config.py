"""
Configuration Management for Semantic Video Search

Loads and validates environment variables with sensible defaults.
Uses pydantic-settings for type-safe configuration.
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ===========================================
    # API Keys (Free Tier Stack)
    # ===========================================
    huggingface_api_key: str = Field(..., description="Hugging Face API Key")
    groq_api_key: str = Field(..., description="Groq API Key")
    jina_api_key: str = Field(..., description="Jina AI API Key")
    
    # ===========================================
    # Infrastructure
    # ===========================================
    qdrant_host: str = Field(default="localhost", description="Qdrant server host")
    qdrant_port: int = Field(default=6333, description="Qdrant server port")
    redis_host: str = Field(default="localhost", description="Redis server host")
    redis_port: int = Field(default=6380, description="Redis server port")
    
    # ===========================================
    # Application Settings
    # ===========================================
    max_video_size_mb: int = Field(default=500, description="Max video size in MB")
    frame_extraction_fps: float = Field(default=1.0, description="Frames per second to extract")
    min_search_score: float = Field(default=0.15, description="Minimum search score threshold")
    
    # ===========================================
    # Logging
    # ===========================================
    log_level: str = Field(default="INFO", description="Logging level")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # ===========================================
    # Paths (computed at runtime)
    # ===========================================
    @property
    def base_dir(self) -> Path:
        """Base directory of the backend."""
        return Path(__file__).parent.parent
    
    @property
    def upload_dir(self) -> Path:
        """Directory for uploaded videos."""
        path = self.base_dir / "uploads"
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def temp_dir(self) -> Path:
        """Directory for temporary processing files."""
        path = self.base_dir / "temp"
        path.mkdir(exist_ok=True)
        return path
    
    @property
    def thumbnails_dir(self) -> Path:
        """Directory for video thumbnails."""
        path = self.base_dir / "thumbnails"
        path.mkdir(exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures we only load settings once.
    """
    return Settings()


# ===========================================
# Constants
# ===========================================

# Qdrant collection name for video embeddings
COLLECTION_NAME = "video_embeddings"

# Embedding dimension for Jina embeddings v3
EMBEDDING_DIMENSION = 1024

# Supported video formats
SUPPORTED_VIDEO_FORMATS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# Batch size for embedding generation
EMBEDDING_BATCH_SIZE = 10
