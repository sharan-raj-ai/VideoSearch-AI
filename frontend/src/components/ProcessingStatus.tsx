'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { JobStatusResponse } from '@/types/api';

interface ProcessingStatusProps {
    videoId: string;
    onComplete: () => void;
}

const STEPS = [
    { id: 1, label: 'Validating video', threshold: 0.1 },
    { id: 2, label: 'Extracting frames', threshold: 0.3 },
    { id: 3, label: 'Analyzing visuals', threshold: 0.6 },
    { id: 4, label: 'Processing audio', threshold: 0.8 },
    { id: 5, label: 'Building index', threshold: 1.0 },
];

export default function ProcessingStatus({ videoId, onComplete }: ProcessingStatusProps) {
    const [status, setStatus] = useState<JobStatusResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = useCallback(async () => {
        try {
            const data = await api.getJobStatus(videoId);
            setStatus(data);

            if (data.status === 'completed') {
                onComplete();
            } else if (data.status === 'failed') {
                setError(data.error || 'Processing failed');
            }
        } catch (err) {
            console.error('Failed to fetch status:', err);
        }
    }, [videoId, onComplete]);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(() => {
            if (status?.status !== 'completed' && status?.status !== 'failed') {
                fetchStatus();
            }
        }, 2000);
        return () => clearInterval(interval);
    }, [fetchStatus, status?.status]);

    const progress = status?.progress ?? 0;

    const getStepStatus = (threshold: number): 'done' | 'active' | 'pending' => {
        const prevThreshold = STEPS.find(s => s.threshold === threshold)?.id === 1
            ? 0
            : STEPS[STEPS.findIndex(s => s.threshold === threshold) - 1]?.threshold ?? 0;

        if (progress >= threshold) return 'done';
        if (progress > prevThreshold) return 'active';
        return 'pending';
    };

    return (
        <div className="card p-8">
            {/* Header */}
            <div className="flex items-center gap-4 mb-8">
                <div className="spinner-lg" />
                <div>
                    <h3 className="text-lg font-semibold">Processing your video</h3>
                    <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                        This may take a few minutes
                    </p>
                </div>
            </div>

            {/* Progress */}
            <div className="space-y-6">
                <div>
                    <div className="flex justify-between text-sm mb-2">
                        <span style={{ color: 'var(--text-secondary)' }}>Progress</span>
                        <span style={{ color: 'var(--accent)' }}>{Math.round(progress * 100)}%</span>
                    </div>
                    <div className="progress" style={{ height: '8px' }}>
                        <div className="progress-bar" style={{ width: `${progress * 100}%` }} />
                    </div>
                </div>

                {/* Steps */}
                <div className="space-y-3 pt-4">
                    {STEPS.map((step) => {
                        const stepStatus = getStepStatus(step.threshold);
                        return (
                            <div key={step.id} className="flex items-center gap-3">
                                <div
                                    className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium"
                                    style={{
                                        background: stepStatus === 'done'
                                            ? 'var(--success)'
                                            : stepStatus === 'active'
                                                ? 'var(--accent)'
                                                : 'var(--bg-elevated)',
                                        color: stepStatus === 'pending' ? 'var(--text-muted)' : 'white'
                                    }}
                                >
                                    {stepStatus === 'done' ? '✓' : step.id}
                                </div>
                                <span
                                    className="text-sm"
                                    style={{
                                        color: stepStatus === 'pending'
                                            ? 'var(--text-muted)'
                                            : 'var(--text-primary)'
                                    }}
                                >
                                    {step.label}
                                </span>
                                {stepStatus === 'active' && (
                                    <span
                                        className="ml-auto text-xs animate-pulse"
                                        style={{ color: 'var(--accent)' }}
                                    >
                                        In progress...
                                    </span>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Error */}
            {error && (
                <div
                    className="mt-6 p-4 rounded-lg"
                    style={{ background: 'rgba(239, 68, 68, 0.1)' }}
                >
                    <p className="font-medium" style={{ color: 'var(--error)' }}>Processing failed</p>
                    <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>{error}</p>
                </div>
            )}
        </div>
    );
}
