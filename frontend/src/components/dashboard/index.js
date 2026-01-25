/**
 * Dashboard Components - 工作台组件库
 * 统一的工作台组件导出
 */

export { default as DashboardStatCard } from "./DashboardStatCard";
export { default as DashboardLayout } from "./DashboardLayout";
export { BaseDashboard, default as BaseDashboardDefault } from "./BaseDashboard";
export { useDashboardData, useMultipleDashboardData } from "./useDashboardData";
export { default as LazyChart, createLazyChart } from "./LazyChart";
export { default as VirtualizedList } from "./VirtualizedList";
export { default as VirtualizedProjectList } from "./VirtualizedProjectList";

// 导出懒加载图表组件
export * from "./LazyCharts";
