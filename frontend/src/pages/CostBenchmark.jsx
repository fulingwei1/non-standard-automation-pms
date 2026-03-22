/**
 * 成本对标分析
 * - 查找相似历史项目
 * - 成本对比分析
 * - 劳动力成本明细
 * - 对标报告
 */

import { useState, useEffect } from "react";
import {
  GitCompare,
  TrendingUp,
  AlertTriangle,
  Users,
  Target,
  Percent,
} from "lucide-react";
import { staggerContainer, fadeIn } from "../lib/animations";
import { costBenchmarkApi } from "../services/api/costBenchmark";

// 相似度级别颜色
const SIMILARITY_COLORS = {
  HIGH: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "高度相似" },
  MEDIUM: { bg: "bg-blue-500/20", text: "text-blue-400", label: "中度相似" },
  LOW: { bg: "bg-amber-500/20", text: "text-amber-400", label: "低度相似" },
  MINIMAL: { bg: "bg-slate-500/20", text: "text-slate-400", label: "相似度低" },
};

function StatCard({ icon: Icon, label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-surface-1/50 border border-white/5 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs text-slate-400">{label}</span>
      </div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  );
}

function SimilarityBadge({ level }) {
  const config = SIMILARITY_COLORS[level] || SIMILARITY_COLORS.MINIMAL;
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}

function ProgressBar({ value, max = 100, color = "bg-blue-500" }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
      <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function CostBenchmark() {
  const [projectId, setProjectId] = useState("");
  const [similarProjects, setSimilarProjects] = useState([]);
  const [benchmarks, setBenchmarks] = useState([]);
  const [report, setReport] = useState(null);
  const [laborCosts, setLaborCosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("similar"); // similar | benchmarks | labor

  // 查找相似项目
  const handleFindSimilar = async () => {
    if (!projectId) {
      alert("请输入项目ID");
      return;
    }
    try {
      setLoading(true);
      const res = await costBenchmarkApi.findSimilarProjects(projectId, { top_k: 10 });
      setSimilarProjects(res.data || res || []);
    } catch (err) {
      alert("查找失败: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // 加载对标记录
  const loadBenchmarks = async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      const res = await costBenchmarkApi.getBenchmarks(projectId);
      setBenchmarks(res.data || res || []);
    } catch (err) {
    } finally {
      setLoading(false);
    }
  };

  // 生成对标报告
  const handleGenerateReport = async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      const res = await costBenchmarkApi.generateReport(projectId);
      setReport(res.data || res);
    } catch (err) {
      alert("生成报告失败: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // 加载劳动力成本
  const loadLaborCosts = async () => {
    if (!projectId) return;
    try {
      setLoading(true);
      const res = await costBenchmarkApi.getLaborCosts(projectId);
      setLaborCosts(res.data || res || []);
    } catch (err) {
    } finally {
      setLoading(false);
    }
  };

  // 创建对标
  const handleCreateBenchmark = async (benchmarkProjectId) => {
    try {
      await costBenchmarkApi.createBenchmark(projectId, {
        benchmark_project_id: benchmarkProjectId,
      });
      alert("对标记录已创建");
      loadBenchmarks();
    } catch (err) {
      alert("创建失败: " + err.message);
    }
  };

  // Tab 切换时加载数据
  useEffect(() => {
    if (!projectId) return;
    if (activeTab === "benchmarks") {
      loadBenchmarks();
    } else if (activeTab === "labor") {
      loadLaborCosts();
    }
  }, [activeTab, projectId]);

  const formatWan = (value) => `¥${((value || 0) / 10000).toFixed(2)}万`;

  return (
    <div className="space-y-6">
      <PageHeader title="成本对标分析" subtitle="历史对标 · 相似项目 · 劳动力成本" />

      <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
        {/* 项目选择 */}
        <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-4">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-xs text-slate-400 mb-1 block">项目 ID</label>
              <input
                type="text"
                className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                placeholder="输入要分析的项目ID..."
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
              />
            </div>
            <div className="flex items-end gap-2">
              <button
                onClick={handleFindSimilar}
                disabled={loading || !projectId}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white text-sm rounded-lg flex items-center gap-2"
              >
                <Search className="w-4 h-4" />
                查找相似项目
              </button>
              <button
                onClick={handleGenerateReport}
                disabled={loading || !projectId}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-slate-700 text-white text-sm rounded-lg flex items-center gap-2"
              >
                <FileText className="w-4 h-4" />
                生成报告
              </button>
            </div>
          </div>
        </motion.div>

        {/* Tab 切换 */}
        <motion.div variants={fadeIn} className="flex gap-2">
          {[
            { key: "similar", label: "相似项目", icon: GitCompare, count: similarProjects.length },
            { key: "benchmarks", label: "对标记录", icon: Target },
            { key: "labor", label: "劳动力成本", icon: Users },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                activeTab === tab.key
                  ? "bg-blue-600 text-white"
                  : "bg-surface-1/50 text-slate-400 hover:text-white"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className="px-1.5 py-0.5 rounded-full bg-blue-500/30 text-white text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </motion.div>

        {/* 对标报告摘要 */}
        {report && (
          <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              icon={GitCompare}
              label="对标项目数"
              value={report.benchmark_count}
              color="text-blue-400"
            />
            <StatCard
              icon={Percent}
              label="平均相似度"
              value={`${report.average_similarity}%`}
              color="text-emerald-400"
            />
            <StatCard
              icon={TrendingUp}
              label="成本差异率"
              value={`${report.average_cost_variance_ratio > 0 ? "+" : ""}${report.average_cost_variance_ratio}%`}
              color={report.average_cost_variance_ratio > 10 ? "text-red-400" : "text-emerald-400"}
            />
            <StatCard
              icon={AlertTriangle}
              label="风险等级"
              value={report.risk_level === "HIGH" ? "高" : report.risk_level === "MEDIUM" ? "中" : "低"}
              color={
                report.risk_level === "HIGH"
                  ? "text-red-400"
                  : report.risk_level === "MEDIUM"
                  ? "text-amber-400"
                  : "text-emerald-400"
              }
            />
          </motion.div>
        )}

        {/* 相似项目列表 */}
        {activeTab === "similar" && (
          <motion.div variants={fadeIn} className="space-y-4">
            {loading ? (
              <div className="text-center text-slate-500 py-12">加载中...</div>
            ) : similarProjects.length === 0 ? (
              <div className="text-center text-slate-500 py-12 bg-surface-1/50 border border-white/5 rounded-xl">
                请先输入项目ID并点击"查找相似项目"
              </div>
            ) : (
              similarProjects.map((project, index) => (
                <div
                  key={project.project_id}
                  className="bg-surface-1/50 border border-white/5 rounded-xl p-4 hover:border-white/10 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className="text-slate-500 text-sm">#{index + 1}</span>
                        <h4 className="text-white font-medium">{project.project_name}</h4>
                        <span className="text-xs text-slate-500 font-mono">{project.project_no}</span>
                        <SimilarityBadge level={project.similarity_level} />
                      </div>
                      <p className="text-sm text-slate-400 mt-1">
                        {project.customer_name || "未知客户"} · {project.industry || "未知行业"}
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-400">
                        {project.total_score}%
                      </div>
                      <div className="text-xs text-slate-500">相似度</div>
                    </div>
                  </div>

                  {/* 相似度细分 */}
                  <div className="grid grid-cols-5 gap-4 mt-4">
                    <div>
                      <div className="text-xs text-slate-500 mb-1">行业</div>
                      <ProgressBar value={project.industry_score} color="bg-blue-500" />
                      <div className="text-xs text-slate-400 mt-1">{project.industry_score}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1">测试类型</div>
                      <ProgressBar value={project.test_type_score} color="bg-purple-500" />
                      <div className="text-xs text-slate-400 mt-1">{project.test_type_score}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1">规模</div>
                      <ProgressBar value={project.scale_score} color="bg-emerald-500" />
                      <div className="text-xs text-slate-400 mt-1">{project.scale_score}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1">复杂度</div>
                      <ProgressBar value={project.complexity_score} color="bg-amber-500" />
                      <div className="text-xs text-slate-400 mt-1">{project.complexity_score}%</div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 mb-1">客户类型</div>
                      <ProgressBar value={project.customer_score} color="bg-pink-500" />
                      <div className="text-xs text-slate-400 mt-1">{project.customer_score}%</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-4 pt-3 border-t border-white/5">
                    <div className="flex gap-4">
                      <span className="text-sm text-slate-400">
                        历史成本: <span className="text-white font-mono">{formatWan(project.total_cost)}</span>
                      </span>
                      {project.completed_at && (
                        <span className="text-sm text-slate-500">
                          完成于 {new Date(project.completed_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleCreateBenchmark(project.project_id)}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs rounded flex items-center gap-1"
                    >
                      <Target className="w-3 h-3" />
                      设为对标
                    </button>
                  </div>
                </div>
              ))
            )}
          </motion.div>
        )}

        {/* 对标记录 */}
        {activeTab === "benchmarks" && (
          <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-800/50">
                <tr>
                  <th className="text-left text-slate-400 py-3 px-4">对标项目</th>
                  <th className="text-right text-slate-400 py-3 px-4">相似度</th>
                  <th className="text-right text-slate-400 py-3 px-4">当前预估</th>
                  <th className="text-right text-slate-400 py-3 px-4">对标实际</th>
                  <th className="text-right text-slate-400 py-3 px-4">差异</th>
                  <th className="text-center text-slate-400 py-3 px-4">状态</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center text-slate-500 py-12">加载中...</td>
                  </tr>
                ) : benchmarks.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center text-slate-500 py-12">
                      暂无对标记录，请先查找相似项目并设为对标
                    </td>
                  </tr>
                ) : (
                  benchmarks.map((b) => (
                    <tr key={b.id} className="border-t border-white/5 hover:bg-white/[0.02]">
                      <td className="py-3 px-4 text-slate-300">
                        项目 #{b.benchmark_project_id}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="text-blue-400 font-mono">{b.similarity_score}%</span>
                      </td>
                      <td className="py-3 px-4 text-right text-slate-300">
                        {formatWan(b.current_estimated_cost)}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-300">
                        {formatWan(b.benchmark_actual_cost)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={`font-mono ${
                          b.cost_variance_ratio > 10 ? "text-red-400" :
                          b.cost_variance_ratio > 0 ? "text-amber-400" : "text-emerald-400"
                        }`}>
                          {b.cost_variance_ratio > 0 ? "+" : ""}{b.cost_variance_ratio}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        {b.cost_variance_ratio > 20 ? (
                          <span className="flex items-center justify-center gap-1 text-red-400">
                            <AlertTriangle className="w-4 h-4" /> 高风险
                          </span>
                        ) : b.cost_variance_ratio > 10 ? (
                          <span className="flex items-center justify-center gap-1 text-amber-400">
                            <TrendingUp className="w-4 h-4" /> 偏高
                          </span>
                        ) : (
                          <span className="flex items-center justify-center gap-1 text-emerald-400">
                            <CheckCircle className="w-4 h-4" /> 正常
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </motion.div>
        )}

        {/* 劳动力成本 */}
        {activeTab === "labor" && (
          <motion.div variants={fadeIn} className="space-y-4">
            {loading ? (
              <div className="text-center text-slate-500 py-12">加载中...</div>
            ) : laborCosts.length === 0 ? (
              <div className="text-center text-slate-500 py-12 bg-surface-1/50 border border-white/5 rounded-xl">
                暂无劳动力成本数据
              </div>
            ) : (
              <>
                {/* 汇总卡片 */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {laborCosts.map((cost) => (
                    <div
                      key={cost.work_type}
                      className="bg-surface-1/50 border border-white/5 rounded-xl p-4"
                    >
                      <div className="text-xs text-slate-400 mb-2">{cost.work_type_label}</div>
                      <div className="text-xl font-bold text-white">{cost.actual_hours || cost.estimated_hours}h</div>
                      <div className="text-sm text-emerald-400 mt-1">{formatWan(cost.total_cost)}</div>
                    </div>
                  ))}
                </div>

                {/* 详细表格 */}
                <div className="bg-surface-1/50 border border-white/5 rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-800/50">
                      <tr>
                        <th className="text-left text-slate-400 py-3 px-4">工作类型</th>
                        <th className="text-right text-slate-400 py-3 px-4">预估工时</th>
                        <th className="text-right text-slate-400 py-3 px-4">实际工时</th>
                        <th className="text-right text-slate-400 py-3 px-4">时薪</th>
                        <th className="text-right text-slate-400 py-3 px-4">总成本</th>
                        <th className="text-right text-slate-400 py-3 px-4">差异</th>
                      </tr>
                    </thead>
                    <tbody>
                      {laborCosts.map((cost) => {
                        const variance = cost.actual_hours - cost.estimated_hours;
                        return (
                          <tr key={cost.work_type} className="border-t border-white/5">
                            <td className="py-3 px-4 text-slate-300">{cost.work_type_label}</td>
                            <td className="py-3 px-4 text-right text-slate-400">{cost.estimated_hours}h</td>
                            <td className="py-3 px-4 text-right text-white">{cost.actual_hours || "-"}h</td>
                            <td className="py-3 px-4 text-right text-slate-400">¥{cost.hourly_rate}/h</td>
                            <td className="py-3 px-4 text-right text-emerald-400">{formatWan(cost.total_cost)}</td>
                            <td className="py-3 px-4 text-right">
                              <span className={`font-mono ${
                                variance > 0 ? "text-red-400" : variance < 0 ? "text-emerald-400" : "text-slate-400"
                              }`}>
                                {variance > 0 ? "+" : ""}{variance}h
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
