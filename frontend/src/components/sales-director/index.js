/**
 * Sales Director Components Index
 * 销售总监组件统一导出
 */

// 核心组件
export { default as SalesDirectorStatsOverview } from './SalesDirectorStatsOverview';
export { default as SalesTeamPerformance } from './SalesTeamPerformance';

// 配置和工具函数
export {
  DEFAULT_STATS,
  RANKING_PRIMARY_KEYS,
  RANKING_METRIC_LIBRARY,
  TIME_PERIODS,
  SALES_STAGES,
  CUSTOMER_TIERS,
  SALES_REGIONS,
  PERFORMANCE_GRADES,
  REPORT_TYPES,
  ALERT_TYPES,
  FORECAST_MODELS,
  TREND_TYPES,
  getPeriodRange,
  toISODate,
  calculateTrend,
  getPerformanceGrade,
  getCustomerTier,
  formatCurrency,
  formatPercentage,
  calculateRankingValidation,
  validateMetricConfig,
} from './salesDirectorConstants';

// 工具函数别名
export {
  TIME_PERIODS as PERIODS,
  SALES_STAGES as STAGES,
  CUSTOMER_TIERS as TIERS,
  SALES_REGIONS as REGIONS,
  PERFORMANCE_GRADES as GRADES,
  REPORT_TYPES as REPORTS,
  ALERT_TYPES as ALERTS,
  FORECAST_MODELS as MODELS,
  TREND_TYPES as TRENDS,
} from './salesDirectorConstants';