/**
 * ECN 组件导出
 * 统一导出所有 ECN 相关组件
 */

// 配置和常量
export * from './ecnConstants';

// 组件
export { default as ECNDetailHeader } from './ECNDetailHeader';
export { default as ECNInfoTab } from './ECNInfoTab';
export { ECNEvaluationsTab } from './ECNEvaluationsTab';
export { ECNApprovalsTab } from './ECNApprovalsTab';
export { ECNTasksTab } from './ECNTasksTab.simple';
export { ECNImpactAnalysisTab } from './ECNImpactAnalysisTab';
export { ECNLogsTab } from './ECNLogsTab';

// TODO: 添加其他组件的导出
// export { default as ECNTasksTab } from './ECNTasksTab';
// export { default as ECNImpactAnalysisTab } from './ECNImpactAnalysisTab';
// export { default as ECNLogsTab } from './ECNLogsTab';
