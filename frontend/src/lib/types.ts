export interface Submission {
  id: string;
  title: string;
  content_type: 'html' | 'markdown' | 'pdf' | 'docx';
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  submitted_at: string;
  submitted_by?: string;
}

export interface ComplianceCheck {
  id: string;
  submission_id: string;
  overall_score: number;
  irdai_score: number;
  brand_score: number;
  seo_score: number;
  status: 'passed' | 'flagged' | 'failed';
  grade: string;
  ai_summary: string;
  check_date: string;
  violations: Violation[];
}

export interface Violation {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: 'irdai' | 'brand' | 'seo';
  description: string;
  location: string;
  current_text: string;
  suggested_fix: string;
  is_auto_fixable: boolean;
}

export interface DashboardStats {
  total_submissions: number;
  avg_compliance_score: number;
  pending_count: number;
  flagged_count: number;
}

// Phase 2: Admin rule management types
export interface Rule {
  id: string;
  category: 'irdai' | 'brand' | 'seo';
  rule_text: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  keywords: string[];
  pattern: string | null;
  points_deduction: number;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
}

export interface RuleListResponse {
  rules: Rule[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface RuleGenerationResponse {
  success: boolean;
  rules_created: number;
  rules_failed: number;
  rules: Array<{
    id: string;
    category: string;
    rule_text: string;
    severity: string;
    points_deduction: number;
  }>;
  errors: string[];
}

export interface RuleStats {
  total_rules: number;
  active_rules: number;
  inactive_rules: number;
  by_category: {
    irdai: number;
    brand: number;
    seo: number;
  };
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}
