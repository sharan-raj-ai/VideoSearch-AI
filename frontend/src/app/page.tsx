'use client';

import { useState, useCallback } from 'react';
import {
  Header,
  VideoUploader,
  ProcessingStatus,
  SearchBar,
  VideoPlayer,
  SearchResults
} from '@/components';
import { api, APIError } from '@/lib/api';
import type { UploadResponse, SearchResult } from '@/types/api';

type AppState = 'upload' | 'processing' | 'ready';

export default function Home() {
  const [appState, setAppState] = useState<AppState>('upload');
  const [videoId, setVideoId] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [lastQuery, setLastQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [seekTimestamp, setSeekTimestamp] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadComplete = useCallback((response: UploadResponse) => {
    setVideoId(response.video_id);
    setAppState('processing');
    setError(null);
  }, []);

  const handleProcessingComplete = useCallback(() => {
    setAppState('ready');
  }, []);

  const handleSearch = useCallback(async (query: string) => {
    if (!videoId) return;

    setIsSearching(true);
    setLastQuery(query);
    setError(null);

    try {
      const response = await api.search({ video_id: videoId, query, top_k: 10 });
      setSearchResults(response.results);
    } catch (err) {
      setError(err instanceof APIError ? err.message : 'Search failed');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [videoId]);

  const handleNewVideo = () => {
    setAppState('upload');
    setVideoId(null);
    setSearchResults([]);
    setLastQuery('');
    setSeekTimestamp(null);
    setError(null);
  };

  return (
    <div className="min-h-screen">
      <Header />

      <main style={{ paddingTop: '100px', paddingBottom: '80px' }}>
        <div className="container">

          {/* Upload State */}
          {appState === 'upload' && (
            <div className="max-w-2xl mx-auto animate-fade-in">
              {/* Hero - Centered */}
              <div className="text-center mb-10">
                <h1 className="mb-4">
                  Search inside{' '}
                  <span style={{
                    background: 'var(--gradient-primary)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}>
                    videos
                  </span>
                </h1>
                <p className="text-lg max-w-lg mx-auto" style={{ color: 'var(--text-secondary)' }}>
                  Upload a video and search through it using natural language.
                  Find exact moments in seconds.
                </p>
              </div>

              {/* Upload Box - Centered */}
              <div className="mb-12">
                <VideoUploader onUploadComplete={handleUploadComplete} />
              </div>

              {/* Features - Centered Grid */}
              <div className="grid grid-cols-3 gap-5">
                <div className="feature-card">
                  <div className="icon-box mb-4">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="mb-2">Visual Analysis</h3>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    AI understands what&apos;s in each frame
                  </p>
                </div>

                <div className="feature-card">
                  <div className="icon-box mb-4">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                  </div>
                  <h3 className="mb-2">Audio Transcription</h3>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Every spoken word is searchable
                  </p>
                </div>

                <div className="feature-card">
                  <div className="icon-box mb-4">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="mb-2">Instant Search</h3>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Find moments in milliseconds
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Processing State */}
          {appState === 'processing' && videoId && (
            <div className="max-w-lg mx-auto animate-fade-in">
              <ProcessingStatus videoId={videoId} onComplete={handleProcessingComplete} />
            </div>
          )}

          {/* Ready State */}
          {appState === 'ready' && videoId && (
            <div className="animate-fade-in">
              {/* Top bar */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <span className="badge badge-success">
                    <span className="w-2 h-2 rounded-full" style={{ background: 'var(--success)' }} />
                    Ready
                  </span>
                  <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Video indexed successfully
                  </span>
                </div>
                <button onClick={handleNewVideo} className="btn btn-secondary">
                  Upload new video
                </button>
              </div>

              {/* Main grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Video */}
                <div className="space-y-6">
                  <VideoPlayer videoId={videoId} seekToTimestamp={seekTimestamp} />
                </div>

                {/* Search */}
                <div className="space-y-6">
                  <SearchBar onSearch={handleSearch} isLoading={isSearching} />

                  {error && (
                    <div className="p-4 rounded-lg" style={{ background: 'var(--error-bg)', color: 'var(--error)' }}>
                      {error}
                    </div>
                  )}

                  {lastQuery ? (
                    <SearchResults
                      results={searchResults}
                      query={lastQuery}
                      onTimestampClick={setSeekTimestamp}
                    />
                  ) : (
                    <div className="card p-12 text-center">
                      <div className="icon-box-lg mx-auto mb-4" style={{ background: 'var(--bg-elevated)' }}>
                        <svg className="w-8 h-8" style={{ color: 'var(--text-muted)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      </div>
                      <h3 className="font-semibold mb-2">Search your video</h3>
                      <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                        Describe what you&apos;re looking for
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

        </div>
      </main>

      {/* Footer */}
      <footer
        className="fixed bottom-0 left-0 right-0 py-4 text-center text-sm"
        style={{
          color: 'var(--text-muted)',
          background: 'linear-gradient(to top, var(--bg-base) 0%, transparent 100%)'
        }}
      >
        <div className="flex items-center justify-center gap-2">
          <span>Built with</span>
          <span style={{ color: 'var(--text-secondary)' }}>Next.js</span>
          <span style={{ color: 'var(--border)' }}>•</span>
          <span style={{ color: 'var(--text-secondary)' }}>FastAPI</span>
          <span style={{ color: 'var(--border)' }}>•</span>
          <span style={{ color: 'var(--text-secondary)' }}>Gemini AI</span>
          <span style={{ color: 'var(--border)' }}>•</span>
          <span style={{ color: 'var(--text-secondary)' }}>Qdrant</span>
        </div>
      </footer>
    </div>
  );
}
