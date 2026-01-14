/**
 * HR组件统一导出入口
 */

// 配置和常量
export * from './hrConstants';

// 基础组件
export { default as StatCard } from './StatCard';
export { default as HRDashboardOverview } from './HRDashboardOverview';

// 标签页组件
export { HRRecruitmentTab } from './HRRecruitmentTab';
export { HREmployeesTab } from './HREmployeesTab';
export { HRPerformanceTab } from './HRPerformanceTab';
export { HRAttendanceTab } from './HRAttendanceTab';
export { HRTrainingTab } from './HRTrainingTab';
export { HRRelationsTab } from './HRRelationsTab';

// TODO: 添加其他HR组件的导出
