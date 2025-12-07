/**
 * ScoreComparisonRadar Component
 * Displays compliance scores across all categories (IRDAI, Brand, SEO, Overall) in a radar chart
 */

import React, { useMemo } from 'react';
import Chart from 'react-apexcharts';
import { ApexOptions } from 'apexcharts';
import { ScoreComparisonRadarProps } from './types';
import { prepareRadarData } from '../../../utils/chartDataTransformers';

const ScoreComparisonRadar: React.FC<ScoreComparisonRadarProps> = ({
  results,
  height = 400,
}) => {
  // Transform data for radar chart
  const chartData = useMemo(() => prepareRadarData(results), [results]);

  // Configure ApexCharts options
  const options: ApexOptions = useMemo(
    () => ({
      chart: {
        type: 'radar',
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
        fontFamily: 'Inter, system-ui, sans-serif',
      },
      title: {
        text: 'Compliance Score Overview',
        align: 'center',
        style: {
          fontSize: '18px',
          fontWeight: 600,
          color: '#1F2937',
        },
      },
      xaxis: {
        categories: chartData.categories,
        labels: {
          style: {
            fontSize: '12px',
            fontWeight: 500,
            colors: ['#374151', '#374151', '#374151', '#374151'],
          },
        },
      },
      yaxis: {
        min: 0,
        max: 100,
        tickAmount: 5,
        labels: {
          formatter: (value) => `${value.toFixed(0)}`,
          style: {
            fontSize: '11px',
            colors: '#6B7280',
          },
        },
      },
      plotOptions: {
        radar: {
          size: undefined,
          offsetX: 0,
          offsetY: 0,
          polygons: {
            strokeColors: '#E5E7EB',
            strokeWidth: 1,
            connectorColors: '#E5E7EB',
            fill: {
              colors: ['#F9FAFB', '#F3F4F6'],
            },
          },
        },
      },
      colors: ['#3B82F6'], // blue-500
      fill: {
        opacity: 0.2,
      },
      stroke: {
        show: true,
        width: 2,
        colors: ['#3B82F6'],
        dashArray: 0,
      },
      markers: {
        size: 5,
        colors: ['#3B82F6'],
        strokeColors: '#fff',
        strokeWidth: 2,
        hover: {
          size: 7,
        },
      },
      tooltip: {
        enabled: true,
        y: {
          formatter: (value) => `${value.toFixed(1)} / 100`,
        },
        style: {
          fontSize: '12px',
        },
      },
      legend: {
        show: false,
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
            xaxis: {
              labels: {
                style: {
                  fontSize: '10px',
                },
              },
            },
          },
        },
      ],
    }),
    [chartData]
  );

  // Prepare series data
  const series = useMemo(() => chartData.series, [chartData]);

  // Calculate average score for summary
  const averageScore = useMemo(() => {
    const total = chartData.series[0].data.reduce((acc, val) => acc + val, 0);
    return (total / chartData.series[0].data.length).toFixed(1);
  }, [chartData]);

  // Determine score status
  const getScoreStatus = (score: number): { text: string; color: string } => {
    if (score >= 80) return { text: 'Excellent', color: 'text-green-600' };
    if (score >= 60) return { text: 'Good', color: 'text-blue-600' };
    if (score >= 40) return { text: 'Fair', color: 'text-yellow-600' };
    return { text: 'Needs Improvement', color: 'text-red-600' };
  };

  const scoreStatus = getScoreStatus(results.overall_score);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header with summary */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            Score Comparison
          </h3>
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              {results.overall_score.toFixed(1)}
            </div>
            <div className={`text-sm font-medium ${scoreStatus.color}`}>
              {scoreStatus.text}
            </div>
          </div>
        </div>
        <p className="text-sm text-gray-600">
          Breakdown of compliance scores across all categories
        </p>
      </div>

      {/* Radar Chart */}
      <div className="flex justify-center">
        <Chart options={options} series={series} type="radar" height={height} />
      </div>

      {/* Score breakdown cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
          <div className="text-xs font-medium text-blue-700 mb-1">IRDAI</div>
          <div className="text-xl font-bold text-blue-900">
            {results.irdai_score.toFixed(1)}
          </div>
          <div className="text-xs text-blue-600">Critical compliance</div>
        </div>

        <div className="bg-violet-50 rounded-lg p-3 border border-violet-200">
          <div className="text-xs font-medium text-violet-700 mb-1">Brand</div>
          <div className="text-xl font-bold text-violet-900">
            {results.brand_score.toFixed(1)}
          </div>
          <div className="text-xs text-violet-600">Guidelines adherence</div>
        </div>

        <div className="bg-cyan-50 rounded-lg p-3 border border-cyan-200">
          <div className="text-xs font-medium text-cyan-700 mb-1">SEO</div>
          <div className="text-xl font-bold text-cyan-900">
            {results.seo_score.toFixed(1)}
          </div>
          <div className="text-xs text-cyan-600">Optimization score</div>
        </div>

        <div className="bg-gray-50 rounded-lg p-3 border border-gray-300">
          <div className="text-xs font-medium text-gray-700 mb-1">Overall</div>
          <div className="text-xl font-bold text-gray-900">
            {results.overall_score.toFixed(1)}
          </div>
          <div className="text-xs text-gray-600">Weighted average</div>
        </div>
      </div>

      {/* Score interpretation */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
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
            <p className="text-xs font-medium text-gray-700 mb-1">
              Score Calculation
            </p>
            <p className="text-xs text-gray-600">
              Overall score is weighted: IRDAI (50%), Brand (30%), SEO (20%).
              Higher scores indicate better compliance with respective guidelines.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScoreComparisonRadar;
