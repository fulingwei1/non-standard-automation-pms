import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout/PageHeader";
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
import { GitCompare, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "../lib/utils";

const sevConfig = {
  CRITICAL: "bg-red-500 text-white",
  HIGH: "bg-orange-500 text-white",
  MEDIUM: "bg-yellow-500 text-white",
  LOW: "bg-green-500 text-white",
};

const dirConfig = {
  better: { icon: TrendingUp, color: "text-green-600", label: "改善" },
  worse: { icon: TrendingDown, color: "text-red-600", label: "恶化" },
  stable: { icon: Minus, color: "text-gray-400", label: "持平" },
};

export default function OTDProjectCompare() {
  const [tab, setTab] = useState("projects"); // projects | trend
  const [projectCompare, setProjectCompare] = useState(null);
  const [trendCompare, setTrendCompare] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const scanResp = await otdApi.scan({ detail_level: "summary" });
      const projects = (scanResp.data?.data || scanResp.data)?.projects || [];
      // 取前 5 个对比
      const top5 = projects.slice(0, 5).map((p) => p.project_id);
      if (top5.length >= 2) {
        const resp = await otdApi.compareProjects(top5);
        setProjectCompare(resp.data?.data || resp.data);
      }
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTrend = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await otdApi.compareTrend(30);
      setTrendCompare(resp.data?.data || resp.data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tab === "projects") fetchProjects();
    else fetchTrend();
  }, [tab, fetchProjects, fetchTrend]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="对比分析"
        description="项目间风险对比 · 本期 vs 上期指标变化"
      />

      {/* Tab 切换 */}
      <div className="flex gap-2">
        <Button
          variant={tab === "projects" ? "default" : "outline"}
          size="sm"
          onClick={() => setTab("projects")}
        >
          <GitCompare className="w-4 h-4 mr-1" />
          项目间对比
        </Button>
        <Button
          variant={tab === "trend" ? "default" : "outline"}
          size="sm"
          onClick={() => setTab("trend")}
        >
          <TrendingUp className="w-4 h-4 mr-1" />
          时间对比
        </Button>
      </div>

      {loading && <LoadingSpinner text="加载对比数据..." />}
      {error && <ApiIntegrationError message={error} />}

      {!loading && tab === "projects" && projectCompare && (
        <ProjectCompareView data={projectCompare} />
      )}
      {!loading && tab === "trend" && trendCompare && (
        <TrendCompareView data={trendCompare} />
      )}
    </div>
  );
}

function ProjectCompareView({ data }) {
  if (!data?.projects?.length) {
    return <EmptyState title="无项目可对比" />;
  }
  return (
    <div className="space-y-4">
      {/* 共有风险 */}
      {data.shared_risks?.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h3 className="text-sm font-semibold mb-2">共有风险维度</h3>
            <div className="flex flex-wrap gap-2">
              {data.shared_risks.map((r) => (
                <Badge key={r.dim} variant="destructive">
                  {r.dim}（{r.project_count} 个项目）
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 对比表 */}
      <Card>
        <CardContent className="p-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2 pr-4">项目</th>
                <th className="pb-2 pr-4">风险等级</th>
                <th className="pb-2 pr-4">命中率</th>
                <th className="pb-2 pr-4">毛利率</th>
                <th className="pb-2 pr-4">偏差</th>
                <th className="pb-2 pr-4">进度</th>
              </tr>
            </thead>
            <tbody>
              {data.projects.map((p, idx) => (
                <motion.tr
                  key={p.project_id || idx}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="border-b hover:bg-gray-50"
                >
                  <td className="py-2 pr-4">
                    <div className="font-medium">
                      {p.project_name || p.project_code}
                    </div>
                    <div className="text-xs text-gray-400">
                      {p.project_code} · {p.stage}
                    </div>
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-xs",
                        sevConfig[p.severity] || sevConfig.LOW
                      )}
                    >
                      {p.severity}
                    </span>
                  </td>
                  <td className="py-2 pr-4">{p.risk_items_count} 维</td>
                  <td className="py-2 pr-4">
                    {p.current_margin_rate != null
                      ? `${p.current_margin_rate}%`
                      : "-"}
                  </td>
                  <td className="py-2 pr-4">
                    {p.margin_gap != null ? (
                      <span
                        className={
                          p.margin_gap < 0
                            ? "text-red-600"
                            : "text-green-600"
                        }
                      >
                        {p.margin_gap}%
                      </span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="py-2 pr-4">{p.progress}%</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function TrendCompareView({ data }) {
  const comparisons = data?.comparisons || [];
  const summary = data?.summary || {};

  return (
    <div className="space-y-4">
      {/* 汇总 */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="border-l-4 border-green-200">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-green-600">
              {summary.better_count}
            </p>
            <p className="text-xs text-gray-500">项改善</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-gray-200">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-gray-400">
              {summary.stable_count}
            </p>
            <p className="text-xs text-gray-500">项持平</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-red-200">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-red-600">
              {summary.worse_count}
            </p>
            <p className="text-xs text-gray-500">项恶化</p>
          </CardContent>
        </Card>
      </div>

      {/* 指标对比 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">指标变化</h3>
            <span className="text-xs text-gray-400">
              {data?.period?.current?.label} vs {data?.period?.previous?.label}
            </span>
          </div>
          <div className="space-y-2">
            {comparisons.map((c) => {
              const dir = dirConfig[c.direction] || dirConfig.stable;
              const DirIcon = dir.icon;
              return (
                <div
                  key={c.metric}
                  className="flex items-center gap-3 p-3 rounded-lg border"
                >
                  <DirIcon className={cn("w-4 h-4", dir.color)} />
                  <span className="text-sm font-medium flex-1">{c.metric}</span>
                  <div className="text-right">
                    <span className="text-sm font-semibold">
                      {c.current}
                    </span>
                    {c.change !== null && c.change !== 0 && (
                      <span
                        className={cn(
                          "text-xs ml-2",
                          c.change > 0 ? "text-green-600" : "text-red-600"
                        )}
                      >
                        {c.change > 0 ? "+" : ""}
                        {c.change}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-400 w-12 text-right">
                    上期 {c.previous}
                  </span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
