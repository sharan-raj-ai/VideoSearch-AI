# Implementation Plan - Semantic Video Search Engine

## Goal
Build a **production-quality Semantic Video Search Engine** that allows users to upload videos and search for specific moments using natural language queries (e.g., "person in red shirt talking about budget").

---

## Portfolio Impact Assessment

| Criteria | Rating | Justification |
|----------|--------|---------------|
| **Technical Complexity** | ⭐⭐⭐⭐⭐ | Multi-modal AI (Vision + Audio), Vector Search, Async Processing |
| **Industry Relevance** | ⭐⭐⭐⭐⭐ | RAG, Video AI, and Embeddings are top enterprise AI skills |
| **Uniqueness** | ⭐⭐⭐⭐⭐ | Very few portfolios have multi-modal video search |
| **Engineering Maturity** | ⭐⭐⭐⭐⭐ | Job queues, error handling, observability, API design |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Upload  │  │  Search  │  │  Video   │  │  Results List    │ │
│  │   UI     │  │   Bar    │  │  Player  │  │  (Timestamps)    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────┼─────────────────┼───────────┘
        │             │             │                 │
        ▼             ▼             ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ POST /upload │  │ POST /search │  │ GET /status/{job_id}   │ │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬───────────┘ │
│         │                 │                       │              │
│         ▼                 │                       │              │
│  ┌──────────────┐         │                       │              │
│  │  Job Queue   │◄────────┼───────────────────────┘              │
│  │   (Redis)    │         │                                      │
│  └──────┬───────┘         │                                      │
│         │                 │                                      │
│         ▼                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    AI SERVICE                             │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌─────────────┐ │   │
│  │  │ Video Processor│  │ Gemini Vision  │  │ Transcriber │ │   │
│  │  │   (FFmpeg)     │  │  (Embeddings)  │  │  (Whisper)  │ │   │
│  │  └────────────────┘  └────────────────┘  └─────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         STORAGE                                  │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │   Qdrant Vector DB   │  │      File System (uploads/)      │ │
│  │  - Frame embeddings  │  │  - Original videos               │ │
│  │  - Text embeddings   │  │  - Extracted thumbnails          │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Production Considerations & Edge Cases

### 1. Video Processing Failures
| Problem | Solution |
|---------|----------|
| Corrupted video file | Validate with FFprobe before processing; return clear error |
| Unsupported codec | Transcode to H.264 via FFmpeg on upload |
| Very long videos (>1hr) | Implement chunked processing with progress tracking |
| No audio track | Gracefully skip transcription; index visual only |

### 2. AI/Embedding Failures
| Problem | Solution |
|---------|----------|
| API rate limits (Gemini) | Implement exponential backoff + retry logic |
| API timeout on large batch | Process frames in batches of 10-20, not all at once |
| Embedding dimension mismatch | Validate vector size before Qdrant insert |
| Transcription returns empty | Log warning, continue with visual-only index |

### 3. Search Quality Issues
| Problem | Solution |
|---------|----------|
| Low relevance results | Return confidence scores; filter below threshold (0.7) |
| Duplicate timestamps | Deduplicate results within ±2 second window |
| Ambiguous queries | Return top-K results (K=5) with thumbnails |

### 4. System Reliability
| Problem | Solution |
|---------|----------|
| Server crash mid-processing | Use job queue with persistence |
| Qdrant unavailable | Health checks + graceful degradation |
| Large file uploads fail | Chunked uploads; validate file size limits |

---

## API Design

### Endpoints

| Endpoint | Method | Description | Request | Response |
|----------|--------|-------------|---------|----------|
| `/upload` | POST | Upload video | `multipart/form-data` | `{ job_id, status }` |
| `/status/{job_id}` | GET | Check job status | - | `{ status, progress, error? }` |
| `/search` | POST | Search video | `{ video_id, query }` | `{ results: [{timestamp, score, thumbnail}] }` |
| `/video/{video_id}` | GET | Stream video | - | `video/mp4` |
| `/health` | GET | Health check | - | `{ status, qdrant, redis }` |

### Response Schemas

```python
# Job Status Response
{
    "job_id": "uuid",
    "status": "pending" | "processing" | "completed" | "failed",
    "progress": 0.75,  # 0-1
    "frames_processed": 45,
    "total_frames": 60,
    "error": null | "Error message"
}

# Search Response
{
    "query": "person walking",
    "video_id": "uuid",
    "results": [
        {
            "timestamp": 12.5,
            "score": 0.89,
            "type": "visual" | "audio",
            "thumbnail_url": "/thumbnails/abc123.jpg",
            "transcript_snippet": "...walking through the park..."
        }
    ]
}
```

---

## Development Phases

### Phase 1: Core Pipeline (MVP)
- [x] Project structure creation
- [ ] Docker Compose (Qdrant + Redis)
- [ ] Python dependencies
- [ ] Config management (.env)
- [ ] Video processor (FFmpeg)
- [ ] AI Service (Gemini embeddings)
- [ ] Qdrant integration
- [ ] Basic FastAPI endpoints

### Phase 2: Production Hardening
- [ ] Job queue with Redis
- [ ] Error handling + retries
- [ ] Structured logging (loguru)
- [ ] Input validation
- [ ] Progress tracking

### Phase 3: Frontend
- [ ] Next.js setup
- [ ] Upload with progress bar
- [ ] Video player with timestamp jumping
- [ ] Search UI with result thumbnails

### Phase 4: Polish
- [ ] Unit tests
- [ ] Integration tests
- [ ] README documentation
- [ ] Demo video for portfolio
- [ ] Optional: Cloud deployment

---

## File-by-File Implementation

### `backend/src/config.py`
- Load environment variables
- Validate required keys (GEMINI_API_KEY)
- Define constants (UPLOAD_DIR, TEMP_DIR, etc.)

### `backend/src/video_processor.py`
- `validate_video(path)` - FFprobe check
- `get_video_duration(path)` - Duration in seconds
- `extract_frames(path, fps=1)` - Returns list of (timestamp, frame_path)
- `extract_audio(path)` - Returns audio file path

### `backend/src/ai_service.py`
- `get_image_embedding(image_path)` - Gemini multimodal
- `get_text_embedding(text)` - Gemini text embedding
- `transcribe_audio(audio_path)` - Audio to text with timestamps
- Includes retry logic and error handling

### `backend/src/vector_db.py`
- `create_collection(name, dimension)`
- `index_frame(video_id, timestamp, embedding, thumbnail_path)`
- `index_transcript(video_id, start_time, end_time, text, embedding)`
- `search(query_embedding, video_id, top_k=5)`

### `backend/src/job_queue.py`
- `enqueue_video_processing(video_id, path)`
- `get_job_status(job_id)`
- Worker function for background processing

### `backend/src/main.py`
- FastAPI app with all endpoints
- CORS configuration
- Static file serving for thumbnails
