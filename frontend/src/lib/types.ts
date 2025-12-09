export interface Submission {
  id: string;
  title: string;
  content_type: 'html' | 'markdown' | 'pdf' | 'docx';
  // Updated for chunked workflow: uploaded → preprocessing → preprocessed → analyzing → analyzed
  // Legacy statuses: pending, completed, failed still supported
  status: 'pending' | 'uploaded' | 'preprocessing' | 'preprocessed' | 'analyzing' | 'analyzed' | 'completed' | 'failed';
  submitted_at: string;
  submitted_by?: string;
  has_deep_analysis?: boolean;
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
  has_deep_analysis?: boolean;
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

// Dashboard analytics types
export interface ComplianceTrendsResponse {
  dates: string[];
  scores: number[];
  counts: number[];
}

export interface HeatmapSeriesItem {
  name: string;
  data: number[];
}

export interface ViolationsHeatmapResponse {
  series: HeatmapSeriesItem[];
  categories: string[];
}

export interface TopViolation {
  description: string;
  count: number;
  severity: string;
  category: string;
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

// Rule Preview Types (Phase 2 Enhancement)
export interface DraftRule {
  temp_id: string;
  category: 'irdai' | 'brand' | 'seo';
  rule_text: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  keywords: string[];
  pattern: string | null;
  points_deduction: number;
  is_approved: boolean;
}

export interface RulePreviewResponse {
  success: boolean;
  document_title: string;
  draft_rules: DraftRule[];
  total_extracted: number;
  errors: string[];
}

export interface RuleRefineRequest {
  rule_text: string;
  refinement_instruction: string;
  category: string;
  severity: string;
}

export interface RuleRefineResponse {
  success: boolean;
  original_text: string;
  refined_text: string;
  refined_keywords: string[];
  error: string | null;
}

export interface RuleBulkSubmitRequest {
  document_title: string;
  approved_rules: DraftRule[];
}

export interface RuleBulkSubmitResponse {
  success: boolean;
  rules_created: number;
  rules_failed: number;
  created_rule_ids: string[];
  errors: string[];
}

// Deep Compliance Research Mode Types
export interface SeverityWeights {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface RuleImpact {
  rule_id: string;
  rule_text: string;
  category: string;
  severity: string;
  base_deduction: number;
  weight_multiplier: number;
  weighted_deduction: number;
  violation_reason: string;
}

export interface LineAnalysis {
  id: string;
  line_number: number;
  line_content: string;
  line_score: number;
  relevance_context: string;
  rule_impacts: RuleImpact[];
}

export interface DeepAnalysisRequest {
  severity_weights: SeverityWeights;
}

export interface DeepAnalysisResponse {
  check_id: string;
  submission_id: string;
  document_title: string;
  total_lines: number;
  average_score: number;
  min_score: number;
  max_score: number;
  severity_config: SeverityWeights;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  lines: LineAnalysis[];
  analysis_timestamp: string;
}

export const SEVERITY_PRESETS = {
  strict: { critical: 2.0, high: 1.5, medium: 1.0, low: 0.5 },
  balanced: { critical: 1.5, high: 1.0, medium: 0.5, low: 0.2 },
  lenient: { critical: 1.0, high: 0.5, medium: 0.2, low: 0.1 },
};

// Phase 3: Chunked Content Processing Types
export interface ContentChunk {
  id: string;
  submission_id: string;
  chunk_index: number;
  text: string;
  token_count: number;
  metadata: {
    source_type?: string;
    page_number?: number;
    section_title?: string;
    char_offset_start?: number;
    char_offset_end?: number;
    chunk_method?: string;
    synthetic?: boolean;
    legacy_mode?: boolean;
  };
  created_at: string;
}

export interface PreprocessingStats {
  total_submissions: number;
  preprocessed_submissions: number;
  total_chunks: number;
  avg_chunks_per_submission: number;
  by_content_type: {
    pdf: number;
    docx: number;
    html: number;
    markdown: number;
  };
  recent_preprocessing: Array<{
    submission_id: string;
    title: string;
    chunks_created: number;
    preprocessed_at: string;
  }>;
}

export interface ChunkListResponse {
  submission_id: string;
  submission_title: string;
  submission_status: string;
  total_chunks: number;
  chunks: ContentChunk[];
}
