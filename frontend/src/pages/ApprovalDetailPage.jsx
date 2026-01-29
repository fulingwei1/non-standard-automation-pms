/**
 * ApprovalDetailPage - 审批详情页
 *
 * 左右两栏布局：
 * - 左侧：基本信息 + 审批操作
 * - 右侧：审批进度时间线
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  FileText,
  User,
  Calendar,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  Send,
  Undo2,
  Bell,
  ExternalLink,
  Loader2,
} from "lucide-react";

import { PageHeader } from "../components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { cn } from "../lib/utils";
import ApprovalTimeline from "../components/approval/ApprovalTimeline";
import { api } from "../services/api/client";

/**
 * 紧急程度配置
 */
const URGENCY_CONFIG = {
  NORMAL: { label: "普通", color: "bg-slate-500", textColor: "text-slate-400" },
  URGENT: { label: "紧急", color: "bg-orange-500", textColor: "text-orange-400" },
  CRITICAL: { label: "特急", color: "bg-red-500", textColor: "text-red-400" },
};

/**
 * 状态配置
 */
const STATUS_CONFIG = {
  DRAFT: { label: "草稿", color: "bg-slate-500", icon: FileText },
  PENDING: { label: "审批中", color: "bg-amber-500", icon: Clock },
  APPROVED: { label: "已通过", color: "bg-emerald-500", icon: CheckCircle2 },
  REJECTED: { label: "已驳回", color: "bg-red-500", icon: XCircle },
  WITHDRAWN: { label: "已撤回", color: "bg-slate-500", icon: Undo2 },
  TERMINATED: { label: "已终止", color: "bg-slate-600", icon: XCircle },
};

/**
 * 实体类型配置
 */
const ENTITY_TYPE_CONFIG = {
  ECN: { label: "工程变更", path: "/ecn" },
  QUOTE: { label: "报价", path: "/quotes" },
  CONTRACT: { label: "合同", path: "/contracts" },
  INVOICE: { label: "发票", path: "/invoices" },
};

/**
 * 格式化日期时间
 */
const formatDateTime = (dateStr) => {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const ApprovalDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [instance, setInstance] = useState(null);
  const [error, setError] = useState(null);

  // 审批操作状态
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [actionType, setActionType] = useState(null); // 'approve' | 'reject' | 'withdraw'

  // 当前用户信息（从 localStorage 或 context 获取）
  const currentUserId = parseInt(localStorage.getItem("userId") || "0");

  /**
   * 加载审批详情
   */
  const loadInstance = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/instances/${id}`);
      setInstance(response.data);
    } catch (err) {
      console.error("加载审批详情失败:", err);
      setError(err.response?.data?.detail || "加载失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadInstance();
  }, [loadInstance]);

  /**
   * 获取当前用户的待处理任务
   */
  const getCurrentUserTask = () => {
    if (!instance?.tasks) return null;
    return instance.tasks.find(
      (task) => task.assignee_id === currentUserId && task.status === "PENDING"
    );
  };

  /**
   * 判断当前用户是否是发起人
   */
  const isInitiator = instance?.initiator_id === currentUserId;

  /**
   * 判断当前用户是否可以审批
   */
  const canApprove = getCurrentUserTask() !== null;

  /**
   * 判断是否可以撤回（发起人且状态为 PENDING）
   */
  const canWithdraw = isInitiator && instance?.status === "PENDING";

  /**
   * 执行审批操作
   */
  const handleApprovalAction = async (action) => {
    const task = getCurrentUserTask();
    if (!task && action !== "withdraw") {
      return;
    }

    setActionType(action);
    setSubmitting(true);

    try {
      if (action === "approve") {
        await api.post(`/tasks/${task.id}/approve`, {
          comment: comment || "同意",
        });
      } else if (action === "reject") {
        await api.post(`/tasks/${task.id}/reject`, {
          comment: comment || "驳回",
        });
      } else if (action === "withdraw") {
        await api.post(`/instances/${id}/withdraw`, {
          comment: comment || "撤回申请",
        });
      }

      // 重新加载数据
      await loadInstance();
      setComment("");
    } catch (err) {
      console.error("操作失败:", err);
      setError(err.response?.data?.detail || "操作失败，请稍后重试");
    } finally {
      setSubmitting(false);
      setActionType(null);
    }
  };

  /**
   * 催办
   */
  const handleUrge = async () => {
    try {
      await api.post(`/instances/${id}/urge`);
      // TODO: 显示成功提示
    } catch (err) {
      console.error("催办失败:", err);
    }
  };

  // 加载中状态
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // 错误状态
  if (error && !instance) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertTriangle className="h-12 w-12 text-red-400" />
        <p className="text-slate-400">{error}</p>
        <Button variant="outline" onClick={() => navigate(-1)}>
          返回
        </Button>
      </div>
    );
  }

  if (!instance) {
    return null;
  }

  const statusConfig = STATUS_CONFIG[instance.status] || STATUS_CONFIG.PENDING;
  const urgencyConfig = URGENCY_CONFIG[instance.urgency] || URGENCY_CONFIG.NORMAL;
  const entityConfig = ENTITY_TYPE_CONFIG[instance.entity_type];
  const StatusIcon = statusConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title={
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={() => navigate(-1)}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <span>审批详情</span>
          </div>
        }
        description={instance.instance_no}
        actions={
          <div className="flex items-center gap-2">
            {canWithdraw && (
              <Button
                variant="outline"
                onClick={() => handleApprovalAction("withdraw")}
                disabled={submitting}
              >
                {submitting && actionType === "withdraw" ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Undo2 className="h-4 w-4 mr-2" />
                )}
                撤回申请
              </Button>
            )}
            {isInitiator && instance.status === "PENDING" && (
              <Button variant="outline" onClick={handleUrge}>
                <Bell className="h-4 w-4 mr-2" />
                催办
              </Button>
            )}
          </div>
        }
      />

      {/* 主体内容 - 左右两栏 */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* 左侧 - 基本信息 + 操作 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 基本信息卡片 */}
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white text-lg">基本信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* 标题 */}
              <div>
                <p className="text-sm text-slate-500 mb-1">审批标题</p>
                <p className="text-white font-medium">{instance.title}</p>
              </div>

              {/* 编号和状态 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500 mb-1">审批编号</p>
                  <p className="text-slate-300 font-mono text-sm">
                    {instance.instance_no}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">当前状态</p>
                  <Badge className={cn(statusConfig.color, "text-white")}>
                    <StatusIcon className="h-3 w-3 mr-1" />
                    {statusConfig.label}
                  </Badge>
                </div>
              </div>

              {/* 发起人和时间 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500 mb-1">发起人</p>
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-slate-500" />
                    <span className="text-slate-300">{instance.initiator_name}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">发起时间</p>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-slate-500" />
                    <span className="text-slate-300 text-sm">
                      {formatDateTime(instance.created_at)}
                    </span>
                  </div>
                </div>
              </div>

              {/* 紧急程度和当前节点 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500 mb-1">紧急程度</p>
                  <Badge
                    className={cn(
                      urgencyConfig.color,
                      "text-white"
                    )}
                  >
                    {urgencyConfig.label}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">当前节点</p>
                  <span className={cn("text-sm", urgencyConfig.textColor)}>
                    {instance.current_node_name || "-"}
                  </span>
                </div>
              </div>

              {/* 关联业务 */}
              {entityConfig && (
                <div>
                  <p className="text-sm text-slate-500 mb-1">关联业务</p>
                  <Link
                    to={`${entityConfig.path}/${instance.entity_id}`}
                    className="inline-flex items-center gap-1.5 text-primary hover:underline"
                  >
                    <FileText className="h-4 w-4" />
                    {entityConfig.label} #{instance.entity_id}
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
              )}

              {/* 摘要 */}
              {instance.summary && (
                <div>
                  <p className="text-sm text-slate-500 mb-1">审批摘要</p>
                  <p className="text-slate-300 text-sm bg-slate-900/50 rounded-lg p-3">
                    {instance.summary}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 审批操作区 - 仅当前审批人可见 */}
          {canApprove && (
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-lg">审批操作</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-slate-500 mb-2">审批意见</p>
                  <Textarea
                    placeholder="请输入审批意见（可选）"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    className="bg-slate-900/50 border-slate-700 min-h-[100px]"
                  />
                </div>

                <div className="flex gap-3">
                  <Button
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                    onClick={() => handleApprovalAction("approve")}
                    disabled={submitting}
                  >
                    {submitting && actionType === "approve" ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                    )}
                    通过
                  </Button>
                  <Button
                    variant="destructive"
                    className="flex-1"
                    onClick={() => handleApprovalAction("reject")}
                    disabled={submitting}
                  >
                    {submitting && actionType === "reject" ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <XCircle className="h-4 w-4 mr-2" />
                    )}
                    驳回
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 错误提示 */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* 右侧 - 时间线 */}
        <div className="lg:col-span-3">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <ApprovalTimeline instance={instance} />
            </CardContent>
          </Card>
        </div>
      </div>
    </motion.div>
  );
};

export default ApprovalDetailPage;
