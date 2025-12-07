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
};
