/**
 * 客户沟通配置常量
 * 沟通状态、类型、优先级、渠道等基础配置
 */

import { cn, formatDate, formatDateTime } from "../../utils";

export { cn, formatDate, formatDateTime };

// 沟通状态配置
export const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500", textColor: "text-slate-50" },
  PENDING_REVIEW: { label: "待审核", color: "bg-amber-500", textColor: "text-amber-50" },
  PENDING_APPROVAL: { label: "待审批", color: "bg-yellow-500", textColor: "text-yellow-50" },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500", textColor: "text-blue-50" },
  COMPLETED: { label: "已完成", color: "bg-green-500", textColor: "text-green-50" },
  CANCELLED: { label: "已取消", color: "bg-gray-500", textColor: "text-gray-50" },
  ON_HOLD: { label: "暂停", color: "bg-orange-500", textColor: "text-orange-50" },
  CLOSED: { label: "已关闭", color: "bg-slate-600", textColor: "text-slate-50" },
  OVERDUE: { label: "已逾期", color: "bg-red-500", textColor: "text-red-50" },
};

// 沟通类型配置
export const typeConfigs = {
  // 客户需求类
  REQUIREMENT_CLARIFICATION: { label: "需求澄清", color: "bg-blue-500", textColor: "text-blue-50", icon: "❓" },
  REQUIREMENT_CHANGE: { label: "需求变更", color: "bg-blue-600", textColor: "text-blue-50", icon: "🔄" },
  REQUIREMENT_CONFIRMATION: { label: "需求确认", color: "bg-blue-400", textColor: "text-blue-50", icon: "✅" },
  REQUIREMENT_REVIEW: { label: "需求评审", color: "bg-blue-700", textColor: "text-blue-50", icon: "👁️" },
  // 技术交流类
  TECHNICAL_DISCUSSION: { label: "技术讨论", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "💬" },
  TECHNICAL_PRESENTATION: { label: "技术演示", color: "bg-cyan-600", textColor: "text-cyan-50", icon: "🎯" },
  TECHNICAL_CONFIRMATION: { label: "技术确认", color: "bg-cyan-400", textColor: "text-cyan-50", icon: "📋" },
  // 项目进展类
  PROGRESS_UPDATE: { label: "进展更新", color: "bg-emerald-500", textColor: "text-emerald-50", icon: "📈" },
  MILESTONE_REVIEW: { label: "里程碑评审", color: "bg-emerald-600", textColor: "text-emerald-50", icon: "🚩" },
  PHASE_COMPLETION: { label: "阶段完成", color: "bg-emerald-400", textColor: "text-emerald-50", icon: "✨" },
  // 问题处理类
  ISSUE_NOTIFICATION: { label: "问题通知", color: "bg-red-500", textColor: "text-red-50", icon: "🚨" },
  ISSUE_STATUS_UPDATE: { label: "问题状态更新", color: "bg-red-600", textColor: "text-red-50", icon: "🔍" },
  ISSUE_RESOLUTION: { label: "问题解决", color: "bg-red-400", textColor: "text-red-50", icon: "🎉" },
  // 客户服务类
  SERVICE_REQUEST: { label: "服务请求", color: "bg-purple-500", textColor: "text-purple-50", icon: "🔧" },
  COMPLAINT_HANDLING: { label: "投诉处理", color: "bg-purple-600", textColor: "text-purple-50", icon: "😞" },
  FEEDBACK_COLLECTION: { label: "反馈收集", color: "bg-purple-400", textColor: "text-purple-50", icon: "📝" },
  SATISFACTION_SURVEY: { label: "满意度调查", color: "bg-purple-700", textColor: "text-purple-50", icon: "📊" },
  // 商务洽谈类
  QUOTE_DISCUSSION: { label: "报价洽谈", color: "bg-amber-500", textColor: "text-amber-50", icon: "💰" },
  CONTRACT_NEGOTIATION: { label: "合同洽谈", color: "bg-amber-600", textColor: "text-amber-50", icon: "📄" },
  PAYMENT_DISCUSSION: { label: "付款讨论", color: "bg-amber-400", textColor: "text-amber-50", icon: "💳" },
  // 售后支持类
  AFTER_SALES_SUPPORT: { label: "售后支持", color: "bg-green-500", textColor: "text-green-50", icon: "🛟" },
  MAINTENANCE_NOTIFICATION: { label: "维保通知", color: "bg-green-600", textColor: "text-green-50", icon: "🔧" },
  WARRANTY_CLAIM: { label: "保修申请", color: "bg-green-400", textColor: "text-green-50", icon: "🛡️" },
  // 会议相关
  MEETING_INVITATION: { label: "会议邀请", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "📅" },
  MEETING_SUMMARY: { label: "会议纪要", color: "bg-indigo-600", textColor: "text-indigo-50", icon: "📝" },
  ACTION_ITEM_TRACKING: { label: "行动计划跟踪", color: "bg-indigo-400", textColor: "text-indigo-50", icon: "📋" },
  // 其他
  OTHER: { label: "其他", color: "bg-gray-500", textColor: "text-gray-50", icon: "📌" },
};

// 优先级配置
export const priorityConfigs = {
  LOW: { label: "低", color: "bg-slate-500", textColor: "text-slate-50", value: 1, icon: "🟢" },
  MEDIUM: { label: "中", color: "bg-blue-500", textColor: "text-blue-50", value: 2, icon: "🔵" },
  HIGH: { label: "高", color: "bg-orange-500", textColor: "text-orange-50", value: 3, icon: "🟠" },
  URGENT: { label: "紧急", color: "bg-red-500", textColor: "text-red-50", value: 4, icon: "🔴" },
  CRITICAL: { label: "关键", color: "bg-purple-500", textColor: "text-purple-50", value: 5, icon: "⚡" },
};

// 沟通渠道配置
export const channelConfigs = {
  EMAIL: { label: "邮件", color: "bg-blue-500", textColor: "text-blue-50", icon: "✉️" },
  PHONE: { label: "电话", color: "bg-green-500", textColor: "text-green-50", icon: "📞" },
  WECHAT: { label: "微信", color: "bg-green-600", textColor: "text-green-50", icon: "💬" },
  MEETING: { label: "会议", color: "bg-purple-500", textColor: "text-purple-50", icon: "👥" },
  VISIT: { label: "拜访", color: "bg-amber-500", textColor: "text-amber-50", icon: "🏢" },
  VIDEO_CALL: { label: "视频会议", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "🎥" },
  SYSTEM: { label: "系统消息", color: "bg-slate-500", textColor: "text-slate-50", icon: "💻" },
  OTHER: { label: "其他", color: "bg-gray-500", textColor: "text-gray-50", icon: "📌" },
};

// 响应时间配置
export const responseTimeConfigs = {
  IMMEDIATE: { label: "即时", color: "bg-red-500", textColor: "text-red-50", hours: 0 },
  WITHIN_1_HOUR: { label: "1小时内", color: "bg-orange-500", textColor: "text-orange-50", hours: 1 },
  WITHIN_4_HOURS: { label: "4小时内", color: "bg-amber-500", textColor: "text-amber-50", hours: 4 },
  WITHIN_24_HOURS: { label: "24小时内", color: "bg-blue-500", textColor: "text-blue-50", hours: 24 },
  WITHIN_48_HOURS: { label: "48小时内", color: "bg-green-500", textColor: "text-green-50", hours: 48 },
  WITHIN_1_WEEK: { label: "1周内", color: "bg-slate-500", textColor: "text-slate-50", hours: 168 },
};

// 消息类型配置
export const messageTypeConfigs = {
  TEXT: { label: "文本", color: "bg-slate-500", textColor: "text-slate-50" },
  DOCUMENT: { label: "文档", color: "bg-blue-500", textColor: "text-blue-50", icon: "📄" },
  IMAGE: { label: "图片", color: "bg-green-500", textColor: "text-green-50", icon: "🖼️" },
  ATTACHMENT: { label: "附件", color: "bg-purple-500", textColor: "text-purple-50", icon: "📎" },
  LINK: { label: "链接", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "🔗" },
  TEMPLATE: { label: "模板", color: "bg-amber-500", textColor: "text-amber-50", icon: "📋" },
};

// 消息状态配置
export const messageStatusConfigs = {
  SENDING: { label: "发送中", color: "bg-blue-500", textColor: "text-blue-50" },
  SENT: { label: "已发送", color: "bg-green-500", textColor: "text-green-50" },
  DELIVERED: { label: "已送达", color: "bg-emerald-500", textColor: "text-emerald-50" },
  READ: { label: "已读", color: "bg-purple-500", textColor: "text-purple-50" },
  FAILED: { label: "发送失败", color: "bg-red-500", textColor: "text-red-50" },
  PENDING: { label: "待发送", color: "bg-amber-500", textColor: "text-amber-50" },
};
