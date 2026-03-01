/**
 * AI 辅助战略管理 API 服务
 */
import { api } from "./client.js";

// ============================================
// AI 战略分析
// ============================================
export const aiStrategyApi = {
  /**
   * AI 战略分析 - SWOT 分析、战略定位、核心竞争力
   */
  analyze: (data) =>
    api.post("/ai-strategy/analyze", null, {
      params: {
        company_info: data.companyInfo,
        financial_data: data.financialData || "",
        market_info: data.marketInfo || "",
        challenges: data.challenges || "",
      },
    }),

  /**
   * AI 战略分解 - BSC 四维度 CSF + KPI
   */
  decompose: (data) =>
    api.post("/ai-strategy/decompose", null, {
      params: {
        strategy_name: data.strategyName,
        strategy_vision: data.strategyVision,
        strategy_year: data.strategyYear,
        industry: data.industry || "非标自动化测试设备",
      },
    }),

  /**
   * AI 年度经营计划 - 生成重点工作
   */
  annualPlan: (data) =>
    api.post("/ai-strategy/annual-plan", null, {
      params: {
        company_info: data.companyInfo,
        year: data.year,
        revenue_target: data.revenueTarget,
        strategy_id: data.strategyId || "",
        additional_info: data.additionalInfo || "",
      },
    }),

  /**
   * AI 部门工作分解 - 生成部门 OKR
   */
  deptObjectives: (data) =>
    api.post("/ai-strategy/dept-objectives", null, {
      params: {
        department_name: data.departmentName,
        department_role: data.departmentRole,
        year: data.year,
        strategy_id: data.strategyId || "",
      },
    }),

  /**
   * 应用 AI 生成结果到数据库
   */
  apply: (type, data, strategyId) =>
    api.post("/ai-strategy/apply", {
      type,
      data,
      strategy_id: strategyId || null,
    }),
};

// ============================================
// 便捷方法
// ============================================

/**
 * 获取 BSC 维度标签
 */
export const getDimensionLabel = (dimension) => {
  const labels = {
    FINANCIAL: "财务维度",
    CUSTOMER: "客户维度",
    INTERNAL: "内部流程",
    LEARNING: "学习与成长",
  };
  return labels[dimension] || dimension;
};

/**
 * 获取维度颜色
 */
export const getDimensionColor = (dimension) => {
  const colors = {
    FINANCIAL: "text-red-400 bg-red-500/10 border-red-500/20",
    CUSTOMER: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    INTERNAL: "text-green-400 bg-green-500/10 border-green-500/20",
    LEARNING: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  };
  return colors[dimension] || "text-gray-400 bg-gray-500/10 border-gray-500/20";
};

/**
 * 获取优先级标签
 */
export const getPriorityLabel = (priority) => {
  const labels = {
    HIGH: "高优先级",
    MEDIUM: "中优先级",
    LOW: "低优先级",
  };
  return labels[priority] || priority;
};

/**
 * 获取优先级颜色
 */
export const getPriorityColor = (priority) => {
  const colors = {
    HIGH: "text-red-400 bg-red-500/10 border-red-500/20",
    MEDIUM: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
    LOW: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  };
  return colors[priority] || "text-gray-400 bg-gray-500/10 border-gray-500/20";
};

/**
 * 获取 VOC 来源标签
 */
export const getVocSourceLabel = (source) => {
  const labels = {
    SHAREHOLDER: "股东声音",
    CUSTOMER: "客户声音",
    EMPLOYEE: "员工声音",
    COMPLIANCE: "合规要求",
  };
  return labels[source] || source;
};
