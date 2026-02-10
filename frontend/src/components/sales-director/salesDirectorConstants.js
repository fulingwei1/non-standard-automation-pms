/**
 * Sales Director Management Constants (legacy path)
 *
 * [DEPRECATED] Re-export shim for backward compatibility.
 * Canonical source: components/sales/salesConstants.js
 */

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
  formatPercentage,
  calculateRankingValidation,
  validateMetricConfig,
  TIME_PERIODS as PERIODS,
  SALES_STAGES as STAGES,
  CUSTOMER_TIERS as TIERS,
  SALES_REGIONS as REGIONS,
  PERFORMANCE_GRADES as GRADES,
  REPORT_TYPES as REPORTS,
  ALERT_TYPES as ALERTS,
  FORECAST_MODELS as MODELS,
  TREND_TYPES as TRENDS
} from "../sales/salesConstants";

export { formatCurrencySymbol as formatCurrency } from "../sales/salesConstants";
