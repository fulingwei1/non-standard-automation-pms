/**
 * Sidebar导航配置
 * 包含所有角色的导航组配置
 * 
 * 注意：此文件已拆分为多个模块文件，位于 sidebarConfig/ 目录下
 * 此文件仅用于向后兼容，重新导出所有配置
 */

// 从拆分后的模块重新导出所有配置
export { defaultNavGroups } from "./sidebarConfig/default";
export { engineerNavGroups, teamLeaderNavGroups } from "./sidebarConfig/engineer";
export { pmoDirectorNavGroups, pmcNavGroups } from "./sidebarConfig/pmo";
export {
  buyerNavGroups,
  procurementNavGroups,
  procurementManagerNavGroups
} from "./sidebarConfig/procurement";
export {
  productionManagerNavGroups,
  assemblerNavGroups,
  manufacturingDirectorNavGroups
} from "./sidebarConfig/production";
export {
  salesNavGroups,
  businessSupportNavGroups,
  presalesNavGroups
} from "./sidebarConfig/sales";
export { financeManagerNavGroups } from "./sidebarConfig/finance";
export {
  customerServiceManagerNavGroups,
  customerServiceEngineerNavGroups
} from "./sidebarConfig/customerService";
