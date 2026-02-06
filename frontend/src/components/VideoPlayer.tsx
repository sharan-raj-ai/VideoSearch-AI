'use client';

import { useRef, useEffect, useState } from 'react';
import { api } from '@/lib/api';

interface VideoPlayerProps {
    videoId: string;
    seekToTimestamp?: number | null;
}

export default function VideoPlayer({ videoId, seekToTimestamp }: VideoPlayerProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const videoUrl = api.getVideoUrl(videoId);

    useEffect(() => {
        if (seekToTimestamp !== null && seekToTimestamp !== undefined && videoRef.current) {
            videoRef.current.currentTime = seekToTimestamp;
            videoRef.current.play();
            setIsPlaying(true);
        }
    }, [seekToTimestamp]);

    const handleTimeUpdate = () => {
        if (videoRef.current) {
            setCurrentTime(videoRef.current.currentTime);
        }
    };

    const handleLoadedMetadata = () => {
        if (videoRef.current) {
            setDuration(videoRef.current.duration);
            setIsLoading(false);
        }
    };

    const togglePlay = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause();
            } else {
                videoRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
        const time = parseFloat(e.target.value);
        if (videoRef.current) {
            videoRef.current.currentTime = time;
            setCurrentTime(time);
        }
    };

    const formatTime = (seconds: number): string => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="video-wrapper">
            {/* Video */}
            <div className="relative bg-black aspect-video">
                {isLoading && (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="spinner-lg" />
                    </div>
                )}

                <video
                    ref={videoRef}
                    src={videoUrl}
                    onTimeUpdate={handleTimeUpdate}
                    onLoadedMetadata={handleLoadedMetadata}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    className="w-full h-full object-contain"
                    onClick={togglePlay}
                />

                {/* Center play button on hover */}
                <button
                    onClick={togglePlay}
                    className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity bg-black/20"
                >
                    <div
                        className="w-16 h-16 rounded-full flex items-center justify-center"
                        style={{ background: 'var(--accent)' }}
                    >
                        {isPlaying ? (
                            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                            </svg>
                        ) : (
                            <svg className="w-6 h-6 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z" />
                            </svg>
                        )}
                    </div>
                </button>
            </div>

            {/* Controls */}
            <div className="p-4 space-y-3">
                {/* Progress */}
                <input
                    type="range"
                    min={0}
                    max={duration || 100}
                    value={currentTime}
                    onChange={handleSeek}
                    className="w-full h-1 rounded-full cursor-pointer appearance-none"
                    style={{
                        background: `linear-gradient(to right, var(--accent) 0%, var(--accent) ${(currentTime / duration) * 100}%, var(--bg-elevated) ${(currentTime / duration) * 100}%, var(--bg-elevated) 100%)`
                    }}
                />

                {/* Time & Play */}
                <div className="flex items-center justify-between">
                    <button onClick={togglePlay} className="btn btn-secondary" style={{ padding: '8px 12px' }}>
                        {isPlaying ? (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                            </svg>
                        ) : (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z" />
                            </svg>
                        )}
                    </button>

                    <div className="timestamp">
                        {formatTime(currentTime)} / {formatTime(duration)}
                    </div>
                </div>
            </div>
        </div>
    );
}
