import { useState, useEffect } from 'react';
import { api } from '../lib/api';
import { Rule, RuleStats, RuleGenerationResponse } from '../lib/types';
import {
  RuleStatsCards,
  RuleUploadForm,
  RuleFilters,
  RulesTable,
  Pagination,
  RuleEditModal,
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

  // Handle file upload
  const handleUpload = async (file: File, documentTitle: string) => {
    try {
      setUploading(true);
      setError(null);
      setUploadResult(null);

      const response = await api.generateRulesFromDocument(
        file,
        documentTitle,
        SUPER_ADMIN_USER_ID
      );

      const result: RuleGenerationResponse = response.data;
      setUploadResult(result);

      if (result.success) {
        // Refresh rules list and stats
        await fetchRules();
        await fetchStats();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate rules');
    } finally {
      setUploading(false);
    }
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

      {/* Upload Section - Only show on Active tab */}
      {activeTab === 'active' && (
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
