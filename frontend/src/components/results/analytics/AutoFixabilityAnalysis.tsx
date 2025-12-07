/**
 * AutoFixabilityAnalysis Component
 * Displays analysis of auto-fixable vs manual review violations
 */

import React, { useMemo } from 'react';
import Chart from 'react-apexcharts';
import { ApexOptions } from 'apexcharts';
import { AutoFixabilityAnalysisProps, COMPLIANCE_COLORS } from './types';
import {
  prepareFixabilityPieData,
  prepareFixabilityStackedBarData,
  calculateAutoFixability,
  isValidChartData,
  getEmptyStateMessage,
} from '../../../utils/chartDataTransformers';

const AutoFixabilityAnalysis: React.FC<AutoFixabilityAnalysisProps> = ({
  violations,
  height = 350,
}) => {
  // Check if we have valid data
  const hasValidData = useMemo(() => isValidChartData(violations), [violations]);
  const emptyMessage = useMemo(
    () => getEmptyStateMessage(violations),
    [violations]
  );

  // Calculate statistics
  const stats = useMemo(
    () => (hasValidData ? calculateAutoFixability(violations) : null),
    [violations, hasValidData]
  );

  // Transform data for charts
  const pieData = useMemo(
    () => (hasValidData ? prepareFixabilityPieData(violations) : null),
    [violations, hasValidData]
  );

  const stackedBarData = useMemo(
    () => (hasValidData ? prepareFixabilityStackedBarData(violations) : null),
    [violations, hasValidData]
  );

  // Pie chart options for overall fixability
  const pieOptions: ApexOptions = useMemo(
    () => ({
      chart: {
        type: 'pie',
        fontFamily: 'Inter, system-ui, sans-serif',
        toolbar: {
          show: true,
          tools: {
            download: true,
          },
        },
      },
      title: {
        text: 'Auto-Fixability Overview',
        align: 'center',
        style: {
          fontSize: '16px',
          fontWeight: 600,
          color: '#1F2937',
        },
      },
      labels: pieData?.labels || [],
      colors: pieData?.colors || [],
      legend: {
        position: 'bottom',
        fontSize: '13px',
        fontWeight: 500,
        labels: {
          colors: '#374151',
        },
        markers: {
          width: 14,
          height: 14,
          radius: 3,
        },
      },
      plotOptions: {
        pie: {
          donut: {
            size: '0%',
          },
          expandOnClick: true,
        },
      },
      dataLabels: {
        enabled: true,
        formatter: (val: number, opts) => {
          const value = opts.w.globals.series[opts.seriesIndex];
          return `${value}\n(${val.toFixed(1)}%)`;
        },
        style: {
          fontSize: '13px',
          fontWeight: 600,
          colors: ['#fff'],
        },
        dropShadow: {
          enabled: true,
          top: 1,
          left: 1,
          blur: 1,
          opacity: 0.4,
        },
      },
      tooltip: {
        enabled: true,
        y: {
          formatter: (value) => {
            const total = stats?.totalViolations || 0;
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
            return `${value} violations (${percentage}%)`;
          },
        },
        style: {
          fontSize: '12px',
        },
      },
      responsive: [
        {
          breakpoint: 640,
          options: {
            chart: {
              height: 280,
            },
            title: {
              style: {
                fontSize: '14px',
              },
            },
            legend: {
              fontSize: '11px',
            },
            dataLabels: {
              style: {
                fontSize: '11px',
              },
            },
          },
        },
      ],
    }),
    [pieData, stats]
  );

  // Stacked bar chart options for fixability by severity
  const stackedBarOptions: ApexOptions = useMemo(
    () => ({
      chart: {
        type: 'bar',
        stacked: true,
        fontFamily: 'Inter, system-ui, sans-serif',
        toolbar: {
          show: true,
          tools: {
            download: true,
          },
        },
      },
      title: {
        text: 'Fixability by Severity',
        align: 'center',
        style: {
          fontSize: '16px',
          fontWeight: 600,
          color: '#1F2937',
        },
      },
      plotOptions: {
        bar: {
          horizontal: false,
          borderRadius: 6,
          borderRadiusApplication: 'end',
          dataLabels: {
            total: {
              enabled: true,
              style: {
                fontSize: '12px',
                fontWeight: 600,
                color: '#374151',
              },
            },
          },
        },
      },
      dataLabels: {
        enabled: true,
        formatter: (val: number) => (val > 0 ? val.toString() : ''),
        style: {
          fontSize: '11px',
          fontWeight: 600,
          colors: ['#fff'],
        },
      },
      xaxis: {
        categories: stackedBarData?.categories || [],
        labels: {
          style: {
            fontSize: '12px',
            fontWeight: 500,
            colors: '#374151',
          },
        },
        axisBorder: {
          show: true,
          color: '#E5E7EB',
        },
        axisTicks: {
          show: false,
        },
      },
      yaxis: {
        title: {
          text: 'Number of Violations',
          style: {
            fontSize: '12px',
            fontWeight: 500,
            color: '#6B7280',
          },
        },
        labels: {
          style: {
            fontSize: '11px',
            colors: '#6B7280',
          },
          formatter: (value) => Math.floor(value).toString(),
        },
      },
      colors: [COMPLIANCE_COLORS.autoFixable, COMPLIANCE_COLORS.manualReview],
      fill: {
        opacity: 1,
      },
      grid: {
        borderColor: '#F3F4F6',
        strokeDashArray: 4,
        xaxis: {
          lines: {
            show: false,
          },
        },
        yaxis: {
          lines: {
            show: true,
          },
        },
      },
      legend: {
        position: 'bottom',
        fontSize: '12px',
        fontWeight: 500,
        labels: {
          colors: '#374151',
        },
        markers: {
          width: 12,
          height: 12,
          radius: 3,
        },
      },
      tooltip: {
        enabled: true,
        y: {
          formatter: (value, { seriesIndex, dataPointIndex }) => {
            const severityLevel = stackedBarData?.categories[dataPointIndex] || '';
            const type = seriesIndex === 0 ? 'auto-fixable' : 'manual review';
            return `${value} ${type} violations`;
          },
        },
        style: {
          fontSize: '12px',
        },
      },
      responsive: [
        {
          breakpoint: 640,
          options: {
            chart: {
              height: 280,
            },
            title: {
              style: {
                fontSize: '14px',
              },
            },
            plotOptions: {
              bar: {
                borderRadius: 4,
              },
            },
          },
        },
      ],
    }),
    [stackedBarData]
  );

  // Render empty state if no violations
  if (!hasValidData) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Auto-Fixability Analysis
        </h3>
        <div className="flex flex-col items-center justify-center py-12">
          <svg
            className="w-16 h-16 text-green-500 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-lg font-medium text-gray-900 mb-1">
            No Violations Found
          </p>
          <p className="text-sm text-gray-600">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header with Key Metrics */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            Auto-Fixability Analysis
          </h3>
          {stats && (
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600">
                {stats.autoFixablePercentage.toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600">Auto-Fixable</div>
            </div>
          )}
        </div>
        <p className="text-sm text-gray-600">
          Analysis of violations that can be automatically fixed vs. requiring
          manual review
        </p>
      </div>

      {/* Key Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div className="text-xs font-medium text-green-700 mb-1">
              Auto-Fixable
            </div>
            <div className="text-2xl font-bold text-green-900">
              {stats.autoFixable}
            </div>
            <div className="text-xs text-green-700">
              {stats.autoFixablePercentage.toFixed(1)}% of total
            </div>
          </div>

          <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-4 border border-amber-200">
            <div className="text-xs font-medium text-amber-700 mb-1">
              Manual Review
            </div>
            <div className="text-2xl font-bold text-amber-900">
              {stats.manualReview}
            </div>
            <div className="text-xs text-amber-700">
              {stats.manualReviewPercentage.toFixed(1)}% of total
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="text-xs font-medium text-blue-700 mb-1">
              Total Violations
            </div>
            <div className="text-2xl font-bold text-blue-900">
              {stats.totalViolations}
            </div>
            <div className="text-xs text-blue-700">All categories</div>
          </div>

          <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
            <div className="text-xs font-medium text-purple-700 mb-1">
              Fix Efficiency
            </div>
            <div className="text-2xl font-bold text-purple-900">
              {stats.autoFixable > 0
                ? ((stats.autoFixable / stats.totalViolations) * 100).toFixed(0)
                : '0'}
              %
            </div>
            <div className="text-xs text-purple-700">Can be automated</div>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pie Chart - Overall Distribution */}
        <div className="flex flex-col">
          <Chart
            options={pieOptions}
            series={pieData?.series || []}
            type="pie"
            height={height}
          />
        </div>

        {/* Stacked Bar Chart - By Severity */}
        <div className="flex flex-col">
          <Chart
            options={stackedBarOptions}
            series={stackedBarData?.series || []}
            type="bar"
            height={height}
          />
        </div>
      </div>

      {/* Action Recommendations */}
      {stats && (
        <div className="mt-6 space-y-3">
          {/* High auto-fixability message */}
          {stats.autoFixablePercentage >= 50 && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-start space-x-3">
                <svg
                  className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900 mb-1">
                    Good News! High Auto-Fix Rate
                  </p>
                  <p className="text-xs text-green-700">
                    {stats.autoFixable} violations can be automatically fixed. Use
                    the "Apply Fixes to PDF" button to resolve them instantly.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Low auto-fixability message */}
          {stats.autoFixablePercentage < 50 && stats.manualReview > 0 && (
            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
              <div className="flex items-start space-x-3">
                <svg
                  className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-medium text-amber-900 mb-1">
                    Manual Review Required
                  </p>
                  <p className="text-xs text-amber-700">
                    {stats.manualReview} violations require manual review and
                    cannot be automatically fixed. Review the suggestions below and
                    apply changes manually.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Info about auto-fixability */}
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-start space-x-3">
              <svg
                className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div className="flex-1">
                <p className="text-xs font-medium text-blue-900 mb-1">
                  What Makes a Violation Auto-Fixable?
                </p>
                <p className="text-xs text-blue-700">
                  A violation is auto-fixable when the AI has identified the exact
                  text that needs to be changed and can provide a specific
                  replacement. Violations requiring contextual understanding or
                  creative input need manual review.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutoFixabilityAnalysis;
