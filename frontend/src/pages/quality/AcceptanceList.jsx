/**
 * 验收管理列表
 * 调用 GET /acceptance-orders
 */
import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Award, Search, ChevronLeft, ChevronRight, Plus,
  RefreshCw, Clock, CheckCircle, Play, AlertTriangle,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { acceptanceApi } from "../../services/api/acceptance";

const STATUS_OPTIONS = [
  { value: "", label: "全部状态" },
  { value: "pending", label: "待验收" },
  { value: "in_progress", label: "验收中" },
  { value: "completed", label: "已完成" },
  { value: "rejected", label: "未通过" },
];

function StatusBadge({ status }) {
  const map = {
    pending: { bg: "bg-blue-500/20", text: "text-blue-400", label: "待验收", icon: Clock },
    in_progress: { bg: "bg-amber-500/20", text: "text-amber-400", label: "验收中", icon: Play },
    completed: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "已完成", icon: CheckCircle },
    rejected: { bg: "bg-red-500/20", text: "text-red-400", label: "未通过", icon: AlertTriangle },
  };
  const cfg = map[status] || map.pending;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${cfg.bg} ${cfg.text}`}>
      <Icon className="h-3 w-3" /> {cfg.label}
    </span>
  );
}

export default function AcceptanceList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = 20;
  const status = searchParams.get("status") || "";
  const [searchText, setSearchText] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, page_size: pageSize };
      if (status) params.status = status;

      const res = await acceptanceApi.orders.list(params);
      const resData = res.data || res;
      setData({
        items: resData.items || resData.data || [],
        total: resData.total || 0,
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "加载失败");
    } finally {
      setLoading(false);
    }
  }, [page, status]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));

  const updateFilter = (key, value) => {
    const params = new URLSearchParams(searchParams);
    if (value) params.set(key, value);
    else params.delete(key);
    params.set("page", "1");
    setSearchParams(params);
  };

  const filteredItems = searchText
    ? data.items.filter((item) =>
        JSON.stringify(item).toLowerCase().includes(searchText.toLowerCase())
      )
    : data.items;

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="验收管理"
        subtitle="项目验收任务列表"
        icon={<Award className="h-6 w-6" />}
        actions={
          <Button onClick={() => navigate("/quality/acceptance/new")} className="gap-2">
            <Plus className="h-4 w-4" /> 新建验收
          </Button>
        }
      />

      <main className="container mx-auto px-4 py-6 max-w-7xl">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-4 mb-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="text"
                placeholder="搜索验收单..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-violet-500"
              />
            </div>
            <select
              value={status}
              onChange={(e) => updateFilter("status", e.target.value)}
              className="px-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-violet-500"
            >
              {STATUS_OPTIONS.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <Button variant="ghost" size="sm" onClick={fetchData} className="gap-1">
              <RefreshCw className="h-4 w-4" /> 刷新
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-4 text-red-400 text-sm">{error}</div>
        )}

        <div className="bg-surface-200 rounded-xl border border-white/5 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="h-6 w-6 text-violet-400 animate-spin" />
              <span className="ml-2 text-text-muted">加载中...</span>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="text-center py-20 text-text-muted">暂无验收记录</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left px-4 py-3 text-text-muted font-medium">验收单号</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">项目名称</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">验收类型</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">状态</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">计划日期</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">客户</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredItems.map((item) => (
                    <motion.tr
                      key={item.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="border-b border-white/5 hover:bg-surface-300 transition-colors cursor-pointer"
                      onClick={() => navigate(`/quality/acceptance/${item.id}`)}
                    >
                      <td className="px-4 py-3 text-text-primary font-medium">{item.order_no || `#${item.id}`}</td>
                      <td className="px-4 py-3 text-text-primary">{item.project_name || "-"}</td>
                      <td className="px-4 py-3 text-text-muted">{item.acceptance_type || item.type || "-"}</td>
                      <td className="px-4 py-3"><StatusBadge status={item.status} /></td>
                      <td className="px-4 py-3 text-text-muted">{item.scheduled_date || item.planned_date || "-"}</td>
                      <td className="px-4 py-3 text-text-muted">{item.customer_name || item.customer || "-"}</td>
                      <td className="px-4 py-3">
                        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); navigate(`/quality/acceptance/${item.id}`); }}>
                          详情
                        </Button>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {data.total > 0 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-white/5">
              <span className="text-sm text-text-muted">共 {data.total} 条记录</span>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" disabled={page <= 1}
                  onClick={() => { const p = new URLSearchParams(searchParams); p.set("page", String(page - 1)); setSearchParams(p); }}>
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-text-primary">{page} / {totalPages}</span>
                <Button variant="ghost" size="sm" disabled={page >= totalPages}
                  onClick={() => { const p = new URLSearchParams(searchParams); p.set("page", String(page + 1)); setSearchParams(p); }}>
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
