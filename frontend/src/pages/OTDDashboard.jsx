import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout/PageHeader";
import { NumericTrendChart, useTrendData } from "../components/otd/TrendChart";
import {
  Card,
  CardContent,
  Button,
  Badge,
  LoadingSpinner,
  EmptyState,
  ApiIntegrationError,
} from "../components/ui";
import { otdApi } from "../services/api/otd";
import {
  ShieldCheck,
  AlertTriangle,
  AlertOctagon,
  Download,
  RefreshCw,
  TrendingUp,
  FileBarChart,
} from "lucide-react";
import { cn } from "../lib/utils";

// severity 配色
const severityConfig = {
  CRITICAL: { color: "bg-red-500 text-white", label: "严重" },
  HIGH: { color: "bg-orange-500 text-white", label: "高危" },
  MEDIUM: { color: "bg-yellow-500 text-white", label: "中等" },
  LOW: { color: "bg-green-500 text-white", label: "低风险" },
};

export default function OTDDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [metricsData, setMetricsData] = useState(null);

  const fetchData = useCallback(
    async (force = false) => {
      try {
        if (force) setRefreshing(true);
        else setLoading(true);
        setError(null);

        const resp = await otdApi.scan({
          detail_level: "summary",
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
    []
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 全局风险趋势（每日各等级项目数）
  const trendData = useTrendData(() => otdApi.scanTrend(14), []);

  const handleExport = async () => {
    try {
      const resp = await otdApi.exportScan("summary");
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `OTD风险扫描_${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // 静默
    }
  };

  const loadMetrics = async () => {
    if (metricsData) {
      setShowMetrics(!showMetrics);
      return;
    }
    try {
      const resp = await otdApi.metrics({ include_offenders: false });
      setMetricsData(resp.data?.data || resp.data);
      setShowMetrics(true);
    } catch {
      // 静默
    }
  };

  if (loading) return <LoadingSpinner text="正在扫描项目风险..." />;
  if (error) return <ApiIntegrationError message={error} onRetry={fetchData} />;

  const projects = data?.projects || [];
  const summary = {
    scanned: data?.scanned || 0,
    withRisk: data?.with_risk || 0,
    highOrCritical: data?.high_or_critical || 0,
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="OTD 项目交付风险"
        description="11 维风险检测 · AI 归因 · 实时预警"
        action={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadMetrics}
            >
              <FileBarChart className="w-4 h-4 mr-1" />
              7 核心指标
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
            >
              <Download className="w-4 h-4 mr-1" />
              导出 Excel
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchData(true)}
              disabled={refreshing}
            >
              <RefreshCw className={cn("w-4 h-4 mr-1", refreshing && "animate-spin")} />
              {refreshing ? "刷新中..." : "强制刷新"}
            </Button>
          </div>
        }
      />

      {/* KPI 卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          icon={<ShieldCheck className="w-5 h-5 text-blue-500" />}
          label="在管项目"
          value={summary.scanned}
          color="border-blue-200"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5 text-yellow-500" />}
          label="有风险项目"
          value={summary.withRisk}
          color="border-yellow-200"
        />
        <StatCard
          icon={<AlertOctagon className="w-5 h-5 text-red-500" />}
          label="高危/严重"
          value={summary.highOrCritical}
          color="border-red-200"
        />
      </div>

      {/* 7 核心指标折叠区 */}
      {showMetrics && metricsData && (
        <Card>
          <CardContent className="p-4">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-1">
              <TrendingUp className="w-4 h-4" /> OTD 核心指标
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <MetricItem
                label="准时交付率"
                value={`${metricsData.metrics?.on_time_delivery_rate?.rate_pct || 0}%`}
              />
              <MetricItem
                label="平均延期天数"
                value={`${metricsData.metrics?.delay_days?.avg_delay_days || 0} 天`}
              />
              <MetricItem
                label="变更次数"
                value={metricsData.metrics?.change_count?.grand_total || 0}
              />
              <MetricItem
                label="平均毛利偏差"
                value={`${metricsData.metrics?.margin_deviation?.avg_margin_gap_pct || 0}%`}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* 风险列表 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">风险项目列表（按严重程度排序）</h3>
            {data?._from_cache && (
              <Badge variant="secondary" className="text-xs">
                缓存数据
              </Badge>
            )}
          </div>

          {projects.length === 0 ? (
            <EmptyState
              title="暂无风险项目"
              description="所有在管项目均未检测到风险"
            />
          ) : (
            <div className="space-y-2">
              {projects.map((p) => {
                const sev = severityConfig[p.severity] || severityConfig.LOW;
                return (
                  <motion.div
                    key={p.project_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/otd/scan/${p.project_id}`)}
                  >
                    <span
                      className={cn(
                        "px-2 py-1 rounded text-xs font-medium whitespace-nowrap",
                        sev.color
                      )}
                    >
                      {sev.label}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">
                          {p.project_name || p.project_code}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {p.stage}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500 truncate mt-0.5">
                        {p.top_cause || "无主要风险"}
                      </p>
                    </div>
                    {p.alert_id && (
                      <Badge variant="destructive" className="text-xs">
                        预警
                      </Badge>
                    )}
                  </motion.div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 全局风险趋势（每日 HIGH+CRITICAL 项目数） */}
      {trendData.data && (
        <NumericTrendChart
          dates={trendData.data.dates || []}
          values={(trendData.data.severity_trend || []).map(
            (d) => (d.HIGH || 0) + (d.CRITICAL || 0)
          )}
          title="全局高危项目数趋势（近 14 天）"
          unit=" 个"
          color="bg-red-500"
        />
      )}
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  return (
    <Card className={cn("border-l-4", color)}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-1">
          {icon}
          <span className="text-xs text-gray-500">{label}</span>
        </div>
        <p className="text-2xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}

function MetricItem({ label, value }) {
  return (
    <div className="p-2 rounded border">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-semibold mt-1">{value}</p>
    </div>
  );
}
