/**
 * 风险管理组件 - 统一导出
 */

export { default as CreateRiskDialog } from "./CreateRiskDialog";
export { default as AssessRiskDialog } from "./AssessRiskDialog";
export { default as ResponseRiskDialog } from "./ResponseRiskDialog";
export { default as StatusRiskDialog } from "./StatusRiskDialog";
export { default as CloseRiskDialog } from "./CloseRiskDialog";
export { default as RiskDetailDialog } from "./RiskDetailDialog";
export {
  getRiskLevelBadge,
  getStatusBadge,
  getProbabilityLabel,
  getImpactLabel
} from "./riskUtils";
