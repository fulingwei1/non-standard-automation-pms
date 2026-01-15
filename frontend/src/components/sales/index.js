/**
 * Sales Components Export
 * 销售管理组件统一导出
 */

// 配置和常量
export * from "./salesConstants";

// 核心组件
export { SalesStatsOverview } from "./SalesStatsOverview";
export { SalesTeamManager } from "./SalesTeamManager";
export { default as SalesFunnel } from "./SalesFunnel";
export { default as CustomerCard } from "./CustomerCard";
export { default as OpportunityCard } from "./OpportunityCard";
export { default as PaymentTimeline, PaymentStats } from "./PaymentTimeline";
export { default as AdvantageProducts } from "./AdvantageProducts";

// TODO: 添加其他组件的导出
// export { CustomerManager } from "./CustomerManager";
// export { OpportunityManager } from "./OpportunityManager";
// export { SalesAnalytics } from "./SalesAnalytics";
