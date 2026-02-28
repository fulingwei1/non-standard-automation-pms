import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, TrendingUp, DollarSign, Lightbulb, BarChart3 } from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer, fadeIn } from "../lib/animations";
import { costVarianceApi } from "../services/api/costVariance";

export default function CostVarianceAnalysis() {
  const [summary, setSummary] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [s, p] = await Promise.all([costVarianceApi.summary(), costVarianceApi.patterns()]);
        setSummary(s.data || s);
        setPatterns(p.data || p);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  const s = summary?.summary || {};
  const projects = summary?.projects || [];
  const byType = patterns?.by_cost_type || [];
  const byCategory = patterns?.by_category || [];
  const insights = patterns?.insights || [];

  const COST_COLORS = {
    material: "bg-blue-500/60", labor: "bg-purple-500/60", equipment: "bg-cyan-500/60",
    outsource: "bg-amber-500/60", travel: "bg-pink-500/60", overhead: "bg-slate-500/60",
  };

  return (
    <div className="space-y-6">
      <PageHeader title="成本偏差分析" subtitle="预算偏差 · 根因定位 · 模式洞察" />
      {loading ? (
        <div className="text-center text-slate-500 py-12">加载中...</div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
          {/* Summary */}
          <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: BarChart3, label: "总项目", value: s.total_projects, color: "text-blue-400" },
              { icon: AlertTriangle, label: "超支项目", value: s.overrun_count, color: "text-red-400" },
              { icon: DollarSign, label: "总超支额", value: `¥${((s.total_overrun_amount||0)/10000).toFixed(0)}万`, color: "text-red-400" },
              { icon: TrendingUp, label: "最大偏差", value: `${s.worst_variance||0}%`, sub: s.worst_project, color: "text-amber-400" },
            ].map((c, i) => (
              <div key={i} className="bg-surface-1/50 border border-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <c.icon className={`w-4 h-4 ${c.color}`} />
                  <span className="text-xs text-slate-400">{c.label}</span>
                </div>
                <div className={`text-2xl font-bold ${c.color}`}>{c.value}</div>
                {c.sub && <div className="text-[10px] text-slate-500 mt-1">{c.sub}</div>}
              </div>
            ))}
          </motion.div>

          {/* Insights */}
          {insights.length > 0 && (
            <motion.div variants={fadeIn} className="bg-surface-1/50 border border-amber-500/20 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="w-4 h-4 text-amber-400" />
                <span className="text-sm font-bold text-amber-400">模式洞察</span>
              </div>
              <div className="space-y-1">
                {insights.map((ins, i) => <div key={i} className="text-xs text-slate-300">{ins}</div>)}
              </div>
            </motion.div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Heatmap table */}
            <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
              <h3 className="text-sm font-bold text-white mb-4">项目偏差热力图</h3>
              <div className="space-y-3">
                {projects.map(p => (
                  <div key={p.project_id}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-300 truncate w-32">{p.project_name}</span>
                      <span className={`text-xs font-mono ${p.variance > 0 ? "text-red-400" : "text-emerald-400"}`}>
                        {p.variance > 0 ? "+" : ""}{p.variance_pct}%
                      </span>
                    </div>
                    <div className="flex gap-1 h-4">
                      {Object.entries(p.cost_breakdown).map(([type, amount]) => {
                        const total = Object.values(p.cost_breakdown).reduce((a, b) => a + b, 0);
                        const pct = total > 0 ? (amount / total) * 100 : 0;
                        return (
                          <div
                            key={type}
                            className={`${COST_COLORS[type] || "bg-slate-500/60"} rounded-sm relative group`}
                            style={{ width: `${pct}%`, minWidth: pct > 0 ? "4px" : "0" }}
                            title={`${type}: ¥${(amount/10000).toFixed(1)}万 (${pct.toFixed(0)}%)`}
                          />
                        );
                      })}
                    </div>
                  </div>
                ))}
                <div className="flex gap-3 mt-3 flex-wrap">
                  {Object.entries(COST_COLORS).map(([type, cls]) => (
                    <div key={type} className="flex items-center gap-1">
                      <div className={`w-3 h-3 rounded-sm ${cls}`} />
                      <span className="text-[10px] text-slate-500">{type}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* By category */}
            <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
              <h3 className="text-sm font-bold text-white mb-4">按类型分析</h3>
              <div className="space-y-4">
                <div>
                  <div className="text-[10px] text-slate-400 mb-2 font-medium">成本类型分布</div>
                  {byType.map(t => (
                    <div key={t.cost_type} className="flex items-center justify-between text-xs py-1.5 border-b border-white/5">
                      <span className="text-slate-300">{t.cost_type}</span>
                      <span className="text-slate-400">{t.project_count}个项目</span>
                      <span className="text-slate-300 font-mono">¥{(t.total_cost/10000).toFixed(1)}万</span>
                    </div>
                  ))}
                </div>
                <div>
                  <div className="text-[10px] text-slate-400 mb-2 font-medium">产品类别偏差</div>
                  {byCategory.map(c => (
                    <div key={c.category} className="flex items-center justify-between text-xs py-1.5 border-b border-white/5">
                      <span className="text-slate-300">{c.category}</span>
                      <span className="text-slate-400">{c.count}个</span>
                      <span className={`font-mono ${c.avg_variance_pct > 0 ? "text-red-400" : "text-emerald-400"}`}>
                        {c.avg_variance_pct > 0 ? "+" : ""}{c.avg_variance_pct}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
