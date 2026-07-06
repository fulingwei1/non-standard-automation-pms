import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout/PageHeader";
import { SeverityTrendChart, useTrendData } from "../components/otd/TrendChart";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Progress,
  LoadingSpinner,
  EmptyState,
  ApiIntegrationError,
} from "../components/ui";
import { otdApi } from "../services/api/otd";
import {
  ChevronLeft,
  Download,
  RefreshCw,
  Sparkles,
  AlertTriangle,
  CheckCircle,
  Lightbulb,
} from "lucide-react";
import { cn } from "../lib/utils";

const severityConfig = {
  CRITICAL: { color: "bg-red-500 text-white", border: "border-red-500", label: "严重" },
  HIGH: { color: "bg-orange-500 text-white", border: "border-orange-500", label: "高危" },
  MEDIUM: { color: "bg-yellow-500 text-white", border: "border-yellow-500", label: "中等" },
  LOW: { color: "bg-green-500 text-white", border: "border-green-500", label: "低风险" },
};

export default function OTDProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [includeAi, setIncludeAi] = useState(false);

  const fetchData = useCallback(
    async (force = false, withAi = null) => {
      try {
        if (force) setRefreshing(true);
        else setLoading(true);
        setError(null);

        const useAi = withAi !== null ? withAi : includeAi;
        const resp = await otdApi.scanProject(projectId, {
          include_ai: useAi,
          force_refresh: force,
        });
        setData(resp.data?.data || resp.data);
      } catch (err) {
        setError(err.message || "加载失败");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [projectId, includeAi]
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 单项目风险趋势
  const trendData = useTrendData(
    () => otdApi.scanProjectTrend(projectId, 30),
    [projectId]
  );
  // 单项目指标
  const metricsData = useTrendData(
    () => otdApi.projectMetrics(projectId),
    [projectId]
  );

  const handleExport = async () => {
    try {
      const resp = await otdApi.exportProject(projectId, includeAi);
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `OTD_${data?.project_code || projectId}_${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // 静默
    }
  };

  const toggleAi = () => {
    const newVal = !includeAi;
    setIncludeAi(newVal);
    fetchData(true, newVal);
  };

  if (loading) return <LoadingSpinner text="正在扫描项目风险..." />;
  if (error) return <ApiIntegrationError message={error} onRetry={() => fetchData()} />;

  const sev = severityConfig[data?.severity] || severityConfig.LOW;
  const riskItems = data?.risk_items || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={data?.project_name || `项目 ${projectId}`}
        description={`${data?.project_code || ""} · 阶段 ${data?.stage || "?"} · 进度 ${data?.progress || 0}%`}
        breadcrumbs={[
          { label: "OTD 风险", path: "/otd/dashboard" },
          { label: data?.project_code || "详情" },
        ]}
        action={
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => navigate("/otd/dashboard")}>
              <ChevronLeft className="w-4 h-4 mr-1" />
              返回
            </Button>
            <Button
              variant={includeAi ? "default" : "outline"}
              size="sm"
              onClick={toggleAi}
              disabled={refreshing}
            >
              <Sparkles className="w-4 h-4 mr-1" />
              {includeAi ? "AI 已开启" : "开启 AI"}
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="w-4 h-4 mr-1" />
              导出
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchData(true)}
              disabled={refreshing}
            >
              <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              {refreshing ? "刷新中" : "刷新"}
            </Button>
          </div>
        }
      />

      {/* 风险概览卡 */}
      <Card className={cn("border-l-4", sev.border)}>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={cn("px-3 py-1.5 rounded-lg text-sm font-bold", sev.color)}>
                {data?.severity} · {sev.label}
              </span>
              <div>
                <p className="text-sm font-medium">{data?.top_cause || "无主要风险"}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  命中 {riskItems.length} 个风险维度
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="text-center">
                <p className="text-xs text-gray-500">计划交付</p>
                <p className="font-medium">{data?.planned_end || "-"}</p>
              </div>
              <div className="w-24">
                <Progress value={data?.progress || 0} className="h-2" />
                <p className="text-xs text-center mt-1">{data?.progress || 0}%</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI / 规则建议 */}
      {data?.suggestion && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-start gap-2">
              <div className="flex items-center gap-1 text-sm font-semibold text-blue-600">
                {data.suggestion_source === "ai" ? (
                  <Sparkles className="w-4 h-4" />
                ) : (
                  <Lightbulb className="w-4 h-4" />
                )}
                {data.suggestion_source === "ai" ? "AI 归因建议" : "规则建议"}
              </div>
              <p className="text-sm text-gray-700 flex-1 mt-0.5">
                {data.suggestion}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 风险维度详情 */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-semibold mb-3">
            11 维风险检测详情
          </h3>
          {riskItems.length === 0 ? (
            <EmptyState
              icon={<CheckCircle className="w-8 h-8 text-green-500" />}
              title="未检测到风险"
              description="该项目在 11 维检测中均未命中风险阈值"
            />
          ) : (
            <div className="space-y-2">
              {riskItems.map((item, idx) => {
                const dimSev = severityConfig[item.severity] || severityConfig.LOW;
                return (
                  <motion.div
                    key={`${item.dim}-${idx}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-start gap-3 p-3 rounded-lg border hover:bg-gray-50"
                  >
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap mt-0.5",
                        dimSev.color
                      )}
                    >
                      {item.severity}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{item.label}</span>
                        {item.dim && (
                          <Badge variant="outline" className="text-xs font-mono">
                            {item.dim}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 mt-1">{item.msg}</p>
                      {item.evidence && (
                        <details className="mt-1">
                          <summary className="text-xs text-blue-500 cursor-pointer">
                            查看证据
                          </summary>
                          <pre className="text-xs text-gray-500 mt-1 p-2 bg-gray-100 rounded overflow-auto">
                            {JSON.stringify(item.evidence, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 单项目风险趋势 */}
      <SeverityTrendChart
        dates={trendData.data?.dates || []}
        severity={trendData.data?.severity || []}
        title="风险等级趋势（近 30 天）"
      />

      {/* 单项目 OTD 指标 */}
      <Card>
        <CardContent className="p-4">
          <h3 className="text-sm font-semibold mb-3">项目 OTD 指标</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <MetricMini label="准时交付率" value={`${metricsData?.metrics?.on_time_delivery_rate?.rate_pct ?? "-"}%`} />
            <MetricMini label="延期天数" value={`${metricsData?.metrics?.delay_days?.avg_delay_days ?? "-"} 天`} />
            <MetricMini label="变更次数" value={metricsData?.metrics?.change_count?.grand_total ?? "-"} />
            <MetricMini label="毛利偏差" value={`${metricsData?.metrics?.margin_deviation?.avg_margin_gap_pct ?? "-"}%`} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricMini({ label, value }) {
  return (
    <div className="p-2 rounded border">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-semibold mt-1">{value}</p>
    </div>
  );
}
