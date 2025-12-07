/**
 * Data transformation utilities for converting compliance data to chart formats
 */

import { ComplianceCheck, Violation } from '../types';
import {
  RadarChartData,
  DonutChartData,
  BarChartData,
  HeatmapChartData,
  PieChartData,
  StackedBarChartData,
  SeverityDistribution,
  CategoryDistribution,
  CategorySeverityMatrix,
  AutoFixabilityStats,
  AnalyticsData,
  COMPLIANCE_COLORS,
  SEVERITY_LEVELS,
  CATEGORIES,
} from '../components/results/analytics/types';

// ============================================================================
// Score Comparison Transformers
// ============================================================================

/**
 * Prepare radar chart data for score comparison
 * Shows IRDAI, Brand, SEO, and Overall scores
 */
export function prepareRadarData(results: ComplianceCheck): RadarChartData {
  return {
    categories: ['IRDAI Score', 'Brand Score', 'SEO Score', 'Overall Score'],
    series: [
      {
        name: 'This Submission',
        data: [
          results.irdai_score,
          results.brand_score,
          results.seo_score,
          results.overall_score,
        ],
      },
    ],
  };
}

// ============================================================================
// Violation Distribution Transformers
// ============================================================================

/**
 * Calculate violation distribution by severity
 */
export function calculateSeverityDistribution(
  violations: Violation[]
): SeverityDistribution {
  return {
    critical: violations.filter((v) => v.severity === 'critical').length,
    high: violations.filter((v) => v.severity === 'high').length,
    medium: violations.filter((v) => v.severity === 'medium').length,
    low: violations.filter((v) => v.severity === 'low').length,
  };
}

/**
 * Calculate violation distribution by category
 */
export function calculateCategoryDistribution(
  violations: Violation[]
): CategoryDistribution {
  return {
    irdai: violations.filter((v) => v.category === 'irdai').length,
    brand: violations.filter((v) => v.category === 'brand').length,
    seo: violations.filter((v) => v.category === 'seo').length,
  };
}

/**
 * Prepare donut chart data for severity distribution
 */
export function prepareSeverityDonutData(
  violations: Violation[]
): DonutChartData {
  const distribution = calculateSeverityDistribution(violations);

  return {
    labels: ['Critical', 'High', 'Medium', 'Low'],
    series: [
      distribution.critical,
      distribution.high,
      distribution.medium,
      distribution.low,
    ],
    colors: [
      COMPLIANCE_COLORS.critical,
      COMPLIANCE_COLORS.high,
      COMPLIANCE_COLORS.medium,
      COMPLIANCE_COLORS.low,
    ],
  };
}

/**
 * Prepare bar chart data for category distribution
 */
export function prepareCategoryBarData(violations: Violation[]): BarChartData {
  const distribution = calculateCategoryDistribution(violations);

  return {
    categories: ['IRDAI', 'Brand', 'SEO'],
    series: [
      {
        name: 'Violations',
        data: [distribution.irdai, distribution.brand, distribution.seo],
      },
    ],
  };
}

// ============================================================================
// Heatmap Transformers
// ============================================================================

/**
 * Calculate category-severity matrix for heatmap
 */
export function calculateCategorySeverityMatrix(
  violations: Violation[]
): CategorySeverityMatrix {
  const matrix: CategorySeverityMatrix = {};

  // Initialize matrix
  CATEGORIES.forEach((category) => {
    matrix[category] = {};
    SEVERITY_LEVELS.forEach((severity) => {
      matrix[category][severity] = 0;
    });
  });

  // Populate matrix
  violations.forEach((violation) => {
    const category = violation.category;
    const severity = violation.severity;
    if (matrix[category] && matrix[category][severity] !== undefined) {
      matrix[category][severity]++;
    }
  });

  return matrix;
}

/**
 * Prepare heatmap chart data for category-severity distribution
 */
export function prepareHeatmapData(violations: Violation[]): HeatmapChartData {
  const matrix = calculateCategorySeverityMatrix(violations);

  const series = SEVERITY_LEVELS.map((severity) => ({
    name: severity.charAt(0).toUpperCase() + severity.slice(1),
    data: CATEGORIES.map((category) => ({
      x: category.toUpperCase(),
      y: matrix[category][severity],
    })),
  }));

  return {
    series,
    categories: CATEGORIES.map((cat) => cat.toUpperCase()),
  };
}

// ============================================================================
// Auto-Fixability Transformers
// ============================================================================

/**
 * Calculate auto-fixability statistics
 */
export function calculateAutoFixability(
  violations: Violation[]
): AutoFixabilityStats {
  const totalViolations = violations.length;
  const autoFixable = violations.filter(
    (v) => v.suggested_fix && v.current_text
  ).length;
  const manualReview = totalViolations - autoFixable;

  // Calculate by severity
  const bySeverity: AutoFixabilityStats['bySeverity'] = {};

  SEVERITY_LEVELS.forEach((severity) => {
    const severityViolations = violations.filter((v) => v.severity === severity);
    const severityAutoFixable = severityViolations.filter(
      (v) => v.suggested_fix && v.current_text
    ).length;

    bySeverity[severity] = {
      total: severityViolations.length,
      autoFixable: severityAutoFixable,
      manualReview: severityViolations.length - severityAutoFixable,
    };
  });

  return {
    totalViolations,
    autoFixable,
    manualReview,
    autoFixablePercentage:
      totalViolations > 0 ? (autoFixable / totalViolations) * 100 : 0,
    manualReviewPercentage:
      totalViolations > 0 ? (manualReview / totalViolations) * 100 : 0,
    bySeverity,
  };
}

/**
 * Prepare pie chart data for auto-fixability overview
 */
export function prepareFixabilityPieData(violations: Violation[]): PieChartData {
  const stats = calculateAutoFixability(violations);

  return {
    labels: ['Auto-Fixable', 'Manual Review'],
    series: [stats.autoFixable, stats.manualReview],
    colors: [COMPLIANCE_COLORS.autoFixable, COMPLIANCE_COLORS.manualReview],
  };
}

/**
 * Prepare stacked bar chart data for fixability by severity
 */
export function prepareFixabilityStackedBarData(
  violations: Violation[]
): StackedBarChartData {
  const stats = calculateAutoFixability(violations);

  return {
    categories: SEVERITY_LEVELS.map(
      (s) => s.charAt(0).toUpperCase() + s.slice(1)
    ),
    series: [
      {
        name: 'Auto-Fixable',
        data: SEVERITY_LEVELS.map((severity) => stats.bySeverity[severity]?.autoFixable || 0),
      },
      {
        name: 'Manual Review',
        data: SEVERITY_LEVELS.map((severity) => stats.bySeverity[severity]?.manualReview || 0),
      },
    ],
  };
}

// ============================================================================
// Complete Analytics Data Transformer
// ============================================================================

/**
 * Transform compliance check results into complete analytics data
 * This is the main entry point for preparing all analytics data at once
 */
export function transformComplianceDataToAnalytics(
  results: ComplianceCheck,
  violations: Violation[]
): AnalyticsData {
  return {
    scores: {
      irdai: results.irdai_score,
      brand: results.brand_score,
      seo: results.seo_score,
      overall: results.overall_score,
    },
    severityDistribution: calculateSeverityDistribution(violations),
    categoryDistribution: calculateCategoryDistribution(violations),
    categorySeveityMatrix: calculateCategorySeverityMatrix(violations),
    autoFixability: calculateAutoFixability(violations),
    totalViolations: violations.length,
    violations,
  };
}

// ============================================================================
// Filtering Utilities
// ============================================================================

/**
 * Filter violations by categories
 */
export function filterViolationsByCategories(
  violations: Violation[],
  categories: string[]
): Violation[] {
  if (categories.length === 0) return violations;
  return violations.filter((v) => categories.includes(v.category));
}

/**
 * Filter violations by severities
 */
export function filterViolationsBySeverities(
  violations: Violation[],
  severities: string[]
): Violation[] {
  if (severities.length === 0) return violations;
  return violations.filter((v) => severities.includes(v.severity));
}

/**
 * Filter violations by auto-fixability
 */
export function filterViolationsByFixability(
  violations: Violation[],
  autoFixableOnly: boolean
): Violation[] {
  if (!autoFixableOnly) return violations;
  return violations.filter((v) => v.suggested_fix && v.current_text);
}

/**
 * Apply all filters to violations
 */
export function applyViolationFilters(
  violations: Violation[],
  filters: {
    categories?: string[];
    severities?: string[];
    autoFixableOnly?: boolean;
  }
): Violation[] {
  let filtered = violations;

  if (filters.categories && filters.categories.length > 0) {
    filtered = filterViolationsByCategories(filtered, filters.categories);
  }

  if (filters.severities && filters.severities.length > 0) {
    filtered = filterViolationsBySeverities(filtered, filters.severities);
  }

  if (filters.autoFixableOnly) {
    filtered = filterViolationsByFixability(filtered, true);
  }

  return filtered;
}

// ============================================================================
// Responsive Height Utilities
// ============================================================================

/**
 * Get responsive chart height based on screen size
 */
export function getResponsiveChartHeight(
  defaultHeight: number = 400
): number {
  if (typeof window === 'undefined') return defaultHeight;

  const width = window.innerWidth;

  if (width < 640) {
    // Mobile
    return Math.min(defaultHeight, 300);
  } else if (width < 1024) {
    // Tablet
    return Math.min(defaultHeight, 350);
  } else {
    // Desktop
    return defaultHeight;
  }
}

// ============================================================================
// Data Validation Utilities
// ============================================================================

/**
 * Check if violations data is valid for chart rendering
 */
export function isValidChartData(violations: Violation[]): boolean {
  return Array.isArray(violations) && violations.length > 0;
}

/**
 * Get empty state message for charts
 */
export function getEmptyStateMessage(violations: Violation[]): string {
  if (!Array.isArray(violations)) {
    return 'Invalid data format';
  }
  if (violations.length === 0) {
    return 'No violations found - content is compliant!';
  }
  return '';
}
