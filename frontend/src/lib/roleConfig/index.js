/**
 * 角色配置模块统一导出
 * 
 * 模块结构:
 * ├── roleInfo.js        # 角色信息配置和基础函数
 * ├── demoUsers.js       # 演示账户配置
 * ├── navigation.js      # 导航配置
 * ├── permissions.js     # 权限检查函数
 * ├── strategyAccess.js  # 战略模块访问权限
 * └── roleUtils.js       # 角色工具函数
 */

// 角色信息
export { ROLE_INFO, getRoleInfo } from './roleInfo';

// 演示账户
export { DEMO_USERS } from './demoUsers';

// 导航配置
export { getNavForRole } from './navigation';

// 权限检查
export {
  hasProcurementAccess,
  hasFinanceAccess,
  hasProductionAccess,
  hasProjectReviewAccess,
} from './permissions';

// 战略访问权限
export {
  hasStrategyAccess,
  getStrategyAccessLevel,
} from './strategyAccess';

// 角色工具函数
export {
  isEngineerRole,
  isManagerRole,
} from './roleUtils';
