/**
 * 检验详情页
 * 展示单条检验记录的完整信息
 */
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileCheck, ArrowLeft, RefreshCw, CheckCircle, XCircle,
  Clock, AlertTriangle, Package, Clipboard, Calendar,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { qualityApi } from "../../services/api/quality";

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
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-sm font-medium ${cfg.bg} ${cfg.text}`}>
      <Icon className="h-4 w-4" /> {cfg.label}
    </span>
  );
}

function InfoItem({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-surface-300">
      <div className="p-2 rounded-lg bg-surface-400">
        <Icon className="h-4 w-4 text-text-muted" />
      </div>
      <div>
        <p className="text-xs text-text-muted">{label}</p>
        <p className="text-sm font-medium text-text-primary mt-0.5">{value || "-"}</p>
      </div>
    </div>
  );
}

export default function InspectionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        // The list API is used since there's no single-get endpoint;
        // we fetch the list and find the matching item by ID.
        // If a dedicated GET endpoint exists, replace this.
        const res = await qualityApi.inspection.list({ skip: 0, limit: 100 });
        const resData = res.data || res;
        const items = resData.items || resData.inspections || [];
        const found = items.find((i) => String(i.id) === String(id));
        if (found) {
          setItem(found);
        } else {
          setError("未找到该检验记录");
        }
      } catch (err) {
        setError(err.response?.data?.detail || err.message || "加载失败");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const passRate = item && item.inspection_qty > 0
    ? ((item.qualified_qty / item.inspection_qty) * 100).toFixed(1)
    : "-";

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title={`检验详情 #${id}`}
        subtitle="检验任务详细信息"
        icon={<FileCheck className="h-6 w-6" />}
        actions={
          <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2">
            <ArrowLeft className="h-4 w-4" /> 返回
          </Button>
        }
      />

      <main className="container mx-auto px-4 py-6 max-w-4xl">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw className="h-6 w-6 text-violet-400 animate-spin" />
            <span className="ml-2 text-text-muted">加载中...</span>
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 text-red-400 text-sm">{error}</div>
        ) : item ? (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            {/* 头部概览 */}
            <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-bold text-text-primary">检验记录 #{item.id}</h3>
                  <p className="text-sm text-text-muted mt-1">
                    创建于 {item.created_at ? new Date(item.created_at).toLocaleString() : "-"}
                  </p>
                </div>
                <ResultBadge result={item.inspection_result || item.result} />
              </div>

              {/* 数量统计 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-surface-300 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-text-primary">{item.inspection_qty ?? "-"}</p>
                  <p className="text-xs text-text-muted mt-1">送检数量</p>
                </div>
                <div className="bg-surface-300 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-emerald-400">{item.qualified_qty ?? "-"}</p>
                  <p className="text-xs text-text-muted mt-1">合格数量</p>
                </div>
                <div className="bg-surface-300 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-red-400">{item.defect_qty ?? 0}</p>
                  <p className="text-xs text-text-muted mt-1">不良数量</p>
                </div>
                <div className="bg-surface-300 rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-violet-400">{passRate}%</p>
                  <p className="text-xs text-text-muted mt-1">合格率</p>
                </div>
              </div>
            </div>

            {/* 详细信息 */}
            <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
              <h4 className="text-lg font-semibold text-text-primary mb-4">详细信息</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <InfoItem icon={Clipboard} label="检验类型" value={item.inspection_type} />
                <InfoItem icon={Package} label="物料ID" value={item.material_id} />
                <InfoItem icon={Clipboard} label="工单ID" value={item.work_order_id} />
                <InfoItem icon={Calendar} label="检验日期" value={item.inspection_date ? new Date(item.inspection_date).toLocaleDateString() : item.created_at ? new Date(item.created_at).toLocaleDateString() : "-"} />
                {item.measured_value != null && (
                  <InfoItem icon={Clipboard} label="测量值" value={item.measured_value} />
                )}
                {item.inspector_name && (
                  <InfoItem icon={Clipboard} label="检验员" value={item.inspector_name} />
                )}
                {item.remark && (
                  <InfoItem icon={Clipboard} label="备注" value={item.remark} />
                )}
              </div>
            </div>
          </motion.div>
        ) : null}
      </main>
    </div>
  );
}
