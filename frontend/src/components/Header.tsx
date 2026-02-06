'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';

export default function Header() {
    const [isOnline, setIsOnline] = useState<boolean | null>(null);

    useEffect(() => {
        const checkHealth = async () => {
            try {
                const health = await api.health();
                setIsOnline(health.qdrant && health.redis);
            } catch {
                setIsOnline(false);
            }
        };

        checkHealth();
        const interval = setInterval(checkHealth, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <header
            className="fixed top-0 left-0 right-0 z-50 backdrop-blur-lg"
            style={{
                background: 'rgba(9, 9, 11, 0.8)',
                borderBottom: '1px solid var(--border)'
            }}
        >
            <div className="container">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <div className="flex items-center gap-3">
                        <div
                            className="w-8 h-8 rounded-lg flex items-center justify-center"
                            style={{ background: 'var(--accent)' }}
                        >
                            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <span className="font-semibold text-lg tracking-tight">
                            VideoSearch
                            <span style={{ color: 'var(--accent)' }}>.ai</span>
                        </span>
                    </div>

                    {/* Status */}
                    <div className="flex items-center gap-3">
                        <div
                            className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
                            style={{
                                background: isOnline
                                    ? 'rgba(16, 185, 129, 0.1)'
                                    : isOnline === false
                                        ? 'rgba(239, 68, 68, 0.1)'
                                        : 'rgba(245, 158, 11, 0.1)',
                                color: isOnline
                                    ? 'var(--success)'
                                    : isOnline === false
                                        ? 'var(--error)'
                                        : 'var(--warning)'
                            }}
                        >
                            <span
                                className={`w-2 h-2 rounded-full ${isOnline === null ? 'animate-pulse' : ''}`}
                                style={{
                                    background: isOnline
                                        ? 'var(--success)'
                                        : isOnline === false
                                            ? 'var(--error)'
                                            : 'var(--warning)'
                                }}
                            />
                            {isOnline === null ? 'Connecting...' : isOnline ? 'Online' : 'Offline'}
                        </div>
                    </div>
                </div>
            </div>
        </header>
    );
}
