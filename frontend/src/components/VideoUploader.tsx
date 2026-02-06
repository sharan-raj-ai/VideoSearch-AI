'use client';

import { useState, useCallback, useRef } from 'react';
import { api, APIError } from '@/lib/api';
import type { UploadResponse } from '@/types/api';

interface VideoUploaderProps {
    onUploadComplete: (response: UploadResponse) => void;
}

export default function VideoUploader({ onUploadComplete }: VideoUploaderProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const validateFile = (file: File): boolean => {
        const validTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm', 'video/quicktime'];
        if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
            setError('Please upload a video file (MP4, AVI, MOV, MKV, or WebM)');
            return false;
        }

        const maxSize = 500 * 1024 * 1024;
        if (file.size > maxSize) {
            setError('File size must be under 500MB');
            return false;
        }

        return true;
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        setError(null);

        const file = e.dataTransfer.files[0];
        if (file && validateFile(file)) {
            setSelectedFile(file);
        }
    }, []);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        setError(null);
        const file = e.target.files?.[0];
        if (file && validateFile(file)) {
            setSelectedFile(file);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setIsUploading(true);
        setError(null);
        setUploadProgress(0);

        const progressInterval = setInterval(() => {
            setUploadProgress(prev => prev >= 90 ? prev : prev + Math.random() * 15);
        }, 200);

        try {
            const response = await api.uploadVideo(selectedFile);
            clearInterval(progressInterval);
            setUploadProgress(100);

            setTimeout(() => {
                onUploadComplete(response);
                setSelectedFile(null);
                setUploadProgress(0);
                setIsUploading(false);
            }, 300);

        } catch (err) {
            clearInterval(progressInterval);
            setIsUploading(false);
            setUploadProgress(0);
            setError(err instanceof APIError ? err.message : 'Upload failed. Please try again.');
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    return (
        <div className="card p-8">
            <input
                ref={fileInputRef}
                type="file"
                accept="video/*"
                onChange={handleFileSelect}
                className="hidden"
            />

            <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !isUploading && fileInputRef.current?.click()}
                className={`dropzone ${isDragging ? 'active' : ''} ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
            >
                {isUploading ? (
                    <div className="text-center space-y-6 w-full max-w-sm">
                        <div className="spinner-lg mx-auto" />
                        <div className="space-y-2">
                            <p className="font-medium">Uploading video...</p>
                            <div className="progress">
                                <div className="progress-bar" style={{ width: `${uploadProgress}%` }} />
                            </div>
                            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                {Math.round(uploadProgress)}% complete
                            </p>
                        </div>
                    </div>
                ) : selectedFile ? (
                    <div className="text-center space-y-4">
                        <div
                            className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto"
                            style={{ background: 'rgba(59, 130, 246, 0.1)' }}
                        >
                            <svg
                                className="w-8 h-8"
                                style={{ color: 'var(--accent)' }}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <div>
                            <p className="font-medium truncate max-w-xs mx-auto">{selectedFile.name}</p>
                            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                                {formatFileSize(selectedFile.size)}
                            </p>
                        </div>
                        <button
                            onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                            className="text-sm hover:underline"
                            style={{ color: 'var(--text-muted)' }}
                        >
                            Choose different file
                        </button>
                    </div>
                ) : (
                    <div className="text-center space-y-4">
                        <div
                            className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto"
                            style={{
                                background: isDragging ? 'rgba(59, 130, 246, 0.1)' : 'var(--bg-elevated)',
                                transition: 'all 0.2s'
                            }}
                        >
                            <svg
                                className="w-8 h-8"
                                style={{ color: isDragging ? 'var(--accent)' : 'var(--text-muted)' }}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                        </div>
                        <div>
                            <p className="font-medium">
                                {isDragging ? 'Drop your video here' : 'Drop a video file here'}
                            </p>
                            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                                or click to browse • MP4, WebM, MOV up to 500MB
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {error && (
                <div
                    className="mt-4 p-3 rounded-lg text-sm"
                    style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--error)' }}
                >
                    {error}
                </div>
            )}

            {selectedFile && !isUploading && (
                <button onClick={handleUpload} className="btn btn-primary btn-lg w-full mt-6">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Start Processing
                </button>
            )}
        </div>
    );
}
