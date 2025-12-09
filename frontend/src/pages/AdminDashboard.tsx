import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { Rule, RuleStats, RuleGenerationResponse, DraftRule, RulePreviewResponse, RuleBulkSubmitResponse } from '../lib/types';
import {
  RuleStatsCards,
  RuleUploadForm,
  RuleFilters,
  RulesTable,
  Pagination,
  RuleEditModal,
  RulePreviewPanel,
} from '../components/admin';

// POC: Hard-coded super admin user ID
// In production: Get from authentication context/JWT
const SUPER_ADMIN_USER_ID = '11111111-1111-1111-1111-111111111111';

type TabType = 'active' | 'deactivated';

export default function AdminDashboard() {
  // Tab state
  const [activeTab, setActiveTab] = useState<TabType>('active');

  // Data state
  const [rules, setRules] = useState<Rule[]>([]);
  const [stats, setStats] = useState<RuleStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalRules, setTotalRules] = useState(0);

  // Filter state
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<RuleGenerationResponse | null>(null);

  // Preview state (new workflow)
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState<RulePreviewResponse | null>(null);
  const [draftRules, setDraftRules] = useState<DraftRule[]>([]);

  // Edit modal state
  const [editingRule, setEditingRule] = useState<Rule | null>(null);

  // Delete all state
  const [deletingAll, setDeletingAll] = useState(false);

  // Fetch rules based on current tab
  const fetchRules = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.getRules({
        page: currentPage,
        page_size: 20,
        category: categoryFilter || undefined,
        severity: severityFilter || undefined,
        is_active: activeTab === 'active' ? true : false,
        search: searchQuery || undefined,
        userId: SUPER_ADMIN_USER_ID,
      });

      const data = response.data;
      setRules(data.rules);
      setTotalPages(data.total_pages);
      setTotalRules(data.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch rules');
    } finally {
      setLoading(false);
    }
  };

  // Fetch stats
  const fetchStats = async () => {
    try {
      setStatsLoading(true);
      const response = await api.getRuleStats(SUPER_ADMIN_USER_ID);
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setStatsLoading(false);
    }
  };

  // Reset page when switching tabs
  useEffect(() => {
    setCurrentPage(1);
  }, [activeTab]);

  // Fetch rules when dependencies change
  useEffect(() => {
    fetchRules();
  }, [currentPage, categoryFilter, severityFilter, activeTab, searchQuery]);

  useEffect(() => {
    fetchStats();
  }, []);

  // Handle file upload - NEW PREVIEW WORKFLOW
  const handleUpload = async (file: File, documentTitle: string) => {
    try {
      setUploading(true);
      setError(null);
      setUploadResult(null);
      setPreviewData(null);

      // Use preview endpoint instead of generate
      const response = await api.previewRulesFromDocument(
        file,
        documentTitle,
        SUPER_ADMIN_USER_ID
      );

      const result: RulePreviewResponse = response.data;
      setPreviewData(result);

      if (result.success && result.draft_rules.length > 0) {
        setDraftRules(result.draft_rules);
        setShowPreview(true);
      } else if (result.errors.length > 0) {
        setError(result.errors.join(', '));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate rule preview');
    } finally {
      setUploading(false);
    }
  };

  // Handle preview submit success
  const handlePreviewSubmitSuccess = async (response: RuleBulkSubmitResponse) => {
    setShowPreview(false);
    setPreviewData(null);
    setDraftRules([]);

    // Show success message as uploadResult for compatibility
    setUploadResult({
      success: response.success,
      rules_created: response.rules_created,
      rules_failed: response.rules_failed,
      rules: [],
      errors: response.errors,
    });

    // Refresh rules list and stats
    await fetchRules();
    await fetchStats();
  };

  // Handle preview cancel
  const handlePreviewCancel = () => {
    setShowPreview(false);
    setPreviewData(null);
    setDraftRules([]);
  };

  // Handle rule update
  const handleUpdateRule = async (ruleId: string, updates: Partial<Rule>) => {
    try {
      await api.updateRule(ruleId, updates, SUPER_ADMIN_USER_ID);
      await fetchRules();
      await fetchStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update rule');
      throw err;
    }
  };

  // Handle rule delete (deactivate)
  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to deactivate this rule?')) return;

    try {
      await api.deleteRule(ruleId, SUPER_ADMIN_USER_ID);
      await fetchRules();
      await fetchStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete rule');
    }
  };

  // Handle rule restore (reactivate)
  const handleRestoreRule = async (ruleId: string) => {
    try {
      await api.updateRule(ruleId, { is_active: true }, SUPER_ADMIN_USER_ID);
      await fetchRules();
      await fetchStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to restore rule');
    }
  };

  // Handle delete all rules
  const handleDeleteAllRules = async () => {
    if (rules.length === 0) {
      alert('No rules to delete.');
      return;
    }

    if (!confirm(`Are you sure you want to deactivate ALL ${totalRules} rule(s)? This will soft-delete all rules (they can be restored from the Deactivated tab).`)) {
      return;
    }

    setDeletingAll(true);
    try {
      const response = await api.deleteAllRules(SUPER_ADMIN_USER_ID);
      alert(response.data.message);
      await fetchRules();
      await fetchStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete all rules');
    } finally {
      setDeletingAll(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Admin Dashboard</h2>
          <p className="text-gray-500 mt-1">Manage compliance rules and generation</p>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center">
            <svg
              className="w-5 h-5 mr-2"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <RuleStatsCards stats={stats} loading={statsLoading} />

      {/* Severity Points Configuration Reference */}
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            Severity Points Configuration
          </h3>
          <span className="text-xs text-gray-500">Click on rule's "Edit" to customize points</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Critical */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-sm font-medium text-red-800">Critical</span>
            </div>
            <div className="text-2xl font-bold text-red-600">-20</div>
            <div className="text-xs text-red-600/70 mt-1">Severe penalty</div>
          </div>

          {/* High */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-orange-500"></div>
              <span className="text-sm font-medium text-orange-800">High</span>
            </div>
            <div className="text-2xl font-bold text-orange-600">-10</div>
            <div className="text-xs text-orange-600/70 mt-1">Significant penalty</div>
          </div>

          {/* Medium */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <span className="text-sm font-medium text-yellow-800">Medium</span>
            </div>
            <div className="text-2xl font-bold text-yellow-600">-5</div>
            <div className="text-xs text-yellow-600/70 mt-1">Moderate penalty</div>
          </div>

          {/* Low */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-sm font-medium text-blue-800">Low</span>
            </div>
            <div className="text-2xl font-bold text-blue-600">-2</div>
            <div className="text-xs text-blue-600/70 mt-1">Minor penalty</div>
          </div>
        </div>

        <p className="text-xs text-gray-500 mt-4 text-center">
          These are the default point deductions per severity. Each rule can be customized individually using the Edit button.
        </p>
      </div>

      {/* Rule Preview Panel - Shows when previewing generated rules */}
      {showPreview && previewData && (
        <RulePreviewPanel
          documentTitle={previewData.document_title}
          draftRules={draftRules}
          totalExtracted={previewData.total_extracted}
          errors={previewData.errors}
          onRulesChange={setDraftRules}
          onSubmitSuccess={handlePreviewSubmitSuccess}
          onCancel={handlePreviewCancel}
        />
      )}

      {/* Upload Section - Only show on Active tab and when NOT previewing */}
      {activeTab === 'active' && !showPreview && (
        <RuleUploadForm
          onUpload={handleUpload}
          uploading={uploading}
          uploadResult={uploadResult}
        />
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('active')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'active'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
          >
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              Active Rules
              {stats && (
                <span className="bg-blue-100 text-blue-600 text-xs px-2 py-0.5 rounded-full">
                  {stats.active_rules}
                </span>
              )}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('deactivated')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'deactivated'
              ? 'border-red-500 text-red-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
          >
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              Deactivated Rules
              {stats && (
                <span className="bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full">
                  {stats.inactive_rules}
                </span>
              )}
            </span>
          </button>
        </nav>
      </div>

      {/* Filters */}
      <RuleFilters
        categoryFilter={categoryFilter}
        severityFilter={severityFilter}
        activeFilter={undefined} // Hidden since tabs handle this
        searchQuery={searchQuery}
        onCategoryChange={setCategoryFilter}
        onSeverityChange={setSeverityFilter}
        onActiveChange={() => { }} // No-op since tabs handle this
        onSearchChange={setSearchQuery}
        hideActiveFilter={true}
      />

      {/* Rules Table */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">
            {activeTab === 'active' ? 'Active Rules' : 'Deactivated Rules'}
            {totalRules > 0 && (
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({totalRules} total)
              </span>
            )}
          </h2>
          {activeTab === 'active' && (
            <button
              onClick={handleDeleteAllRules}
              disabled={deletingAll || rules.length === 0}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${deletingAll || rules.length === 0
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-red-600 text-white hover:bg-red-700'
                }`}
            >
              {deletingAll ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Deleting...
                </span>
              ) : (
                'Deactivate All'
              )}
            </button>
          )}
        </div>

        <RulesTable
          rules={rules}
          loading={loading}
          onEdit={setEditingRule}
          onDelete={activeTab === 'active' ? handleDeleteRule : undefined}
          onRestore={activeTab === 'deactivated' ? handleRestoreRule : undefined}
          showRestoreButton={activeTab === 'deactivated'}
        />

        {/* Pagination */}
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      </div>

      {/* Edit Modal */}
      <RuleEditModal
        rule={editingRule}
        onClose={() => setEditingRule(null)}
        onSave={handleUpdateRule}
      />
    </div>
  );
}
