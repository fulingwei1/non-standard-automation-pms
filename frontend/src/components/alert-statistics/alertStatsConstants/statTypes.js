/**
 * 告警统计类型配置 - Alert Stat Types
 * 包含告警类型、级别、状态、类型的统计配置定义
 */

// ==================== 告警统计类型配置 ====================
export const ALERT_STAT_TYPES = {
 OVERVIEW: {
 label: "总体概览",
 description: "告警总体统计信息",
  icon: "BarChart3",
 metrics: ["total", "pending", "resolved", "processing", "ignored"]
 },
 BY_LEVEL: {
  label: "按级别统计",
 description: "按告警级别分类统计",
  icon: "AlertTriangle",
   metrics: ["critical", "high", "medium", "low", "info"]
  },
 BY_STATUS: {
 label: "按状态统计",
  description: "按告警状态分类统计",
  icon: "Circle",
 metrics: ["pending", "acknowledged", "assigned", "in_progress", "resolved", "closed", "ignored"]
 },
 BY_TYPE: {
 label: "按类型统计",
 description: "按告警类型分类统计",
 icon: "Tag",
 metrics: ["project", "system", "business", "operation", "quality"]
  },
 BY_TIME: {
  label: "时间趋势",
 description: "告警时间趋势分析",
  icon: "Clock",
  metrics: ["daily", "weekly", "monthly", "hourly"]
 },
 BY_PROJECT: {
 label: "项目分布",
  description: "按项目维度告警分布",
  icon: "FolderOpen",
 metrics: ["active", "delayed", "completed", "on_hold"]
  },
 BY_RULE: {
 label: "规则统计",
 description: "按告警规则统计",
 icon: "Settings",
 metrics: ["active_rules", "triggered_rules", "efficiency", "accuracy"]
 },
 BY_RESPONSE: {
 label: "响应统计",
 description: "告警响应时效统计",
  icon: "Timer",
 metrics: ["avg_response", "avg_resolution", "sla_compliance", "escalation_rate"]
  }
};

// ==================== 告警级别统计配置 ====================
export const ALERT_LEVEL_STATS = {
 CRITICAL: {
  label: "严重",
 value: 5,
 color: "rgb(239, 68, 68)",
 bgColor: "rgba(239, 68, 68, 0.1)",
  borderColor: "rgb(239, 68, 68)",
  priority: 1,
  targetResponseTime: 5,
 targetResolutionTime: 1,
  trendDirection: "down"
 },
 HIGH: {
 label: "高",
 value: 4,
  color: "rgb(251, 146, 60)",
  bgColor: "rgba(251, 146, 60, 0.1)",
 borderColor: "rgb(251, 146, 60)",
 priority: 2,
  targetResponseTime: 30,
 targetResolutionTime: 4,
 trendDirection: "stable"
 },
 MEDIUM: {
 label: "中",
 value: 3,
  color: "rgb(245, 158, 11)",
 bgColor: "rgba(245, 158, 11, 0.1)",
  borderColor: "rgb(245, 158, 11)",
  priority: 3,
  targetResponseTime: 120,
  targetResolutionTime: 24,
  trendDirection: "up"
 },
 LOW: {
  label: "低",
 value: 2,
 color: "rgb(59, 130, 246)",
 bgColor: "rgba(59, 130, 246, 0.1)",
  borderColor: "rgb(59, 130, 246)",
 priority: 4,
 targetResponseTime: 480,
 targetResolutionTime: 72,
 trendDirection: "stable"
 },
 INFO: {
   label: "信息",
 value: 1,
  color: "rgb(107, 114, 128)",
  bgColor: "rgba(107, 114, 128, 0.1)",
 borderColor: "rgb(107, 114, 128)",
 priority: 5,
 targetResponseTime: 1440,
  targetResolutionTime: 168,
 trendDirection: "down"
 }
};

// ==================== 告警状态统计配置 ====================
export const ALERT_STATUS_STATS = {
 PENDING: {
 label: "待处理",
 value: 1,
  color: "rgb(245, 158, 11)",
 bgColor: "rgba(245, 158, 11, 0.1)",
 borderColor: "rgb(245, 158, 11)",
 urgency: "high"
  },
 ACKNOWLEDGED: {
 label: "已确认",
 value: 2,
 color: "rgb(59, 130, 246)",
 bgColor: "rgba(59, 130, 246, 0.1)",
 borderColor: "rgb(59, 130, 246)",
 urgency: "medium"
 },
 ASSIGNED: {
 label: "已分配",
 value: 3,
 color: "rgb(147, 51, 234)",
 bgColor: "rgba(147, 51, 234, 0.1)",
  borderColor: "rgb(147, 51, 234)",
 urgency: "medium"
 },
 IN_PROGRESS: {
  label: "处理中",
 value: 4,
 color: "rgb(79, 70, 229)",
  bgColor: "rgba(79, 70, 229, 0.1)",
 borderColor: "rgb(79, 70, 229)",
 urgency: "medium"
 },
 RESOLVED: {
  label: "已解决",
 value: 5,
 color: "rgb(34, 197, 94)",
 bgColor: "rgba(34, 197, 94, 0.1)",
 borderColor: "rgb(34, 197, 94)",
 urgency: "low"
 },
 CLOSED: {
  label: "已关闭",
 value: 6,
 color: "rgb(107, 114, 128)",
  bgColor: "rgba(107, 114, 128, 0.1)",
 borderColor: "rgb(107, 114, 128)",
  urgency: "low"
 },
 IGNORED: {
 label: "已忽略",
 value: 7,
 color: "rgb(156, 163, 175)",
 bgColor: "rgba(156, 163, 175, 0.1)",
 borderColor: "rgb(156, 163, 175)",
 urgency: "none"
 }
};

// ==================== 告警类型统计配置 ====================
export const ALERT_TYPE_STATS = {
 PROJECT: {
 label: "项目预警",
  category: "项目管理",
  icon: "\u{1F4C1}",
 color: "rgb(59, 130, 246)",
 bgColor: "rgba(59, 130, 246, 0.1)",
  borderColor: "rgb(59, 130, 246)",
  subtypes: {
 DELAY: { label: "进度延期", color: "rgb(239, 68, 68)" },
 BUDGET: { label: "预算超支", color: "rgb(245, 158, 11)" },
 MILESTONE: { label: "里程碑逾期", color: "rgb(251, 146, 60)" },
 RESOURCE: { label: "资源不足", color: "rgb(34, 197, 94)" },
  QUALITY: { label: "质量风险", color: "rgb(147, 51, 234)" }
  }
 },
 SYSTEM: {
  label: "系统告警",
 category: "系统监控",
 icon: "\u{1F4BB}",
  color: "rgb(147, 51, 234)",
 bgColor: "rgba(147, 51, 234, 0.1)",
  borderColor: "rgb(147, 51, 234)",
 subtypes: {
  PERFORMANCE: { label: "性能异常", color: "rgb(239, 68, 68)" },
  SECURITY: { label: "安全威胁", color: "rgb(239, 68, 68)" },
 CAPACITY: { label: "容量不足", color: "rgb(245, 158, 11)" },
   BACKUP: { label: "备份失败", color: "rgb(251, 146, 60)" },
   CONNECTIVITY: { label: "连接中断", color: "rgb(239, 68, 68)" }
 }
 },
 BUSINESS: {
  label: "业务告警",
 category: "业务监控",
 icon: "\u{1F4CA}",
 color: "rgb(34, 197, 94)",
   bgColor: "rgba(34, 197, 94, 0.1)",
 borderColor: "rgb(34, 197, 94)",
 subtypes: {
   SALES: { label: "销售下滑", color: "rgb(251, 146, 60)" },
 INVENTORY: { label: "库存异常", color: "rgb(239, 68, 68)" },
 CUSTOMER: { label: "客户投诉", color: "rgb(245, 158, 11)" },
  FINANCIAL: { label: "财务异常", color: "rgb(239, 68, 68)" },
  COMPLIANCE: { label: "合规风险", color: "rgb(147, 51, 234)" }
  }
 },
 OPERATION: {
 label: "运营告警",
 category: "运营管理",
 icon: "\u{2699}\u{FE0F}",
 color: "rgb(245, 158, 11)",
  bgColor: "rgba(245, 158, 11, 0.1)",
 borderColor: "rgb(245, 158, 11)",
 subtypes: {
  EQUIPMENT: { label: "设备故障", color: "rgb(239, 68, 68)" },
 MAINTENANCE: { label: "维护超期", color: "rgb(251, 146, 60)" },
  SAFETY: { label: "安全事故", color: "rgb(239, 68, 68)" },
 COMPLAINT: { label: "客诉激增", color: "rgb(245, 158, 11)" },
 STAFF: { label: "人员异常", color: "rgb(147, 51, 234)" }
 }
  },
 QUALITY: {
  label: "质量告警",
  category: "质量管理",
 icon: "\u{1F6E1}\u{FE0F}",
 color: "rgb(147, 51, 234)",
  bgColor: "rgba(147, 51, 234, 0.1)",
 borderColor: "rgb(147, 51, 234)",
  subtypes: {
  DEFECT: { label: "质量缺陷", color: "rgb(239, 68, 68)" },
 INSPECTION: { label: "检验失败", color: "rgb(245, 158, 11)" },
 CERTIFICATION: { label: "认证问题", color: "rgb(251, 146, 60)" },
  RECALL: { label: "产品召回", color: "rgb(239, 68, 68)" },
  COMPLIANCE: { label: "标准违规", color: "rgb(147, 51, 234)" }
 }
 }
};
