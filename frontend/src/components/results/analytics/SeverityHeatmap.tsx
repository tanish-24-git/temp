/**
 * SeverityHeatmap Component
 * Displays a heatmap showing the intersection of categories and severity levels
 */

import React, { useMemo } from 'react';
import Chart from 'react-apexcharts';
import { ApexOptions } from 'apexcharts';
import { SeverityHeatmapProps, COMPLIANCE_COLORS } from './types';
import {
  prepareHeatmapData,
  isValidChartData,
  getEmptyStateMessage,
} from '../../../utils/chartDataTransformers';

const SeverityHeatmap: React.FC<SeverityHeatmapProps> = ({
  violations,
  height = 350,
}) => {
  // Check if we have valid data
  const hasValidData = useMemo(() => isValidChartData(violations), [violations]);
  const emptyMessage = useMemo(
    () => getEmptyStateMessage(violations),
    [violations]
  );

  // Transform data for heatmap
  const heatmapData = useMemo(
    () => (hasValidData ? prepareHeatmapData(violations) : null),
    [violations, hasValidData]
  );

  // Configure ApexCharts heatmap options
  const options: ApexOptions = useMemo(
    () => ({
      chart: {
        type: 'heatmap',
        fontFamily: 'Inter, system-ui, sans-serif',
        toolbar: {
          show: true,
          tools: {
            download: true,
            selection: false,
            zoom: false,
            zoomin: false,
            zoomout: false,
            pan: false,
            reset: false,
          },
        },
      },
      title: {
        text: 'Severity × Category Heatmap',
        align: 'center',
        style: {
          fontSize: '18px',
          fontWeight: 600,
          color: '#1F2937',
        },
      },
      plotOptions: {
        heatmap: {
          radius: 4,
          enableShades: true,
          shadeIntensity: 0.5,
          reverseNegativeShade: false,
          distributed: false,
          useFillColorAsStroke: false,
          colorScale: {
            ranges: [
              {
                from: 0,
                to: 0,
                color: '#F3F4F6',
                name: 'None',
              },
              {
                from: 1,
                to: 2,
                color: '#DBEAFE',
                name: 'Low (1-2)',
              },
              {
                from: 3,
                to: 5,
                color: '#93C5FD',
                name: 'Medium (3-5)',
              },
              {
                from: 6,
                to: 10,
                color: '#3B82F6',
                name: 'High (6-10)',
              },
              {
                from: 11,
                to: 100,
                color: '#1E40AF',
                name: 'Very High (11+)',
              },
            ],
          },
        },
      },
      dataLabels: {
        enabled: true,
        style: {
          fontSize: '14px',
          fontWeight: 600,
          colors: ['#1F2937'],
        },
        formatter: (val: number) => (val > 0 ? val.toString() : ''),
      },
      xaxis: {
        type: 'category',
        categories: heatmapData?.categories || [],
        labels: {
          style: {
            fontSize: '13px',
            fontWeight: 600,
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
        labels: {
          style: {
            fontSize: '13px',
            fontWeight: 500,
            colors: ['#DC2626', '#EA580C', '#F59E0B', '#10B981'],
          },
        },
      },
      grid: {
        borderColor: '#E5E7EB',
        strokeDashArray: 0,
        padding: {
          top: 0,
          right: 10,
          bottom: 0,
          left: 10,
        },
      },
      tooltip: {
        enabled: true,
        y: {
          formatter: (value, { seriesIndex, dataPointIndex, w }) => {
            const severityName = w.globals.seriesNames[seriesIndex];
            const categoryName = w.globals.labels[dataPointIndex];
            return `${value} ${severityName.toLowerCase()} violations in ${categoryName}`;
          },
        },
        style: {
          fontSize: '12px',
        },
      },
      legend: {
        show: true,
        position: 'bottom',
        fontSize: '11px',
        fontWeight: 500,
        labels: {
          colors: '#374151',
        },
        markers: {
          width: 16,
          height: 16,
          radius: 2,
        },
      },
      responsive: [
        {
          breakpoint: 640,
          options: {
            chart: {
              height: 300,
            },
            title: {
              style: {
                fontSize: '16px',
              },
            },
            dataLabels: {
              style: {
                fontSize: '12px',
              },
            },
            xaxis: {
              labels: {
                style: {
                  fontSize: '11px',
                },
              },
            },
            yaxis: {
              labels: {
                style: {
                  fontSize: '11px',
                },
              },
            },
          },
        },
      ],
    }),
    [heatmapData]
  );

  // Calculate summary statistics
  const statistics = useMemo(() => {
    if (!heatmapData) return null;

    const stats = {
      hottestCategory: { name: '', count: 0 },
      hottestSeverity: { name: '', count: 0 },
      totalCells: 0,
      nonZeroCells: 0,
    };

    const categoryTotals: { [key: string]: number } = {};
    const severityTotals: { [key: string]: number } = {};

    heatmapData.series.forEach((severity) => {
      let severityTotal = 0;
      severity.data.forEach((point) => {
        const count = point.y;
        severityTotal += count;

        // Track category totals
        categoryTotals[point.x] = (categoryTotals[point.x] || 0) + count;

        stats.totalCells++;
        if (count > 0) stats.nonZeroCells++;
      });

      severityTotals[severity.name] = severityTotal;
    });

    // Find hottest category
    Object.entries(categoryTotals).forEach(([name, count]) => {
      if (count > stats.hottestCategory.count) {
        stats.hottestCategory = { name, count };
      }
    });

    // Find hottest severity
    Object.entries(severityTotals).forEach(([name, count]) => {
      if (count > stats.hottestSeverity.count) {
        stats.hottestSeverity = { name, count };
      }
    });

    return stats;
  }, [heatmapData]);

  // Render empty state if no violations
  if (!hasValidData) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Severity Heatmap
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
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Severity Distribution Matrix
        </h3>
        <p className="text-sm text-gray-600">
          Intersection of violation categories and severity levels - darker colors
          indicate higher violation counts
        </p>
      </div>

      {/* Heatmap Chart */}
      <div className="flex justify-center">
        <Chart
          options={options}
          series={heatmapData?.series || []}
          type="heatmap"
          height={height}
        />
      </div>

      {/* Statistics Summary */}
      {statistics && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center space-x-2 mb-2">
              <svg
                className="w-5 h-5 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
              <div className="text-xs font-medium text-blue-700">
                Hottest Category
              </div>
            </div>
            <div className="text-xl font-bold text-blue-900">
              {statistics.hottestCategory.name}
            </div>
            <div className="text-sm text-blue-700">
              {statistics.hottestCategory.count} total violations
            </div>
          </div>

          <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-4 border border-red-200">
            <div className="flex items-center space-x-2 mb-2">
              <svg
                className="w-5 h-5 text-red-600"
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
              <div className="text-xs font-medium text-red-700">
                Hottest Severity
              </div>
            </div>
            <div className="text-xl font-bold text-red-900">
              {statistics.hottestSeverity.name}
            </div>
            <div className="text-sm text-red-700">
              {statistics.hottestSeverity.count} violations
            </div>
          </div>

          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center space-x-2 mb-2">
              <svg
                className="w-5 h-5 text-gray-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
              <div className="text-xs font-medium text-gray-700">Coverage</div>
            </div>
            <div className="text-xl font-bold text-gray-900">
              {statistics.nonZeroCells}/{statistics.totalCells}
            </div>
            <div className="text-sm text-gray-700">
              cells with violations
            </div>
          </div>
        </div>
      )}

      {/* Interpretation Guide */}
      <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-start space-x-2">
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
              How to Read This Chart
            </p>
            <p className="text-xs text-blue-700">
              Each cell represents the count of violations for a specific
              category-severity combination. Darker blue colors indicate higher
              violation counts. Focus on Critical and High severity rows for
              priority fixes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SeverityHeatmap;
