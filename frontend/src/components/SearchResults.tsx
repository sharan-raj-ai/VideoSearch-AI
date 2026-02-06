'use client';

import { api } from '@/lib/api';
import type { SearchResult } from '@/types/api';

interface SearchResultsProps {
    results: SearchResult[];
    query: string;
    onTimestampClick: (timestamp: number) => void;
}

export default function SearchResults({ results, query, onTimestampClick }: SearchResultsProps) {
    const formatTime = (seconds: number): string => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const getScoreColor = (score: number): string => {
        if (score >= 0.8) return 'var(--success)';
        if (score >= 0.6) return 'var(--warning)';
        return 'var(--error)';
    };

    if (results.length === 0) {
        return (
            <div className="card p-12 text-center">
                <div
                    className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                    style={{ background: 'var(--bg-elevated)' }}
                >
                    <svg className="w-8 h-8" style={{ color: 'var(--text-muted)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>
                <h3 className="font-semibold mb-1">No results found</h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Try a different search term
                </p>
            </div>
        );
    }

    return (
        <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    Found <span className="font-medium" style={{ color: 'var(--text-primary)' }}>{results.length}</span> results for &quot;{query}&quot;
                </p>
            </div>

            <div className="space-y-2">
                {results.map((result, index) => (
                    <button
                        key={index}
                        onClick={() => onTimestampClick(result.timestamp)}
                        className="result-item w-full text-left animate-fade-in"
                        style={{ animationDelay: `${index * 50}ms` }}
                    >
                        {/* Thumbnail */}
                        <div className="shrink-0">
                            {result.thumbnail_url ? (
                                <div className="w-24 h-14 rounded-lg overflow-hidden bg-black">
                                    <img
                                        src={api.getThumbnailUrl(result.thumbnail_url)}
                                        alt=""
                                        className="w-full h-full object-cover"
                                    />
                                </div>
                            ) : (
                                <div
                                    className="w-24 h-14 rounded-lg flex items-center justify-center"
                                    style={{ background: 'var(--bg-base)' }}
                                >
                                    <svg className="w-6 h-6" style={{ color: 'var(--text-muted)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        {result.type === 'visual' ? (
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                        ) : (
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                                        )}
                                    </svg>
                                </div>
                            )}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                                <span className="timestamp">{formatTime(result.timestamp)}</span>
                                <span
                                    className="badge"
                                    style={{
                                        fontSize: '10px',
                                        padding: '2px 6px',
                                        background: result.type === 'visual' ? 'rgba(139, 92, 246, 0.1)' : 'rgba(6, 182, 212, 0.1)',
                                        color: result.type === 'visual' ? '#a78bfa' : 'var(--secondary)',
                                        border: 'none'
                                    }}
                                >
                                    {result.type}
                                </span>
                            </div>

                            {result.transcript_snippet && (
                                <p className="text-sm truncate" style={{ color: 'var(--text-secondary)' }}>
                                    &quot;{result.transcript_snippet}&quot;
                                </p>
                            )}
                        </div>

                        {/* Score */}
                        <div className="shrink-0 text-right">
                            <div className="text-lg font-semibold" style={{ color: getScoreColor(result.score) }}>
                                {Math.round(result.score * 100)}%
                            </div>
                            <div className="text-xs" style={{ color: 'var(--text-muted)' }}>match</div>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
}
