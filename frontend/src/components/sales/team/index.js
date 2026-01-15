/**
 * Sales Team Components - 统一导出入口
 * 销售团队管理相关组件的集中导出
 */

// ==================== 常量配置 ====================
export {
  formatDateInput,
  getDefaultDateRange,
  getWeekDateRange,
  QUICK_RANGE_PRESETS,
  formatCurrency,
  followUpTypeLabels,
  formatFollowUpType,
  formatTimeAgo,
  formatDateTime,
  formatAutoRefreshTime,
  DEFAULT_RANKING_METRICS,
  FALLBACK_RANKING_FIELDS,
  statusConfig,
  getAchievementStatus,
  DEFAULT_TEAM_STATS,
  isAmountMetric,
  isPercentageMetric,
  buildMetricDetailMap,
  formatMetricValueDisplay,
  formatMetricScoreDisplay,
} from "./constants/salesTeamConstants";

// ==================== 工具函数 ====================
export {
  normalizeDistribution,
  transformTeamMember,
  aggregateTargets,
  calculateTeamStats,
} from "./utils/salesTeamTransformers";

// ==================== 自定义 Hooks ====================
export { useSalesTeamFilters } from "./hooks/useSalesTeamFilters";
export { useSalesTeamData } from "./hooks/useSalesTeamData";
export { useSalesTeamRanking } from "./hooks/useSalesTeamRanking";

// ==================== 组件 ====================
export { default as TeamStatsCards } from "./components/TeamStatsCards";
export { default as TeamFilters } from "./components/TeamFilters";
export { default as TeamRankingBoard } from "./components/TeamRankingBoard";
export { default as TeamMemberCard } from "./components/TeamMemberCard";
export { default as TeamMemberList } from "./components/TeamMemberList";
export { default as TeamMemberDetailDialog } from "./components/TeamMemberDetailDialog";
