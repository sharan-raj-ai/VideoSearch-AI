// API Client for Semantic Video Search Backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import type {
    UploadResponse,
    JobStatusResponse,
    SearchRequest,
    SearchResponse,
    HealthResponse
} from '@/types/api';

class APIError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'APIError';
    }
}

async function fetchAPI<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new APIError(response.status, error.detail || 'Request failed');
    }

    return response.json();
}

export const api = {
    /**
     * Check API health status
     */
    async health(): Promise<HealthResponse> {
        return fetchAPI<HealthResponse>('/health');
    },

    /**
     * Upload a video for processing
     */
    async uploadVideo(file: File): Promise<UploadResponse> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
            throw new APIError(response.status, error.detail);
        }

        return response.json();
    },

    /**
     * Get job processing status
     */
    async getJobStatus(videoId: string): Promise<JobStatusResponse> {
        return fetchAPI<JobStatusResponse>(`/status/${videoId}`);
    },

    /**
     * Search within a video
     */
    async search(request: SearchRequest): Promise<SearchResponse> {
        return fetchAPI<SearchResponse>('/search', {
            method: 'POST',
            body: JSON.stringify(request),
        });
    },

    /**
     * Get video URL for streaming
     */
    getVideoUrl(videoId: string): string {
        return `${API_BASE_URL}/video/${videoId}`;
    },

    /**
     * Get thumbnail URL
     */
    getThumbnailUrl(path: string): string {
        if (path.startsWith('http')) return path;
        return `${API_BASE_URL}${path}`;
    },

    /**
     * Delete a video
     */
    async deleteVideo(videoId: string): Promise<void> {
        await fetchAPI(`/video/${videoId}`, { method: 'DELETE' });
    },
};

export { APIError };
