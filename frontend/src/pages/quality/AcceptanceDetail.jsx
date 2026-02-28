/**
 * 验收详情页
 * 调用 GET /acceptance-orders/:id
 */
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Award, ArrowLeft, RefreshCw, Clock, CheckCircle, Play,
  AlertTriangle, User, Calendar, FileText, Clipboard,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { acceptanceApi } from "../../services/api/acceptance";

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

export default function AcceptanceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await acceptanceApi.orders.get(id);
        setOrder(res.data || res);
        try {
          const itemsRes = await acceptanceApi.orders.getItems(id);
          setItems((itemsRes.data || itemsRes)?.items || itemsRes.data?.items || itemsRes.data || []);
        } catch { /* ignore */ }
      } catch (err) {
        setError(err.response?.data?.detail || err.message || "加载失败");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title={`验收详情 #${id}`}
        subtitle="项目验收详细信息"
        icon={<Award className="h-6 w-6" />}
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
        ) : order ? (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            {/* 头部概览 */}
            <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-text-primary">{order.order_no || `验收单 #${order.id}`}</h3>
                  <p className="text-sm text-text-muted mt-1">{order.project_name || ""}</p>
                </div>
                <StatusBadge status={order.status} />
              </div>
            </div>

            {/* 详细信息 */}
            <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
              <h4 className="text-lg font-semibold text-text-primary mb-4">验收信息</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <InfoItem icon={FileText} label="验收类型" value={order.acceptance_type || order.type} />
                <InfoItem icon={User} label="客户" value={order.customer_name || order.customer} />
                <InfoItem icon={Calendar} label="计划日期" value={order.scheduled_date || order.planned_date} />
                <InfoItem icon={Calendar} label="实际日期" value={order.actual_date || order.completed_date} />
                <InfoItem icon={User} label="验收负责人" value={order.inspector_name || order.leader_name} />
                <InfoItem icon={Clipboard} label="验收地点" value={order.location} />
                <InfoItem icon={Calendar} label="创建时间" value={order.created_at ? new Date(order.created_at).toLocaleString() : "-"} />
                <InfoItem icon={Calendar} label="更新时间" value={order.updated_at ? new Date(order.updated_at).toLocaleString() : "-"} />
              </div>
              {order.remark && (
                <div className="mt-4 p-4 rounded-lg bg-surface-300">
                  <p className="text-xs text-text-muted mb-1">备注</p>
                  <p className="text-sm text-text-primary whitespace-pre-wrap">{order.remark}</p>
                </div>
              )}
            </div>

            {/* 验收项 */}
            {items?.length > 0 && (
              <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
                <h4 className="text-lg font-semibold text-text-primary mb-4">验收项目</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-white/5">
                        <th className="text-left px-4 py-2 text-text-muted font-medium">序号</th>
                        <th className="text-left px-4 py-2 text-text-muted font-medium">检查项</th>
                        <th className="text-left px-4 py-2 text-text-muted font-medium">标准</th>
                        <th className="text-left px-4 py-2 text-text-muted font-medium">结果</th>
                        <th className="text-left px-4 py-2 text-text-muted font-medium">备注</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(items || []).map((item, idx) => (
                        <tr key={item.id || idx} className="border-b border-white/5">
                          <td className="px-4 py-2 text-text-muted">{idx + 1}</td>
                          <td className="px-4 py-2 text-text-primary">{item.check_item || item.name || "-"}</td>
                          <td className="px-4 py-2 text-text-muted">{item.standard || item.criteria || "-"}</td>
                          <td className="px-4 py-2">
                            {item.result === "pass" || item.is_passed ? (
                              <span className="text-emerald-400">✓ 通过</span>
                            ) : item.result === "fail" ? (
                              <span className="text-red-400">✗ 不通过</span>
                            ) : (
                              <span className="text-text-muted">-</span>
                            )}
                          </td>
                          <td className="px-4 py-2 text-text-muted">{item.remark || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </motion.div>
        ) : null}
      </main>
    </div>
  );
}
