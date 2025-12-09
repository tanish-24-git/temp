import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Submissions
  uploadSubmission: (data: FormData) =>
    apiClient.post('/api/submissions/upload', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  getSubmissions: () => apiClient.get('/api/submissions'),

  getSubmission: (id: string) =>
    apiClient.get(`/api/submissions/${id}`),

  getSubmissionById: (id: string) =>
    apiClient.get(`/api/submissions/${id}`),

  analyzeSubmission: (id: string) =>
    apiClient.post(`/api/submissions/${id}/analyze`),

  deleteSubmission: (id: string) =>
    apiClient.delete(`/api/submissions/${id}`),

  deleteAllSubmissions: () =>
    apiClient.delete('/api/submissions'),

  // PDF Modification
  applyPdfFixes: (id: string) =>
    apiClient.post(`/api/submissions/${id}/apply-fixes`),

  downloadModifiedPdf: (id: string) =>
    apiClient.get(`/api/submissions/${id}/download-modified`, {
      responseType: 'blob'
    }),

  // Compliance
  getComplianceResults: (submissionId: string) =>
    apiClient.get(`/api/compliance/${submissionId}`),

  getViolations: (submissionId: string) =>
    apiClient.get(`/api/compliance/${submissionId}/violations`),

  // Dashboard
  getDashboardStats: () => apiClient.get('/api/dashboard/stats'),

  getRecentSubmissions: () => apiClient.get('/api/dashboard/recent'),

  getDashboardTrends: (days: number = 30) =>
    apiClient.get('/api/dashboard/trends', { params: { days } }),

  getViolationsHeatmap: () =>
    apiClient.get('/api/dashboard/violations-heatmap'),

  getTopViolations: (limit: number = 5) =>
    apiClient.get('/api/dashboard/top-violations', { params: { limit } }),

  // Phase 2: Admin - Rule Management
  generateRulesFromDocument: (file: File, documentTitle: string, userId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_title', documentTitle);

    return apiClient.post('/api/admin/rules/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-User-Id': userId,
      },
    });
  },

  getRules: (params: {
    page?: number;
    page_size?: number;
    category?: string;
    severity?: string;
    is_active?: boolean;
    search?: string;
    userId: string;
  }) => {
    const { userId, ...queryParams } = params;
    return apiClient.get('/api/admin/rules', {
      params: queryParams,
      headers: { 'X-User-Id': userId },
    });
  },

  getRule: (ruleId: string, userId: string) =>
    apiClient.get(`/api/admin/rules/${ruleId}`, {
      headers: { 'X-User-Id': userId },
    }),

  updateRule: (ruleId: string, data: any, userId: string) =>
    apiClient.put(`/api/admin/rules/${ruleId}`, data, {
      headers: { 'X-User-Id': userId },
    }),

  deleteRule: (ruleId: string, userId: string) =>
    apiClient.delete(`/api/admin/rules/${ruleId}`, {
      headers: { 'X-User-Id': userId },
    }),

  deleteAllRules: (userId: string) =>
    apiClient.delete('/api/admin/rules', {
      headers: { 'X-User-Id': userId },
    }),

  createRule: (data: any, userId: string) =>
    apiClient.post('/api/admin/rules', data, {
      headers: { 'X-User-Id': userId },
    }),

  getRuleStats: (userId: string) =>
    apiClient.get('/api/admin/rules/stats/summary', {
      headers: { 'X-User-Id': userId },
    }),

  // Rule Preview Workflow (Phase 2 Enhancement)
  previewRulesFromDocument: (file: File, documentTitle: string, userId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_title', documentTitle);

    return apiClient.post('/api/admin/rules/preview', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-User-Id': userId,
      },
    });
  },

  refineRule: (data: {
    rule_text: string;
    refinement_instruction: string;
    category: string;
    severity: string;
  }, userId: string) =>
    apiClient.post('/api/admin/rules/refine', data, {
      headers: { 'X-User-Id': userId },
    }),

  bulkSubmitRules: (data: {
    document_title: string;
    approved_rules: any[];
  }, userId: string) =>
    apiClient.post('/api/admin/rules/bulk-submit', data, {
      headers: { 'X-User-Id': userId },
    }),

  // Deep Compliance Research Mode
  triggerDeepAnalysis: (submissionId: string, severityWeights: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  }) =>
    apiClient.post(`/api/compliance/${submissionId}/deep-analyze`, {
      severity_weights: severityWeights
    }),

  getDeepAnalysisResults: (submissionId: string) =>
    apiClient.get(`/api/compliance/${submissionId}/deep-results`),

  getDeepAnalysisPresets: (submissionId: string) =>
    apiClient.get(`/api/compliance/${submissionId}/deep-analyze/presets`),

  downloadDeepAnalysisReport: (submissionId: string) =>
    apiClient.get(`/api/compliance/${submissionId}/deep-analysis/export`, {
      responseType: 'blob'
    }),

  syncDeepAnalysisResults: (submissionId: string) =>
    apiClient.post(`/api/compliance/${submissionId}/deep-analysis/sync`),

  // Phase 3: Chunked Content Processing
  getPreprocessingStats: () =>
    apiClient.get('/api/dashboard/preprocessing-stats'),

  getSubmissionChunks: (submissionId: string) =>
    apiClient.get(`/api/preprocessing/${submissionId}/chunks`),

  getPreprocessingStatus: (submissionId: string) =>
    apiClient.get(`/api/preprocessing/${submissionId}/status`),

  triggerPreprocessing: (submissionId: string, params?: { chunk_size?: number; overlap?: number }) =>
    apiClient.post(`/api/preprocessing/${submissionId}`, params),

  // Adaptive Compliance Engine: Onboarding
  startOnboarding: (data: {
    user_id: string;
    industry: string;
    brand_name: string;
    brand_guidelines?: string;
    analysis_scope: string[];
    region?: string;
  }) =>
    apiClient.post('/api/onboarding/start', data),

  getUserConfig: (userId: string) =>
    apiClient.get(`/api/onboarding/${userId}/config`),

  updateUserConfig: (
    userId: string,
    updates: { industry?: string; brand_name?: string; analysis_scope?: string[] }
  ) => {
    const params = new URLSearchParams();
    if (updates.industry) params.append("industry", updates.industry);
    if (updates.brand_name) params.append("brand_name", updates.brand_name);
    if (updates.analysis_scope) {
      updates.analysis_scope.forEach(scope => params.append("analysis_scope", scope));
    }
    return apiClient.put(`/api/onboarding/${userId}/config?${params}`);
  },
};
