"""
Background Worker for Video Processing

This module contains the actual video processing logic that runs
in the background via Redis Queue.
"""

import os
import shutil
from pathlib import Path
from loguru import logger

from .config import get_settings
from .video_processor import get_video_processor, VideoProcessingError
from .ai_service import get_ai_service, AIServiceError
from .vector_db import get_vector_db, VectorDBError
from .job_queue import get_job_queue


def process_video(video_id: str, video_path: str) -> None:
    """
    Process a video for semantic search indexing.
    
    This function:
    1. Validates the video
    2. Extracts frames at configured FPS
    3. Generates embeddings for each frame
    4. Extracts and transcribes audio
    5. Generates embeddings for transcript segments
    6. Indexes everything in Qdrant
    
    Args:
        video_id: Unique video ID
        video_path: Path to video file
    """
    settings = get_settings()
    job_queue = get_job_queue()
    video_processor = get_video_processor()
    ai_service = get_ai_service()
    vector_db = get_vector_db()
    
    # Create temp directory for this video
    temp_dir = settings.temp_dir / video_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Starting video processing: {video_id}")
        job_queue.update_job_progress(video_id, 0.05, status="processing")
        
        # Step 1: Validate video
        logger.info("Step 1: Validating video...")
        metadata = video_processor.validate_video(video_path)
        job_queue.update_job_progress(video_id, 0.1, status="processing")
        
        # Step 2: Extract frames
        logger.info("Step 2: Extracting frames...")
        frames = video_processor.extract_frames(
            video_path,
            str(temp_dir / "frames")
        )
        total_frames = len(frames)
        job_queue.update_job_progress(
            video_id, 0.2,
            frames_processed=0,
            total_frames=total_frames
        )
        
        # Step 3: Generate frame embeddings
        logger.info(f"Step 3: Generating embeddings for {total_frames} frames...")
        frames_indexed = 0
        
        for timestamp, frame_path in frames:
            try:
                # Generate embedding
                embedding = ai_service.get_image_embedding(frame_path)
                
                # Generate thumbnail
                thumbnail_name = f"{video_id}_{timestamp:.1f}.jpg"
                thumbnail_path = settings.thumbnails_dir / thumbnail_name
                video_processor.generate_thumbnail(
                    video_path,
                    timestamp,
                    str(thumbnail_path)
                )
                
                # Index in vector DB
                vector_db.index_frame(
                    video_id=video_id,
                    timestamp=timestamp,
                    embedding=embedding,
                    thumbnail_path=str(thumbnail_path)
                )
                
                frames_indexed += 1
                progress = 0.2 + (0.5 * frames_indexed / total_frames)
                job_queue.update_job_progress(
                    video_id, progress,
                    frames_processed=frames_indexed,
                    total_frames=total_frames
                )
                
            except (AIServiceError, VectorDBError) as e:
                logger.warning(f"Failed to process frame at {timestamp}s: {e}")
                continue
        
        logger.info(f"Indexed {frames_indexed}/{total_frames} frames")
        
        # Step 4: Extract and transcribe audio (if available)
        if metadata.get("has_audio", False):
            logger.info("Step 4: Processing audio...")
            job_queue.update_job_progress(video_id, 0.75, status="processing")
            
            try:
                audio_path = video_processor.extract_audio(
                    video_path,
                    str(temp_dir)
                )
                
                if audio_path:
                    # Transcribe
                    segments = ai_service.transcribe_audio(audio_path)
                    logger.info(f"Got {len(segments)} transcript segments")
                    
                    # Index each segment
                    for segment in segments:
                        try:
                            embedding = ai_service.get_text_embedding(segment["text"])
                            vector_db.index_transcript(
                                video_id=video_id,
                                start_time=segment["start"],
                                end_time=segment["end"],
                                text=segment["text"],
                                embedding=embedding
                            )
                        except (AIServiceError, VectorDBError) as e:
                            logger.warning(f"Failed to index transcript segment: {e}")
                            continue
                    
            except (VideoProcessingError, AIServiceError) as e:
                logger.warning(f"Audio processing failed: {e}")
        else:
            logger.info("Step 4: Skipping audio (no audio track)")
        
        # Step 5: Cleanup and complete
        logger.info("Step 5: Cleaning up...")
        video_processor.cleanup_temp_files(str(temp_dir))
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Get final stats
        stats = vector_db.get_video_stats(video_id)
        logger.info(f"Video processing complete: {stats}")
        
        job_queue.mark_job_complete(video_id)
        
    except Exception as e:
        logger.exception(f"Video processing failed: {e}")
        job_queue.mark_job_failed(video_id, str(e))
        
        # Cleanup on failure
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
