// API Types for Semantic Video Search

export interface UploadResponse {
    job_id: string;
    video_id: string;
    status: JobStatus;
    message: string;
}

export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface JobStatusResponse {
    job_id: string;
    video_id: string;
    status: JobStatus;
    progress: number;
    frames_processed: number;
    total_frames: number;
    created_at: string;
    updated_at: string;
    error: string | null;
}

export interface SearchRequest {
    video_id: string;
    query: string;
    top_k?: number;
}

export interface SearchResult {
    timestamp: number;
    score: number;
    type: 'visual' | 'audio';
    thumbnail_url: string | null;
    transcript_snippet: string | null;
}

export interface SearchResponse {
    query: string;
    video_id: string;
    results: SearchResult[];
    total_results: number;
}

export interface HealthResponse {
    status: string;
    qdrant: boolean;
    redis: boolean;
    timestamp: string;
}
