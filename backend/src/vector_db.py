"""
Vector Database Module

Handles all Qdrant operations for semantic search:
- Collection management
- Indexing video frames and transcripts
- Semantic search with filtering
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from .config import get_settings, COLLECTION_NAME, EMBEDDING_DIMENSION


class VectorDBError(Exception):
    """Raised when vector database operations fail."""
    pass


class VectorDB:
    """
    Handles vector database operations using Qdrant.
    
    Features:
    - Automatic collection creation
    - Separate indexing for frames and transcripts
    - Hybrid search across modalities
    - Deduplication of results
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = self._connect()
        self._ensure_collection()
    
    def _connect(self) -> QdrantClient:
        """Establish connection to Qdrant."""
        try:
            client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                timeout=60  # Increase timeout to avoid ReadTimeout errors
            )
            # Test connection
            client.get_collections()
            logger.info(f"Connected to Qdrant at {self.settings.qdrant_host}:{self.settings.qdrant_port}")
            return client
        except Exception as e:
            raise VectorDBError(f"Failed to connect to Qdrant: {e}")
    
    def _ensure_collection(self) -> None:
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=models.VectorParams(
                        size=EMBEDDING_DIMENSION,
                        distance=models.Distance.COSINE
                    )
                )
                
                # Create payload index for filtering
                self.client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name="video_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name="type",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
                logger.info(f"Created collection: {COLLECTION_NAME}")
            else:
                logger.info(f"Collection exists: {COLLECTION_NAME}")
                
        except Exception as e:
            raise VectorDBError(f"Failed to ensure collection: {e}")
    
    def index_frame(
        self,
        video_id: str,
        timestamp: float,
        embedding: List[float],
        thumbnail_path: Optional[str] = None
    ) -> str:
        """
        Index a video frame embedding.
        
        Args:
            video_id: ID of the parent video
            timestamp: Timestamp in seconds
            embedding: Frame embedding vector
            thumbnail_path: Optional path to thumbnail image
            
        Returns:
            ID of the indexed point
        """
        point_id = str(uuid.uuid4())
        
        payload = {
            "video_id": video_id,
            "timestamp": timestamp,
            "type": "visual",
            "thumbnail_path": thumbnail_path,
            "indexed_at": datetime.utcnow().isoformat()
        }
        
        try:
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            return point_id
        except Exception as e:
            raise VectorDBError(f"Failed to index frame: {e}")
    
    def index_transcript(
        self,
        video_id: str,
        start_time: float,
        end_time: float,
        text: str,
        embedding: List[float]
    ) -> str:
        """
        Index a transcript segment embedding.
        
        Args:
            video_id: ID of the parent video
            start_time: Start timestamp in seconds
            end_time: End timestamp in seconds
            text: Transcript text
            embedding: Text embedding vector
            
        Returns:
            ID of the indexed point
        """
        point_id = str(uuid.uuid4())
        
        payload = {
            "video_id": video_id,
            "timestamp": start_time,  # Use start_time as primary timestamp
            "end_time": end_time,
            "type": "audio",
            "text": text,
            "indexed_at": datetime.utcnow().isoformat()
        }
        
        try:
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            return point_id
        except Exception as e:
            raise VectorDBError(f"Failed to index transcript: {e}")
    
    def search(
        self,
        query_embedding: List[float],
        video_id: Optional[str] = None,
        result_type: Optional[str] = None,
        top_k: int = 5,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content.
        
        Args:
            query_embedding: Query embedding vector
            video_id: Optional filter by video ID
            result_type: Optional filter by type ("visual" or "audio")
            top_k: Number of results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of search results with scores and metadata
        """
        min_score = min_score or self.settings.min_search_score
        
        # Build filter
        filter_conditions = []
        if video_id:
            filter_conditions.append(
                models.FieldCondition(
                    key="video_id",
                    match=models.MatchValue(value=video_id)
                )
            )
        if result_type:
            filter_conditions.append(
                models.FieldCondition(
                    key="type",
                    match=models.MatchValue(value=result_type)
                )
            )
        
        search_filter = None
        if filter_conditions:
            search_filter = models.Filter(must=filter_conditions)
        
        try:
            results = self.client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_embedding,
                query_filter=search_filter,
                limit=top_k * 2,  # Get extra for filtering
                score_threshold=min_score
            )
            
            # Process and deduplicate results
            processed = []
            seen_timestamps = set()
            
            for hit in results.points:
                timestamp = hit.payload.get("timestamp", 0)
                
                # Deduplicate within 2-second window
                window_key = round(timestamp / 2) * 2
                if window_key in seen_timestamps:
                    continue
                seen_timestamps.add(window_key)
                
                processed.append({
                    "timestamp": timestamp,
                    "score": hit.score,
                    "type": hit.payload.get("type"),
                    "thumbnail_path": hit.payload.get("thumbnail_path"),
                    "text": hit.payload.get("text"),
                    "video_id": hit.payload.get("video_id")
                })
                
                if len(processed) >= top_k:
                    break
            
            return processed
            
        except Exception as e:
            raise VectorDBError(f"Search failed: {e}")
    
    def delete_video(self, video_id: str) -> int:
        """
        Delete all indexed data for a video.
        
        Args:
            video_id: ID of the video to delete
            
        Returns:
            Number of points deleted
        """
        try:
            # Get count before deletion
            count_before = self.client.count(
                collection_name=COLLECTION_NAME,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="video_id",
                            match=models.MatchValue(value=video_id)
                        )
                    ]
                )
            ).count
            
            # Delete points
            self.client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="video_id",
                                match=models.MatchValue(value=video_id)
                            )
                        ]
                    )
                )
            )
            
            logger.info(f"Deleted {count_before} points for video {video_id}")
            return count_before
            
        except Exception as e:
            raise VectorDBError(f"Failed to delete video data: {e}")
    
    def get_video_stats(self, video_id: str) -> Dict[str, int]:
        """
        Get indexing statistics for a video.
        
        Returns:
            Dictionary with frame_count and transcript_count
        """
        try:
            visual_count = self.client.count(
                collection_name=COLLECTION_NAME,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="video_id", match=models.MatchValue(value=video_id)),
                        models.FieldCondition(key="type", match=models.MatchValue(value="visual"))
                    ]
                )
            ).count
            
            audio_count = self.client.count(
                collection_name=COLLECTION_NAME,
                count_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="video_id", match=models.MatchValue(value=video_id)),
                        models.FieldCondition(key="type", match=models.MatchValue(value="audio"))
                    ]
                )
            ).count
            
            return {
                "frame_count": visual_count,
                "transcript_count": audio_count,
                "total": visual_count + audio_count
            }
            
        except Exception as e:
            raise VectorDBError(f"Failed to get video stats: {e}")
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy."""
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False


# Singleton instance
_db: Optional[VectorDB] = None


def get_vector_db() -> VectorDB:
    """Get or create VectorDB instance."""
    global _db
    if _db is None:
        _db = VectorDB()
    return _db
