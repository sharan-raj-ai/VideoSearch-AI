# Semantic Video Search Engine - Development Progress

> **Project:** AI-powered semantic video search using Gemini, Qdrant, and FastAPI  
> **Started:** 2026-02-06  
> **Last Updated:** 2026-02-06 15:42 IST

---

## Document Structure

This log tracks **all** changes, errors, and fixes in reverse chronological order (newest first).

| Section | Purpose |
|---------|---------|
| `✅ Change` | Feature additions, code changes |
| `🐛 Bug Fix` | Error encountered and resolution |
| `⚙️ Config` | Configuration or setup changes |
| `📝 Note` | Important observations or decisions |

---

## Changelog

### 2026-02-06 15:33 — Migrated to Groq Vision
- `🚀 Feature` **Replaced HF Vision with Groq**
  - Hugging Face `Qwen2.5-VL` returned `410 Gone` (Deprecated)
  - Switched to Groq `meta-llama/llama-4-scout-17b-16e-instruct` (Vision)
  - **New Stack:** Groq (Vision+Audio), Jina (Embeddings)

---

### 2026-02-06 15:23 — Qdrant Timeout Fix
- `🐛 Bug Fix` **Qdrant Connection Timeout**
  - Error: `httpx.ReadTimeout` during `create_payload_index`
  - Cause: Default timeout (5s) too short for Docker I/O
  - Fix: Increased `QdrantClient` timeout to 60s in `vector_db.py`

- `⚙️ Config` **Manual Index Repair**
  - Ran `fix_indices.py` to manually create missing Qdrant indices
  - Confirmed database is now healthy and responsive
  - `📝 Note` Previous upload failed during init, re-upload required

---

### 2026-02-06 15:38 — Search Threshold Fix
- `🐛 Bug Fix` **Search returned 0 results**
  - Symptom: Valid vectors indexed but filtered out by search
  - Cause: `.env` had `MIN_SEARCH_SCORE=0.5` overriding `config.py` default
  - Fix: Updated `.env` to `MIN_SEARCH_SCORE=0.15`
  - Result: Search now correctly returns matches (e.g., "middle finger" -> 2 hits)

---

### 2026-02-06 15:20 — Migrated to Free Tier AI Stack
- `⚙️ Config` **Replaced Gemini with Multi-Provider Stack** to avoid rate limits
  - **Vision:** Hugging Face Inference API (`Qwen/Qwen2.5-VL-7B-Instruct`)
  - **Audio:** Groq API (`whisper-large-v3`)
  - **Embeddings:** Jina AI (`jina-embeddings-v3`, 1024 dims)
- `⚙️ Config` Updated `config.py`:
  - Changed `EMBEDDING_DIMENSION` from 3072 to 1024
  - Added new API keys (Hugging Face, Groq, Jina)
- `♻️ Refactor` Rewrote `ai_service.py` to use `httpx` and new providers
- `📝 Note` Deleted old Qdrant collection to support new embedding dimension
- `📝 Note` Backed up old service to `ai_service_gemini.py`

---

### 2026-02-06 13:41 — Vision Model Fix
- `🐛 Bug Fix` **Gemini vision model not found**
  - Error: `404 models/gemini-1.5-flash is not found for API version v1beta`
  - Cause: `gemini-1.5-flash` deprecated, no longer available
  - Discovery: Used `genai.list_models()` to find available models
  - Fix: Changed to `gemini-2.0-flash` in `ai_service.py` line 49
  - Impact: 0 frames were indexed because all vision calls failed
  - `📝 Note` User must re-upload video

---

### 2026-02-06 13:38 — Vector Dimension Mismatch Fix
- `🐛 Bug Fix` **Vector dimension mismatch (768 vs 3072)**
  - Error: `Vector dimension error: expected dim: 768, got 3072`
  - Cause: `EMBEDDING_DIMENSION=768` but `gemini-embedding-001` produces 3072-dim vectors
  - Fix: Changed `config.py` line 96: `EMBEDDING_DIMENSION = 3072`
  - Cleanup: Deleted old `video_embeddings` collection from Qdrant
  - `📝 Note` User must re-upload video as old data was deleted

---

### 2026-02-06 13:35 — Qdrant Search API Fix
- `🐛 Bug Fix` **QdrantClient 'search' method not found**
  - Error: `'QdrantClient' object has no attribute 'search'`
  - Cause: qdrant-client 1.16.2 deprecated `search()` method
  - Discovery: Used `dir(QdrantClient)` to find new method `query_points`
  - Fix: In `vector_db.py`:
    - Changed `client.search()` → `client.query_points()`
    - Changed `query_vector=` → `query=`
    - Changed `for hit in results` → `for hit in results.points`

---

### 2026-02-06 13:32 — Embedding Model Fix
- `🐛 Bug Fix` **Gemini embedding model not found**
  - Error: `404 models/text-embedding-004 is not found for API version v1beta`
  - Cause: Model `text-embedding-004` doesn't exist in current Gemini API
  - Discovery: Used `genai.list_models()` to find available embedding models
  - Fix: Changed to `models/gemini-embedding-001` in `ai_service.py` line 50

---

### 2026-02-06 13:30 — Worker Restart After FFmpeg Install
- `⚙️ Config` Restarted RQ worker to pick up newly installed FFmpeg
- `📝 Note` Previous worker had cached "FFmpeg not found" error

---

### 2026-02-06 13:28 — Progress Tracking Structure
- `📝 Note` Established professional structure for PROGRESS.md with defined format

---

### 2026-02-06 13:24 — FFmpeg Installation
- `🐛 Bug Fix` **FFmpeg not found**
  - Error: `FileNotFoundError: No such file or directory: 'ffmpeg'`
  - Cause: FFmpeg not installed on system
  - Fix: `sudo apt install -y ffmpeg`

---

### 2026-02-06 13:20 — RQ Worker Queue Mismatch
- `🐛 Bug Fix` **Worker listening on wrong queue**
  - Error: Video processing stuck at 0% despite worker running
  - Cause: Jobs enqueued to `default` queue, worker listening on `video-processing`
  - Fix: Started worker on correct queue: `rq worker --url redis://localhost:6380 default`

---

### 2026-02-06 13:19 — RQ Worker Not Running
- `🐛 Bug Fix` **Video processing not starting**
  - Error: Upload successful but progress stuck at 0%
  - Cause: RQ background worker process not started
  - Fix: Started worker manually with `rq worker` command

---

### 2026-02-06 13:15 — Browser Ad-Blocker Blocking Requests
- `🐛 Bug Fix` **API requests blocked**
  - Error: `net::ERR_BLOCKED_BY_CLIENT` on `/health` and `/upload` endpoints
  - Cause: Browser ad-blocker extension intercepting localhost:8000 requests
  - Fix: User disabled ad-blocker for localhost

---

### 2026-02-06 13:08 — Frontend UI Polish
- `✅ Change` Removed all emojis, replaced with SVG icons
- `✅ Change` Changed color palette to elegant purple/indigo gradient
- `✅ Change` Centralized all content from hero to feature cards
- `✅ Change` Added `feature-card` CSS class with hover animations
- `✅ Change` Updated `globals.css` with new design system variables
- `✅ Change` Updated `page.tsx` with icon-based feature cards

---

### 2026-02-06 13:02 — Frontend Redesign
- `✅ Change` Complete CSS redesign removing "amateur" styling
- `✅ Change` Fixed overlapping header text (SEMANTIC VIDEO / Video Search)
- `✅ Change` Redesigned all 7 components with clean minimal styling
- `✅ Change` New files: `Header.tsx`, `VideoUploader.tsx`, `ProcessingStatus.tsx`, `SearchBar.tsx`, `VideoPlayer.tsx`, `SearchResults.tsx`, `page.tsx`

---

### 2026-02-06 12:56 — Python Package Compatibility
- `🐛 Bug Fix` **qdrant-client version incompatible**
  - Error: `No matching distribution found for qdrant-client==1.7.0`
  - Cause: Python 3.13 not supported by pinned version
  - Fix: Changed `requirements.txt` from exact versions (`==`) to minimum versions (`>=`)

---

### 2026-02-06 12:52 — Docker Port Conflict
- `🐛 Bug Fix` **Redis port already in use**
  - Error: `Error starting userland proxy: listen tcp4 0.0.0.0:6379: bind: address already in use`
  - Cause: Existing Redis server running on port 6379
  - Fix: Changed Redis port to 6380 in `docker-compose.yml` and `.env`

---

### 2026-02-06 12:00 — Frontend Implementation
- `✅ Change` Initialized Next.js 14 with TypeScript
- `✅ Change` Created Iron Man themed design (later redesigned)
- `✅ Change` Implemented 7 React components
- `✅ Change` Added TypeScript types matching backend API
- `✅ Change` Created API client in `lib/api.ts`
- `⚙️ Config` Created `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`

---

### 2026-02-06 11:00 — Backend Implementation
- `✅ Change` Created `docker-compose.yml` for Qdrant + Redis
- `✅ Change` Created `requirements.txt` with all dependencies
- `✅ Change` Created core modules:
  - `config.py` - Pydantic settings configuration
  - `models.py` - Request/response schemas
  - `video_processor.py` - FFmpeg operations
  - `ai_service.py` - Gemini API integration
  - `vector_db.py` - Qdrant operations
  - `job_queue.py` - Redis Queue management
  - `worker.py` - Background processing
  - `main.py` - FastAPI endpoints
  - `utils.py` - Helper functions
- `⚙️ Config` Created `.env` with Gemini API key

---

### 2026-02-06 10:00 — Project Initialization
- `✅ Change` Created project directory structure
- `✅ Change` Created `README.md` with project overview
- `✅ Change` Created `docs/IMPLEMENTATION_PLAN.md`
- `✅ Change` Created initial `docs/PROGRESS.md`

---

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Docker (Qdrant) | ✅ Running | Port 6333 |
| Docker (Redis) | ✅ Running | Port 6380 |
| Backend API | ✅ Running | Port 8000 |
| Frontend | ✅ Running | Port 3001 |
| RQ Worker | ✅ Running | Default queue |
| FFmpeg | ✅ Installed | v7.1.1 |

**Next Action:** Upload video to test full pipeline
