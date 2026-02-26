/**
 * 检验任务列表
 * 调用 GET /production/quality/inspection
 */
import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileCheck, Search, Filter, ChevronLeft, ChevronRight, Plus,
  RefreshCw, CheckCircle, XCircle, Clock, AlertTriangle,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { qualityApi } from "../../services/api/quality";

const INSPECTION_TYPES = [
  { value: "", label: "全部类型" },
  { value: "IQC", label: "来料检验 (IQC)" },
  { value: "IPQC", label: "过程检验 (IPQC)" },
  { value: "FQC", label: "成品检验 (FQC)" },
  { value: "OQC", label: "出货检验 (OQC)" },
];

const RESULT_OPTIONS = [
  { value: "", label: "全部结果" },
  { value: "PASS", label: "合格" },
  { value: "FAIL", label: "不合格" },
  { value: "CONDITIONAL", label: "让步接收" },
];

function ResultBadge({ result }) {
  const map = {
    PASS: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "合格", icon: CheckCircle },
    FAIL: { bg: "bg-red-500/20", text: "text-red-400", label: "不合格", icon: XCircle },
    CONDITIONAL: { bg: "bg-amber-500/20", text: "text-amber-400", label: "让步接收", icon: AlertTriangle },
    PENDING: { bg: "bg-blue-500/20", text: "text-blue-400", label: "待检", icon: Clock },
  };
  const cfg = map[result] || map.PENDING;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${cfg.bg} ${cfg.text}`}>
      <Icon className="h-3 w-3" />
      {cfg.label}
    </span>
  );
}

function TypeBadge({ type }) {
  const colors = {
    IQC: "bg-blue-500/20 text-blue-400",
    IPQC: "bg-violet-500/20 text-violet-400",
    FQC: "bg-emerald-500/20 text-emerald-400",
    OQC: "bg-amber-500/20 text-amber-400",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs ${colors[type] || "bg-gray-500/20 text-gray-400"}`}>
      {type}
    </span>
  );
}

export default function InspectionList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = 20;
  const inspectionType = searchParams.get("inspection_type") || "";
  const inspectionResult = searchParams.get("inspection_result") || "";
  const [searchText, setSearchText] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
      };
      if (inspectionType) params.inspection_type = inspectionType;
      if (inspectionResult) params.inspection_result = inspectionResult;

      const res = await qualityApi.inspection.list(params);
      const resData = res.data || res;
      setData({
        items: resData.items || resData.inspections || [],
        total: resData.total || 0,
      });
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "加载失败");
    } finally {
      setLoading(false);
    }
  }, [page, inspectionType, inspectionResult]);

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
        title="检验任务"
        subtitle="质量检验任务列表"
        icon={<FileCheck className="h-6 w-6" />}
        actions={
          <Button onClick={() => navigate("/quality/inspections/new")} className="gap-2">
            <Plus className="h-4 w-4" /> 新建检验
          </Button>
        }
      />

      <main className="container mx-auto px-4 py-6 max-w-7xl">
        {/* 筛选栏 */}
        <div className="bg-surface-200 rounded-xl border border-white/5 p-4 mb-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
              <input
                type="text"
                placeholder="搜索检验记录..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-1 focus:ring-violet-500"
              />
            </div>
            <select
              value={inspectionType}
              onChange={(e) => updateFilter("inspection_type", e.target.value)}
              className="px-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-violet-500"
            >
              {INSPECTION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <select
              value={inspectionResult}
              onChange={(e) => updateFilter("inspection_result", e.target.value)}
              className="px-3 py-2 rounded-lg bg-surface-300 border border-white/5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-violet-500"
            >
              {RESULT_OPTIONS.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
            <Button variant="ghost" size="sm" onClick={fetchData} className="gap-1">
              <RefreshCw className="h-4 w-4" /> 刷新
            </Button>
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* 表格 */}
        <div className="bg-surface-200 rounded-xl border border-white/5 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <RefreshCw className="h-6 w-6 text-violet-400 animate-spin" />
              <span className="ml-2 text-text-muted">加载中...</span>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="text-center py-20 text-text-muted">暂无检验记录</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left px-4 py-3 text-text-muted font-medium">ID</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">检验类型</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">物料</th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">送检数</th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">合格数</th>
                    <th className="text-right px-4 py-3 text-text-muted font-medium">不良数</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">结果</th>
                    <th className="text-left px-4 py-3 text-text-muted font-medium">检验时间</th>
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
                      onClick={() => navigate(`/quality/inspections/${item.id}`)}
                    >
                      <td className="px-4 py-3 text-text-primary font-medium">#{item.id}</td>
                      <td className="px-4 py-3"><TypeBadge type={item.inspection_type} /></td>
                      <td className="px-4 py-3 text-text-primary">{item.material_name || item.material_id || "-"}</td>
                      <td className="px-4 py-3 text-right text-text-primary">{item.inspection_qty ?? "-"}</td>
                      <td className="px-4 py-3 text-right text-emerald-400">{item.qualified_qty ?? "-"}</td>
                      <td className="px-4 py-3 text-right text-red-400">{item.defect_qty ?? 0}</td>
                      <td className="px-4 py-3"><ResultBadge result={item.inspection_result || item.result} /></td>
                      <td className="px-4 py-3 text-text-muted">{item.inspection_date ? new Date(item.inspection_date).toLocaleDateString() : item.created_at ? new Date(item.created_at).toLocaleDateString() : "-"}</td>
                      <td className="px-4 py-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => { e.stopPropagation(); navigate(`/quality/inspections/${item.id}`); }}
                        >
                          详情
                        </Button>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 分页 */}
          {data.total > 0 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-white/5">
              <span className="text-sm text-text-muted">共 {data.total} 条记录</span>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => { const p = new URLSearchParams(searchParams); p.set("page", String(page - 1)); setSearchParams(p); }}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-text-primary">{page} / {totalPages}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => { const p = new URLSearchParams(searchParams); p.set("page", String(page + 1)); setSearchParams(p); }}
                >
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
