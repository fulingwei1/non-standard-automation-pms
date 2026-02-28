import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ArrowLeftRight, TrendingUp, TrendingDown, DollarSign, BarChart3, AlertTriangle } from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer, fadeIn } from "../lib/animations";
import { quoteCompareApi } from "../services/api/quoteCompare";

export default function QuoteActualCompare() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await quoteCompareApi.list();
        setData(res.data || res);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  const s = data?.summary || {};
  const projects = data?.projects || [];

  return (
    <div className="space-y-6">
      <PageHeader title="报价对比" subtitle="报价预算 vs 实际成本" />
      {loading ? (
        <div className="text-center text-slate-500 py-12">加载中...</div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
          <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: BarChart3, label: "项目数", value: s.total_projects, color: "text-blue-400" },
              { icon: TrendingUp, label: "计划毛利", value: `${s.overall_planned_margin}%`, color: "text-blue-400" },
              { icon: DollarSign, label: "实际毛利", value: `${s.overall_actual_margin}%`,
                color: s.overall_actual_margin > s.overall_planned_margin ? "text-emerald-400" : "text-amber-400" },
              { icon: AlertTriangle, label: "超支项目", value: s.overrun_count, color: "text-red-400" },
            ].map((c, i) => (
              <div key={i} className="bg-surface-1/50 border border-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <c.icon className={`w-4 h-4 ${c.color}`} />
                  <span className="text-xs text-slate-400">{c.label}</span>
                </div>
                <div className={`text-2xl font-bold ${c.color}`}>{c.value}</div>
              </div>
            ))}
          </motion.div>

          <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <ArrowLeftRight className="w-4 h-4 text-blue-400" /> 项目对比明细
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10">
                    {["项目","合同额","预算","实际成本","计划毛利","实际毛利","偏差","状态"].map(h => (
                      <th key={h} className="text-left text-slate-400 py-2 px-2">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {projects.map(p => (
                    <tr key={p.project_id} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="py-2.5 px-2">
                        <div className="text-slate-300">{p.project_name}</div>
                        <div className="text-[10px] text-slate-500">{p.product_category}</div>
                      </td>
                      <td className="py-2 px-2 text-slate-400">¥{(p.contract_amount/10000).toFixed(0)}万</td>
                      <td className="py-2 px-2 text-slate-400">¥{(p.budget_amount/10000).toFixed(0)}万</td>
                      <td className="py-2 px-2 text-slate-300 font-mono">¥{(p.actual_cost/10000).toFixed(1)}万</td>
                      <td className="py-2 px-2 text-blue-400">{p.planned_margin}%</td>
                      <td className={`py-2 px-2 font-mono ${p.actual_margin > 25 ? "text-emerald-400" : p.actual_margin > 15 ? "text-amber-400" : "text-red-400"}`}>
                        {p.actual_margin}%
                      </td>
                      <td className={`py-2 px-2 font-mono ${p.margin_gap >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {p.margin_gap > 0 ? "+" : ""}{p.margin_gap}%
                      </td>
                      <td className="py-2 px-2">
                        {p.overrun ? (
                          <span className="text-red-400 flex items-center gap-1"><TrendingDown className="w-3 h-3" />超支</span>
                        ) : (
                          <span className="text-emerald-400 flex items-center gap-1"><TrendingUp className="w-3 h-3" />节余</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Cost breakdown per project */}
          <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
            <h3 className="text-sm font-bold text-white mb-4">成本结构对比</h3>
            <div className="space-y-4">
              {projects.filter(p => Object.keys(p.cost_breakdown || {}).length > 0).map(p => (
                <div key={p.project_id} className="border-b border-white/5 pb-3 last:border-0">
                  <div className="text-xs text-slate-300 mb-2 font-medium">{p.project_name}</div>
                  <div className="flex gap-2 flex-wrap">
                    {Object.entries(p.cost_breakdown).map(([type, amount]) => (
                      <div key={type} className="bg-slate-800 rounded-lg px-3 py-1.5 text-[10px]">
                        <span className="text-slate-400">{type}</span>
                        <span className="text-slate-300 ml-2 font-mono">¥{(amount/10000).toFixed(1)}万</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
