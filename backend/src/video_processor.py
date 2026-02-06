"""
Video Processing Module

Handles all FFmpeg operations for video analysis:
- Video validation and metadata extraction
- Frame extraction at configurable FPS
- Audio extraction for transcription
- Thumbnail generation
"""

import subprocess
import json
import os
from pathlib import Path
from typing import List, Tuple, Optional
from loguru import logger

from .config import get_settings, SUPPORTED_VIDEO_FORMATS


class VideoProcessingError(Exception):
    """Raised when video processing fails."""
    pass


class VideoProcessor:
    """
    Handles video processing operations using FFmpeg.
    
    All operations are designed to be resilient and provide
    meaningful error messages for debugging.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._verify_ffmpeg_installed()
    
    def _verify_ffmpeg_installed(self) -> None:
        """Verify FFmpeg and FFprobe are available."""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["ffprobe", "-version"],
                capture_output=True,
                check=True
            )
        except FileNotFoundError:
            raise VideoProcessingError(
                "FFmpeg not found. Please install FFmpeg: "
                "sudo apt install ffmpeg (Linux) or brew install ffmpeg (Mac)"
            )
    
    def validate_video(self, file_path: str) -> dict:
        """
        Validate video file and extract metadata.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Dictionary with video metadata
            
        Raises:
            VideoProcessingError: If video is invalid or corrupted
        """
        path = Path(file_path)
        
        # Check file exists
        if not path.exists():
            raise VideoProcessingError(f"Video file not found: {file_path}")
        
        # Check file extension
        if path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
            raise VideoProcessingError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {SUPPORTED_VIDEO_FORMATS}"
            )
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.settings.max_video_size_mb:
            raise VideoProcessingError(
                f"File too large: {file_size_mb:.1f}MB. "
                f"Maximum: {self.settings.max_video_size_mb}MB"
            )
        
        # Extract metadata using FFprobe
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    file_path
                ],
                capture_output=True,
                text=True,
                check=True
            )
            probe_data = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise VideoProcessingError(f"Failed to probe video: {e.stderr}")
        except json.JSONDecodeError:
            raise VideoProcessingError("Failed to parse video metadata")
        
        # Extract video stream info
        video_stream = None
        audio_stream = None
        for stream in probe_data.get("streams", []):
            if stream["codec_type"] == "video" and video_stream is None:
                video_stream = stream
            elif stream["codec_type"] == "audio" and audio_stream is None:
                audio_stream = stream
        
        if not video_stream:
            raise VideoProcessingError("No video stream found in file")
        
        # Parse duration
        duration = float(probe_data.get("format", {}).get("duration", 0))
        if duration == 0:
            # Try getting from video stream
            duration = float(video_stream.get("duration", 0))
        
        if duration == 0:
            raise VideoProcessingError("Could not determine video duration")
        
        # Parse FPS
        fps_str = video_stream.get("r_frame_rate", "30/1")
        fps_parts = fps_str.split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 30.0
        
        metadata = {
            "filename": path.name,
            "file_path": str(path.absolute()),
            "duration_seconds": duration,
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "fps": fps,
            "has_audio": audio_stream is not None,
            "codec": video_stream.get("codec_name", "unknown"),
            "file_size_mb": file_size_mb
        }
        
        logger.info(f"Video validated: {path.name} ({duration:.1f}s, {metadata['width']}x{metadata['height']})")
        return metadata
    
    def extract_frames(
        self,
        video_path: str,
        output_dir: str,
        fps: Optional[float] = None
    ) -> List[Tuple[float, str]]:
        """
        Extract frames from video at specified FPS.
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save extracted frames
            fps: Frames per second to extract (default from config)
            
        Returns:
            List of (timestamp, frame_path) tuples
        """
        fps = fps or self.settings.frame_extraction_fps
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate unique prefix for this extraction
        video_name = Path(video_path).stem
        frame_pattern = str(output_path / f"{video_name}_frame_%06d.jpg")
        
        logger.info(f"Extracting frames at {fps} FPS from {video_path}")
        
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", video_path,
                    "-vf", f"fps={fps}",
                    "-q:v", "2",  # High quality JPEG
                    "-y",  # Overwrite existing
                    frame_pattern
                ],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise VideoProcessingError(f"Frame extraction failed: {e.stderr.decode()}")
        
        # Collect extracted frames with timestamps
        frames: List[Tuple[float, str]] = []
        for frame_file in sorted(output_path.glob(f"{video_name}_frame_*.jpg")):
            # Extract frame number from filename
            frame_num = int(frame_file.stem.split("_")[-1])
            timestamp = (frame_num - 1) / fps  # Frame numbers start at 1
            frames.append((timestamp, str(frame_file)))
        
        logger.info(f"Extracted {len(frames)} frames from {video_path}")
        return frames
    
    def extract_audio(self, video_path: str, output_dir: str) -> Optional[str]:
        """
        Extract audio track from video.
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save audio file
            
        Returns:
            Path to extracted audio file, or None if no audio
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        video_name = Path(video_path).stem
        audio_file = str(output_path / f"{video_name}_audio.wav")
        
        logger.info(f"Extracting audio from {video_path}")
        
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i", video_path,
                    "-vn",  # No video
                    "-acodec", "pcm_s16le",  # WAV format
                    "-ar", "16000",  # 16kHz for transcription
                    "-ac", "1",  # Mono
                    "-y",  # Overwrite
                    audio_file
                ],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            if "does not contain any stream" in error_msg.lower() or "no audio" in error_msg.lower():
                logger.warning(f"No audio stream in {video_path}")
                return None
            raise VideoProcessingError(f"Audio extraction failed: {error_msg}")
        
        # Verify file was created and has content
        if not Path(audio_file).exists() or Path(audio_file).stat().st_size == 0:
            logger.warning(f"Audio extraction produced empty file for {video_path}")
            return None
        
        logger.info(f"Extracted audio to {audio_file}")
        return audio_file
    
    def generate_thumbnail(
        self,
        video_path: str,
        timestamp: float,
        output_path: str,
        width: int = 320
    ) -> str:
        """
        Generate thumbnail at specific timestamp.
        
        Args:
            video_path: Path to video file
            timestamp: Timestamp in seconds
            output_path: Path to save thumbnail
            width: Thumbnail width (height auto-calculated)
            
        Returns:
            Path to generated thumbnail
        """
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-ss", str(timestamp),
                    "-i", video_path,
                    "-vf", f"scale={width}:-1",
                    "-vframes", "1",
                    "-q:v", "2",
                    "-y",
                    output_path
                ],
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise VideoProcessingError(f"Thumbnail generation failed: {e.stderr.decode()}")
        
        return output_path
    
    def cleanup_temp_files(self, directory: str) -> None:
        """Remove temporary processing files."""
        path = Path(directory)
        if path.exists():
            for file in path.iterdir():
                if file.is_file():
                    file.unlink()
            logger.info(f"Cleaned up temp files in {directory}")


# Singleton instance
_processor: Optional[VideoProcessor] = None


def get_video_processor() -> VideoProcessor:
    """Get or create VideoProcessor instance."""
    global _processor
    if _processor is None:
        _processor = VideoProcessor()
    return _processor
