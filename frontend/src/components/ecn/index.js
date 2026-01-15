/**
 * ECN 组件导出
 * 统一导出所有 ECN 相关组件
 */

// 配置和常量
export * from "./ecnConstants";
import * as ecnManagementConstants from "./ecnManagementConstants";
export { ecnManagementConstants };
export { formatDate } from "../../lib/utils";

// 详情页面组件
export { ECNBasicInfo } from "./ECNBasicInfo";
export { ECNEvaluationManager } from "./ECNEvaluationManager";
export { ECNApprovalFlow } from "./ECNApprovalFlow";
export { ECNTaskBoard } from "./ECNTaskBoard";
export { ECNImpactAnalysis } from "./ECNImpactAnalysis";
export { ECNChangeLog } from "./ECNChangeLog";

// 管理页面组件
export { ECNListHeader } from "./ECNListHeader";
export { ECNStatsCards } from "./ECNStatsCards";
export { ECNListTable } from "./ECNListTable";
export { ECNBatchActions } from "./ECNBatchActions";
export { ECNCreateDialog } from "./ECNCreateDialog";
