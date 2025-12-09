import React, { useState, useEffect, useRef } from 'react';
import { DeepAnalysisResponse, SeverityWeights, SEVERITY_PRESETS } from '../../lib/types';
import { SeverityWeightSlider } from './SeverityWeightSlider';
import { LineScoreCard } from './LineScoreCard';
import { api } from '../../lib/api';

interface Props {
    submissionId: string;
    onClose?: () => void;
    onAnalysisComplete?: () => void;
}

interface ProgressState {
    status: 'idle' | 'started' | 'processing' | 'classified' | 'complete' | 'error';
    progress: number;
    currentIndex: number;
    totalLines: number;
    currentLine?: {
        line_number: number;
        content: string;
    };
    lastResult?: {
        line_number: number;
        content: string;
        score: number;
        relevance_context: string;
        violations_count: number;
    };
    message?: string;
}

export const DeepAnalysisPanel: React.FC<Props> = ({ submissionId, onClose, onAnalysisComplete }) => {
    const [weights, setWeights] = useState<SeverityWeights>(SEVERITY_PRESETS.balanced);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [results, setResults] = useState<DeepAnalysisResponse | null>(null);
    const [filterScore, setFilterScore] = useState<number | null>(null);
    const [showOnlyViolations, setShowOnlyViolations] = useState(false);
    const [hasExistingResults, setHasExistingResults] = useState(false);

    // Progress state
    const [progress, setProgress] = useState<ProgressState>({
        status: 'idle',
        progress: 0,
        currentIndex: 0,
        totalLines: 0
    });
    const [classifiedChunks, setClassifiedChunks] = useState<Array<{
        line_number: number;
        content: string;
        score: number;
        relevance_context: string;
        violations_count: number;
    }>>([]);

    const progressRef = useRef<HTMLDivElement>(null);

    // Auto-load existing results when panel opens
    useEffect(() => {
        const checkExistingResults = async () => {
            try {
                const response = await api.getDeepAnalysisResults(submissionId);
                // Handle different statuses
                if (response.data) {
                    setResults(response.data);
                    setWeights(response.data.severity_config);

                    if (response.data.status === 'completed' && response.data.lines && response.data.lines.length > 0) {
                        setHasExistingResults(true);
                    } else if (response.data.status === 'processing') {
                        // If processing, we can either try to resume stream or just show loading state
                        // For now, let's show it as "Resume/In Progress" state
                        setHasExistingResults(true); // Show the results we have so far? Or show spinner?
                        // Actually, if it is processing, we might want to poll or just indicate it.
                        // Let's set a local status to indicate background processing if needed, 
                        // but for simplest UI fix:
                        if (response.data.lines.length === 0) {
                            // Started but no lines yet
                            setProgress(prev => ({ ...prev, status: 'processing', progress: 0, message: 'Analysis running in background...' }));
                            setLoading(true);
                        } else {
                            // Has partial lines
                            setHasExistingResults(true);
                        }
                    } else if (response.data.lines && response.data.lines.length > 0) {
                        // Fallback for legacy records without status
                        setHasExistingResults(true);
                    }
                }
            } catch {
                setHasExistingResults(false);
            }
        };
        checkExistingResults();
    }, [submissionId]);

    const runStreamingAnalysis = async () => {
        setLoading(true);
        setError(null);
        setResults(null);
        setClassifiedChunks([]);
        setProgress({ status: 'started', progress: 0, currentIndex: 0, totalLines: 0 });

        try {
            const response = await fetch(`http://localhost:8000/api/compliance/${submissionId}/deep-analyze/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ severity_weights: weights })
            });

            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value);
                const lines = text.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.status === 'error') {
                                setError(data.message);
                                setLoading(false);
                                return;
                            }

                            if (data.status === 'started') {
                                setProgress({
                                    status: 'started',
                                    progress: 0,
                                    currentIndex: 0,
                                    totalLines: data.total_lines
                                });
                            }

                            if (data.status === 'processing') {
                                setProgress(prev => ({
                                    ...prev,
                                    status: 'processing',
                                    progress: data.progress,
                                    currentIndex: data.current_index,
                                    totalLines: data.total_lines,
                                    currentLine: data.current_line
                                }));
                            }

                            if (data.status === 'classified') {
                                setProgress(prev => ({
                                    ...prev,
                                    status: 'classified',
                                    progress: data.progress,
                                    currentIndex: data.current_index,
                                    lastResult: data.last_result
                                }));

                                setClassifiedChunks(prev => [...prev, data.last_result]);

                                // Auto-scroll to latest
                                if (progressRef.current) {
                                    progressRef.current.scrollTop = progressRef.current.scrollHeight;
                                }
                            }

                            if (data.status === 'complete') {
                                setProgress({
                                    status: 'complete',
                                    progress: 100,
                                    currentIndex: data.total_lines,
                                    totalLines: data.total_lines
                                });

                                // Reload full results
                                const fullResults = await api.getDeepAnalysisResults(submissionId);
                                setResults(fullResults.data);
                                setHasExistingResults(true);
                                onAnalysisComplete?.();
                            }
                        } catch (parseError) {
                            // Ignore parse errors for incomplete chunks
                        }
                    }
                }
            }
        } catch (err: any) {
            setError(err.message || 'Failed to run deep analysis');
        } finally {
            setLoading(false);
        }
    };

    // Filter lines based on settings
    const filteredLines = results?.lines.filter(line => {
        if (filterScore !== null && line.line_score >= filterScore) return false;
        if (showOnlyViolations && (!line.rule_impacts || line.rule_impacts.length === 0)) return false;
        return true;
    }) || [];

    const getScoreGrade = (score: number): { grade: string; color: string } => {
        if (score >= 90) return { grade: 'A', color: 'text-green-600' };
        if (score >= 80) return { grade: 'B', color: 'text-green-500' };
        if (score >= 70) return { grade: 'C', color: 'text-yellow-600' };
        if (score >= 60) return { grade: 'D', color: 'text-orange-600' };
        return { grade: 'F', color: 'text-red-600' };
    };

    const getScoreColor = (score: number): string => {
        if (score >= 90) return 'bg-green-500';
        if (score >= 80) return 'bg-green-400';
        if (score >= 70) return 'bg-yellow-500';
        if (score >= 60) return 'bg-orange-500';
        return 'bg-red-500';
    };

    return (
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-5">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                            Deep Compliance Research Mode
                        </h2>
                        <p className="text-purple-100 text-sm mt-1">
                            Line-by-line analysis with custom severity weights
                        </p>
                    </div>
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="text-white/80 hover:text-white transition-colors"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    )}
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Severity Configuration */}
                <SeverityWeightSlider
                    weights={weights}
                    onChange={setWeights}
                    disabled={loading}
                />

                {/* Existing Results Indicator */}
                {hasExistingResults && results && !loading && (
                    <div className={`flex items-center gap-2 p-3 border rounded-xl ${results.status === 'processing'
                            ? 'bg-blue-50 border-blue-200'
                            : 'bg-green-50 border-green-200'
                        }`}>
                        {results.status === 'processing' ? (
                            <>
                                <svg className="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                                </svg>
                                <span className="text-sm text-blue-700">
                                    Analysis in progress in background... (Refresh to see latest)
                                </span>
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span className="text-sm text-green-700">
                                    Previous analysis loaded (analyzed {new Date(results.analysis_timestamp).toLocaleDateString()})
                                </span>
                            </>
                        )}
                    </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-4">
                    <button
                        onClick={runStreamingAnalysis}
                        disabled={loading}
                        className="flex-1 py-3 px-6 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                        {loading ? (
                            <>
                                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Analyzing... {progress.progress.toFixed(0)}%
                            </>
                        ) : (
                            <>
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                                {hasExistingResults ? 'Re-Run Analysis' : 'Run Deep Analysis'}
                            </>
                        )}
                    </button>
                </div>

                {/* Live Progress UI */}
                {loading && progress.status !== 'idle' && (
                    <div className="space-y-4 animate-fade-in">
                        {/* Progress Bar */}
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="font-medium text-gray-700">
                                    Analyzing line {progress.currentIndex} of {progress.totalLines}
                                </span>
                                <span className="text-purple-600 font-bold">{progress.progress.toFixed(1)}%</span>
                            </div>
                            <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300 ease-out"
                                    style={{ width: `${progress.progress}%` }}
                                />
                            </div>
                        </div>

                        {/* Current Line Being Analyzed */}
                        {progress.currentLine && (
                            <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl animate-pulse">
                                <div className="flex items-center gap-2 mb-2">
                                    <svg className="w-4 h-4 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                                    </svg>
                                    <span className="text-sm font-medium text-blue-700">Analyzing Line {progress.currentLine.line_number}...</span>
                                </div>
                                <p className="text-sm text-blue-600 font-mono">{progress.currentLine.content}</p>
                            </div>
                        )}

                        {/* Last Classified Chunk */}
                        {progress.lastResult && (
                            <div className="p-4 bg-white border-2 border-green-300 rounded-xl shadow-lg">
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span className="font-semibold text-gray-800">
                                            Line {progress.lastResult.line_number} Classified
                                        </span>
                                    </div>
                                    <div className={`px-3 py-1 rounded-full text-white font-bold ${getScoreColor(progress.lastResult.score)}`}>
                                        Score: {progress.lastResult.score}
                                    </div>
                                </div>
                                <p className="text-sm text-gray-700 mb-2 font-mono bg-gray-50 p-2 rounded">
                                    {progress.lastResult.content}
                                </p>
                                {progress.lastResult.relevance_context && (
                                    <p className="text-xs text-gray-500 italic">
                                        Context: {progress.lastResult.relevance_context}
                                    </p>
                                )}
                                {progress.lastResult.violations_count > 0 && (
                                    <div className="mt-2 flex items-center gap-1 text-xs text-red-600">
                                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                        </svg>
                                        {progress.lastResult.violations_count} violation(s) found
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Classified Chunks History */}
                        {classifiedChunks.length > 1 && (
                            <div className="space-y-2">
                                <h4 className="text-sm font-medium text-gray-600">Recently Classified:</h4>
                                <div ref={progressRef} className="max-h-48 overflow-y-auto space-y-2">
                                    {classifiedChunks.slice(-5).reverse().slice(1).map((chunk, idx) => (
                                        <div key={idx} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg text-sm">
                                            <span className="text-gray-400 w-12">#{chunk.line_number}</span>
                                            <div className={`w-2 h-2 rounded-full ${getScoreColor(chunk.score)}`} />
                                            <span className="flex-1 truncate text-gray-600">{chunk.content}</span>
                                            <span className={`font-bold ${chunk.score >= 80 ? 'text-green-600' : chunk.score >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                                                {chunk.score}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Error */}
                {error && (
                    <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
                        {error}
                    </div>
                )}

                {/* Results */}
                {results && !loading && (
                    <div className="space-y-6">
                        {/* Summary Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 text-center">
                                <p className="text-3xl font-bold text-blue-600">{results.total_lines}</p>
                                <p className="text-sm text-blue-600/70">Total Lines</p>
                            </div>
                            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 text-center">
                                <p className={`text-3xl font-bold ${getScoreGrade(results.average_score).color}`}>
                                    {results.average_score.toFixed(1)}
                                </p>
                                <p className="text-sm text-green-600/70">Avg Score</p>
                            </div>
                            <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl p-4 text-center">
                                <p className="text-3xl font-bold text-emerald-600">{results.max_score.toFixed(0)}</p>
                                <p className="text-sm text-emerald-600/70">Best Score</p>
                            </div>
                            <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-4 text-center">
                                <p className="text-3xl font-bold text-red-600">{results.min_score.toFixed(0)}</p>
                                <p className="text-sm text-red-600/70">Worst Score</p>
                            </div>
                            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 text-center">
                                <p className={`text-3xl font-bold ${getScoreGrade(results.average_score).color}`}>
                                    {getScoreGrade(results.average_score).grade}
                                </p>
                                <p className="text-sm text-purple-600/70">Grade</p>
                            </div>
                        </div>

                        {/* Filters */}
                        <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-50 rounded-xl">
                            <div className="flex items-center gap-2">
                                <label className="text-sm font-medium text-gray-600">Show lines with score below:</label>
                                <select
                                    value={filterScore ?? ''}
                                    onChange={(e) => setFilterScore(e.target.value ? parseInt(e.target.value) : null)}
                                    className="px-3 py-1.5 border rounded-lg text-sm"
                                >
                                    <option value="">All</option>
                                    <option value="100">100</option>
                                    <option value="90">90</option>
                                    <option value="80">80</option>
                                    <option value="70">70</option>
                                    <option value="50">50</option>
                                </select>
                            </div>

                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={showOnlyViolations}
                                    onChange={(e) => setShowOnlyViolations(e.target.checked)}
                                    className="w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                                />
                                <span className="text-sm text-gray-600">Only show lines with violations</span>
                            </label>

                            <div className="ml-auto text-sm text-gray-500">
                                Showing {filteredLines.length} of {results.lines.length} lines
                            </div>
                        </div>

                        {/* Line Cards */}
                        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
                            {filteredLines.map((line) => (
                                <LineScoreCard key={line.line_number} line={line} />
                            ))}

                            {filteredLines.length === 0 && (
                                <div className="text-center py-12 text-gray-500">
                                    No lines match the current filters
                                </div>
                            )}
                        </div>

                        {/* Analysis Metadata */}
                        <div className="text-xs text-gray-400 pt-4 border-t flex justify-between">
                            <span>Document: {results.document_title}</span>
                            <span>Analyzed: {new Date(results.analysis_timestamp).toLocaleString()}</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DeepAnalysisPanel;
