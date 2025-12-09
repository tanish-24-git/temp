import React, { useState } from 'react';
import { LineAnalysis, RuleImpact } from '../../lib/types';

interface Props {
    line: LineAnalysis;
    isExpanded?: boolean;
    onToggle?: () => void;
}

const getScoreColor = (score: number): string => {
    if (score >= 90) return 'bg-green-500';
    if (score >= 70) return 'bg-yellow-500';
    if (score >= 50) return 'bg-orange-500';
    return 'bg-red-500';
};

const getScoreBgColor = (score: number): string => {
    if (score >= 90) return 'bg-green-50 border-green-200';
    if (score >= 70) return 'bg-yellow-50 border-yellow-200';
    if (score >= 50) return 'bg-orange-50 border-orange-200';
    return 'bg-red-50 border-red-200';
};

const getSeverityBadge = (severity: string): string => {
    switch (severity.toLowerCase()) {
        case 'critical':
            return 'bg-red-100 text-red-800';
        case 'high':
            return 'bg-orange-100 text-orange-800';
        case 'medium':
            return 'bg-yellow-100 text-yellow-800';
        case 'low':
            return 'bg-blue-100 text-blue-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
};

export const LineScoreCard: React.FC<Props> = ({
    line,
    isExpanded = false,
    onToggle
}) => {
    const [expanded, setExpanded] = useState(isExpanded);
    const hasViolations = line.rule_impacts && line.rule_impacts.length > 0;

    const handleToggle = () => {
        setExpanded(!expanded);
        onToggle?.();
    };

    return (
        <div className={`border rounded-lg overflow-hidden transition-all duration-200 ${getScoreBgColor(line.line_score)}`}>
            {/* Header Row */}
            <div
                className="flex items-center gap-4 p-4 cursor-pointer hover:bg-white/50 transition-colors"
                onClick={handleToggle}
            >
                {/* Line Number */}
                <div className="flex-shrink-0 w-12 text-center">
                    <span className="text-sm font-mono text-gray-500">#{line.line_number}</span>
                </div>

                {/* Score Badge */}
                <div className="flex-shrink-0">
                    <div className={`w-14 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm ${getScoreColor(line.line_score)}`}>
                        {line.line_score.toFixed(0)}
                    </div>
                </div>

                {/* Line Content */}
                <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 truncate font-mono">
                        {line.line_content}
                    </p>
                    {line.relevance_context && (
                        <p className="text-xs text-gray-500 mt-1 truncate">
                            {line.relevance_context}
                        </p>
                    )}
                </div>

                {/* Violation Count */}
                {hasViolations && (
                    <div className="flex-shrink-0">
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700">
                            {line.rule_impacts.length} violation{line.rule_impacts.length > 1 ? 's' : ''}
                        </span>
                    </div>
                )}

                {/* Expand/Collapse Icon */}
                <div className="flex-shrink-0">
                    <svg
                        className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>
            </div>

            {/* Expanded Details */}
            {expanded && (
                <div className="border-t bg-white p-4 space-y-4">
                    {/* Full Line Content */}
                    <div>
                        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                            Full Content
                        </h4>
                        <div className="p-3 bg-gray-50 rounded-lg font-mono text-sm text-gray-800 whitespace-pre-wrap">
                            {line.line_content}
                        </div>
                    </div>

                    {/* Relevance Context */}
                    {line.relevance_context && (
                        <div>
                            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                                Relevance Context
                            </h4>
                            <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
                                {line.relevance_context}
                            </div>
                        </div>
                    )}

                    {/* Rule Impact Breakdown */}
                    {hasViolations && (
                        <div>
                            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                                Rule Impact Breakdown
                            </h4>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b">
                                            <th className="text-left py-2 px-3 font-medium text-gray-600">Category</th>
                                            <th className="text-left py-2 px-3 font-medium text-gray-600">Severity</th>
                                            <th className="text-left py-2 px-3 font-medium text-gray-600">Rule</th>
                                            <th className="text-right py-2 px-3 font-medium text-gray-600">Base</th>
                                            <th className="text-right py-2 px-3 font-medium text-gray-600">Weight</th>
                                            <th className="text-right py-2 px-3 font-medium text-gray-600">Deduction</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {line.rule_impacts.map((impact, idx) => (
                                            <tr key={idx} className="border-b last:border-b-0 hover:bg-gray-50">
                                                <td className="py-2 px-3">
                                                    <span className="px-2 py-0.5 text-xs font-medium rounded bg-gray-100 text-gray-700 uppercase">
                                                        {impact.category}
                                                    </span>
                                                </td>
                                                <td className="py-2 px-3">
                                                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${getSeverityBadge(impact.severity)}`}>
                                                        {impact.severity.toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="py-2 px-3 max-w-xs">
                                                    <p className="truncate text-gray-700" title={impact.rule_text}>
                                                        {impact.rule_text.substring(0, 60)}...
                                                    </p>
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        {impact.violation_reason}
                                                    </p>
                                                </td>
                                                <td className="py-2 px-3 text-right font-mono text-gray-600">
                                                    {impact.base_deduction.toFixed(1)}
                                                </td>
                                                <td className="py-2 px-3 text-right font-mono text-gray-600">
                                                    {impact.weight_multiplier.toFixed(1)}x
                                                </td>
                                                <td className="py-2 px-3 text-right font-mono font-bold text-red-600">
                                                    {impact.weighted_deduction.toFixed(1)}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {/* No Violations Message */}
                    {!hasViolations && (
                        <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
                            <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            <span className="text-sm text-green-700">No violations detected for this line</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default LineScoreCard;
