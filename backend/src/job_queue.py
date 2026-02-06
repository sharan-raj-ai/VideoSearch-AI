"""
Job Queue Module

Handles background video processing using Redis Queue (RQ).
Features:
- Persistent job storage
- Progress tracking
- Error recovery
"""

import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger
import redis
from rq import Queue, Worker
from rq.job import Job

from .config import get_settings


class JobQueueError(Exception):
    """Raised when job queue operations fail."""
    pass


class JobQueue:
    """
    Manages background video processing jobs.
    
    Uses Redis for persistence and RQ for job execution.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_conn = self._connect_redis()
        self.queue = Queue(connection=self.redis_conn)
    
    def _connect_redis(self) -> redis.Redis:
        """Establish connection to Redis."""
        try:
            conn = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                decode_responses=False
            )
            conn.ping()
            logger.info(f"Connected to Redis at {self.settings.redis_host}:{self.settings.redis_port}")
            return conn
        except redis.ConnectionError as e:
            raise JobQueueError(f"Failed to connect to Redis: {e}")
    
    def enqueue_video_processing(
        self,
        video_id: str,
        video_path: str
    ) -> str:
        """
        Enqueue a video for processing.
        
        Args:
            video_id: Unique video ID
            video_path: Path to video file
            
        Returns:
            Job ID for tracking
        """
        job = self.queue.enqueue(
            'src.worker.process_video',
            video_id,
            video_path,
            job_timeout='1h',
            job_id=f"video_{video_id}"
        )
        
        # Store initial job metadata
        self._set_job_metadata(video_id, {
            "job_id": job.id,
            "video_id": video_id,
            "video_path": video_path,
            "status": "pending",
            "progress": 0.0,
            "frames_processed": 0,
            "total_frames": 0,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "error": None
        })
        
        logger.info(f"Enqueued video processing job: {job.id}")
        return job.id
    
    def get_job_status(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a processing job.
        
        Args:
            video_id: Video ID to check
            
        Returns:
            Job status dictionary or None if not found
        """
        metadata = self._get_job_metadata(video_id)
        if not metadata:
            return None
        
        # Update status from RQ job if available
        job_id = metadata.get("job_id")
        if job_id:
            try:
                job = Job.fetch(job_id, connection=self.redis_conn)
                if job.is_failed:
                    metadata["status"] = "failed"
                    metadata["error"] = str(job.exc_info) if job.exc_info else "Unknown error"
                elif job.is_finished:
                    metadata["status"] = "completed"
                    metadata["progress"] = 1.0
                elif job.is_started:
                    metadata["status"] = "processing"
            except Exception:
                pass  # Job not found in RQ
        
        return metadata
    
    def update_job_progress(
        self,
        video_id: str,
        progress: float,
        frames_processed: int = 0,
        total_frames: int = 0,
        status: str = "processing"
    ) -> None:
        """
        Update job progress.
        
        Args:
            video_id: Video ID
            progress: Progress from 0.0 to 1.0
            frames_processed: Number of frames processed
            total_frames: Total frames to process
            status: Current status
        """
        metadata = self._get_job_metadata(video_id) or {}
        metadata.update({
            "progress": progress,
            "frames_processed": frames_processed,
            "total_frames": total_frames,
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        })
        self._set_job_metadata(video_id, metadata)
    
    def mark_job_complete(self, video_id: str) -> None:
        """Mark job as completed."""
        self.update_job_progress(video_id, 1.0, status="completed")
        logger.info(f"Job completed: {video_id}")
    
    def mark_job_failed(self, video_id: str, error: str) -> None:
        """Mark job as failed with error message."""
        metadata = self._get_job_metadata(video_id) or {}
        metadata.update({
            "status": "failed",
            "error": error,
            "updated_at": datetime.utcnow().isoformat()
        })
        self._set_job_metadata(video_id, metadata)
        logger.error(f"Job failed: {video_id} - {error}")
    
    def _get_job_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get job metadata from Redis."""
        key = f"job_metadata:{video_id}"
        data = self.redis_conn.get(key)
        if data:
            return json.loads(data)
        return None
    
    def _set_job_metadata(self, video_id: str, metadata: Dict[str, Any]) -> None:
        """Store job metadata in Redis."""
        key = f"job_metadata:{video_id}"
        self.redis_conn.set(key, json.dumps(metadata))
        # Set TTL of 24 hours
        self.redis_conn.expire(key, 86400)
    
    def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            self.redis_conn.ping()
            return True
        except Exception:
            return False


# Singleton instance
_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    """Get or create JobQueue instance."""
    global _queue
    if _queue is None:
        _queue = JobQueue()
    return _queue
