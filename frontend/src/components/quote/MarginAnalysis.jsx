/**
 * 毛利分析组件
 * 整合自毛利率预测页面，嵌入报价管理模块
 *
 * 功能：
 * - 历史毛利率统计（按类型/金额区间）
 * - 新项目毛利率预测（AI预测）
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
  Zap,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { fadeIn } from "../../lib/animations";
import { marginPredictionApi } from "../../services/api/marginPrediction";

const ALL_PRODUCT_CATEGORIES = "__all__";

// 统计卡片组件
// 统计卡片组件
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

// 毛利率条形图组件
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

export default function MarginAnalysis() {
  const [historical, setHistorical] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [variance, setVariance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [importingBom, setImportingBom] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState("");

  // 预测表单
  const [form, setForm] = useState({
    product_category: "",
    industry: "",
    contract_amount: 3000000,
    estimated_material_cost: "",
    estimated_design_change_cost: "",
    estimated_travel_cost: "",
    estimated_rd_hours: "",
    project_complexity: "MEDIUM",
  });

  // 导入 BOM 成本
  const handleImportBom = async () => {
    if (!selectedProjectId) {
      alert("请选择项目");
      return;
    }
    setImportingBom(true);
    try {
      const res = await marginPredictionApi.getBomCosts(selectedProjectId);
      const data = res.data || res;
      if (data.total_cost > 0) {
        setForm((prev) => ({ ...prev, estimated_material_cost: data.total_cost }));
        alert(
          `已导入 BOM 物料成本：¥${(data.total_cost / 10000).toFixed(2)}万\n` +
          `共${data.total_items}项物料\n` +
          `已采购：${data.purchased_count}项\n` +
          `未采购：${data.unpurchased_count}项`
        );
      } else {
        alert(data.message || "未找到 BOM 数据");
      }
    } catch (error) {
      alert("导入失败：" + error.message);
    } finally {
      setImportingBom(false);
    }
  };

  // 加载历史数据
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

  // 执行预测
  const handlePredict = useCallback(async () => {
    try {
      setPredicting(true);
      const params = {
        contract_amount: form.contract_amount,
        project_complexity: form.project_complexity,
      };
      if (form.product_category) params.product_category = form.product_category;
      if (form.estimated_material_cost) params.estimated_material_cost = form.estimated_material_cost;
      if (form.estimated_design_change_cost) params.estimated_design_change_cost = form.estimated_design_change_cost;
      if (form.estimated_travel_cost) params.estimated_travel_cost = form.estimated_travel_cost;
      if (form.estimated_rd_hours) params.estimated_rd_hours = form.estimated_rd_hours;
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

  if (loading) {
    return <div className="text-center text-slate-500 py-12">加载中...</div>;
  }

  return (
    <motion.div variants={fadeIn} className="space-y-6">
      {/* 汇总统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard icon={BarChart3} label="历史项目" value={summary.total_projects || 0} color="text-blue-400" />
        <StatCard
          icon={Percent}
          label="平均毛利率"
          value={`${summary.avg_margin || 0}%`}
          color={summary.avg_margin > 25 ? "text-emerald-400" : "text-amber-400"}
        />
        <StatCard icon={TrendingUp} label="最高毛利" value={`${summary.max_margin || 0}%`} color="text-emerald-400" />
        <StatCard icon={AlertTriangle} label="最低毛利" value={`${summary.min_margin || 0}%`} color="text-red-400" />
        <StatCard
          icon={DollarSign}
          label="总合同额"
          value={`¥${((summary.total_contract_value || 0) / 10000).toFixed(0)}万`}
          color="text-purple-400"
        />
      </div>

      {/* 两栏布局：历史分析 + 预测 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：按类型历史分析 */}
        <Card className="bg-slate-900/60 border-slate-800 text-white">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" /> 按设备类型分析
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
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

            {/* 各项目毛利率 */}
            <div className="pt-4 border-t border-slate-800">
              <h4 className="text-xs font-bold text-slate-400 mb-3">各项目毛利率</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {projects.map((p) => (
                  <div key={p.project_id} className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 w-28 truncate">{p.project_name}</span>
                    <div className="flex-1">
                      <MarginBar label={p.product_category || "-"} value={p.gross_margin} />
                    </div>
                    <span
                      className={`text-xs font-mono w-16 text-right ${
                        p.gross_margin > 25 ? "text-emerald-400" : p.gross_margin > 15 ? "text-amber-400" : "text-red-400"
                      }`}
                    >
                      ¥{(p.contract_amount / 10000).toFixed(0)}万
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 右侧：毛利率预测 */}
        <div className="space-y-5">
          {/* 预测表单 */}
          <Card className="bg-slate-900/60 border-slate-800 text-white">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Calculator className="w-4 h-4 text-purple-400" /> 毛利率预测
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-xs text-slate-400 mb-1 block">设备类型</label>
                <Select
                  value={form.product_category || ALL_PRODUCT_CATEGORIES}
                  onValueChange={(value) =>
                    setForm({
                      ...form,
                      product_category: value === ALL_PRODUCT_CATEGORIES ? "" : value,
                    })
                  }
                >
                  <SelectTrigger className="bg-slate-800 border-white/10">
                    <SelectValue placeholder="不限" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-900 border-slate-700 text-white">
                    <SelectItem value={ALL_PRODUCT_CATEGORIES}>不限</SelectItem>
                    <SelectItem value="ICT">ICT 在线测试</SelectItem>
                    <SelectItem value="FCT">FCT 功能测试</SelectItem>
                    <SelectItem value="EOL">EOL 终检设备</SelectItem>
                    <SelectItem value="aging">老化测试</SelectItem>
                    <SelectItem value="vision">视觉检测</SelectItem>
                  </SelectContent>
                </Select>
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

              {/* BOM 导入 */}
              <div className="border-t border-white/10 pt-4">
                <div className="flex items-center gap-2 mb-3">
                  <Target className="w-4 h-4 text-purple-400" />
                  <span className="text-xs text-slate-400">从 BOM 导入物料成本</span>
                </div>
                <div className="flex gap-2">
                  <select
                    className="flex-1 bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-slate-300"
                    value={selectedProjectId}
                    onChange={(e) => setSelectedProjectId(e.target.value)}
                  >
                    <option value="">选择项目...</option>
                    <option value="1">项目 A - ICT 测试设备</option>
                    <option value="2">项目 B - FCT 测试线</option>
                    <option value="3">项目 C - EOL 检测设备</option>
                  </select>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleImportBom}
                    disabled={importingBom || !selectedProjectId}
                  >
                    <RefreshCw className={`w-4 h-4 mr-1 ${importingBom ? "animate-spin" : ""}`} />
                    {importingBom ? "导入中" : "导入"}
                  </Button>
                </div>
              </div>

              <Button onClick={handlePredict} disabled={predicting} className="w-full bg-purple-600 hover:bg-purple-500">
                <Zap className="w-4 h-4 mr-2" />
                {predicting ? "预测中..." : "开始预测"}
              </Button>
            </CardContent>
          </Card>

          {/* 预测结果 */}
          {pred && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <Card className="bg-slate-900/60 border-slate-800 text-white">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Target className="w-4 h-4 text-emerald-400" /> 预测结果
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {/* 主预测值 */}
                  <div className="text-center py-4">
                    <div
                      className={`text-4xl font-bold ${
                        pred.predicted_margin > 25
                          ? "text-emerald-400"
                          : pred.predicted_margin > 15
                          ? "text-amber-400"
                          : "text-red-400"
                      }`}
                    >
                      {pred.predicted_margin}%
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      预测毛利率 (置信度 {(pred.confidence * 100).toFixed(0)}%)
                    </div>
                    <div className="text-xs text-slate-600 mt-1">
                      区间: {pred.margin_range[0]}% ~ {pred.margin_range[1]}%
                    </div>
                  </div>

                  {/* 关键数字 */}
                  <div className="grid grid-cols-3 gap-3 mt-3">
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-400">¥{(pred.predicted_cost / 10000).toFixed(0)}万</div>
                      <div className="text-[10px] text-slate-500">预测成本</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-emerald-400">
                        ¥{(pred.predicted_profit / 10000).toFixed(0)}万
                      </div>
                      <div className="text-[10px] text-slate-500">预测利润</div>
                    </div>
                    <div className="text-center">
                      <div
                        className={`text-lg font-bold ${
                          pred.risk_level === "low"
                            ? "text-emerald-400"
                            : pred.risk_level === "medium"
                            ? "text-amber-400"
                            : "text-red-400"
                        }`}
                      >
                        {pred.risk_level === "low" ? "低" : pred.risk_level === "medium" ? "中" : "高"}
                      </div>
                      <div className="text-[10px] text-slate-500">风险等级</div>
                    </div>
                  </div>

                  {/* 建议 */}
                  {prediction?.recommendations?.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-white/5">
                      <div className="text-[10px] text-slate-400 font-medium mb-2">建议</div>
                      {prediction.recommendations.map((r, i) => (
                        <div key={i} className="text-xs text-slate-300 mb-1">
                          {r}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 参考项目 */}
                  {prediction?.similar_projects?.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-white/5">
                      <div className="text-[10px] text-slate-400 font-medium mb-2">参考项目</div>
                      {prediction.similar_projects.map((p, i) => (
                        <div key={i} className="flex items-center justify-between text-xs py-1">
                          <span className="text-slate-300 truncate w-32">{p.project_name}</span>
                          <span className="text-slate-500">¥{(p.contract_amount / 10000).toFixed(0)}万</span>
                          <span className={`font-mono ${p.gross_margin > 25 ? "text-emerald-400" : "text-amber-400"}`}>
                            {p.gross_margin}%
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </div>

      {/* 偏差分析表 */}
      <Card className="bg-slate-900/60 border-slate-800 text-white">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <ArrowUpRight className="w-4 h-4 text-amber-400" /> 报价 vs 实际偏差分析
          </CardTitle>
        </CardHeader>
        <CardContent>
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
                    <td
                      className={`py-2 px-2 text-right font-mono ${
                        p.actual_margin > 25 ? "text-emerald-400" : p.actual_margin > 15 ? "text-amber-400" : "text-red-400"
                      }`}
                    >
                      {p.actual_margin}%
                    </td>
                    <td className={`py-2 px-2 text-right font-mono ${p.margin_gap >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {p.margin_gap > 0 ? "+" : ""}
                      {p.margin_gap}%
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
        </CardContent>
      </Card>
    </motion.div>
  );
}
