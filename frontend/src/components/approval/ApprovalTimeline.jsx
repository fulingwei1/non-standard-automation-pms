/**
 * ApprovalTimeline - 审批流程时间线组件
 *
 * 垂直时间线展示审批流程的完整进度，包括：
 * - 节点名称和状态图标
 * - 操作人和操作时间
 * - 耗时、审批意见、附件、委托信息
 */

import {
  CheckCircle2,
  XCircle,
  Circle,
  Clock,
  Undo2,
  FileText,
  MessageSquare,
  Users,
  Loader2
} from "lucide-react";
import { cn } from "../../lib/utils";
import { Badge } from "../ui/badge";

/**
 * 计算两个时间之间的耗时
 * @param {string} startTime - 开始时间
 * @param {string} endTime - 结束时间
 * @returns {string} 格式化的耗时字符串
 */
const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return null;

  const start = new Date(startTime);
  const end = new Date(endTime);
  const diffMs = end - start;

  if (diffMs < 0) return null;

  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) {
    const remainingHours = diffHours % 24;
    return remainingHours > 0 ? `${diffDays}天 ${remainingHours}小时` : `${diffDays}天`;
  }
  if (diffHours > 0) {
    const remainingMinutes = diffMinutes % 60;
    return remainingMinutes > 0 ? `${diffHours}小时 ${remainingMinutes}分钟` : `${diffHours}小时`;
  }
  return `${diffMinutes}分钟`;
};

/**
 * 格式化日期时间
 * @param {string} dateStr - ISO 日期字符串
 * @returns {string} 格式化的日期时间
 */
const formatDateTime = (dateStr) => {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

/**
 * 节点状态配置
 */
const NODE_STATUS_CONFIG = {
  submitted: {
    icon: Circle,
    color: "text-blue-400",
    bgColor: "bg-blue-400",
    borderColor: "border-blue-400",
    label: "已提交",
  },
  completed: {
    icon: CheckCircle2,
    color: "text-emerald-400",
    bgColor: "bg-emerald-400",
    borderColor: "border-emerald-400",
    label: "已通过",
  },
  rejected: {
    icon: XCircle,
    color: "text-red-400",
    bgColor: "bg-red-400",
    borderColor: "border-red-400",
    label: "已驳回",
  },
  current: {
    icon: Loader2,
    color: "text-amber-400",
    bgColor: "bg-amber-400",
    borderColor: "border-amber-400",
    label: "进行中",
    animate: true,
  },
  pending: {
    icon: Circle,
    color: "text-slate-500",
    bgColor: "bg-slate-500",
    borderColor: "border-slate-500",
    label: "待处理",
  },
  withdrawn: {
    icon: Undo2,
    color: "text-slate-400",
    bgColor: "bg-slate-400",
    borderColor: "border-slate-400",
    label: "已撤回",
  },
};

/**
 * 时间线节点组件
 */
const TimelineNode = ({ node, isLast, previousNodeTime }) => {
  const config = NODE_STATUS_CONFIG[node.status] || NODE_STATUS_CONFIG.pending;
  const Icon = config.icon;

  // 计算耗时
  const duration = node.action_time && previousNodeTime
    ? calculateDuration(previousNodeTime, node.action_time)
    : null;

  // 如果是当前节点且还在等待，计算等待时间
  const waitingTime = node.status === "current" && node.created_at
    ? calculateDuration(node.created_at, new Date().toISOString())
    : null;

  return (
    <div className="relative flex gap-4">
      {/* 时间线竖线 */}
      {!isLast && (
        <div
          className={cn(
            "absolute left-[15px] top-[32px] w-0.5 h-[calc(100%-16px)]",
            node.status === "pending" ? "bg-slate-700" : "bg-slate-600"
          )}
        />
      )}

      {/* 节点图标 */}
      <div className="relative z-10 flex-shrink-0">
        <div
          className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center",
            "border-2",
            config.borderColor,
            node.status === "pending" ? "bg-slate-800" : "bg-slate-900"
          )}
        >
          <Icon
            className={cn(
              "h-4 w-4",
              config.color,
              config.animate && "animate-spin"
            )}
          />
        </div>
      </div>

      {/* 节点内容 */}
      <div className="flex-1 pb-6">
        {/* 节点名称和状态 */}
        <div className="flex items-center gap-2 mb-1">
          <span className="text-white font-medium">{node.node_name}</span>
          {node.status === "current" && (
            <Badge variant="warning" className="text-xs">当前</Badge>
          )}
          {duration && (
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              耗时 {duration}
            </span>
          )}
        </div>

        {/* 操作人和时间 */}
        {node.operator_name && (
          <div className="text-sm text-slate-400 mb-1">
            <span>{node.operator_name}</span>
            {node.operator_role && (
              <span className="text-slate-500">（{node.operator_role}）</span>
            )}
          </div>
        )}

        {node.action_time && (
          <div className="text-xs text-slate-500 mb-2">
            {formatDateTime(node.action_time)}
          </div>
        )}

        {/* 等待中状态 */}
        {node.status === "current" && node.assignee_name && (
          <div className="text-sm text-amber-400/80 mb-2">
            待 {node.assignee_name} 处理
            {waitingTime && (
              <span className="text-slate-500 ml-2">· 已等待 {waitingTime}</span>
            )}
          </div>
        )}

        {/* 待处理状态 */}
        {node.status === "pending" && node.assignee_name && (
          <div className="text-sm text-slate-500 mb-2">
            待 {node.assignee_name} 处理
          </div>
        )}

        {/* 委托信息 */}
        {node.delegate_info && (
          <div className="flex items-center gap-2 text-sm text-purple-400 mb-2">
            <Users className="h-3.5 w-3.5" />
            <span>
              {node.delegate_info.from} → 委托给 {node.delegate_info.to}
            </span>
          </div>
        )}

        {/* 审批意见 */}
        {node.comment && (
          <div className="bg-slate-800/50 rounded-lg p-3 mb-2">
            <div className="flex items-start gap-2">
              <MessageSquare className="h-4 w-4 text-slate-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-slate-300">{node.comment}</p>
            </div>
          </div>
        )}

        {/* 附件 */}
        {node.attachments && node.attachments?.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {(node.attachments || []).map((attachment, idx) => (
              <a
                key={idx}
                href={attachment.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 rounded text-xs text-slate-300 transition-colors"
              >
                <FileText className="h-3.5 w-3.5 text-slate-500" />
                {attachment.name}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * 将后端数据转换为时间线节点格式
 * @param {Object} instance - 审批实例详情
 * @returns {Array} 时间线节点数组
 */
export const transformToTimelineNodes = (instance) => {
  const nodes = [];

  // 1. 添加"提交申请"节点
  nodes.push({
    node_name: "提交申请",
    status: "submitted",
    operator_name: instance.initiator_name,
    action_time: instance.created_at,
  });

  // 2. 根据 tasks 构建审批节点
  if (instance.tasks && instance.tasks?.length > 0) {
    (instance.tasks || []).forEach((task, index) => {
      let status = "pending";

      if (task.status === "COMPLETED") {
        status = task.action === "REJECT" ? "rejected" : "completed";
      } else if (task.status === "PENDING") {
        // 判断是否是当前节点
        if (instance.current_node_id === task.node_id) {
          status = "current";
        } else {
          status = "pending";
        }
      }

      // 检查是否有委托
      let delegateInfo = null;
      if (task.delegate_from_name) {
        delegateInfo = {
          from: task.delegate_from_name,
          to: task.assignee_name,
        };
      }

      nodes.push({
        node_name: task.node_name || `审批节点 ${index + 1}`,
        status,
        operator_name: task.status === "COMPLETED" ? task.assignee_name : null,
        operator_role: task.assignee_role,
        assignee_name: task.status !== "COMPLETED" ? task.assignee_name : null,
        action_time: task.completed_at,
        created_at: task.created_at,
        comment: task.comment,
        attachments: task.attachments,
        delegate_info: delegateInfo,
      });
    });
  }

  // 3. 如果审批已完成，添加"审批完成"节点
  if (instance.status === "APPROVED") {
    nodes.push({
      node_name: "审批完成",
      status: "completed",
      action_time: instance.completed_at,
    });
  } else if (instance.status === "REJECTED") {
    nodes.push({
      node_name: "审批结束",
      status: "rejected",
      action_time: instance.completed_at,
    });
  } else if (instance.status === "WITHDRAWN") {
    nodes.push({
      node_name: "已撤回",
      status: "withdrawn",
      action_time: instance.withdrawn_at,
    });
  }

  return nodes;
};

/**
 * ApprovalTimeline 主组件
 */
const ApprovalTimeline = ({
  nodes = [],
  instance = null,
  className
}) => {
  // 如果传入 instance，自动转换为 nodes
  const timelineNodes = instance ? transformToTimelineNodes(instance) : nodes;

  if (!timelineNodes || timelineNodes.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        暂无审批记录
      </div>
    );
  }

  return (
    <div className={cn("space-y-0", className)}>
      <h3 className="text-white font-medium mb-4 flex items-center gap-2">
        <Clock className="h-4 w-4 text-slate-400" />
        审批进度
      </h3>
      <div className="pl-1">
        {(timelineNodes || []).map((node, index) => (
          <TimelineNode
            key={index}
            node={node}
            isLast={index === timelineNodes.length - 1}
            previousNodeTime={index > 0 ? timelineNodes[index - 1].action_time : null}
          />
        ))}
      </div>
    </div>
  );
};

export default ApprovalTimeline;
