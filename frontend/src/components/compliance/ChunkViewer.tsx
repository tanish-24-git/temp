/**
 * ChunkViewer Component
 * 
 * Displays individual chunk content with optional violation highlighting.
 * Used in Results page to show violation context at chunk level.
 */

import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { ContentChunk, Violation } from '../../lib/types';
import { formatChunkLocation } from '../../utils/ChunkLocationParser';

interface ChunkViewerProps {
    chunkId: string;
    submissionId: string;
    violations?: Violation[];
    showMetadata?: boolean;
    className?: string;
}

export const ChunkViewer: React.FC<ChunkViewerProps> = ({
    chunkId,
    submissionId,
    violations = [],
    showMetadata = true,
    className = ''
}) => {
    const [chunk, setChunk] = useState<ContentChunk | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchChunk();
    }, [chunkId, submissionId]);

    const fetchChunk = async () => {
        try {
            setLoading(true);
            setError(null);

            // Fetch all chunks for submission and find the one we need
            const response = await api.getSubmissionChunks(submissionId);
            const chunks: ContentChunk[] = response.data.chunks || [];

            const targetChunk = chunks.find(c => c.id === chunkId);

            if (targetChunk) {
                setChunk(targetChunk);
            } else {
                setError('Chunk not found');
            }
        } catch (err: any) {
            console.error('Failed to fetch chunk:', err);
            setError(err.message || 'Failed to load chunk');
        } finally {
            setLoading(false);
        }
    };

    const highlightViolations = (text: string): React.ReactNode => {
        if (!violations || violations.length === 0 || !text) {
            return text;
        }

        // Simple highlight: wrap violation current_text in span
        let highlightedText = text;
        violations.forEach((violation) => {
            if (violation.current_text && text.includes(violation.current_text)) {
                const regex = new RegExp(`(${escapeRegex(violation.current_text)})`, 'gi');
                highlightedText = highlightedText.replace(
                    regex,
                    '<mark class="bg-yellow-200 font-semibold">$1</mark>'
                );
            }
        });

        return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />;
    };

    const escapeRegex = (str: string): string => {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    };

    if (loading) {
        return (
            <div className={`bg-gray-50 rounded-lg p-6 ${className}`}>
                <div className="flex items-center justify-center space-x-2">
                    <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-gray-600">Loading chunk content...</span>
                </div>
            </div>
        );
    }

    if (error || !chunk) {
        return (
            <div className={`bg-red-50 rounded-lg p-4 border border-red-200 ${className}`}>
                <p className="text-red-800 text-sm">
                    ⚠️ {error || 'Failed to load chunk content'}
                </p>
            </div>
        );
    }

    return (
        <div className={`bg-white rounded-lg border border-gray-300 shadow-sm ${className}`}>
            {/* Chunk Metadata Header */}
            {showMetadata && (
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <div>
                                <p className="text-sm font-semibold text-gray-900">
                                    Chunk {chunk.chunk_index + 1}
                                </p>
                                <p className="text-xs text-gray-600">
                                    {formatChunkLocation(chunk.metadata)}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center space-x-4 text-xs text-gray-600">
                            {chunk.token_count && (
                                <span className="flex items-center space-x-1">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                                    </svg>
                                    <span>{chunk.token_count} tokens</span>
                                </span>
                            )}
                            {violations.length > 0 && (
                                <span className="flex items-center space-x-1 text-orange-600">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                    <span>{violations.length} violation{violations.length > 1 ? 's' : ''}</span>
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Chunk Content */}
            <div className="p-4">
                <div className="prose max-w-none">
                    <pre className="bg-gray-50 p-4 rounded-lg text-sm leading-relaxed whitespace-pre-wrap font-mono text-gray-800 overflow-x-auto">
                        {highlightViolations(chunk.text)}
                    </pre>
                </div>
            </div>

            {/* Footer with additional metadata */}
            {showMetadata && chunk.metadata && (
                <div className="bg-gray-50 px-4 py-2 border-t border-gray-200 text-xs text-gray-600">
                    <div className="flex items-center space-x-4">
                        {chunk.metadata.source_type && (
                            <span>Type: <strong>{chunk.metadata.source_type}</strong></span>
                        )}
                        {chunk.metadata.chunk_method && (
                            <span>Method: <strong>{chunk.metadata.chunk_method}</strong></span>
                        )}
                        {chunk.metadata.char_offset_start !== undefined && (
                            <span>
                                Position: <strong>{chunk.metadata.char_offset_start}</strong>
                                {chunk.metadata.char_offset_end && ` - ${chunk.metadata.char_offset_end}`}
                            </span>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChunkViewer;
