/**
 * Type definitions for Results page analytics components
 */

import { ComplianceCheck, Violation } from '../../../lib/types';

// ============================================================================
// Chart Data Types
// ============================================================================

/**
 * Radar chart series data for score comparison
 */
export interface RadarSeriesData {
  name: string;
  data: number[];
}

export interface RadarChartData {
  categories: string[];
  series: RadarSeriesData[];
}

/**
 * Donut chart data for severity distribution
 */
export interface DonutChartData {
  labels: string[];
  series: number[];
  colors: string[];
}

/**
 * Heatmap data point
 */
export interface HeatmapDataPoint {
  x: string; // Category name
  y: number; // Count value
}

export interface HeatmapSeriesData {
  name: string; // Severity level
  data: HeatmapDataPoint[];
}

export interface HeatmapChartData {
  series: HeatmapSeriesData[];
  categories: string[];
}

/**
 * Bar chart data for category distribution
 */
export interface BarChartData {
  categories: string[];
  series: {
    name: string;
    data: number[];
  }[];
}

/**
 * Pie chart data for auto-fixability
 */
export interface PieChartData {
  labels: string[];
  series: number[];
  colors: string[];
}

/**
 * Stacked bar chart data for fixability by severity
 */
export interface StackedBarChartData {
  categories: string[];
  series: {
    name: string;
    data: number[];
  }[];
}

// ============================================================================
// Analytics Computation Types
// ============================================================================

/**
 * Violation distribution by severity
 */
export interface SeverityDistribution {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

/**
 * Violation distribution by category
 */
export interface CategoryDistribution {
  irdai: number;
  brand: number;
  seo: number;
}

/**
 * Category-Severity matrix for heatmap
 */
export interface CategorySeverityMatrix {
  [category: string]: {
    [severity: string]: number;
  };
}

/**
 * Auto-fixability statistics
 */
export interface AutoFixabilityStats {
  totalViolations: number;
  autoFixable: number;
  manualReview: number;
  autoFixablePercentage: number;
  manualReviewPercentage: number;
  bySeverity: {
    [severity: string]: {
      total: number;
      autoFixable: number;
      manualReview: number;
    };
  };
}

/**
 * Complete analytics data computed from compliance check results
 */
export interface AnalyticsData {
  // Score metrics
  scores: {
    irdai: number;
    brand: number;
    seo: number;
    overall: number;
  };

  // Distribution metrics
  severityDistribution: SeverityDistribution;
  categoryDistribution: CategoryDistribution;
  categorySeveityMatrix: CategorySeverityMatrix;

  // Fixability metrics
  autoFixability: AutoFixabilityStats;

  // Violation details
  totalViolations: number;
  violations: Violation[];
}

// ============================================================================
// Component Props Types
// ============================================================================

/**
 * Props for ScoreComparisonRadar component
 */
export interface ScoreComparisonRadarProps {
  results: ComplianceCheck;
  height?: number;
}

/**
 * Props for ViolationDistributionCharts component
 */
export interface ViolationDistributionChartsProps {
  violations: Violation[];
  height?: number;
}

/**
 * Props for SeverityHeatmap component
 */
export interface SeverityHeatmapProps {
  violations: Violation[];
  height?: number;
}

/**
 * Props for AutoFixabilityAnalysis component
 */
export interface AutoFixabilityAnalysisProps {
  violations: Violation[];
  height?: number;
}

/**
 * Props for PDFModificationPanel component
 */
export interface PDFModificationPanelProps {
  submissionId: string;
  contentType: string;
  violationsCount: number;
  onFixesApplied?: () => void;
}

// ============================================================================
// State Management Types
// ============================================================================

/**
 * PDF modification state
 */
export interface PDFModificationState {
  applyingFixes: boolean;
  fixesApplied: boolean;
  fixMessage: string;
  error: string | null;
}

/**
 * Chart filter state
 */
export interface ChartFilterState {
  selectedCategories: string[];
  selectedSeverities: string[];
  showAutoFixableOnly: boolean;
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Responsive height configuration
 */
export interface ResponsiveHeightConfig {
  mobile: number;
  tablet: number;
  desktop: number;
}

/**
 * Chart color palette
 */
export interface ChartColorPalette {
  critical: string;
  high: string;
  medium: string;
  low: string;
  irdai: string;
  brand: string;
  seo: string;
  autoFixable: string;
  manualReview: string;
}

/**
 * Default color palette for compliance charts
 */
export const COMPLIANCE_COLORS: ChartColorPalette = {
  critical: '#DC2626', // red-600
  high: '#EA580C',     // orange-600
  medium: '#F59E0B',   // amber-500
  low: '#10B981',      // emerald-500
  irdai: '#3B82F6',    // blue-500
  brand: '#8B5CF6',    // violet-500
  seo: '#06B6D4',      // cyan-500
  autoFixable: '#10B981', // emerald-500
  manualReview: '#F59E0B', // amber-500
};

/**
 * Severity levels in priority order
 */
export const SEVERITY_LEVELS = ['critical', 'high', 'medium', 'low'] as const;
export type SeverityLevel = typeof SEVERITY_LEVELS[number];

/**
 * Category types
 */
export const CATEGORIES = ['irdai', 'brand', 'seo'] as const;
export type CategoryType = typeof CATEGORIES[number];
