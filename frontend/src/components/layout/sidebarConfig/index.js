/**
 * Sidebar导航配置聚合导出
 * 从各个模块文件重新导出所有导航组配置
 */

// 默认导航组
export { defaultNavGroups } from "./default";

// 工程师相关
export { engineerNavGroups, teamLeaderNavGroups } from "./engineer";

// PMO相关
export { pmoDirectorNavGroups, pmcNavGroups } from "./pmo";

// 采购相关
export {
  buyerNavGroups,
  procurementNavGroups,
  procurementManagerNavGroups
} from "./procurement";

// 生产相关
export {
  productionNavGroups,
  productionManagerNavGroups,
  assemblerNavGroups,
  manufacturingDirectorNavGroups
} from "./production";

// 销售相关
export {
  salesNavGroups,
  businessSupportNavGroups,
  presalesNavGroups
} from "./sales";

// 财务相关
export { financeManagerNavGroups } from "./finance";

// 客服相关
export {
  customerServiceManagerNavGroups,
  customerServiceEngineerNavGroups
} from "./customerService";
