/**
 * 质量问题详情页
 */
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  AlertCircle, ArrowLeft, RefreshCw, AlertTriangle, Clock,
  CheckCircle, User, Calendar, MessageSquare, Tag,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { issueApi } from "../../services/api/issues";

function SeverityBadge({ level }) {
  const map = {
    critical: { bg: "bg-red-500/20", text: "text-red-400", label: "严重" },
    major: { bg: "bg-amber-500/20", text: "text-amber-400", label: "主要" },
    minor: { bg: "bg-blue-500/20", text: "text-blue-400", label: "次要" },
  };
  const cfg = map[level] || { bg: "bg-gray-500/20", text: "text-gray-400", label: level || "未知" };
  return <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-lg text-sm font-medium ${cfg.bg} ${cfg.text}`}>{cfg.label}</span>;
}

function StatusBadge({ status }) {
  const map = {
    open: { bg: "bg-red-500/20", text: "text-red-400", label: "待处理", icon: AlertTriangle },
    in_progress: { bg: "bg-amber-500/20", text: "text-amber-400", label: "处理中", icon: Clock },
    resolved: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "已解决", icon: CheckCircle },
    closed: { bg: "bg-gray-500/20", text: "text-gray-400", label: "已关闭", icon: CheckCircle },
  };
  const cfg = map[status] || map.open;
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

export default function IssueDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState(null);
  const [followUps, setFollowUps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await issueApi.get(id);
        setItem(res.data || res);
        try {
          const fuRes = await issueApi.getFollowUps(id);
          setFollowUps((fuRes.data || fuRes)?.items || fuRes.data?.items || fuRes.data || []);
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
        title={`问题详情 #${id}`}
        subtitle="质量问题详细信息"
        icon={<AlertCircle className="h-6 w-6" />}
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
            {/* 头部 */}
            <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-text-primary">{item.title || item.issue_no || `问题 #${item.id}`}</h3>
                  <p className="text-sm text-text-muted mt-1">{item.issue_no || `#${item.id}`}</p>
                </div>
                <div className="flex items-center gap-2">
                  <SeverityBadge level={item.severity || item.level} />
                  <StatusBadge status={item.status} />
                </div>
              </div>

              {item.description && (
                <div className="p-4 rounded-lg bg-surface-300 mt-4">
                  <p className="text-sm text-text-primary whitespace-pre-wrap">{item.description}</p>
                </div>
              )}
            </div>

            {/* 详细信息 */}
            <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
              <h4 className="text-lg font-semibold text-text-primary mb-4">详细信息</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <InfoItem icon={Tag} label="分类" value={item.category} />
                <InfoItem icon={User} label="责任人" value={item.assignee_name || item.responsible} />
                <InfoItem icon={User} label="创建人" value={item.creator_name || item.reporter} />
                <InfoItem icon={Calendar} label="创建时间" value={item.created_at ? new Date(item.created_at).toLocaleString() : "-"} />
                <InfoItem icon={Calendar} label="更新时间" value={item.updated_at ? new Date(item.updated_at).toLocaleString() : "-"} />
                {item.resolved_at && (
                  <InfoItem icon={Calendar} label="解决时间" value={new Date(item.resolved_at).toLocaleString()} />
                )}
                {item.project_name && (
                  <InfoItem icon={Tag} label="关联项目" value={item.project_name} />
                )}
                {item.root_cause && (
                  <InfoItem icon={MessageSquare} label="根因分析" value={item.root_cause} />
                )}
              </div>
            </div>

            {/* 跟进记录 */}
            {followUps.length > 0 && (
              <div className="bg-surface-200 rounded-xl border border-white/5 p-6">
                <h4 className="text-lg font-semibold text-text-primary mb-4">跟进记录</h4>
                <div className="space-y-3">
                  {followUps.map((fu, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-surface-300">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-text-primary">{fu.creator_name || "系统"}</span>
                        <span className="text-xs text-text-muted">{fu.created_at ? new Date(fu.created_at).toLocaleString() : ""}</span>
                      </div>
                      <p className="text-sm text-text-secondary">{fu.content || fu.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        ) : null}
      </main>
    </div>
  );
}
