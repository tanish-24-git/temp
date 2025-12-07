/**
 * ViolationDistributionCharts Component
 * Displays violation distribution by severity (donut chart) and category (bar chart)
 */

import React, { useMemo } from 'react';
import Chart from 'react-apexcharts';
import { ApexOptions } from 'apexcharts';
import { ViolationDistributionChartsProps } from './types';
import {
  prepareSeverityDonutData,
  prepareCategoryBarData,
  isValidChartData,
  getEmptyStateMessage,
} from '../../../utils/chartDataTransformers';

const ViolationDistributionCharts: React.FC<
  ViolationDistributionChartsProps
> = ({ violations, height = 350 }) => {
  // Check if we have valid data
  const hasValidData = useMemo(() => isValidChartData(violations), [violations]);
  const emptyMessage = useMemo(
    () => getEmptyStateMessage(violations),
    [violations]
  );

  // Transform data for charts
  const severityData = useMemo(
    () => (hasValidData ? prepareSeverityDonutData(violations) : null),
    [violations, hasValidData]
  );

  const categoryData = useMemo(
    () => (hasValidData ? prepareCategoryBarData(violations) : null),
    [violations, hasValidData]
  );

  // Donut chart options for severity distribution
  const severityOptions: ApexOptions = useMemo(
    () => ({
      chart: {
        type: 'donut',
        fontFamily: 'Inter, system-ui, sans-serif',
        toolbar: {
          show: true,
          tools: {
            download: true,
          },
        },
      },
      title: {
        text: 'Violations by Severity',
        align: 'center',
        style: {
          fontSize: '16px',
          fontWeight: 600,
          color: '#1F2937',
        },
      },
      labels: severityData?.labels || [],
      colors: severityData?.colors || [],
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
      plotOptions: {
        pie: {
          donut: {
            size: '65%',
            labels: {
              show: true,
              name: {
                show: true,
                fontSize: '14px',
                fontWeight: 600,
                color: '#374151',
              },
              value: {
                show: true,
                fontSize: '24px',
                fontWeight: 700,
                color: '#1F2937',
                formatter: (val) => val.toString(),
              },
              total: {
                show: true,
                label: 'Total Violations',
                fontSize: '12px',
                fontWeight: 500,
                color: '#6B7280',
                formatter: (w) => {
                  const total = w.globals.seriesTotals.reduce(
                    (a: number, b: number) => a + b,
                    0
                  );
                  return total.toString();
                },
              },
            },
          },
        },
      },
      dataLabels: {
        enabled: true,
        formatter: (val: number, opts) => {
          const value = opts.w.globals.series[opts.seriesIndex];
          return value > 0 ? value.toString() : '';
        },
        style: {
          fontSize: '12px',
          fontWeight: 600,
          colors: ['#fff'],
        },
        dropShadow: {
          enabled: false,
        },
      },
      tooltip: {
        enabled: true,
        y: {
          formatter: (value, { seriesIndex }) => {
            const total = severityData?.series.reduce((a, b) => a + b, 0) || 0;
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
          },
        },
      ],
    }),
    [severityData]
  );

  // Bar chart options for category distribution
  const categoryOptions: ApexOptions = useMemo(
    () => ({
      chart: {
        type: 'bar',
        fontFamily: 'Inter, system-ui, sans-serif',
        toolbar: {
          show: true,
          tools: {
            download: true,
          },
        },
      },
      title: {
        text: 'Violations by Category',
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
          columnWidth: '50%',
          borderRadius: 6,
          dataLabels: {
            position: 'top',
          },
        },
      },
      dataLabels: {
        enabled: true,
        offsetY: -20,
        style: {
          fontSize: '12px',
          fontWeight: 600,
          colors: ['#374151'],
        },
      },
      xaxis: {
        categories: categoryData?.categories || [],
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
          show: true,
          color: '#E5E7EB',
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
      colors: ['#3B82F6', '#8B5CF6', '#06B6D4'],
      fill: {
        opacity: 1,
        type: 'gradient',
        gradient: {
          shade: 'light',
          type: 'vertical',
          shadeIntensity: 0.2,
          opacityFrom: 0.95,
          opacityTo: 0.75,
          stops: [0, 100],
        },
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
      tooltip: {
        enabled: true,
        y: {
          formatter: (value) => `${value} violations`,
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
                columnWidth: '60%',
              },
            },
          },
        },
      ],
    }),
    [categoryData]
  );

  // Render empty state if no violations
  if (!hasValidData) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Violation Distribution
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
          Violation Distribution
        </h3>
        <p className="text-sm text-gray-600">
          Distribution of {violations.length} violations across severity levels
          and categories
        </p>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Donut Chart */}
        <div className="flex flex-col">
          <Chart
            options={severityOptions}
            series={severityData?.series || []}
            type="donut"
            height={height}
          />
        </div>

        {/* Category Bar Chart */}
        <div className="flex flex-col">
          <Chart
            options={categoryOptions}
            series={categoryData?.series || []}
            type="bar"
            height={height}
          />
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        {severityData?.labels.map((label, index) => {
          const count = severityData.series[index];
          const total = severityData.series.reduce((a, b) => a + b, 0);
          const percentage = total > 0 ? ((count / total) * 100).toFixed(0) : '0';

          return (
            <div
              key={label}
              className="bg-gray-50 rounded-lg p-3 border border-gray-200"
            >
              <div className="flex items-center space-x-2 mb-1">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: severityData.colors[index] }}
                />
                <div className="text-xs font-medium text-gray-700">{label}</div>
              </div>
              <div className="text-lg font-bold text-gray-900">{count}</div>
              <div className="text-xs text-gray-600">{percentage}% of total</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ViolationDistributionCharts;
