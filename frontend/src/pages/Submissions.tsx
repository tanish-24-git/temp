import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../lib/api';
import { Submission } from '../lib/types';
import { format } from 'date-fns';
import { BrainCircuit } from 'lucide-react';

export const Submissions: React.FC = () => {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [deletingAll, setDeletingAll] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const fetchSubmissions = async () => {
    try {
      const response = await api.getSubmissions();
      setSubmissions(response.data);
    } catch (error) {
      console.error('Failed to fetch submissions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (id: string) => {
    setActionLoading(prev => ({ ...prev, [id]: true }));
    try {
      await api.analyzeSubmission(id);
      // Refresh submissions
      await fetchSubmissions();
      // Navigate to results
      navigate(`/results/${id}`);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please try again.');
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  const handlePreprocess = async (id: string) => {
    setActionLoading(prev => ({ ...prev, [id]: true }));
    try {
      await api.triggerPreprocessing(id);
      // Refresh submissions to show new status
      await fetchSubmissions();
    } catch (error) {
      console.error('Preprocessing failed:', error);
      alert('Preprocessing failed. Please try again.');
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this submission? This action cannot be undone.')) {
      return;
    }
    setActionLoading(prev => ({ ...prev, [id]: true }));
    try {
      await api.deleteSubmission(id);
      // Refresh submissions
      await fetchSubmissions();
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete submission. Please try again.');
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  const handleDeleteAll = async () => {
    if (submissions.length === 0) {
      alert('No submissions to delete.');
      return;
    }

    if (!confirm(`Are you sure you want to delete ALL ${submissions.length} submission(s)? This action cannot be undone and will permanently delete all submissions and their files.`)) {
      return;
    }

    setDeletingAll(true);
    try {
      const response = await api.deleteAllSubmissions();
      alert(response.data.message);
      // Refresh submissions
      await fetchSubmissions();
    } catch (error) {
      console.error('Delete all failed:', error);
      alert('Failed to delete all submissions. Please try again.');
    } finally {
      setDeletingAll(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      // Legacy statuses
      pending: 'bg-yellow-100 text-yellow-800',

      // New chunked workflow statuses
      uploaded: 'bg-yellow-100 text-yellow-800',
      preprocessing: 'bg-indigo-100 text-indigo-800',
      preprocessed: 'bg-purple-100 text-purple-800',
      analyzing: 'bg-blue-100 text-blue-800',
      analyzed: 'bg-green-100 text-green-800',

      // Legacy completed status
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status}
      </span>
    );
  };

  if (loading) {
    return <div className="text-center py-12">Loading...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold text-gray-900">Submissions</h2>
        {submissions.length > 0 && (
          <button
            onClick={handleDeleteAll}
            disabled={deletingAll}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${deletingAll
              ? 'bg-red-400 text-white cursor-not-allowed'
              : 'bg-red-600 text-white hover:bg-red-700'
              }`}
          >
            {deletingAll ? 'Deleting All...' : 'Delete All Submissions'}
          </button>
        )}
      </div>

      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Submitted
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {submissions.map((submission) => (
              <tr key={submission.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                  {submission.title}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {submission.content_type.toUpperCase()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    {getStatusBadge(submission.status)}
                    {submission.has_deep_analysis && (
                      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800 border border-purple-200" title="Deep Analysis Ready">
                        <BrainCircuit className="w-3 h-3" />
                        Deep Analyzed
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {format(new Date(submission.submitted_at), 'MMM dd, yyyy')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex gap-2">
                    {/* Preprocess Button - Only for 'uploaded' or legacy 'pending' status */}
                    {(submission.status === 'uploaded' || submission.status === 'pending') && (
                      <button
                        onClick={() => handlePreprocess(submission.id)}
                        disabled={actionLoading[submission.id]}
                        className={`font-medium px-3 py-1 rounded ${actionLoading[submission.id]
                          ? 'bg-purple-100 text-purple-400 cursor-not-allowed'
                          : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}
                      >
                        {actionLoading[submission.id] ? 'Chunking...' : 'Preprocess'}
                      </button>
                    )}

                    {/* Analyze Button - Only for 'preprocessed' or legacy 'pending' status */}
                    {(submission.status === 'preprocessed' ||
                      submission.status === 'pending') && (
                        <button
                          onClick={() => handleAnalyze(submission.id)}
                          disabled={actionLoading[submission.id]}
                          className={`font-medium px-3 py-1 rounded ${actionLoading[submission.id]
                            ? 'bg-blue-100 text-blue-400 cursor-not-allowed'
                            : 'bg-blue-600 text-white hover:bg-blue-700'}`}
                        >
                          {actionLoading[submission.id] ? 'Analyzing...' : 'Analyze'}
                        </button>
                      )}

                    {/* Show progress for preprocessing/analyzing */}
                    {(submission.status === 'preprocessing' || submission.status === 'analyzing') && (
                      <span className="text-blue-600 font-medium px-3 py-1 animate-pulse">
                        {submission.status === 'preprocessing' ? 'Chunking Content...' : 'Running Compliance Checks...'}
                      </span>
                    )}

                    {/* Show View Results for analyzed or completed */}
                    {(submission.status === 'analyzed' || submission.status === 'completed') && (
                      <button
                        onClick={() => navigate(`/results/${submission.id}`)}
                        className="bg-green-600 text-white hover:bg-green-700 font-medium px-3 py-1 rounded"
                      >
                        View Results
                      </button>
                    )}

                    {/* Delete button always available */}
                    <button
                      onClick={() => handleDelete(submission.id)}
                      disabled={actionLoading[submission.id]}
                      className={`font-medium px-3 py-1 rounded ${actionLoading[submission.id]
                        ? 'bg-red-100 text-red-400 cursor-not-allowed'
                        : 'bg-red-600 text-white hover:bg-red-700'}`}
                    >
                      {actionLoading[submission.id] ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {submissions.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No submissions yet. Upload content to get started.
          </div>
        )}
      </div>
    </div>
  );
};
