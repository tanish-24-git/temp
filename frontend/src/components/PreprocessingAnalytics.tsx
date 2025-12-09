import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Package, Layers } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { PreprocessingStats } from "../lib/types";
import ApexCharts from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

export function PreprocessingAnalytics() {
    const [stats, setStats] = useState<PreprocessingStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await api.getPreprocessingStats();
                setStats(response.data);
            } catch (err) {
                console.error("Failed to fetch preprocessing stats:", err);
                setError("Failed to load preprocessing analytics. The backend endpoint may not be implemented yet.");
            } finally {
                setLoading(false);
            }
        };

        fetchStats();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (error || !stats) {
        return (
            <div className="p-6">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-yellow-800 mb-2">
                        📊 Preprocessing Analytics Coming Soon
                    </h3>
                    <p className="text-yellow-700 mb-4">
                        {error || "Preprocessing analytics dashboard will be available once the backend endpoint is implemented."}
                    </p>
                    <div className="bg-white rounded p-4 border border-yellow-300">
                        <h4 className="font-semibold mb-2">What you'll see here:</h4>
                        <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                            <li>Total submissions preprocessed vs. total submissions</li>
                            <li>Average chunks per document</li>
                            <li>Chunk distribution by content type (PDF, DOCX, HTML, Markdown)</li>
                            <li>Recent preprocessing activity timeline</li>
                            <li>Chunk size and token statistics</li>
                        </ul>
                    </div>
                </div>
            </div>
        );
    }

    // Calculate preprocessing percentage
    const preprocessingPercentage = stats.total_submissions > 0
        ? Math.round((stats.preprocessed_submissions / stats.total_submissions) * 100)
        : 0;

    // Content type distribution chart
    const contentTypeData = [
        stats.by_content_type.pdf,
        stats.by_content_type.docx,
        stats.by_content_type.html,
        stats.by_content_type.markdown
    ];

    const donutOptions: ApexOptions = {
        series: contentTypeData,
        chart: { type: "donut", height: 300 },
        labels: ["PDF", "DOCX", "HTML", "Markdown"],
        colors: ["#ef4444", "#3b82f6", "#10b981", "#f59e0b"],
        legend: { position: "bottom" },
        dataLabels: {
            enabled: true,
            formatter: (val: number) => `${Math.round(Number(val))}%`,
        },
        plotOptions: { pie: { donut: { size: "70%" } } },
    };

    return (
        <div className="p-6 bg-gray-50 min-h-screen">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 flex items-center gap-3">
                        <Package className="w-10 h-10 text-purple-600" />
                        Preprocessing Analytics
                    </h1>
                    <p className="text-gray-600 mt-2">
                        Chunked content processing statistics and insights
                    </p>
                </div>

                {/* Key Metrics Row */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <Card className="shadow-lg">
                        <CardContent className="p-6 text-center">
                            <FileText className="w-12 h-12 text-blue-500 mx-auto mb-3" />
                            <p className="text-3xl font-bold">{stats.total_submissions}</p>
                            <p className="text-sm text-gray-600">Total Submissions</p>
                        </CardContent>
                    </Card>

                    <Card className="shadow-lg">
                        <CardContent className="p-6 text-center">
                            <Layers className="w-12 h-12 text-purple-500 mx-auto mb-3" />
                            <p className="text-3xl font-bold">{stats.preprocessed_submissions}</p>
                            <p className="text-sm text-gray-600">Preprocessed</p>
                            <p className="text-xs text-gray-500 mt-1">
                                {preprocessingPercentage}% of total
                            </p>
                        </CardContent>
                    </Card>

                    <Card className="shadow-lg">
                        <CardContent className="p-6 text-center">
                            <Package className="w-12 h-12 text-green-500 mx-auto mb-3" />
                            <p className="text-3xl font-bold">{stats.total_chunks.toLocaleString()}</p>
                            <p className="text-sm text-gray-600">Total Chunks</p>
                        </CardContent>
                    </Card>

                    <Card className="shadow-lg">
                        <CardContent className="p-6 text-center">
                            <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-pink-500 rounded-full mx-auto mb-3 flex items-center justify-center">
                                <span className="text-white font-bold text-lg">
                                    {Math.round(stats.avg_chunks_per_submission)}
                                </span>
                            </div>
                            <p className="text-3xl font-bold">{stats.avg_chunks_per_submission.toFixed(1)}</p>
                            <p className="text-sm text-gray-600">Avg Chunks/Doc</p>
                        </CardContent>
                    </Card>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <Card className="shadow-lg">
                        <CardHeader>
                            <CardTitle>Content Type Distribution</CardTitle>
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

                    <Card className="shadow-lg">
                        <CardHeader>
                            <CardTitle>Preprocessing Progress</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between mb-2">
                                        <span className="text-sm font-medium">Overall Progress</span>
                                        <span className="text-sm font-bold text-purple-600">
                                            {preprocessingPercentage}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-4">
                                        <div
                                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-4 rounded-full transition-all duration-500"
                                            style={{ width: `${preprocessingPercentage}%` }}
                                        ></div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4 mt-6">
                                    <div className="bg-purple-50 p-4 rounded-lg">
                                        <p className="text-2xl font-bold text-purple-700">
                                            {stats.preprocessed_submissions}
                                        </p>
                                        <p className="text-xs text-purple-600">Chunked Documents</p>
                                    </div>
                                    <div className="bg-gray-50 p-4 rounded-lg">
                                        <p className="text-2xl font-bold text-gray-700">
                                            {stats.total_submissions - stats.preprocessed_submissions}
                                        </p>
                                        <p className="text-xs text-gray-600">Legacy Documents</p>
                                    </div>
                                </div>

                                <div className="bg-blue-50 p-4 rounded-lg mt-4">
                                    <p className="text-sm font-semibold text-blue-900 mb-2">
                                        💡 Chunking Benefits:
                                    </p>
                                    <ul className="text-xs text-blue-800 space-y-1">
                                        <li>✓ Precise violation location mapping</li>
                                        <li>✓ Support for documents &gt;10,000 characters</li>
                                        <li>✓ Faster parallel processing capabilities</li>
                                        <li>✓ Page and section-level metadata</li>
                                    </ul>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Recent Activity */}
                {stats.recent_preprocessing && stats.recent_preprocessing.length > 0 && (
                    <Card className="shadow-lg">
                        <CardHeader>
                            <CardTitle>Recent Preprocessing Activity</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {stats.recent_preprocessing.map((item, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                                    >
                                        <div>
                                            <p className="font-semibold text-gray-900">{item.title}</p>
                                            <p className="text-sm text-gray-600">
                                                {new Date(item.preprocessed_at).toLocaleString()}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-2xl font-bold text-purple-600">
                                                {item.chunks_created}
                                            </p>
                                            <p className="text-xs text-gray-500">chunks</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
}
