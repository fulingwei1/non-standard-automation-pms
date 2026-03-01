/**
 * 质量报表页
 * 调用 GET /production/quality/trend, /production/quality/statistics, /production/quality/pareto
 */
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp, RefreshCw, Calendar, BarChart3,
  PieChart, AlertTriangle, CheckCircle, Target,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { qualityApi } from "../../services/api/quality";

function StatCard({ title, value, subtitle, icon: Icon, color, bgColor }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface-200 rounded-xl p-5 border border-white/5"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-text-secondary mb-1">{title}</p>
          <p className="text-3xl font-bold text-text-primary mb-1">{value}</p>
          {subtitle && <p className="text-xs text-text-muted">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${bgColor}`}>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
      </div>
    </motion.div>
  );
}

export default function QualityReports() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [paretoData, setParetoData] = useState(null);
  const [groupBy, setGroupBy] = useState("day");

  const now = new Date();
  const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 3600 * 1000);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 并行请求
      const [statsRes, trendRes, paretoRes] = await Promise.allSettled([
        qualityApi.statistics(),
        qualityApi.trend({
          start_date: thirtyDaysAgo.toISOString(),
          end_date: now.toISOString(),
          group_by: groupBy,
        }),
        qualityApi.pareto({
          start_date: thirtyDaysAgo.toISOString(),
          end_date: now.toISOString(),
          top_n: 10,
        }),
      ]);

      if (statsRes.status === "fulfilled") setStatistics(statsRes.value.data || statsRes.value);
      if (trendRes.status === "fulfilled") setTrendData(trendRes.value.data || trendRes.value);
      if (paretoRes.status === "fulfilled") setParetoData(paretoRes.value.data || paretoRes.value);
    } catch (err) {
      setError(err.message || "加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [groupBy]);

  const inputCls = "px-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-violet-500";

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="质量报表"
        subtitle="质量统计分析报表"
        icon={<TrendingUp className="h-6 w-6" />}
        actions={
          <Button variant="ghost" onClick={fetchData} className="gap-2">
            <RefreshCw className="h-4 w-4" /> 刷新
          </Button>
        }
      />

      <main className="container mx-auto px-4 py-6 max-w-7xl space-y-6">
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 text-sm">{error}</div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="h-6 w-6 text-violet-400 animate-spin" />
            <span className="ml-2 text-text-muted">加载中...</span>
          </div>
        ) : (
          <>
            {/* 统计卡片 */}
            {statistics && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  title="总检验数"
                  value={statistics.total_inspections ?? statistics.total ?? "-"}
                  subtitle="最近30天"
                  icon={Target}
                  color="text-blue-400"
                  bgColor="bg-blue-400/10"
                />
                <StatCard
                  title="合格率"
                  value={`${(statistics.pass_rate ?? statistics.overall_pass_rate ?? 0).toFixed(1)}%`}
                  subtitle={statistics.pass_rate_trend || ""}
                  icon={CheckCircle}
                  color="text-emerald-400"
                  bgColor="bg-emerald-400/10"
                />
                <StatCard
                  title="不良品数"
                  value={statistics.total_defects ?? statistics.defect_count ?? "-"}
                  subtitle="最近30天"
                  icon={AlertTriangle}
                  color="text-red-400"
                  bgColor="bg-red-400/10"
                />
                <StatCard
                  title="返工单数"
                  value={statistics.rework_count ?? statistics.total_rework ?? "-"}
                  subtitle="进行中"
                  icon={BarChart3}
                  color="text-amber-400"
                  bgColor="bg-amber-400/10"
                />
              </div>
            )}

            {/* 趋势分析 */}
            <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-violet-500/10">
                    <TrendingUp className="h-5 w-5 text-violet-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-text-primary">质量趋势</h3>
                </div>
                <select value={groupBy || "unknown"} onChange={(e) => setGroupBy(e.target.value)} className={inputCls}>
                  <option value="day">按日</option>
                  <option value="week">按周</option>
                  <option value="month">按月</option>
                </select>
              </div>

              {trendData?.data_points?.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th className="text-left px-4 py-2 text-text-muted font-medium">日期</th>
                        <th className="text-right px-4 py-2 text-text-muted font-medium">检验数</th>
                        <th className="text-right px-4 py-2 text-text-muted font-medium">合格数</th>
                        <th className="text-right px-4 py-2 text-text-muted font-medium">不良数</th>
                        <th className="text-right px-4 py-2 text-text-muted font-medium">不良率</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(trendData.data_points || []).map((point, idx) => (
                        <tr key={idx} className="border-b border-white/5">
                          <td className="px-4 py-2 text-text-primary">{point.date || point.period}</td>
                          <td className="px-4 py-2 text-right text-text-primary">{point.total_qty ?? point.inspection_count ?? "-"}</td>
                          <td className="px-4 py-2 text-right text-emerald-400">{point.qualified_qty ?? point.pass_count ?? "-"}</td>
                          <td className="px-4 py-2 text-right text-red-400">{point.defect_qty ?? point.fail_count ?? "-"}</td>
                          <td className="px-4 py-2 text-right">
                            <span className={`${(point.defect_rate ?? point.fail_rate ?? 0) > 5 ? "text-red-400" : "text-emerald-400"}`}>
                              {(point.defect_rate ?? point.fail_rate ?? 0).toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 text-text-muted">暂无趋势数据</div>
              )}
            </div>

            {/* 帕累托分析 */}
            <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-amber-500/10">
                  <PieChart className="h-5 w-5 text-amber-400" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary">帕累托分析 (Top 不良类型)</h3>
              </div>

              {paretoData?.items?.length > 0 ? (
                <div className="space-y-3">
                  {(paretoData.items || []).map((item, idx) => {
                    const maxCount = paretoData.items[0]?.count || 1;
                    const widthPct = Math.max(5, (item.count / maxCount) * 100);
                    return (
                      <div key={idx} className="flex items-center gap-3">
                        <span className="text-sm text-text-muted w-32 truncate">{item.defect_type || item.name}</span>
                        <div className="flex-1 bg-surface-300 rounded-full h-6 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full flex items-center justify-end pr-2"
                            style={{ width: `${widthPct}%` }}
                          >
                            <span className="text-xs text-white font-medium">{item.count}</span>
                          </div>
                        </div>
                        <span className="text-sm text-text-muted w-16 text-right">
                          {(item.cumulative_percentage ?? item.percentage ?? 0).toFixed(1)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12 text-text-muted">暂无帕累托分析数据</div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
