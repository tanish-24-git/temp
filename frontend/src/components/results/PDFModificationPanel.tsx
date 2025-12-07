/**
 * PDFModificationPanel Component
 * Handles PDF modification operations - applying fixes and downloading modified PDFs
 */

import React, { useState, useCallback } from 'react';
import { PDFModificationPanelProps } from './analytics/types';
import { api } from '../../lib/api';

const PDFModificationPanel: React.FC<PDFModificationPanelProps> = ({
  submissionId,
  contentType,
  violationsCount,
  onFixesApplied,
}) => {
  const [applyingFixes, setApplyingFixes] = useState(false);
  const [fixesApplied, setFixesApplied] = useState(false);
  const [fixMessage, setFixMessage] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Don't render if not a PDF
  if (contentType !== 'pdf') {
    return null;
  }

  // Don't render if no violations to fix
  if (violationsCount === 0) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
        <div className="flex items-center space-x-3">
          <svg
            className="w-8 h-8 text-green-500 flex-shrink-0"
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
          <div>
            <h3 className="text-lg font-semibold text-green-900">
              No Modifications Needed
            </h3>
            <p className="text-sm text-green-700">
              Your PDF is fully compliant! No violations were found.
            </p>
          </div>
        </div>
      </div>
    );
  }

  /**
   * Handle applying fixes to the PDF
   */
  const handleApplyFixes = useCallback(async () => {
    setApplyingFixes(true);
    setError(null);
    setFixMessage('');

    try {
      const response = await api.applyPdfFixes(submissionId);

      setFixesApplied(true);
      setFixMessage(
        response.data.message ||
          `Successfully applied ${response.data.fixes_applied || 0} fixes`
      );

      // Notify parent component
      if (onFixesApplied) {
        onFixesApplied();
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        'Failed to apply fixes to PDF';
      setError(errorMessage);
      setFixMessage('');
    } finally {
      setApplyingFixes(false);
    }
  }, [submissionId, onFixesApplied]);

  /**
   * Handle downloading the modified PDF
   */
  const handleDownloadModified = useCallback(async () => {
    try {
      const response = await api.downloadModifiedPdf(submissionId);

      // Create a blob from the response data
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);

      // Create a temporary link element and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = `modified_submission_${submissionId}.pdf`;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        'Failed to download modified PDF';
      setError(errorMessage);
    }
  }, [submissionId]);

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6 mb-6 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-100 rounded-lg p-2">
            <svg
              className="w-6 h-6 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              PDF Modifications
            </h3>
            <p className="text-sm text-gray-600">
              Apply AI-suggested fixes directly to your PDF document
            </p>
          </div>
        </div>

        {/* Status Badge */}
        {fixesApplied && (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
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
                d="M5 13l4 4L19 7"
              />
            </svg>
            Fixes Applied
          </span>
        )}
      </div>

      {/* Info Box */}
      <div className="bg-white rounded-lg p-4 mb-4 border border-blue-100">
        <div className="flex items-start space-x-3">
          <svg
            className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div className="flex-1">
            <p className="text-sm text-gray-700">
              <span className="font-semibold">{violationsCount}</span>{' '}
              {violationsCount === 1 ? 'violation' : 'violations'} detected.
              Auto-fixable violations can be applied directly to the PDF with
              suggested replacements.
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <button
          onClick={handleApplyFixes}
          disabled={applyingFixes || fixesApplied}
          className={`flex-1 flex items-center justify-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all ${
            fixesApplied
              ? 'bg-green-100 text-green-700 cursor-not-allowed'
              : applyingFixes
              ? 'bg-blue-400 text-white cursor-wait'
              : 'bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 shadow-sm hover:shadow-md'
          }`}
        >
          {applyingFixes ? (
            <>
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              <span>Applying Fixes...</span>
            </>
          ) : fixesApplied ? (
            <>
              <svg
                className="w-5 h-5"
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
              <span>Fixes Applied</span>
            </>
          ) : (
            <>
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              <span>Apply Fixes to PDF</span>
            </>
          )}
        </button>

        <button
          onClick={handleDownloadModified}
          disabled={!fixesApplied}
          className={`flex-1 flex items-center justify-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all ${
            fixesApplied
              ? 'bg-indigo-600 text-white hover:bg-indigo-700 active:bg-indigo-800 shadow-sm hover:shadow-md'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          <span>Download Modified PDF</span>
        </button>
      </div>

      {/* Success Message */}
      {fixMessage && !error && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <svg
              className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0"
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
            <p className="text-sm text-green-800 font-medium">{fixMessage}</p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <svg
              className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0"
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
            <div className="flex-1">
              <p className="text-sm text-red-800 font-medium mb-1">
                Error occurred
              </p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      {!fixesApplied && (
        <div className="mt-4 text-xs text-gray-600">
          <p>
            <strong>Note:</strong> Only violations with suggested fixes can be
            automatically applied. Review the violations list below to see which
            fixes will be applied.
          </p>
        </div>
      )}
    </div>
  );
};

export default PDFModificationPanel;
