/**
 * 成本归集自动化
 * - 采购订单→材料成本自动归集
 * - 工单→人工/外协成本自动归集
 * - 归集状态、按项目汇总
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ArrowDownToLine,
  Package,
  Wrench,
  CheckCircle2,
  Clock,
  RefreshCw,
  DollarSign,
  FolderOpen,
  Zap,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer, fadeIn } from "../lib/animations";
import { costCollectionApi } from "../services/api/costCollection";

function StatusCard({ icon: Icon, label, collected, pending, total, color }) {
  return (
    <div className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <span className="text-sm font-medium text-white">{label}</span>
      </div>
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <div className="text-xl font-bold text-slate-300">{total}</div>
          <div className="text-[10px] text-slate-500">总单据</div>
        </div>
        <div>
          <div className="text-xl font-bold text-emerald-400">{collected}</div>
          <div className="text-[10px] text-slate-500">已归集</div>
        </div>
        <div>
          <div className="text-xl font-bold text-amber-400">{pending}</div>
          <div className="text-[10px] text-slate-500">待归集</div>
        </div>
      </div>
      {total > 0 && (
        <div className="mt-3">
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500/60 rounded-full transition-all"
              style={{ width: `${(collected / total) * 100}%` }}
            />
          </div>
          <div className="text-[10px] text-slate-500 mt-1 text-right">
            {total > 0 ? ((collected / total) * 100).toFixed(0) : 0}% 已归集
          </div>
        </div>
      )}
    </div>
  );
}

export default function CostCollection() {
  const [status, setStatus] = useState(null);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [result, setResult] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [s, p] = await Promise.all([
        costCollectionApi.status(),
        costCollectionApi.byProject(),
      ]);
      setStatus(s.data || s);
      setProjects((p.data || p).projects || []);
    } catch (err) {
      console.error("Load failed:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleCollect = useCallback(async () => {
    try {
      setCollecting(true);
      setResult(null);
      const res = await costCollectionApi.collect({});
      setResult(res.data || res);
      await loadData(); // Refresh
    } catch (err) {
      console.error("Collection failed:", err);
      setResult({ error: err.message });
    } finally {
      setCollecting(false);
    }
  }, [loadData]);

  const po = status?.purchase_orders || {};
  const wo = status?.work_orders || {};
  const recent = status?.recent_collections || [];

  return (
    <div className="space-y-6">
      <PageHeader title="成本归集" subtitle="自动归集采购订单和工单成本到项目" />

      {loading ? (
        <div className="text-center text-slate-500 py-12">加载中...</div>
      ) : (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
          {/* Action Bar */}
          <motion.div variants={fadeIn} className="flex items-center gap-4">
            <button
              onClick={handleCollect}
              disabled={collecting}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700
                text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
            >
              {collecting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {collecting ? "归集中..." : "执行归集"}
            </button>
            <span className="text-xs text-slate-500">
              待归集: {(po.pending || 0) + (wo.pending || 0)} 条
            </span>
          </motion.div>

          {/* Collection Result */}
          {result && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-xl border ${
                result.error
                  ? "bg-red-900/20 border-red-500/20 text-red-400"
                  : "bg-emerald-900/20 border-emerald-500/20 text-emerald-400"
              }`}
            >
              {result.error ? (
                <span>❌ 归集失败: {result.error}</span>
              ) : (
                <div className="flex items-center gap-3">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">{result.message}</span>
                </div>
              )}
            </motion.div>
          )}

          {/* Status Cards */}
          <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <StatusCard
              icon={Package}
              label="采购订单 → 材料成本"
              collected={po.collected || 0}
              pending={po.pending || 0}
              total={po.total || 0}
              color="bg-blue-600/30"
            />
            <StatusCard
              icon={Wrench}
              label="工单 → 人工/外协成本"
              collected={wo.collected || 0}
              pending={wo.pending || 0}
              total={wo.total || 0}
              color="bg-purple-600/30"
            />
          </motion.div>

          {/* By Project */}
          <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-blue-400" /> 按项目汇总
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left text-slate-400 py-2 px-2">项目</th>
                    <th className="text-right text-slate-400 py-2 px-2">合同额</th>
                    <th className="text-right text-slate-400 py-2 px-2">总成本</th>
                    <th className="text-right text-slate-400 py-2 px-2">采购归集</th>
                    <th className="text-right text-slate-400 py-2 px-2">工单归集</th>
                    <th className="text-right text-slate-400 py-2 px-2">手工录入</th>
                    <th className="text-right text-slate-400 py-2 px-2">毛利率</th>
                    <th className="text-right text-slate-400 py-2 px-2">记录数</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.project_id} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="py-2.5 px-2">
                        <div className="text-slate-300">{p.project_name}</div>
                        <div className="text-[10px] text-slate-500">{p.project_code}</div>
                      </td>
                      <td className="py-2 px-2 text-right text-slate-400">
                        ¥{(p.contract_amount / 10000).toFixed(0)}万
                      </td>
                      <td className="py-2 px-2 text-right text-slate-300 font-mono">
                        ¥{(p.total_cost / 10000).toFixed(1)}万
                      </td>
                      <td className="py-2 px-2 text-right text-blue-400 font-mono">
                        {p.po_cost > 0 ? `¥${(p.po_cost / 10000).toFixed(1)}万` : "-"}
                      </td>
                      <td className="py-2 px-2 text-right text-purple-400 font-mono">
                        {p.wo_cost > 0 ? `¥${(p.wo_cost / 10000).toFixed(1)}万` : "-"}
                      </td>
                      <td className="py-2 px-2 text-right text-slate-500 font-mono">
                        {p.manual_cost > 0 ? `¥${(p.manual_cost / 10000).toFixed(1)}万` : "-"}
                      </td>
                      <td className={`py-2 px-2 text-right font-mono ${
                        p.margin > 25 ? "text-emerald-400" : p.margin > 15 ? "text-amber-400" : "text-red-400"
                      }`}>
                        {p.margin}%
                      </td>
                      <td className="py-2 px-2 text-right text-slate-500">{p.cost_records}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>

          {/* Recent Collections */}
          {recent.length > 0 && (
            <motion.div variants={fadeIn} className="bg-surface-1/50 border border-white/5 rounded-xl p-5">
              <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-400" /> 最近归集记录
              </h3>
              <div className="space-y-2">
                {recent.map((r, i) => (
                  <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-white/5 last:border-0">
                    <div className="flex items-center gap-2">
                      {r.source_type === "purchase_order" ? (
                        <Package className="w-3 h-3 text-blue-400" />
                      ) : (
                        <Wrench className="w-3 h-3 text-purple-400" />
                      )}
                      <span className="text-slate-300">{r.source_no}</span>
                      <span className="text-slate-500">→</span>
                      <span className="text-slate-400">{r.project_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-slate-500">{r.cost_type}</span>
                      <span className="text-emerald-400 font-mono">¥{r.amount.toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </motion.div>
      )}
    </div>
  );
}
