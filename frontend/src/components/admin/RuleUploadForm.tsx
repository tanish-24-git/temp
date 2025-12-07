import React, { useState } from 'react';
import { RuleGenerationResponse } from '../../lib/types';

interface RuleUploadFormProps {
  onUpload: (file: File, title: string) => Promise<void>;
  uploading: boolean;
  uploadResult: RuleGenerationResponse | null;
}

export const RuleUploadForm: React.FC<RuleUploadFormProps> = ({
  onUpload,
  uploading,
  uploadResult,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');

  const handleSubmit = async () => {
    if (!file || !title) return;
    await onUpload(file, title);
    setFile(null);
    setTitle('');
  };

  return (
    <div className="bg-white rounded-lg border p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">
        Generate Rules from Document
      </h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Document Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., IRDAI Marketing Guidelines 2024"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload Document (PDF, DOCX, HTML, MD)
          </label>
          <input
            type="file"
            accept=".pdf,.docx,.html,.htm,.md,.markdown"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
          />
          {file && (
            <p className="mt-2 text-sm text-gray-600">
              Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
            </p>
          )}
        </div>

        <button
          onClick={handleSubmit}
          disabled={uploading || !file || !title}
          className={`w-full px-6 py-3 rounded-lg font-medium transition-colors ${
            uploading || !file || !title
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {uploading ? (
            <span className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
              Generating Rules...
            </span>
          ) : (
            'Generate Rules'
          )}
        </button>
      </div>

      {/* Upload Result */}
      {uploadResult && (
        <div
          className={`mt-4 p-4 rounded-lg border ${
            uploadResult.success
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}
        >
          <div className="font-semibold mb-2">
            {uploadResult.success
              ? '✅ Rules Generated Successfully'
              : '⚠️ Rule Generation Completed with Errors'}
          </div>
          <div className="text-sm space-y-1">
            <div>
              <span className="font-medium">Created:</span> {uploadResult.rules_created} rules
            </div>
            <div>
              <span className="font-medium">Failed:</span> {uploadResult.rules_failed} rules
            </div>
            {uploadResult.errors.length > 0 && (
              <div className="mt-2">
                <div className="font-medium">Errors:</div>
                <ul className="list-disc list-inside space-y-1">
                  {uploadResult.errors.slice(0, 5).map((err, idx) => (
                    <li key={idx} className="text-xs text-red-700">
                      {err}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
