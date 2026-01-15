/**
 * Sales Team Transformers - 销售团队数据转换工具
 * 负责将后端数据转换为前端组件所需格式
 */

import {
  getAchievementStatus,
} from "../constants/salesTeamConstants";

// ==================== 数据归一化 ====================

/**
 * 归一化分布数据
 */
export const normalizeDistribution = (distribution = []) => {
  if (!Array.isArray(distribution)) return [];
  return distribution.map((item, index) => {
    const rawValue = Number(item.value ?? item.count ?? 0);
    const rawPercentage = Number(item.percentage ?? item.rate ?? 0);
    return {
      label: item.label || item.category || `分类${index + 1}`,
      value: Number.isFinite(rawValue) ? rawValue : 0,
      percentage: Number.isFinite(rawPercentage)
        ? Number(rawPercentage.toFixed(1))
        : 0,
    };
  });
};

// ==================== 团队成员数据转换 ====================

/**
 * 转换单个团队成员数据
 * 将后端返回的原始数据转换为前端组件使用的格式
 */
export const transformTeamMember = (member = {}) => {
  const personalTargets =
    member.personal_targets || member.personalTargets || null;
  const monthlyTargetInfo = personalTargets?.monthly;
  const yearlyTargetInfo = personalTargets?.yearly;
  const regionName =
    member.region || member.department_name || member.department || "未分配";

  // 月度目标数据
  const monthlyTarget = Number(
    member.monthly_target ??
      monthlyTargetInfo?.target_value ??
      member.target_amount ??
      member.contract_amount ??
      0,
  );
  const monthlyAchieved = Number(
    member.monthly_actual ??
      monthlyTargetInfo?.actual_value ??
      member.collection_amount ??
      member.contract_amount ??
      0,
  );
  const monthlyCompletion = Number(
    member.monthly_completion_rate ??
      monthlyTargetInfo?.completion_rate ??
      (monthlyTarget > 0 ? (monthlyAchieved / monthlyTarget) * 100 : 0),
  );

  // 年度目标数据
  const yearTarget = Number(
    member.year_target ?? yearlyTargetInfo?.target_value ?? monthlyTarget * 12,
  );
  const yearAchieved = Number(
    member.year_actual ??
      yearlyTargetInfo?.actual_value ??
      member.contract_amount ??
      member.collection_amount ??
      0,
  );
  const yearCompletion = Number(
    member.year_completion_rate ??
      yearlyTargetInfo?.completion_rate ??
      (yearTarget > 0 ? (yearAchieved / yearTarget) * 100 : 0),
  );

  const normalizedMonthlyCompletion = Number.isFinite(monthlyCompletion)
    ? monthlyCompletion
    : 0;
  const normalizedYearCompletion = Number.isFinite(yearCompletion)
    ? yearCompletion
    : 0;

  // 最近跟进记录
  const rawFollowUp = member.recent_follow_up || member.recentFollowUp;
  const recentFollowUp = rawFollowUp
    ? {
        leadName: rawFollowUp.lead_name || rawFollowUp.leadName,
        leadCode: rawFollowUp.lead_code || rawFollowUp.leadCode,
        followUpType: rawFollowUp.follow_up_type || rawFollowUp.followUpType,
        content: rawFollowUp.content,
        createdAt: rawFollowUp.created_at || rawFollowUp.createdAt,
      }
    : null;

  // 客户分布
  const customerDistribution = normalizeDistribution(
    member.customer_distribution || member.customerDistribution || [],
  );
  const customerTotal =
    member.customer_total ??
    member.customerTotal ??
    customerDistribution.reduce((sum, item) => sum + (item.value || 0), 0);

  // 跟进统计
  const followUpStatsRaw =
    member.follow_up_stats || member.followUpStats || member.followUpStatistics;
  const followUpStats = {
    call: Number(followUpStatsRaw?.CALL || 0),
    email: Number(followUpStatsRaw?.EMAIL || 0),
    visit: Number(followUpStatsRaw?.VISIT || 0),
    meeting: Number(followUpStatsRaw?.MEETING || 0),
    other: Number(followUpStatsRaw?.OTHER || 0),
    total: Number(followUpStatsRaw?.total || 0),
  };
  if (!followUpStats.total) {
    followUpStats.total =
      followUpStats.call +
      followUpStats.email +
      followUpStats.visit +
      followUpStats.meeting +
      followUpStats.other;
  }

  // 线索质量
  const leadQualityRaw =
    member.lead_quality_stats ||
    member.leadQualityStats ||
    member.leadQuality ||
    {};
  const leadQuality = {
    totalLeads: Number(leadQualityRaw.total_leads || leadQualityRaw.totalLeads || member.lead_count || 0),
    convertedLeads: Number(
      leadQualityRaw.converted_leads || leadQualityRaw.convertedLeads || 0,
    ),
    modeledLeads: Number(
      leadQualityRaw.modeled_leads || leadQualityRaw.modeledLeads || 0,
    ),
    conversionRate: Number(
      leadQualityRaw.conversion_rate ||
        leadQualityRaw.conversionRate ||
        0,
    ),
    modelingRate: Number(
      leadQualityRaw.modeling_rate || leadQualityRaw.modelingRate || 0,
    ),
    avgCompleteness: Number(
      leadQualityRaw.avg_completeness ||
        leadQualityRaw.avgCompleteness ||
        0,
    ),
  };

  // 商机统计
  const opportunityStatsRaw =
    member.opportunity_stats ||
    member.opportunityStats ||
    member.opportunityMetrics ||
    {};
  const opportunityStats = {
    opportunityCount: Number(
      opportunityStatsRaw.opportunity_count ||
        opportunityStatsRaw.opportunityCount ||
        member.opportunity_count ||
        0,
    ),
    pipelineAmount: Number(
      opportunityStatsRaw.pipeline_amount ||
        opportunityStatsRaw.pipelineAmount ||
        0,
    ),
    avgEstMargin: Number(
      opportunityStatsRaw.avg_est_margin ||
        opportunityStatsRaw.avgEstMargin ||
        0,
    ),
  };

  return {
    id: member.user_id,
    name: member.user_name || member.username || "未知成员",
    role: member.role || "销售",
    department: member.department_name || "未知部门",
    region: regionName,
    email: member.email || "",
    phone: member.phone || "",
    monthlyTarget,
    monthlyAchieved,
    achievementRate: Number(normalizedMonthlyCompletion.toFixed(1)),
    yearTarget,
    yearAchieved,
    yearProgress: Number(normalizedYearCompletion.toFixed(1)),
    activeProjects: member.contract_count ?? member.opportunity_count ?? 0,
    newCustomers: member.new_customers ?? member.newCustomers ?? 0,
    status: getAchievementStatus(
      normalizedMonthlyCompletion || normalizedYearCompletion,
    ),
    joinDate: member.join_date || "",
    lastActivity: member.last_activity || "",
    leadCount: member.lead_count || 0,
    opportunityCount: member.opportunity_count || 0,
    contractCount: member.contract_count || 0,
    contractAmount: member.contract_amount || 0,
    collectionAmount: member.collection_amount || 0,
    personalTargets,
    recentFollowUp,
    customerDistribution,
    customerTotal,
    followUpStats,
    leadQuality,
    opportunityStats,
    pipelineAmount: opportunityStats.pipelineAmount,
    avgEstMargin: opportunityStats.avgEstMargin,
  };
};

// ==================== 团队统计计算 ====================

/**
 * 聚合目标数据
 */
export const aggregateTargets = (targets = []) => {
  if (!targets.length) return null;
  const totals = targets.reduce(
    (acc, target) => {
      const targetValue = Number(target.target_value ?? 0);
      const actualValue = Number(target.actual_value ?? 0);
      return {
        target: acc.target + targetValue,
        actual: acc.actual + actualValue,
      };
    },
    { target: 0, actual: 0 },
  );
  return {
    targetValue: totals.target,
    actualValue: totals.actual,
    completionRate:
      totals.target > 0 ? (totals.actual / totals.target) * 100 : 0,
  };
};

/**
 * 计算团队统计数据
 */
export const calculateTeamStats = (members, summary) => {
  const fallbackTarget = members.reduce(
    (sum, m) => sum + (m.monthlyTarget || 0),
    0,
  );
  const fallbackAchieved = members.reduce(
    (sum, m) => sum + (m.monthlyAchieved || 0),
    0,
  );
  const fallbackProjects = members.reduce(
    (sum, m) => sum + (m.activeProjects || 0),
    0,
  );
  const fallbackNewCustomers = members.reduce(
    (sum, m) => sum + (m.newCustomers || 0),
    0,
  );
  const fallbackCustomerTotal = members.reduce(
    (sum, m) => sum + (m.customerTotal || 0),
    0,
  );

  const targetFromSummary = summary?.team_target_value;
  const achievedFromSummary = summary?.team_actual_value;
  const completionFromSummary = summary?.team_completion_rate;
  const projectsFromSummary = summary?.total_opportunities;
  const customersFromSummary =
    summary?.customer_total ??
    summary?.converted_leads ??
    summary?.total_leads ??
    fallbackCustomerTotal;
  const newCustomersSummary =
    summary?.customer_new_this_month ??
    summary?.new_customers ??
    fallbackNewCustomers ??
    0;

  const totalMembers = members.length;
  const totalTarget = targetFromSummary ?? fallbackTarget;
  const totalAchieved = achievedFromSummary ?? fallbackAchieved;
  const avgAchievementRate =
    completionFromSummary ??
    (totalTarget > 0 ? (totalAchieved / totalTarget) * 100 : 0);

  return {
    totalMembers,
    activeMembers:
      members.filter((m) => m.status !== "poor").length || totalMembers,
    totalTarget,
    totalAchieved,
    avgAchievementRate: Number((avgAchievementRate || 0).toFixed(1)),
    totalProjects: projectsFromSummary ?? fallbackProjects,
    totalCustomers: customersFromSummary ?? 0,
    newCustomersThisMonth:
      newCustomersSummary ??
      fallbackNewCustomers ??
      0,
  };
};
