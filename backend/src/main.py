"""
Semantic Video Search API

Production-grade FastAPI application for semantic video search.
Upload videos, index them with AI embeddings, and search using natural language.
"""

import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .config import get_settings, SUPPORTED_VIDEO_FORMATS
from .models import (
    UploadResponse,
    JobStatusResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    HealthResponse,
    ErrorResponse,
    JobStatus,
    ResultType
)
from .utils import validate_file_extension, get_safe_filename, generate_video_id


# ===========================================
# Application Setup
# ===========================================

app = FastAPI(
    title="VideoSearch AI API",
    description="Semantic search for video content using Groq Vision/Audio and Qdrant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logger.add(
    "logs/api_{time}.log",
    rotation="100 MB",
    retention="7 days",
    level="INFO"
)


# ===========================================
# Dependency Injection (Lazy Loading)
# ===========================================

def get_services():
    """Lazy load services to avoid import-time initialization."""
    from .vector_db import get_vector_db
    from .ai_service import get_ai_service
    from .job_queue import get_job_queue
    return get_vector_db(), get_ai_service(), get_job_queue()


# ===========================================
# API Endpoints
# ===========================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Semantic Video Search API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Check health of all services.
    
    Returns status of Qdrant and Redis connections.
    """
    try:
        vector_db, _, job_queue = get_services()
        
        return HealthResponse(
            status="healthy",
            qdrant=vector_db.health_check(),
            redis=job_queue.health_check(),
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            qdrant=False,
            redis=False,
            timestamp=datetime.utcnow()
        )


@app.post("/upload", response_model=UploadResponse, tags=["Videos"])
async def upload_video(
    file: UploadFile = File(..., description="Video file to upload"),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a video for semantic indexing.
    
    The video will be processed in the background. Use the returned
    job_id to track progress via the /status endpoint.
    
    Supported formats: MP4, AVI, MOV, MKV, WebM
    Maximum size: 500MB (configurable)
    """
    settings = get_settings()
    
    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {SUPPORTED_VIDEO_FORMATS}"
        )
    
    # Generate IDs
    video_id = generate_video_id()
    safe_filename = get_safe_filename(file.filename)
    file_path = settings.upload_dir / f"{video_id}_{safe_filename}"
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.max_video_size_mb:
            file_path.unlink()  # Clean up
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size_mb:.1f}MB. Maximum: {settings.max_video_size_mb}MB"
            )
        
        # Enqueue processing job
        _, _, job_queue = get_services()
        job_id = job_queue.enqueue_video_processing(video_id, str(file_path))
        
        logger.info(f"Uploaded video: {video_id} ({file_size_mb:.1f}MB)")
        
        return UploadResponse(
            job_id=job_id,
            video_id=video_id,
            status=JobStatus.PENDING,
            message=f"Video uploaded successfully ({file_size_mb:.1f}MB). Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        # Clean up on failure
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/status/{video_id}", response_model=JobStatusResponse, tags=["Videos"])
async def get_job_status(video_id: str):
    """
    Get the processing status of a video.
    
    Returns progress percentage, frames processed, and any errors.
    """
    _, _, job_queue = get_services()
    
    status = job_queue.get_job_status(video_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(
        job_id=status.get("job_id", ""),
        video_id=video_id,
        status=JobStatus(status.get("status", "pending")),
        progress=status.get("progress", 0.0),
        frames_processed=status.get("frames_processed", 0),
        total_frames=status.get("total_frames", 0),
        created_at=datetime.fromisoformat(status.get("created_at", datetime.utcnow().isoformat())),
        updated_at=datetime.fromisoformat(status.get("updated_at", datetime.utcnow().isoformat())),
        error=status.get("error")
    )


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_video(request: SearchRequest):
    """
    Search for moments in a video using natural language.
    
    Returns timestamps with confidence scores where the query matches
    visual content or spoken words.
    """
    vector_db, ai_service, _ = get_services()
    
    try:
        # Generate query embedding
        query_embedding = ai_service.get_query_embedding(request.query)
        
        # Search vector database
        raw_results = vector_db.search(
            query_embedding=query_embedding,
            video_id=request.video_id,
            top_k=request.top_k
        )
        
        # Format results
        results = []
        for r in raw_results:
            results.append(SearchResult(
                timestamp=r["timestamp"],
                score=r["score"],
                type=ResultType(r["type"]),
                thumbnail_url=f"/thumbnails/{Path(r['thumbnail_path']).name}" if r.get("thumbnail_path") else None,
                transcript_snippet=r.get("text")
            ))
        
        return SearchResponse(
            query=request.query,
            video_id=request.video_id,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/video/{video_id}", tags=["Videos"])
async def get_video(video_id: str):
    """
    Stream a video file.
    
    Returns the video file for playback.
    """
    settings = get_settings()
    
    # Find video file
    for file in settings.upload_dir.iterdir():
        if file.name.startswith(video_id) and file.is_file():
            return FileResponse(
                file,
                media_type="video/mp4",
                filename=file.name
            )
    
    raise HTTPException(status_code=404, detail="Video not found")


@app.delete("/video/{video_id}", tags=["Videos"])
async def delete_video(video_id: str):
    """
    Delete a video and its indexed data.
    
    Removes the video file and all associated embeddings.
    """
    settings = get_settings()
    vector_db, _, _ = get_services()
    
    try:
        # Delete from vector DB
        deleted_points = vector_db.delete_video(video_id)
        
        # Delete video file
        deleted_file = False
        for file in settings.upload_dir.iterdir():
            if file.name.startswith(video_id):
                file.unlink()
                deleted_file = True
        
        # Delete thumbnails
        for thumb in settings.thumbnails_dir.iterdir():
            if thumb.name.startswith(video_id):
                thumb.unlink()
        
        return {
            "message": "Video deleted successfully",
            "video_id": video_id,
            "points_deleted": deleted_points,
            "file_deleted": deleted_file
        }
        
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


# ===========================================
# Static Files (Thumbnails)
# ===========================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    settings = get_settings()
    
    # Ensure directories exist
    settings.upload_dir.mkdir(exist_ok=True)
    settings.thumbnails_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(exist_ok=True)
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    logger.info("Semantic Video Search API started")


# Mount static files for thumbnails
@app.on_event("startup")
async def mount_static():
    settings = get_settings()
    app.mount(
        "/thumbnails",
        StaticFiles(directory=str(settings.thumbnails_dir)),
        name="thumbnails"
    )


# ===========================================
# Error Handlers
# ===========================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc) if os.getenv("DEBUG") else None
        ).model_dump()
    )
