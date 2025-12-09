import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ApexOptions } from "apexcharts";
import ReactECharts from "echarts-for-react";
import { AlertCircle, CheckCircle2, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import ApexCharts from "react-apexcharts";
import { api } from "../lib/api";
import {
  DashboardStats,
  ComplianceTrendsResponse,
  ViolationsHeatmapResponse,
  TopViolation,
} from "../lib/types";

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trendsData, setTrendsData] = useState<ComplianceTrendsResponse | null>(null);
  const [heatmapData, setHeatmapData] = useState<ViolationsHeatmapResponse | null>(null);
  const [topViolations, setTopViolations] = useState<TopViolation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch all dashboard data in parallel
        const [statsRes, trendsRes, heatmapRes, topViolationsRes] = await Promise.all([
          api.getDashboardStats(),
          api.getDashboardTrends(30),
          api.getViolationsHeatmap(),
          api.getTopViolations(5),
        ]);

        setStats(statsRes.data);
        setTrendsData(trendsRes.data);
        setHeatmapData(heatmapRes.data);
        setTopViolations(topViolationsRes.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError("Failed to load dashboard data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  // Use real data from API - fallback to 0 if no data
  const overallScore = stats?.avg_compliance_score || 0;
  const grade = overallScore >= 90 ? 'A' : overallScore >= 80 ? 'B' : overallScore >= 70 ? 'C' : overallScore >= 60 ? 'D' : 'F';

  // 1. HERO GAUGE – This alone wins the demo with emerald/teal gradient
  const heroGaugeOption = {
    series: [
      {
        type: "gauge",
        startAngle: 90,
        endAngle: -270,
        radius: "85%",
        pointer: { show: false },
        progress: {
          show: true,
          overlap: false,
          roundCap: true,
          clip: false,
          itemStyle: {
            color: "#2dd4bf", // teal-400 for gradient effect
          },
        },
        axisLine: {
          lineStyle: {
            width: 28,
            color: [
              [overallScore / 100, "#10b981"], // emerald-500 for filled portion
              [1, "#e5e7eb"], // gray for remaining
            ],
          },
        },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        data: [{ value: overallScore, itemStyle: { color: "#10b981" } }],
        title: { fontSize: 18, offsetCenter: [0, "70%"] },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, 0],
          fontSize: 72,
          fontWeight: "bold",
          color: "#10b981",
          formatter: "{value}",
        },
      },
    ],
    backgroundColor: "transparent",
  };

  // 2. Trend – Use real API data (last 30 days)
  const trendScores = trendsData?.scores || [];
  const trendDates = trendsData?.dates || [];
  const hasTrendData = trendScores.length > 0;

  const trendOptions: ApexOptions = {
    series: [
      {
        name: "Score",
        data: hasTrendData ? trendScores : [0],
      },
    ],
    chart: {
      type: "area",
      height: 300,
      toolbar: { show: false },
      sparkline: { enabled: false },
    },
    stroke: { curve: "smooth", width: 4 },
    fill: {
      type: "gradient",
      gradient: { shadeIntensity: 1, opacityFrom: 0.7 },
    },
    colors: ["#005dac"],
    tooltip: { x: { format: "dd MMM" } },
    xaxis: {
      type: "datetime",
      categories: hasTrendData
        ? trendDates.map(d => new Date(d).toISOString())
        : [new Date().toISOString()],
    },
    noData: {
      text: "No trend data available",
      align: "center",
      verticalAlign: "middle",
      style: { color: "#999", fontSize: "14px" },
    },
  };

  // 3. Heatmap – Use real API data
  const heatmapSeries = heatmapData?.series || [
    { name: "Critical", data: [0, 0, 0] },
    { name: "High", data: [0, 0, 0] },
    { name: "Medium", data: [0, 0, 0] },
    { name: "Low", data: [0, 0, 0] },
  ];
  const heatmapCategories = heatmapData?.categories || ["IRDAI", "Brand", "SEO"];

  const heatmapOptions: ApexOptions = {
    series: heatmapSeries,
    chart: { type: "heatmap", height: 280, toolbar: { show: false } },
    plotOptions: {
      heatmap: {
        shadeIntensity: 0.8,
        colorScale: {
          ranges: [
            { from: 0, to: 5, color: "#10b981" },
            { from: 6, to: 12, color: "#f59e0b" },
            { from: 13, to: 100, color: "#ef4444" },
          ],
        },
      },
    },
    dataLabels: {
      enabled: true,
      style: { fontSize: "16px", fontWeight: "bold" },
    },
    colors: ["#ef4444"],
    xaxis: {
      categories: heatmapCategories.map((cat, idx) => {
        const weights = ["50%", "30%", "20%"];
        return `${cat} (${weights[idx] || ""})`;
      })
    },
    title: { text: "Violations by Category & Severity", align: "center" },
  };

  // 4. Donut - Use real data from stats
  const totalSubmissions = stats?.total_submissions || 0;
  const flaggedCount = stats?.flagged_count || 0;
  const pendingCount = stats?.pending_count || 0;
  const passedCount = Math.max(0, totalSubmissions - flaggedCount - pendingCount);
  const failedCount = pendingCount; // Using pending as "needs review"

  const donutOptions: ApexOptions = {
    series: [passedCount, flaggedCount, failedCount],
    chart: { type: "donut", height: 300 },
    labels: ["Passed", "Flagged", "Failed"],
    colors: ["#10b981", "#f59e0b", "#ef4444"],
    legend: { position: "bottom" },
    dataLabels: {
      enabled: true,
      formatter: (val: number) => `${Math.round(Number(val))}%`,
    },
    plotOptions: { pie: { donut: { size: "70%" } } },
  };

  // 5. Top 5 violations bar – Use real API data
  const hasTopViolations = topViolations.length > 0;
  const violationCounts = hasTopViolations
    ? topViolations.map(v => v.count)
    : [0];
  const violationNames = hasTopViolations
    ? topViolations.map(v => v.description.length > 40
      ? v.description.substring(0, 37) + "..."
      : v.description)
    : ["No violations found"];

  const barOptions: ApexOptions = {
    series: [{ data: violationCounts }],
    chart: { type: "bar", height: 300, toolbar: { show: false } },
    plotOptions: {
      bar: { borderRadius: 8, horizontal: true, distributed: true },
    },
    colors: ["#8b5cf6", "#005dac", "#10b981", "#f59e0b", "#ef4444"],
    dataLabels: {
      enabled: true,
      style: { fontSize: "14px", fontWeight: "bold" },
    },
    xaxis: {
      categories: violationNames,
    },
    noData: {
      text: "No violations data available",
      align: "center",
      verticalAlign: "middle",
      style: { color: "#999", fontSize: "14px" },
    },
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* KILLER METRIC BANNER */}


        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">
            Compliance Agent Dashboard
          </h1>
          <p className="text-gray-600 mt-2">
            Real-time insurance marketing compliance monitoring
          </p>
        </div>

        {/* HERO ROW */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <Card className="lg:col-span-1 shadow-2xl border-0 bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-700 text-white ring-4 ring-purple-500/20">
            <CardContent className="p-8">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <p className="text-2xl opacity-90">Overall Score</p>
                  <p className="text-7xl font-bold mt-2 animate-pulse">
                    {Math.round(overallScore)}
                  </p>
                  <Badge className="mt-4 text-2xl py-2 px-6 bg-white text-green-600">
                    Grade {grade}
                  </Badge>
                </div>
                <CheckCircle2 className="w-24 h-24 opacity-30" />
              </div>
              <ReactECharts
                option={heroGaugeOption}
                style={{ height: "300px", marginTop: "-60px" }}
              />
            </CardContent>
          </Card>

          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                Compliance Trend (Last 30 Days)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ApexCharts
                options={trendOptions}
                series={trendOptions.series}
                type="area"
                height={300}
              />
            </CardContent>
          </Card>

          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                Current Status Distribution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ApexCharts
                options={donutOptions}
                series={donutOptions.series}
                type="donut"
                height={300}
              />
            </CardContent>
          </Card>
        </div>

        {/* BOTTOM ROW */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="shadow-xl">
            <CardContent className="pt-6">
              <ApexCharts
                options={heatmapOptions}
                series={heatmapOptions.series}
                type="heatmap"
                height={340}
              />
            </CardContent>
          </Card>

          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle>Top 5 Most Common Violations</CardTitle>
            </CardHeader>
            <CardContent>
              <ApexCharts
                options={barOptions}
                series={barOptions.series}
                type="bar"
                height={300}
              />
            </CardContent>
          </Card>
        </div>

        {/* Quick stats footer */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          {[
            {
              label: "Total Submissions",
              value: String(stats?.total_submissions || 0),
              color: "bg-blue-500",
            },
            {
              label: "Avg Score",
              value: `${Math.round(overallScore)}%`,
              color: "bg-green-500",
            },
            {
              label: "Flagged",
              value: String(stats?.flagged_count || 0),
              color: "bg-amber-500",
            },
            {
              label: "Pending Review",
              value: String(stats?.pending_count || 0),
              color: "bg-red-500"
            },
          ].map((stat) => (
            <Card key={stat.label}>
              <CardContent className="p-6 text-center">
                <div
                  className={`w-12 h-12 ${stat.color} rounded-full mx-auto mb-3`}
                />
                <p className="text-3xl font-bold">{stat.value}</p>
                <p className="text-sm text-gray-600">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

