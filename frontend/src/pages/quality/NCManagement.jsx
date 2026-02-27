/**
 * 不合格品管理
 * 调用 /production/quality/defect-analysis, /production/quality/rework, /production/quality/corrective-action
 */
import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  XCircle, Search, ChevronLeft, ChevronRight, RefreshCw,
  Plus, AlertTriangle, Clock, CheckCircle, Wrench, FileText,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { qualityApi } from "../../services/api/quality";

const TABS = [
  { key: "defect", label: "不良品分析", icon: AlertTriangle },
  { key: "rework", label: "返工管理", icon: Wrench },
];

const REWORK_STATUS_OPTIONS = [
  { value: "", label: "全部状态" },
  { value: "pending", label: "待返工" },
  { value: "in_progress", label: "返工中" },
  { value: "completed", label: "已完成" },
];

function StatusBadge({ status }) {
  const map = {
    pending: { bg: "bg-blue-500/20", text: "text-blue-400", label: "待处理" },
    in_progress: { bg: "bg-amber-500/20", text: "text-amber-400", label: "进行中" },
    completed: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "已完成" },
    open: { bg: "bg-red-500/20", text: "text-red-400", label: "开放" },
    closed: { bg: "bg-gray-500/20", text: "text-gray-400", label: "已关闭" },
  };
  const cfg = map[status] || { bg: "bg-gray-500/20", text: "text-gray-400", label: status || "-" };
  return <span className={`px-2 py-0.5 rounded text-xs ${cfg.bg} ${cfg.text}`}>{cfg.label}</span>;
}

// 不良品分析Tab
function DefectAnalysisTab() {
  const [analyses, setAnalyses] = useState([]);
  const [_loading, _setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    inspection_id: "",
    defect_type: "",
    defect_description: "",
    root_cause_category: "Man",
    root_cause_detail: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const inputCls = "w-full px-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-violet-500";

  // No list API for defect analysis, show form-driven view
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        inspection_id: parseInt(form.inspection_id),
        defect_type: form.defect_type,
        defect_description: form.defect_description,
        root_cause_category: form.root_cause_category,
        root_cause_detail: form.root_cause_detail,
      };
      const res = await qualityApi.defectAnalysis.create(payload);
      const newItem = res.data || res;
      setAnalyses((prev) => [newItem, ...prev]);
      setShowForm(false);
      setForm({ inspection_id: "", defect_type: "", defect_description: "", root_cause_category: "Man", root_cause_detail: "" });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "创建失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-text-muted">基于5M1E方法进行不良品根因分析</p>
        <Button onClick={() => setShowForm(!showForm)} className="gap-2">
          <Plus className="h-4 w-4" /> 新建分析
        </Button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-400 text-sm">{error}</div>
      )}

      {showForm && (
        <motion.form
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={handleSubmit}
          className="bg-surface-300 rounded-xl p-4 space-y-4 border border-white/5"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-text-muted mb-1 block">质检记录ID *</label>
              <input type="number" required value={form.inspection_id} onChange={(e) => setForm({ ...form, inspection_id: e.target.value })} className={inputCls} placeholder="关联的质检记录ID" />
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">不良类型 *</label>
              <input type="text" required value={form.defect_type} onChange={(e) => setForm({ ...form, defect_type: e.target.value })} className={inputCls} placeholder="如：尺寸超差、外观缺陷" />
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">根因分类 (5M1E)</label>
              <select value={form.root_cause_category} onChange={(e) => setForm({ ...form, root_cause_category: e.target.value })} className={inputCls}>
                <option value="Man">人 (Man)</option>
                <option value="Machine">机 (Machine)</option>
                <option value="Material">料 (Material)</option>
                <option value="Method">法 (Method)</option>
                <option value="Measurement">测 (Measurement)</option>
                <option value="Environment">环 (Environment)</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-text-muted mb-1 block">根因详情</label>
              <input type="text" value={form.root_cause_detail} onChange={(e) => setForm({ ...form, root_cause_detail: e.target.value })} className={inputCls} placeholder="具体原因描述" />
            </div>
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">不良描述</label>
            <textarea rows={2} value={form.defect_description} onChange={(e) => setForm({ ...form, defect_description: e.target.value })} className={inputCls} placeholder="详细描述不良现象" />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" type="button" onClick={() => setShowForm(false)}>取消</Button>
            <Button type="submit" disabled={submitting}>{submitting ? "提交中..." : "提交分析"}</Button>
          </div>
        </motion.form>
      )}

      {analyses.length > 0 ? (
        <div className="space-y-3">
          {analyses.map((a) => (
            <div key={a.id} className="p-4 rounded-lg bg-surface-300 border border-white/5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-text-primary">分析 #{a.id}</span>
                <span className="text-xs text-text-muted">{a.created_at ? new Date(a.created_at).toLocaleString() : ""}</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div><span className="text-text-muted">不良类型：</span><span className="text-text-primary">{a.defect_type}</span></div>
                <div><span className="text-text-muted">根因分类：</span><span className="text-text-primary">{a.root_cause_category}</span></div>
                <div className="col-span-2"><span className="text-text-muted">描述：</span><span className="text-text-primary">{a.defect_description}</span></div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        !showForm && <div className="text-center py-12 text-text-muted">暂无不良品分析记录，点击「新建分析」开始</div>
      )}
    </div>
  );
}

// 返工管理Tab
function ReworkTab() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState({ items: [], total: 0 });
  const [_loading, _setLoading] = useState(true);
  const [error, setError] = useState(null);

  const page = parseInt(searchParams.get("rw_page") || "1", 10);
  const pageSize = 20;
  const status = searchParams.get("rw_status") || "";

  const fetchData = useCallback(async () => {
    _setLoading(true);
    setError(null);
    try {
      const params = { skip: (page - 1) * pageSize, limit: pageSize };
      if (status) params.status = status;
      const res = await qualityApi.rework.list(params);
      const resData = res.data || res;
      setData({ items: resData.items || [], total: resData.total || 0 });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "加载失败");
    } finally {
      _setLoading(false);
    }
  }, [page, status]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={status}
          onChange={(e) => {
            const p = new URLSearchParams(searchParams);
            if (e.target.value) p.set("rw_status", e.target.value);
            else p.delete("rw_status");
            p.set("rw_page", "1");
            setSearchParams(p);
          }}
          className="px-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-violet-500"
        >
          {REWORK_STATUS_OPTIONS.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
        <Button variant="ghost" size="sm" onClick={fetchData} className="gap-1">
          <RefreshCw className="h-4 w-4" /> 刷新
        </Button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-400 text-sm">{error}</div>
      )}

      {_loading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-6 w-6 text-violet-400 animate-spin" />
          <span className="ml-2 text-text-muted">加载中...</span>
        </div>
      ) : data.items.length === 0 ? (
        <div className="text-center py-12 text-text-muted">暂无返工单</div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left px-4 py-2 text-text-muted font-medium">ID</th>
                  <th className="text-left px-4 py-2 text-text-muted font-medium">关联工单</th>
                  <th className="text-left px-4 py-2 text-text-muted font-medium">状态</th>
                  <th className="text-right px-4 py-2 text-text-muted font-medium">返工数量</th>
                  <th className="text-right px-4 py-2 text-text-muted font-medium">合格数量</th>
                  <th className="text-left px-4 py-2 text-text-muted font-medium">创建时间</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.id} className="border-b border-white/5 hover:bg-surface-300 transition-colors">
                    <td className="px-4 py-2 text-text-primary font-medium">#{item.id}</td>
                    <td className="px-4 py-2 text-text-muted">{item.work_order_id || item.original_order_id || "-"}</td>
                    <td className="px-4 py-2"><StatusBadge status={item.status} /></td>
                    <td className="px-4 py-2 text-right text-text-primary">{item.rework_qty ?? item.quantity ?? "-"}</td>
                    <td className="px-4 py-2 text-right text-emerald-400">{item.qualified_qty ?? item.completed_qty ?? "-"}</td>
                    <td className="px-4 py-2 text-text-muted">{item.created_at ? new Date(item.created_at).toLocaleDateString() : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.total > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-text-muted">共 {data.total} 条</span>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" disabled={page <= 1}
                  onClick={() => { const p = new URLSearchParams(searchParams); p.set("rw_page", String(page - 1)); setSearchParams(p); }}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-text-primary">{page} / {totalPages}</span>
                <Button variant="ghost" size="sm" disabled={page >= totalPages}
                  onClick={() => { const p = new URLSearchParams(searchParams); p.set("rw_page", String(page + 1)); setSearchParams(p); }}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function NCManagement() {
  const [activeTab, setActiveTab] = useState("defect");

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="不合格品管理"
        subtitle="不合格品处理与返工管理"
        icon={<XCircle className="h-6 w-6" />}
      />

      <main className="container mx-auto px-4 py-6 max-w-7xl">
        {/* Tab 切换 */}
        <div className="flex items-center gap-1 mb-6 bg-surface-200 rounded-xl p-1 border border-white/5 w-fit">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? "bg-violet-500/20 text-violet-400"
                    : "text-text-muted hover:text-text-primary hover:bg-surface-300"
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
          {activeTab === "defect" ? <DefectAnalysisTab /> : <ReworkTab />}
        </div>
      </main>
    </div>
  );
}
