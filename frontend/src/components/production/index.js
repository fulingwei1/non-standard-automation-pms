/**
 * Production Components Index
 * 生产组件统一导出
 */

// 核心组件
export { default as ProductionStatsOverview } from './ProductionStatsOverview';
export { default as ProductionLineManager } from './ProductionLineManager';

// 配置和工具函数
export {
  PRODUCTION_PLAN_STATUS,
  WORK_ORDER_STATUS,
  PRODUCTION_LINE_STATUS,
  EQUIPMENT_STATUS,
  WORK_SHIFT,
  PRODUCTION_PRIORITY,
  QUALITY_GRADE,
  PROCESS_TYPE,
  PRODUCTION_TYPE,
  ALERT_LEVEL,
  ALERT_STATUS,
  RANKING_TYPE,
  PRODUCTION_METRICS,
  TIME_RANGE_FILTERS,
  PLAN_STATUS,
  ORDER_STATUS,
  LINE_STATUS,
  EQUIPMENT,
  SHIFT,
  TYPE,
  PROCESS,
  ALERT,
  ALERT_STATE,
  RANKING,
  METRICS,
  TIME_RANGE,
} from './productionConstants';

// 工具函数
export {
  getStatusColor,
  getStatusLabel,
  getPriorityColor,
  getPriorityLabel,
  getQualityGrade,
  getAlertLevelConfig,
  getAlertStatusConfig,
  calculateCompletionRate,
  calculateQualityRate,
  calculateOEE,
  formatProductionData,
  validateProductionData,
} from './productionConstants';