import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  MessageSquare,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { cn } from "../lib/utils";
import { fadeIn } from "../lib/animations";
import { alertApi } from "../services/api";
import { LoadingPage, ErrorMessage, EmptyState } from "../components/common";
import { toast } from "../components/ui/toast";

const alertLevelConfig = {
  URGENT: {
    label: "紧急",
    color: "red",
    icon: AlertTriangle,
    bgColor: "bg-red-500/5",
    borderColor: "border-red-500/20",
    textColor: "text-red-400",
  },
  CRITICAL: {
    label: "严重",
    color: "orange",
    icon: AlertTriangle,
    bgColor: "bg-orange-500/5",
    borderColor: "border-orange-500/20",
    textColor: "text-orange-400",
  },
  WARNING: {
    label: "注意",
    color: "amber",
    icon: AlertTriangle,
    bgColor: "bg-amber-500/5",
    borderColor: "border-amber-500/20",
    textColor: "text-amber-400",
  },
  INFO: {
    label: "提示",
    color: "blue",
    icon: AlertTriangle,
    bgColor: "bg-blue-500/5",
    borderColor: "border-blue-500/20",
    textColor: "text-blue-400",
  },
};

const alertStatusConfig = {
  ACTIVE: { label: "待处理", color: "amber", icon: Clock },
  ACKNOWLEDGED: { label: "已确认", color: "blue", icon: CheckCircle2 },
  RESOLVED: { label: "已解决", color: "emerald", icon: CheckCircle2 },
  CLOSED: { label: "已关闭", color: "slate", icon: XCircle },
};

export default function AlertDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actions, setActions] = useState([]);

  useEffect(() => {
    loadAlert();
  }, [id]);

  const loadAlert = async () => {
    try {
      setLoading(true);
      const res = await alertApi.get(id);
      setAlert(res.data);
      // Load actions
      const actionsRes = await alertApi.get(id);
      setActions(actionsRes.data.actions || []);
      setError(null);
    } catch (err) {
      console.error("Failed to load alert:", err);
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async () => {
    try {
      await alertApi.acknowledge(id);
      await loadAlert();
      toast.success("预警已确认");
    } catch (error) {
      console.error("Failed to acknowledge:", error);
      toast.error("确认失败，请稍后重试");
    }
  };

  const handleResolve = async () => {
    try {
      await alertApi.resolve(id, { resolution: "问题已解决" });
      await loadAlert();
      toast.success("预警已标记为已解决");
    } catch (error) {
      console.error("Failed to resolve:", error);
      toast.error("操作失败，请稍后重试");
    }
  };

  const handleClose = async () => {
    try {
      await alertApi.close(id, { close_reason: "RESOLVED" });
      toast.success("预警已关闭");
      navigate("/alerts");
    } catch (error) {
      console.error("Failed to close:", error);
      toast.error("关闭失败，请稍后重试");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="预警详情" />
        <div className="container mx-auto px-4 py-6">
          <LoadingPage text="加载预警详情..." />
        </div>
      </div>
    );
  }

  if (error && !alert) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="预警详情" />
        <div className="container mx-auto px-4 py-6">
          <ErrorMessage
            error={error}
            onRetry={loadAlert}
            title="加载预警失败"
          />
          <div className="mt-4 text-center">
            <Button onClick={() => navigate("/alerts")} variant="outline">
              返回预警中心
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!alert) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="预警详情" />
        <div className="container mx-auto px-4 py-6">
          <EmptyState
            icon={XCircle}
            title="预警不存在"
            description="该预警可能已被删除或不存在"
            action={
              <Button onClick={() => navigate("/alerts")}>返回预警中心</Button>
            }
          />
        </div>
      </div>
    );
  }

  const levelConfig =
    alertLevelConfig[alert.alert_level] || alertLevelConfig.WARNING;
  const statusConfig =
    alertStatusConfig[alert.status] || alertStatusConfig.ACTIVE;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title={
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/alerts")}
              className="gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              返回
            </Button>
            <span>预警详情</span>
            <span className="font-mono text-sm text-slate-400">
              {alert.alert_no}
            </span>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Alert Header */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card
            className={cn(
              "border",
              levelConfig.bgColor,
              levelConfig.borderColor,
            )}
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <levelConfig.icon
                      className={cn("w-6 h-6", levelConfig.textColor)}
                    />
                    <Badge
                      variant="outline"
                      className={cn(
                        levelConfig.textColor,
                        levelConfig.borderColor,
                      )}
                    >
                      {levelConfig.label}
                    </Badge>
                    <Badge variant="secondary">{statusConfig.label}</Badge>
                  </div>
                  <h1 className="text-2xl font-bold text-white">
                    {alert.title}
                  </h1>
                  <p className="text-slate-400">{alert.content}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Alert Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">预警信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-sm text-slate-500 mb-1">触发时间</p>
                  <p className="text-white">{alert.triggered_at}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">预警规则</p>
                  <p className="text-white">
                    {alert.rule_code || alert.rule_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">当前状态</p>
                  <Badge variant="secondary">{statusConfig.label}</Badge>
                </div>
                {alert.acknowledged_at && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">确认时间</p>
                    <p className="text-white">{alert.acknowledged_at}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">关联信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {alert.project_name && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">关联项目</p>
                    <p className="text-white">{alert.project_name}</p>
                  </div>
                )}
                {alert.assigned_to && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">负责人</p>
                    <p className="text-white">{alert.assigned_to}</p>
                  </div>
                )}
                {alert.metric_value !== undefined && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">指标值</p>
                    <p className="text-white">{alert.metric_value}</p>
                  </div>
                )}
                {alert.threshold_value !== undefined && (
                  <div>
                    <p className="text-sm text-slate-500 mb-1">阈值</p>
                    <p className="text-white">{alert.threshold_value}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Suggestion */}
        {alert.suggestion && (
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">处理建议</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-invert max-w-none">
                  <p className="text-slate-300 whitespace-pre-line">
                    {alert.suggestion}
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Actions History */}
        {actions.length > 0 && (
          <motion.div variants={fadeIn} initial="hidden" animate="visible">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">处理记录</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {actions.map((action, index) => (
                    <div
                      key={index}
                      className="flex gap-4 pb-4 border-b border-slate-700 last:border-0"
                    >
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center">
                          <MessageSquare className="w-4 h-4 text-slate-400" />
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-white font-medium">
                            {action.created_by_name || "系统"}
                          </span>
                          <span className="text-xs text-slate-500">
                            {action.created_at}
                          </span>
                        </div>
                        <p className="text-slate-400 text-sm">
                          {action.action_content}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Actions */}
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-6">
              <div className="flex gap-3">
                {alert.status === "ACTIVE" && (
                  <Button onClick={handleAcknowledge}>确认预警</Button>
                )}
                {alert.status === "ACKNOWLEDGED" && (
                  <Button onClick={handleResolve}>标记已解决</Button>
                )}
                <Button variant="outline" onClick={handleClose}>
                  关闭
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
