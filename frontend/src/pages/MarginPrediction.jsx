/**
 * 毛利率预测与分析
 * - 历史毛利率统计（按类型/金额区间）
 * - 新项目毛利率预测（输入参数→AI预测）
 * - 报价vs实际偏差分析
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  Calculator,
  AlertTriangle,
  BarChart3,
  DollarSign,
  Target,
  Percent,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Zap,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer, fadeIn } from "../lib/animations";
import { marginPredictionApi } from "../services/api/marginPrediction";

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

function MarginBar({ label, value, max = 50 }) {
  const pct = Math.min(100, (Math.abs(value) / max) * 100);
  const isNeg = value < 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-slate-400 w-20 text-right">{label}</span>
      <div className="flex-1 h-5 bg-slate-800 rounded-full overflow-hidden relative">
        <div
          className={`h-full rounded-full transition-all ${
            isNeg ? "bg-red-500/60" : value > 25 ? "bg-emerald-500/60" : "bg-amber-500/60"
          }`}
          style={{ width: `${pct}%` }}
        />
        <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono text-white">
          {value.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}

export default function MarginPrediction() {
  const [historical, setHistorical] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [variance, setVariance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);

  // Prediction form
  const [form, setForm] = useState({
    product_category: "",
    industry: "",
    contract_amount: 3000000,
  });

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const [h, v] = await Promise.all([
          marginPredictionApi.historical(),
          marginPredictionApi.variance(),
        ]);
        setHistorical(h.data || h);
        setVariance(v.data || v);
      } catch (err) {
        console.error("Failed to load margin data:", err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handlePredict = useCallback(async () => {
    try {
      setPredicting(true);
      const params = { contract_amount: form.contract_amount };
      if (form.product_category) params.product_category = form.product_category;
      if (form.industry) params.industry = form.industry;
      const res = await marginPredictionApi.predict(params);
      setPrediction(res.data || res);
    } catch (err) {
      console.error("Prediction failed:", err);
    } finally {
      setPredicting(false);
    }
  }, [form]);

  const summary = historical?.historical_summary || {};
  const categories = historical?.by_category || [];
  const projects = historical?.projects || [];
  const varianceData = variance?.projects || [];
  const pred = prediction?.prediction;

  return (
    <div className="space-y-6">
      <PageHeader title="毛利率预测" subtitle="历史分析 · AI预测 · 偏差对比" />

      {loading ? (
        <div className="text-center text-slate-500 py-12">加载中...</div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
          {/* Summary Stats */}
          <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <StatCard icon={BarChart3} label="历史项目" value={summary.total_projects || 0} color="text-blue-400" />
            <StatCard icon={Percent} label="平均毛利率" value={`${summary.avg_margin || 0}%`}
              color={summary.avg_margin > 25 ? "text-emerald-400" : "text-amber-400"} />
            <StatCard icon={TrendingUp} label="最高毛利" value={`${summary.max_margin || 0}%`} color="text-emerald-400" />
            <StatCard icon={AlertTriangle} label="最低毛利" value={`${summary.min_margin || 0}%`} color="text-red-400" />
            <StatCard icon={DollarSign} label="总合同额"
              value={`¥${((summary.total_contract_value || 0) / 10000).toFixed(0)}万`} color="text-purple-400" />
          </motion.div>

          {/* Two columns: History + Prediction */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Historical by category */}
            <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
              <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-400" /> 按设备类型分析
              </h3>
              <div className="space-y-3">
                {categories.map((cat) => (
                  <div key={cat.category} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-300">{cat.category}</span>
                      <span className="text-xs text-slate-500">{cat.count}个项目</span>
                    </div>
                    <MarginBar label="平均" value={cat.avg_margin} />
                    <div className="flex gap-4 text-[10px] text-slate-500 pl-24">
                      <span>最低 {cat.min_margin}%</span>
                      <span>最高 {cat.max_margin}%</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Per-project margins */}
              <h4 className="text-xs font-bold text-slate-400 mt-6 mb-3">各项目毛利率</h4>
              <div className="space-y-2">
                {projects.map((p) => (
                  <div key={p.project_id} className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 w-28 truncate">{p.project_name}</span>
                    <div className="flex-1">
                      <MarginBar label={p.product_category || "-"} value={p.gross_margin} />
                    </div>
                    <span className={`text-xs font-mono w-16 text-right ${
                      p.gross_margin > 25 ? "text-emerald-400" : p.gross_margin > 15 ? "text-amber-400" : "text-red-400"
                    }`}>
                      ¥{(p.contract_amount / 10000).toFixed(0)}万
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Right: Prediction */}
            <motion.div variants={fadeIn} className="space-y-5">
              {/* Prediction Form */}
              <div className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
                <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                  <Calculator className="w-4 h-4 text-purple-400" /> 毛利率预测
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">设备类型</label>
                    <select
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                      value={form.product_category}
                      onChange={(e) => setForm({ ...form, product_category: e.target.value })}
                    >
                      <option value="">不限</option>
                      <option value="ICT">ICT 在线测试</option>
                      <option value="FCT">FCT 功能测试</option>
                      <option value="EOL">EOL 终检设备</option>
                      <option value="aging">老化测试</option>
                      <option value="vision">视觉检测</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">预估合同金额 (万元)</label>
                    <input
                      type="number"
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                      value={form.contract_amount / 10000}
                      onChange={(e) => setForm({ ...form, contract_amount: (parseFloat(e.target.value) || 0) * 10000 })}
                    />
                  </div>
                  <button
                    onClick={handlePredict}
                    disabled={predicting}
                    className="w-full py-2.5 bg-purple-600 hover:bg-purple-500 disabled:bg-slate-700 
                      text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    <Zap className="w-4 h-4" />
                    {predicting ? "预测中..." : "开始预测"}
                  </button>
                </div>
              </div>

              {/* Prediction Result */}
              {pred && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-surface-1/50 border border-white/5 rounded-xl p-5"
                >
                  <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                    <Target className="w-4 h-4 text-emerald-400" /> 预测结果
                  </h3>
                  
                  {/* Main prediction */}
                  <div className="text-center py-4">
                    <div className={`text-4xl font-bold ${
                      pred.predicted_margin > 25 ? "text-emerald-400" :
                      pred.predicted_margin > 15 ? "text-amber-400" : "text-red-400"
                    }`}>
                      {pred.predicted_margin}%
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      预测毛利率 (置信度 {(pred.confidence * 100).toFixed(0)}%)
                    </div>
                    <div className="text-xs text-slate-600 mt-1">
                      区间: {pred.margin_range[0]}% ~ {pred.margin_range[1]}%
                    </div>
                  </div>

                  {/* Key numbers */}
                  <div className="grid grid-cols-3 gap-3 mt-3">
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-400">
                        ¥{(pred.predicted_cost / 10000).toFixed(0)}万
                      </div>
                      <div className="text-[10px] text-slate-500">预测成本</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-emerald-400">
                        ¥{(pred.predicted_profit / 10000).toFixed(0)}万
                      </div>
                      <div className="text-[10px] text-slate-500">预测利润</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-lg font-bold ${
                        pred.risk_level === "low" ? "text-emerald-400" :
                        pred.risk_level === "medium" ? "text-amber-400" : "text-red-400"
                      }`}>
                        {pred.risk_level === "low" ? "低" : pred.risk_level === "medium" ? "中" : "高"}
                      </div>
                      <div className="text-[10px] text-slate-500">风险等级</div>
                    </div>
                  </div>

                  {/* Recommendations */}
                  {prediction?.recommendations?.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-white/5">
                      <div className="text-[10px] text-slate-400 font-medium mb-2">建议</div>
                      {prediction.recommendations.map((r, i) => (
                        <div key={i} className="text-xs text-slate-300 mb-1">{r}</div>
                      ))}
                    </div>
                  )}

                  {/* Similar projects */}
                  {prediction?.similar_projects?.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-white/5">
                      <div className="text-[10px] text-slate-400 font-medium mb-2">参考项目</div>
                      {prediction.similar_projects.map((p, i) => (
                        <div key={i} className="flex items-center justify-between text-xs py-1">
                          <span className="text-slate-300 truncate w-32">{p.project_name}</span>
                          <span className="text-slate-500">¥{(p.contract_amount / 10000).toFixed(0)}万</span>
                          <span className={`font-mono ${
                            p.gross_margin > 25 ? "text-emerald-400" : "text-amber-400"
                          }`}>
                            {p.gross_margin}%
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}
            </motion.div>
          </div>

          {/* Variance Analysis */}
          <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <ArrowUpRight className="w-4 h-4 text-amber-400" /> 报价 vs 实际偏差分析
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left text-slate-400 py-2 px-2">项目</th>
                    <th className="text-right text-slate-400 py-2 px-2">合同额</th>
                    <th className="text-right text-slate-400 py-2 px-2">预算</th>
                    <th className="text-right text-slate-400 py-2 px-2">实际成本</th>
                    <th className="text-right text-slate-400 py-2 px-2">计划毛利</th>
                    <th className="text-right text-slate-400 py-2 px-2">实际毛利</th>
                    <th className="text-right text-slate-400 py-2 px-2">偏差</th>
                    <th className="text-center text-slate-400 py-2 px-2">状态</th>
                  </tr>
                </thead>
                <tbody>
                  {varianceData.map((p) => (
                    <tr key={p.project_id} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="py-2 px-2 text-slate-300">{p.project_name}</td>
                      <td className="py-2 px-2 text-right text-slate-400">¥{(p.contract_amount / 10000).toFixed(0)}万</td>
                      <td className="py-2 px-2 text-right text-slate-400">¥{(p.budget_amount / 10000).toFixed(0)}万</td>
                      <td className="py-2 px-2 text-right text-slate-300">¥{(p.actual_cost / 10000).toFixed(0)}万</td>
                      <td className="py-2 px-2 text-right text-blue-400">{p.planned_margin}%</td>
                      <td className={`py-2 px-2 text-right font-mono ${
                        p.actual_margin > 25 ? "text-emerald-400" : p.actual_margin > 15 ? "text-amber-400" : "text-red-400"
                      }`}>
                        {p.actual_margin}%
                      </td>
                      <td className={`py-2 px-2 text-right font-mono ${
                        p.margin_gap >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}>
                        {p.margin_gap > 0 ? "+" : ""}{p.margin_gap}%
                      </td>
                      <td className="py-2 px-2 text-center">
                        {p.overrun ? (
                          <span className="text-red-400 flex items-center justify-center gap-1">
                            <ArrowDownRight className="w-3 h-3" /> 超支
                          </span>
                        ) : (
                          <span className="text-emerald-400 flex items-center justify-center gap-1">
                            <ArrowUpRight className="w-3 h-3" /> 节余
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
