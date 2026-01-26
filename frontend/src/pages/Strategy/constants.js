/**
 * 战略管理模块常量配置
 */
import {
  Target,
  TrendingUp,
  Users,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Clock,
  Activity,
  BarChart3,
  PieChart,
  Calendar,
  FileText,
  Award,
} from "lucide-react";

// BSC 四维度配置
export const BSC_DIMENSIONS = {
  FINANCIAL: {
    code: "FINANCIAL",
    name: "财务维度",
    description: "股东满意度和财务绩效",
    icon: TrendingUp,
    color: "#52c41a",
    bgColor: "bg-green-50",
    textColor: "text-green-600",
    borderColor: "border-green-200",
  },
  CUSTOMER: {
    code: "CUSTOMER",
    name: "客户维度",
    description: "客户满意度和市场表现",
    icon: Users,
    color: "#1890ff",
    bgColor: "bg-blue-50",
    textColor: "text-blue-600",
    borderColor: "border-blue-200",
  },
  INTERNAL: {
    code: "INTERNAL",
    name: "内部运营维度",
    description: "内部流程效率和质量",
    icon: Activity,
    color: "#fa8c16",
    bgColor: "bg-orange-50",
    textColor: "text-orange-600",
    borderColor: "border-orange-200",
  },
  LEARNING: {
    code: "LEARNING",
    name: "学习成长维度",
    description: "组织能力和员工发展",
    icon: BookOpen,
    color: "#722ed1",
    bgColor: "bg-purple-50",
    textColor: "text-purple-600",
    borderColor: "border-purple-200",
  },
};

// 健康度等级配置
export const HEALTH_LEVELS = {
  EXCELLENT: {
    label: "优秀",
    color: "#52c41a",
    bgColor: "bg-green-100",
    textColor: "text-green-700",
    icon: CheckCircle2,
    range: "≥90%",
  },
  GOOD: {
    label: "良好",
    color: "#1890ff",
    bgColor: "bg-blue-100",
    textColor: "text-blue-700",
    icon: CheckCircle2,
    range: "70-89%",
  },
  WARNING: {
    label: "预警",
    color: "#faad14",
    bgColor: "bg-yellow-100",
    textColor: "text-yellow-700",
    icon: AlertCircle,
    range: "50-69%",
  },
  DANGER: {
    label: "危险",
    color: "#f5222d",
    bgColor: "bg-red-100",
    textColor: "text-red-700",
    icon: XCircle,
    range: "<50%",
  },
};

// 战略状态配置
export const STRATEGY_STATUS = {
  DRAFT: {
    label: "草稿",
    color: "default",
    icon: FileText,
  },
  ACTIVE: {
    label: "生效中",
    color: "success",
    icon: CheckCircle2,
  },
  ARCHIVED: {
    label: "已归档",
    color: "default",
    icon: Clock,
  },
};

// KPI 数据源类型
export const KPI_DATA_SOURCE_TYPES = {
  MANUAL: {
    label: "手动录入",
    description: "由责任人手动填报数据",
  },
  AUTO: {
    label: "自动采集",
    description: "从系统模块自动获取数据",
  },
  FORMULA: {
    label: "公式计算",
    description: "通过公式计算得出",
  },
};

// KPI IPOOC 类型
export const IPOOC_TYPES = {
  INPUT: {
    label: "投入指标",
    description: "衡量资源投入",
    color: "#1890ff",
  },
  PROCESS: {
    label: "过程指标",
    description: "衡量执行过程",
    color: "#fa8c16",
  },
  OUTPUT: {
    label: "产出指标",
    description: "衡量直接产出",
    color: "#52c41a",
  },
  OUTCOME: {
    label: "结果指标",
    description: "衡量最终成效",
    color: "#722ed1",
  },
};

// KPI 方向
export const KPI_DIRECTIONS = {
  UP: {
    label: "越大越好",
    icon: TrendingUp,
  },
  DOWN: {
    label: "越小越好",
    icon: TrendingUp,
    rotate: true,
  },
};

// 年度重点工作状态
export const ANNUAL_WORK_STATUS = {
  NOT_STARTED: {
    label: "未开始",
    color: "default",
    icon: Clock,
  },
  IN_PROGRESS: {
    label: "进行中",
    color: "processing",
    icon: Activity,
  },
  COMPLETED: {
    label: "已完成",
    color: "success",
    icon: CheckCircle2,
  },
  DELAYED: {
    label: "已延期",
    color: "error",
    icon: AlertCircle,
  },
};

// VOC 来源
export const VOC_SOURCES = {
  CUSTOMER: "客户需求",
  MARKET: "市场分析",
  INTERNAL: "内部改进",
  STRATEGY: "战略规划",
  COMPETITION: "竞争分析",
};

// CSF 导出方法
export const CSF_DERIVATION_METHODS = {
  VISION: "愿景分解",
  BENCHMARK: "标杆对比",
  GAP_ANALYSIS: "差距分析",
  SWOT: "SWOT分析",
  VALUE_CHAIN: "价值链分析",
};

// 审视类型
export const REVIEW_TYPES = {
  MONTHLY: {
    label: "月度审视",
    icon: Calendar,
  },
  QUARTERLY: {
    label: "季度审视",
    icon: BarChart3,
  },
  YEARLY: {
    label: "年度审视",
    icon: Award,
  },
};

// 日历事件类型
export const CALENDAR_EVENT_TYPES = {
  MONTHLY_REVIEW: {
    label: "月度经营分析会",
    color: "#1890ff",
  },
  QUARTERLY_REVIEW: {
    label: "季度战略审视会",
    color: "#fa8c16",
  },
  YEARLY_PLANNING: {
    label: "年度战略规划会",
    color: "#722ed1",
  },
  KPI_COLLECTION: {
    label: "KPI 数据采集",
    color: "#52c41a",
  },
  OTHER: {
    label: "其他",
    color: "#8c8c8c",
  },
};

// 工具函数：获取健康度配置
export const getHealthConfig = (level) => {
  return HEALTH_LEVELS[level?.toUpperCase()] || HEALTH_LEVELS.WARNING;
};

// 工具函数：获取维度配置
export const getDimensionConfig = (dimension) => {
  return BSC_DIMENSIONS[dimension?.toUpperCase()] || BSC_DIMENSIONS.FINANCIAL;
};

// 工具函数：根据分数获取健康等级
export const getHealthLevelFromScore = (score) => {
  if (score === null || score === undefined) return null;
  if (score >= 90) return "EXCELLENT";
  if (score >= 70) return "GOOD";
  if (score >= 50) return "WARNING";
  return "DANGER";
};

// 工具函数：格式化百分比
export const formatPercent = (value, decimals = 1) => {
  if (value === null || value === undefined) return "-";
  return `${Number(value).toFixed(decimals)}%`;
};

// 图表颜色
export const CHART_COLORS = {
  primary: "#1890ff",
  success: "#52c41a",
  warning: "#faad14",
  danger: "#f5222d",
  purple: "#722ed1",
  cyan: "#13c2c2",
  dimensions: ["#52c41a", "#1890ff", "#fa8c16", "#722ed1"],
};
