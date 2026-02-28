/**
 * Issue Management Constants
 * 问题管理系统常量配置
 * 包含问题状态、严重程度、优先级、分类等配置
 */

import { List, Kanban, BarChart3 } from "lucide-react";

// ==================== 问题状态配置 ====================
export const issueStatusConfig = {
  OPEN: {
    label: "待处理",
    value: "OPEN",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "AlertCircle",
    order: 1
  },
  PROCESSING: {
    label: "处理中",
    value: "PROCESSING",
    color: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
    icon: "Clock",
    order: 2
  },
  RESOLVED: {
    label: "已解决",
    value: "RESOLVED",
    color: "text-green-400 bg-green-400/10 border-green-400/30",
    icon: "CheckCircle2",
    order: 3
  },
  CLOSED: {
    label: "已关闭",
    value: "CLOSED",
    color: "text-gray-400 bg-gray-400/10 border-gray-400/30",
    icon: "CheckCircle2",
    order: 4
  },
  DEFERRED: {
    label: "已延期",
    value: "DEFERRED",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    icon: "XCircle",
    order: 5
  }
};

// ==================== 问题严重程度配置 ====================
export const issueSeverityConfig = {
  CRITICAL: {
    label: "严重",
    value: "CRITICAL",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    level: 4,
    description: "严重影响系统运行或用户体验"
  },
  MAJOR: {
    label: "主要",
    value: "MAJOR",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    level: 3,
    description: "影响部分功能或性能"
  },
  MINOR: {
    label: "次要",
    value: "MINOR",
    color: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
    level: 2,
    description: "轻微影响，不影响主要功能"
  },
  TRIVIAL: {
    label: "微不足道",
    value: "TRIVIAL",
    color: "text-gray-400 bg-gray-400/10 border-gray-400/30",
    level: 1,
    description: "几乎没有影响的问题"
  }
};

// ==================== 问题优先级配置 ====================
export const issuePriorityConfig = {
  URGENT: {
    label: "紧急",
    value: "URGENT",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    level: 4,
    timeframe: "24小时内"
  },
  HIGH: {
    label: "高",
    value: "HIGH",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    level: 3,
    timeframe: "3天内"
  },
  MEDIUM: {
    label: "中",
    value: "MEDIUM",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    level: 2,
    timeframe: "1周内"
  },
  LOW: {
    label: "低",
    value: "LOW",
    color: "text-gray-400 bg-gray-400/10 border-gray-400/30",
    level: 1,
    timeframe: "1个月内"
  }
};

// ==================== 问题分类配置 ====================
export const issueCategoryConfig = {
  PROJECT: {
    label: "项目问题",
    value: "PROJECT",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    icon: "Folder",
    description: "项目执行过程中的问题"
  },
  TASK: {
    label: "任务问题",
    value: "TASK",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "CheckSquare",
    description: "具体任务执行中的问题"
  },
  ACCEPTANCE: {
    label: "验收问题",
    value: "ACCEPTANCE",
    color: "text-green-400 bg-green-400/10 border-green-400/30",
    icon: "ClipboardCheck",
    description: "验收测试中发现的问题"
  },
  QUALITY: {
    label: "质量问题",
    value: "QUALITY",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    icon: "Shield",
    description: "产品质量相关问题"
  },
  TECHNICAL: {
    label: "技术问题",
    value: "TECHNICAL",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    icon: "Cpu",
    description: "技术实现相关问题"
  },
  PROCESS: {
    label: "流程问题",
    value: "PROCESS",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "GitBranch",
    description: "工作流程相关问题"
  },
  RESOURCE: {
    label: "资源问题",
    value: "RESOURCE",
    color: "text-cyan-400 bg-cyan-400/10 border-cyan-400/30",
    icon: "Package",
    description: "资源分配或不足问题"
  },
  COMMUNICATION: {
    label: "沟通问题",
    value: "COMMUNICATION",
    color: "text-indigo-400 bg-indigo-400/10 border-indigo-400/30",
    icon: "MessageSquare",
    description: "团队沟通协调问题"
  }
};

// ==================== 问题来源配置 ====================
export const issueSourceConfig = {
  INTERNAL: {
    label: "内部发现",
    value: "INTERNAL",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "Building"
  },
  CUSTOMER: {
    label: "客户反馈",
    value: "CUSTOMER",
    color: "text-green-400 bg-green-400/10 border-green-400/30",
    icon: "Users"
  },
  TESTING: {
    label: "测试发现",
    value: "TESTING",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    icon: "Flask"
  },
  MONITORING: {
    label: "监控告警",
    value: "MONITORING",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    icon: "Activity"
  },
  AUDIT: {
    label: "审计发现",
    value: "AUDIT",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    icon: "FileSearch"
  }
};

// ==================== 解决方案类型配置 ====================
export const issueSolutionTypeConfig = {
  FIX: {
    label: "修复",
    value: "FIX",
    color: "text-green-400 bg-green-400/10 border-green-400/30",
    icon: "Wrench"
  },
  WORKAROUND: {
    label: "临时解决方案",
    value: "WORKAROUND",
    color: "text-yellow-400 bg-yellow-400/10 border-yellow-400/30",
    icon: "Zap"
  },
  CONFIG_CHANGE: {
    label: "配置变更",
    value: "CONFIG_CHANGE",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "Settings"
  },
  DOCUMENTATION: {
    label: "文档更新",
    value: "DOCUMENTATION",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    icon: "FileText"
  },
  PROCESS_IMPROVEMENT: {
    label: "流程改进",
    value: "PROCESS_IMPROVEMENT",
    color: "text-indigo-400 bg-indigo-400/10 border-indigo-400/30",
    icon: "TrendingUp"
  }
};

// ==================== 默认统计数据配置 ====================
export const DEFAULT_ISSUE_STATS = {
  total: 0,
  open: 0,
  processing: 0,
  resolved: 0,
  closed: 0,
  blocking: 0,
  overdue: 0,
  byStatus: {},
  bySeverity: {},
  byCategory: {},
  byAssignee: {},
  createdToday: 0,
  resolvedToday: 0,
  avgResolutionTime: 0,
  slaCompliance: 0
};

// ==================== 视图模式配置 ====================
export const ISSUE_VIEW_MODES = [
{
  value: "list",
  label: "列表视图",
  icon: List,
  description: "传统的表格列表形式展示"
},
{
  value: "kanban",
  label: "看板视图",
  icon: Kanban,
  description: "按状态分组的看板形式展示"
},
{
  value: "analytics",
  label: "分析视图",
  icon: BarChart3,
  description: "统计图表和分析数据"
}];


// ==================== 排序选项配置 ====================
export const ISSUE_SORT_OPTIONS = [
{ value: "created_desc", label: "创建时间（最新）" },
{ value: "created_asc", label: "创建时间（最早）" },
{ value: "updated_desc", label: "更新时间（最新）" },
{ value: "priority_desc", label: "优先级（高到低）" },
{ value: "severity_desc", label: "严重程度（高到低）" },
{ value: "title_asc", label: "标题（A-Z）" },
{ value: "title_desc", label: "标题（Z-A）" }];


// ==================== SLA 配置 ====================
export const ISSUE_SLA_CONFIG = {
  CRITICAL: { response: 1, resolution: 24 }, // 小时
  MAJOR: { response: 4, resolution: 72 },
  MINOR: { response: 8, resolution: 168 },
  TRIVIAL: { response: 24, resolution: 720 }
};

// ==================== 工具函数 ====================

// 获取问题状态配置
export const getIssueStatusConfig = (status) => {
  return issueStatusConfig[status] || issueStatusConfig.OPEN;
};

// 获取问题严重程度配置
export const getIssueSeverityConfig = (severity) => {
  return issueSeverityConfig[severity] || issueSeverityConfig.MINOR;
};

// 获取问题优先级配置
export const getIssuePriorityConfig = (priority) => {
  return issuePriorityConfig[priority] || issuePriorityConfig.MEDIUM;
};

// 获取问题分类配置
export const getIssueCategoryConfig = (category) => {
  return issueCategoryConfig[category] || issueCategoryConfig.TECHNICAL;
};

// 获取问题来源配置
export const getIssueSourceConfig = (source) => {
  return issueSourceConfig[source] || issueSourceConfig.INTERNAL;
};

// 获取解决方案类型配置
export const getIssueSolutionTypeConfig = (type) => {
  return issueSolutionTypeConfig[type] || issueSolutionTypeConfig.FIX;
};

// 计算问题紧急程度（结合严重程度和优先级）
export const calculateIssueUrgency = (severity, priority) => {
  const severityLevel = getIssueSeverityConfig(severity).level;
  const priorityLevel = getIssuePriorityConfig(priority).level;
  return Math.max(severityLevel, priorityLevel);
};

// 检查问题是否逾期
export const isIssueOverdue = (issue) => {
  if (!issue.dueDate || ['RESOLVED', 'CLOSED'].includes(issue.status)) {
    return false;
  }
  return new Date(issue.dueDate) < new Date();
};

// 检查问题是否阻塞
export const isIssueBlocking = (issue) => {
  return issue.isBlocking || issue.priority === 'URGENT' || issue.severity === 'CRITICAL';
};

// 计算 SLA 合规性
export const calculateSLACompliance = (issue) => {
  if (!issue.createdAt || ['RESOLVED', 'CLOSED'].includes(issue.status)) {
    return null;
  }

  const created = new Date(issue.createdAt);
  const now = new Date();
  const hoursElapsed = (now - created) / (1000 * 60 * 60);

  const sla = ISSUE_SLA_CONFIG[issue.severity];
  if (!sla) {return null;}

  return {
    response: hoursElapsed <= sla.response,
    resolution: hoursElapsed <= sla.resolution,
    responseHours: hoursElapsed,
    responseLimit: sla.response,
    resolutionLimit: sla.resolution
  };
};

// 格式化解决时间
export const formatResolutionTime = (hours) => {
  if (hours < 1) {
    return `${Math.round(hours * 60)}分钟`;
  } else if (hours < 24) {
    return `${Math.round(hours)}小时`;
  } else {
    return `${Math.round(hours / 24)}天`;
  }
};

// 获取状态操作按钮
export const getIssueStatusActions = (currentStatus) => {
  const actions = [];

  switch (currentStatus) {
    case 'OPEN':
      actions.push(
        { label: '开始处理', action: 'start', color: 'bg-blue-600' },
        { label: '关闭问题', action: 'close', color: 'bg-gray-600' }
      );
      break;
    case 'PROCESSING':
      actions.push(
        { label: '标记解决', action: 'resolve', color: 'bg-green-600' },
        { label: '延期处理', action: 'defer', color: 'bg-purple-600' }
      );
      break;
    case 'RESOLVED':
      actions.push(
        { label: '验证通过', action: 'verify', color: 'bg-emerald-600' },
        { label: '重新打开', action: 'reopen', color: 'bg-orange-600' }
      );
      break;
    case 'DEFERRED':
      actions.push(
        { label: '重新处理', action: 'reopen', color: 'bg-blue-600' }
      );
      break;
  }

  return actions;
};

// 验证问题数据
export const validateIssueData = (data) => {
  const errors = [];

  if (!data.title || data.title.trim() === '') {
    errors.push('问题标题不能为空');
  }

  if (!data.description || data.description.trim() === '') {
    errors.push('问题描述不能为空');
  }

  if (!data.category) {
    errors.push('问题分类必须选择');
  }

  if (!data.severity) {
    errors.push('严重程度必须选择');
  }

  if (!data.priority) {
    errors.push('优先级必须选择');
  }

  if (data.dueDate && new Date(data.dueDate) <= new Date()) {
    errors.push('截止日期必须是未来时间');
  }

  return errors;
};

// 导出配置对象
export const issueConstants = {
  issueStatusConfig,
  issueSeverityConfig,
  issuePriorityConfig,
  issueCategoryConfig,
  issueSourceConfig,
  issueSolutionTypeConfig,
  DEFAULT_ISSUE_STATS,
  ISSUE_VIEW_MODES,
  ISSUE_SORT_OPTIONS,
  ISSUE_SLA_CONFIG
};