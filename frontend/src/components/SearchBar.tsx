'use client';

import { useState, FormEvent } from 'react';

interface SearchBarProps {
    onSearch: (query: string) => void;
    isLoading?: boolean;
    disabled?: boolean;
}

export default function SearchBar({ onSearch, isLoading = false, disabled = false }: SearchBarProps) {
    const [query, setQuery] = useState('');

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (query.trim() && !isLoading && !disabled) {
            onSearch(query.trim());
        }
    };

    const suggestions = ['person speaking', 'outdoor scene', 'red object', 'walking'];

    return (
        <div className="card p-6">
            <form onSubmit={handleSubmit}>
                <div className="relative">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Describe what you're looking for..."
                        disabled={disabled || isLoading}
                        className="input pr-28"
                        style={{ paddingLeft: '44px' }}
                    />

                    {/* Search icon */}
                    <div className="absolute left-4 top-1/2 -translate-y-1/2">
                        {isLoading ? (
                            <div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                        ) : (
                            <svg
                                className="w-5 h-5"
                                style={{ color: 'var(--text-muted)' }}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        )}
                    </div>

                    {/* Submit button */}
                    <button
                        type="submit"
                        disabled={!query.trim() || isLoading || disabled}
                        className="absolute right-2 top-1/2 -translate-y-1/2 btn btn-primary"
                        style={{ padding: '8px 16px' }}
                    >
                        Search
                    </button>
                </div>
            </form>

            {/* Quick suggestions */}
            {!disabled && (
                <div className="flex flex-wrap gap-2 mt-4">
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Try:</span>
                    {suggestions.map((s) => (
                        <button
                            key={s}
                            onClick={() => { setQuery(s); onSearch(s); }}
                            disabled={isLoading}
                            className="badge hover:bg-opacity-80 cursor-pointer transition-colors"
                            style={{ background: 'var(--bg-elevated)' }}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
