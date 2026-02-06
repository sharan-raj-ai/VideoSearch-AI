"""
Pydantic Models for API Request/Response Schemas

Defines all data structures used in the API with validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


# ===========================================
# Enums
# ===========================================

class JobStatus(str, Enum):
    """Status of a video processing job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResultType(str, Enum):
    """Type of search result (visual frame or audio transcript)."""
    VISUAL = "visual"
    AUDIO = "audio"


# ===========================================
# Request Models
# ===========================================

class SearchRequest(BaseModel):
    """Request body for video search."""
    video_id: str = Field(..., description="ID of the video to search")
    query: str = Field(..., min_length=1, max_length=500, description="Natural language search query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")


# ===========================================
# Response Models
# ===========================================

class UploadResponse(BaseModel):
    """Response after video upload."""
    job_id: str = Field(..., description="Unique job ID for tracking")
    video_id: str = Field(..., description="Unique video ID")
    status: JobStatus = Field(default=JobStatus.PENDING)
    message: str = Field(default="Video uploaded successfully. Processing started.")


class JobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str
    video_id: str
    status: JobStatus
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress from 0 to 1")
    frames_processed: int = Field(default=0)
    total_frames: int = Field(default=0)
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = Field(default=None, description="Error message if failed")


class SearchResult(BaseModel):
    """Single search result with timestamp and confidence."""
    timestamp: float = Field(..., description="Timestamp in seconds")
    score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    type: ResultType = Field(..., description="Whether match is visual or audio")
    thumbnail_url: Optional[str] = Field(default=None, description="URL to frame thumbnail")
    transcript_snippet: Optional[str] = Field(default=None, description="Transcript text if audio match")


class SearchResponse(BaseModel):
    """Response for search query."""
    query: str
    video_id: str
    results: List[SearchResult] = Field(default_factory=list)
    total_results: int = Field(default=0)


class HealthResponse(BaseModel):
    """Response for health check endpoint."""
    status: str = Field(default="healthy")
    qdrant: bool = Field(default=False, description="Qdrant connection status")
    redis: bool = Field(default=False, description="Redis connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===========================================
# Internal Models (not exposed via API)
# ===========================================

class VideoMetadata(BaseModel):
    """Metadata extracted from uploaded video."""
    video_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_path: str
    duration_seconds: float
    width: int
    height: int
    fps: float
    has_audio: bool
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FrameData(BaseModel):
    """Data for a single extracted frame."""
    video_id: str
    timestamp: float
    frame_path: str
    thumbnail_path: Optional[str] = None
    embedding: Optional[List[float]] = None


class TranscriptSegment(BaseModel):
    """Data for a single transcript segment."""
    video_id: str
    start_time: float
    end_time: float
    text: str
    embedding: Optional[List[float]] = None
