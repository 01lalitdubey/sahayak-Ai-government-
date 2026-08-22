import api from '../axios';

export interface TranslationAnalytics {
  total_schemes: number;
  total_translations: number;
  pending_review: number;
  approved: number;
  published: number;
  rejected: number;
  coverage_percentage: number;
}

export interface TranslationHistory {
  id: string;
  translation_id: string;
  version: number;
  translated_content: Record<string, string>;
  editor_id?: string;
  reason?: string;
  created_at: string;
}

export interface TranslationTMSDetail {
  id: string;
  scheme_id: string;
  language_code: string;
  translated_content: Record<string, string>;
  version: number;
  checksum: string;
  translation_quality?: number;
  provider: string;
  status: string;
  review_status?: string;
  approved_by?: string;
  reviewed_at?: string;
  published_at?: string;
  review_comment?: string;
  last_editor?: string;
  last_reviewer?: string;
  manual_override: boolean;
  is_published: boolean;
  approved_version?: number;
  created_at: string;
  updated_at: string;
  original_english?: Record<string, string>;
  scheme_name?: string;
  history?: TranslationHistory[];
}

export interface TranslationListResponse {
  items: TranslationTMSDetail[];
  total: number;
  page: number;
  size: number;
}

export const adminTmsApi = {
  getAnalytics: async (): Promise<TranslationAnalytics> => {
    const res = await api.get('/admin/tms/translations/analytics');
    return res.data;
  },
  
  getTranslations: async (params?: Record<string, unknown>): Promise<TranslationListResponse> => {
    const res = await api.get('/admin/tms/translations', { params });
    return res.data;
  },

  getTranslation: async (id: string): Promise<TranslationTMSDetail> => {
    const res = await api.get(`/admin/tms/translations/${id}`);
    return res.data;
  },

  updateTranslation: async (id: string, translated_content: Record<string, string>, reason?: string): Promise<TranslationTMSDetail> => {
    const res = await api.put(`/admin/tms/translations/${id}`, { translated_content, reason });
    return res.data;
  },

  approveTranslation: async (id: string, comment?: string): Promise<TranslationTMSDetail> => {
    const res = await api.post(`/admin/tms/translations/${id}/approve`, { comment });
    return res.data;
  },

  rejectTranslation: async (id: string, comment?: string): Promise<TranslationTMSDetail> => {
    const res = await api.post(`/admin/tms/translations/${id}/reject`, { comment });
    return res.data;
  },

  publishTranslation: async (id: string): Promise<TranslationTMSDetail> => {
    const res = await api.post(`/admin/tms/translations/${id}/publish`);
    return res.data;
  },

  bulkApprove: async (translation_ids: string[]): Promise<unknown> => {
    const res = await api.post('/admin/tms/translations/bulk-approve', { translation_ids });
    return res.data;
  },

  bulkPublish: async (translation_ids: string[]): Promise<unknown> => {
    const res = await api.post('/admin/tms/translations/bulk-publish', { translation_ids });
    return res.data;
  },

  // --- Execution API ---
  startAll: async (): Promise<{ status: string, job_id: string }> => {
    const res = await api.post('/admin/tms/execution/start-all');
    return res.data;
  },

  pauseExecution: async (): Promise<{ status: string }> => {
    const res = await api.post('/admin/tms/execution/pause');
    return res.data;
  },

  resumeExecution: async (): Promise<{ status: string }> => {
    const res = await api.post('/admin/tms/execution/resume');
    return res.data;
  },

  cancelExecution: async (): Promise<{ status: string }> => {
    const res = await api.post('/admin/tms/execution/cancel');
    return res.data;
  },

  retryFailed: async (job_id: string): Promise<{ status: string }> => {
    const res = await api.post(`/admin/tms/execution/retry-failed?job_id=${job_id}`);
    return res.data;
  },

  getProgress: async (): Promise<unknown> => {
    const res = await api.get('/admin/tms/execution/progress');
    return res.data;
  },

  getHealth: async (): Promise<unknown> => {
    const res = await api.get('/admin/tms/execution/health');
    return res.data;
  }
};
