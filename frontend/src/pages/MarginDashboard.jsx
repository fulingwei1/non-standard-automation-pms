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
  Progress,
  LoadingSpinner,
  EmptyState,
  ApiIntegrationError,
} from "../components/ui";
import { otdApi } from "../services/api/otd";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Target,
} from "lucide-react";
import { cn } from "../lib/utils";

const healthConfig = {
  healthy: { color: "bg-green-500 text-white", label: "健康", icon: CheckCircle },
  warning: { color: "bg-yellow-500 text-white", label: "预警", icon: AlertCircle },
  critical: { color: "bg-red-500 text-white", label: "危险", icon: AlertCircle },
};

export default function MarginDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const resp = await otdApi.marginDashboard();
      setData(resp.data?.data || resp.data);
    } catch (err) {
      setError(err.message || "加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 全局毛利率趋势 + 等级底线 + 回填状态
  const [showTrend, setShowTrend] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const trendData = useTrendData(
    () => otdApi.marginTrend(30),
    []
  );
  const levelsData = useTrendData(
    () => otdApi.marginLevels(),
    []
  );
  // 单项目毛利率趋势（按选择加载）
  const projectTrend = useTrendData(
    () =>
      selectedProject
        ? otdApi.marginProjectTrend(selectedProject, 30)
        : Promise.resolve({ data: { data: null } }),
    [selectedProject]
  );

  const handleBackfill = async () => {
    try {
      // otdApi 没有 backfill 方法，直接用 client 调
      const resp = await import("../services/api/client.js").then((m) =>
        m.default.post("/pmo/margin-dashboard/backfill?days=30")
      );
      if (resp.data?.code === 200) {
        fetchData();
        window.location.reload();
      }
    } catch {
      // 静默
    }
  };

  const handleExport = async () => {
    try {
      const resp = await otdApi.exportMarginDashboard();
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `毛利率看板_${new Date().toISOString().slice(0, 10)}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      // 静默
    }
  };

  if (loading) return <LoadingSpinner text="正在加载毛利率数据..." />;
  if (error) return <ApiIntegrationError message={error} onRetry={fetchData} />;

  const summary = data?.summary || {};
  const distribution = data?.distribution || {};
  const anomalies = data?.anomalies || {};

  return (
    <div className="space-y-6">
      <PageHeader
        title="毛利率 Dashboard"
        description="全局毛利率健康度 · 分级管控 · 异常追踪"
        action={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="w-4 h-4 mr-1" />
              导出 Excel
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setRefreshing(true);
                otdApi.marginSnapshotRun().then(() => {
                  fetchData();
                  setRefreshing(false);
                });
              }}
              disabled={refreshing}
            >
              <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              {refreshing ? "刷新中" : "刷新快照"}
            </Button>
          </div>
        }
      />

      {/* KPI 卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          icon={<DollarSign className="w-5 h-5 text-blue-500" />}
          label="在管项目"
          value={summary.total_projects || 0}
          color="border-blue-200"
        />
        <StatCard
          icon={<TrendingUp className="w-5 h-5 text-green-500" />}
          label="平均毛利率"
          value={`${summary.avg_margin_rate || 0}%`}
          color="border-green-200"
        />
        <StatCard
          icon={<Target className="w-5 h-5 text-purple-500" />}
          label="达标率"
          value={`${summary.achieve_target_rate_pct || 0}%`}
          color="border-purple-200"
        />
        <StatCard
          icon={<TrendingDown className="w-5 h-5 text-red-500" />}
          label="低于目标"
          value={summary.below_target_count || 0}
          color="border-red-200"
        />
      </div>

      {/* 健康度分布 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <h3 className="text-sm font-semibold mb-3">健康度分布</h3>
            <div className="space-y-2">
              {["healthy", "warning", "critical"].map((h) => {
                const cfg = healthConfig[h];
                const count = summary[`${h}_count`] || 0;
                const pct = summary.total_projects
                  ? Math.round((count / summary.total_projects) * 100)
                  : 0;
                return (
                  <div key={h} className="flex items-center gap-3">
                    <span className={cn("px-2 py-1 rounded text-xs", cfg.color)}>
                      {cfg.label}
                    </span>
                    <div className="flex-1">
                      <Progress value={pct} className="h-2" />
                    </div>
                    <span className="text-sm font-medium w-16 text-right">
                      {count} 个 ({pct}%)
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <h3 className="text-sm font-semibold mb-3">毛利率分桶</h3>
            <div className="space-y-2">
              {Object.entries(distribution.by_margin_bucket || {}).map(
                ([bucket, count]) => (
                  <div key={bucket} className="flex items-center gap-2 text-sm">
                    <span className="text-gray-600 w-32">{bucket}</span>
                    <div className="flex-1">
                      <Progress
                        value={
                          summary.total_projects
                            ? (count / summary.total_projects) * 100
                            : 0
                        }
                        className="h-2"
                      />
                    </div>
                    <span className="font-medium w-8 text-right">{count}</span>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 异常项目 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold flex items-center gap-1">
              <AlertCircle className="w-4 h-4 text-red-500" />
              低毛利项目 Top {anomalies.low_profit_projects?.length || 0}
            </h3>
            <Badge variant="destructive" className="text-xs">
              {anomalies.total_low_profit || 0} 个异常
            </Badge>
          </div>
          {anomalies.low_profit_projects?.length > 0 ? (
            <div className="space-y-2">
              {anomalies.low_profit_projects.map((p, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="flex items-center gap-3 p-3 rounded-lg border hover:bg-gray-50"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {p.project_name || p.project_code}
                    </p>
                    {p.root_causes?.length > 0 && (
                      <p className="text-xs text-gray-500 mt-0.5">
                        {p.root_causes.join("、")}
                      </p>
                    )}
                  </div>
                  {p.current_margin_rate !== undefined && (
                    <Badge
                      variant={
                        p.current_margin_rate < 0
                          ? "destructive"
                          : "secondary"
                      }
                    >
                      {p.current_margin_rate}%
                    </Badge>
                  )}
                </motion.div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<CheckCircle className="w-8 h-8 text-green-500" />}
              title="无低毛利项目"
              description="所有项目毛利率均在目标范围内"
            />
          )}
        </CardContent>
      </Card>

      {/* 单项目毛利率趋势（可选项目） */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">单项目毛利率趋势</h3>
            <select
              className="text-sm border rounded px-2 py-1"
              value={selectedProject || ""}
              onChange={(e) =>
                setSelectedProject(e.target.value ? Number(e.target.value) : null)
              }
            >
              <option value="">选择项目...</option>
              {(anomalies.low_profit_projects || []).map((p) => (
                <option key={p.project_id} value={p.project_id}>
                  {p.project_name || p.project_code}
                </option>
              ))}
            </select>
          </div>
          {selectedProject && projectTrend.data ? (
            <NumericTrendChart
              dates={projectTrend.data.dates || []}
              values={projectTrend.data.current_margin_rate || []}
              title={`${projectTrend.data.project_code || ""} 毛利率趋势`}
              unit="%"
              targetLine={projectTrend.data.health?.[0] ? undefined : 25}
            />
          ) : (
            <p className="text-xs text-gray-400 text-center py-4">
              选择一个项目查看毛利率趋势
            </p>
          )}
        </CardContent>
      </Card>

      {/* 全局毛利率趋势 */}
      {trendData.data && (
        <NumericTrendChart
          dates={trendData.data.dates || []}
          values={trendData.data.avg_margin_rate || []}
          title="全局平均毛利率趋势（近 30 天）"
          unit="%"
          targetLine={summary.target_margin_rate || 25}
        />
      )}

      {/* 冷启动回填提示 */}
      {trendData.data?.needs_backfill && (
        <Card className="border-yellow-300 bg-yellow-50">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-800">
                {trendData.data.hint || "趋势数据不足"}
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={handleBackfill}>
              回填 30 天快照
            </Button>
          </CardContent>
        </Card>
      )}

      {/* 项目等级毛利率底线 */}
      {levelsData.data?.levels?.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h3 className="text-sm font-semibold mb-3">
              项目等级毛利率底线（手册红线）
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {levelsData.data.levels.map((lv) => (
                <div
                  key={lv.project_level}
                  className="p-3 rounded-lg border text-center"
                >
                  <p className="text-lg font-bold text-blue-600">
                    {lv.project_level} 级
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    目标 {lv.standard_margin}%
                  </p>
                  <p className="text-xs text-gray-400">
                    底线 {lv.minimum_margin}%
                  </p>
                  <p className="text-xs text-gray-300 mt-1">
                    {lv.description}
                  </p>
                </div>
              ))}
              <div className="p-3 rounded-lg border-2 border-red-200 text-center bg-red-50">
                <p className="text-lg font-bold text-red-600">红线</p>
                <p className="text-xs text-gray-500 mt-1">≥ {levelsData.data.floor_margin}%</p>
                <p className="text-xs text-red-400">低于须特批</p>
              </div>
            </div>
          </CardContent>
        </Card>
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
