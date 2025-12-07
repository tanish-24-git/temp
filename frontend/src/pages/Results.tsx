/**
 * Results Page - Compliance Check Results with Analytics
 * Displays comprehensive compliance analysis with interactive charts and PDF modification
 */

import React, { useEffect, useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../lib/api';
import { ComplianceCheck, Submission } from '../lib/types';

// Analytics Components
import ScoreComparisonRadar from '../components/results/analytics/ScoreComparisonRadar';
import ViolationDistributionCharts from '../components/results/analytics/ViolationDistributionCharts';
import SeverityHeatmap from '../components/results/analytics/SeverityHeatmap';
import AutoFixabilityAnalysis from '../components/results/analytics/AutoFixabilityAnalysis';
import PDFModificationPanel from '../components/results/PDFModificationPanel';

export const Results: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [results, setResults] = useState<ComplianceCheck | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchResults();
    }
  }, [id]);

  const fetchResults = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch compliance results
      const resultsResponse = await api.getComplianceResults(id!);
      setResults(resultsResponse.data);

      // Fetch submission details for PDF functionality
      try {
        const submissionResponse = await api.getSubmissionById(id!);
        setSubmission(submissionResponse.data);
      } catch (err) {
        console.warn('Could not fetch submission details:', err);
      }
    } catch (error: any) {
      console.error('Failed to fetch results:', error);
      setError(
        error.response?.data?.detail ||
          error.message ||
          'Failed to load compliance results'
      );
    } finally {
      setLoading(false);
    }
  };

  // Utility functions
  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-blue-100 text-blue-800 border-blue-300',
    };
    return colors[severity] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 60) return 'text-orange-600';
    return 'text-red-600';
  };

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { bg: string; text: string; label: string }> = {
      passed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Passed' },
      flagged: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Flagged' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: 'Failed' },
    };
    const badge = badges[status] || badges.flagged;
    return (
      <span
        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${badge.bg} ${badge.text}`}
      >
        {badge.label}
      </span>
    );
  };

  // Loading State
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-blue-200 rounded-full"></div>
          <div className="w-16 h-16 border-4 border-blue-600 rounded-full border-t-transparent animate-spin absolute top-0 left-0"></div>
        </div>
        <p className="mt-4 text-gray-600 font-medium">Loading compliance results...</p>
      </div>
    );
  }

  // Error State
  if (error || !results) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <svg
          className="w-20 h-20 text-red-500 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Failed to Load Results
        </h3>
        <p className="text-gray-600 mb-6 text-center max-w-md">
          {error || 'No results found for this submission'}
        </p>
        <button
          onClick={fetchResults}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Compliance Analysis Report
            </h2>
            <p className="text-gray-700 leading-relaxed">{results.ai_summary}</p>
          </div>
          <div className="ml-6">{getStatusBadge(results.status)}</div>
        </div>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center space-x-2">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span>
              Checked on {new Date(results.check_date).toLocaleDateString()}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <span>Submission ID: {results.submission_id.slice(0, 8)}...</span>
          </div>
        </div>
      </div>

      {/* PDF Modification Panel (if applicable) */}
      {submission && (
        <PDFModificationPanel
          submissionId={results.submission_id}
          contentType={submission.content_type}
          violationsCount={results.violations.length}
          onFixesApplied={fetchResults}
        />
      )}

      {/* Executive Summary - Enhanced Score Cards */}
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Executive Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Overall Score */}
          <div className="bg-white rounded-lg border-2 border-gray-300 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="text-sm font-medium text-gray-600 mb-2">
              Overall Score
            </div>
            <div
              className={`text-4xl font-bold ${getScoreColor(
                results.overall_score
              )} mb-2`}
            >
              {results.overall_score.toFixed(1)}%
            </div>
            <div className="mb-3">
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-gray-100 text-gray-800">
                Grade: {results.grade}
              </span>
            </div>
            <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getScoreColor(
                  results.overall_score
                ).replace('text-', 'bg-')}`}
                style={{ width: `${results.overall_score}%` }}
              />
            </div>
          </div>

          {/* IRDAI Score */}
          <div className="bg-white rounded-lg border border-blue-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-blue-500"></div>
              <div className="text-sm font-medium text-gray-600">
                IRDAI Compliance
              </div>
            </div>
            <div
              className={`text-4xl font-bold ${getScoreColor(
                results.irdai_score
              )} mb-2`}
            >
              {results.irdai_score.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600 mb-3">50% weight</div>
            <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getScoreColor(
                  results.irdai_score
                ).replace('text-', 'bg-')}`}
                style={{ width: `${results.irdai_score}%` }}
              />
            </div>
          </div>

          {/* Brand Score */}
          <div className="bg-white rounded-lg border border-violet-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-violet-500"></div>
              <div className="text-sm font-medium text-gray-600">
                Brand Guidelines
              </div>
            </div>
            <div
              className={`text-4xl font-bold ${getScoreColor(
                results.brand_score
              )} mb-2`}
            >
              {results.brand_score.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600 mb-3">30% weight</div>
            <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getScoreColor(
                  results.brand_score
                ).replace('text-', 'bg-')}`}
                style={{ width: `${results.brand_score}%` }}
              />
            </div>
          </div>

          {/* SEO Score */}
          <div className="bg-white rounded-lg border border-cyan-200 p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-cyan-500"></div>
              <div className="text-sm font-medium text-gray-600">SEO Health</div>
            </div>
            <div
              className={`text-4xl font-bold ${getScoreColor(
                results.seo_score
              )} mb-2`}
            >
              {results.seo_score.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600 mb-3">20% weight</div>
            <div className="bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${getScoreColor(
                  results.seo_score
                ).replace('text-', 'bg-')}`}
                style={{ width: `${results.seo_score}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Dashboard */}
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Detailed Analytics
        </h3>

        {/* Top Row: Score Comparison & Violation Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <ScoreComparisonRadar results={results} height={400} />
          <ViolationDistributionCharts
            violations={results.violations}
            height={350}
          />
        </div>

        {/* Bottom Row: Heatmap & Auto-Fixability */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SeverityHeatmap violations={results.violations} height={350} />
          <AutoFixabilityAnalysis violations={results.violations} height={350} />
        </div>
      </div>

      {/* Violations List */}
      <div>
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Detailed Violations ({results.violations.length})
        </h3>

        <div className="bg-white rounded-lg border p-6">
          {results.violations.length > 0 ? (
            <div className="space-y-4">
              {results.violations.map((violation, index) => (
                <div
                  key={violation.id}
                  className={`border rounded-lg p-5 ${getSeverityColor(
                    violation.severity
                  )} hover:shadow-md transition-shadow`}
                >
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-gray-700">
                        #{index + 1}
                      </span>
                      <span className="px-3 py-1 text-xs font-bold rounded-full bg-white shadow-sm">
                        {violation.severity.toUpperCase()}
                      </span>
                      <span className="px-3 py-1 text-xs font-medium rounded-full bg-white shadow-sm">
                        {violation.category.toUpperCase()}
                      </span>
                    </div>
                    {violation.is_auto_fixable && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800">
                        <svg
                          className="w-3 h-3 mr-1"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                        Auto-Fixable
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="font-semibold text-gray-900 mb-3 text-base">
                    {violation.description}
                  </p>

                  {/* Location */}
                  {violation.location && (
                    <div className="mb-3 flex items-start space-x-2">
                      <svg
                        className="w-4 h-4 text-gray-600 mt-0.5 flex-shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                      </svg>
                      <p className="text-sm text-gray-700">
                        <span className="font-medium">Location:</span>{' '}
                        {violation.location}
                      </p>
                    </div>
                  )}

                  {/* Current Text */}
                  {violation.current_text && (
                    <div className="bg-white/70 p-3 rounded-lg mb-3 border border-gray-300">
                      <p className="text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wide">
                        Current Text:
                      </p>
                      <p className="text-sm text-gray-900 leading-relaxed">
                        {violation.current_text}
                      </p>
                    </div>
                  )}

                  {/* Suggested Fix */}
                  {violation.suggested_fix && (
                    <div className="bg-white/90 p-3 rounded-lg border-2 border-green-300">
                      <p className="text-xs font-semibold text-green-800 mb-1 uppercase tracking-wide flex items-center">
                        <svg
                          className="w-4 h-4 mr-1"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        Suggested Fix:
                      </p>
                      <p className="text-sm text-gray-900 leading-relaxed font-medium">
                        {violation.suggested_fix}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <svg
                className="w-20 h-20 text-green-500 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <h4 className="text-xl font-semibold text-gray-900 mb-2">
                Perfect Compliance!
              </h4>
              <p className="text-gray-600">
                No violations found. Your content meets all compliance requirements.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
