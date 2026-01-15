/**
 * 📦 材料分析管理组件库
 * 统一导出所有材料分析相关组件和工具
 */

// 核心组件
export { MaterialStatsOverview } from './MaterialStatsOverview';
export { default as MaterialFilters } from './MaterialFilters';
export { default as MaterialDetailCard } from './MaterialDetailCard';

// 配置常量和工具
export {
  MATERIAL_STATUS,
  MATERIAL_TYPES,
  MATERIAL_PRIORITY,
  TEST_TYPES,
  COMPLIANCE_STANDARDS,
  SUPPLIER_LEVELS,
  IMPACT_LEVELS,
  ANALYSIS_PERIODS,
  RISK_INDICATORS,
  ANALYSIS_METRICS,
  MATERIAL_STATUS_OPTIONS,
  MATERIAL_TYPE_OPTIONS,
  MATERIAL_PRIORITY_OPTIONS,
  TEST_TYPE_OPTIONS,
  COMPLIANCE_STANDARD_OPTIONS,
  SUPPLIER_LEVEL_OPTIONS,
  IMPACT_LEVEL_OPTIONS,
  ANALYSIS_PERIOD_OPTIONS,
  RISK_INDICATOR_OPTIONS,
  ANALYSIS_METRIC_OPTIONS,
  getMaterialStatus,
  getMaterialType,
  getMaterialPriority,
  getTestType,
  getComplianceStandard,
  getSupplierLevel,
  getImpactLevel,
  calculateReadinessRate,
  assessMaterialRisk,
  formatTestResult,
  validateCompliance,
  isExpired,
  calculateAnalysisScore,
  generateAnalysisSuggestions
} from './materialAnalysisConstants';

// 默认导出
export { default as materialAnalysisConstants } from './materialAnalysisConstants';