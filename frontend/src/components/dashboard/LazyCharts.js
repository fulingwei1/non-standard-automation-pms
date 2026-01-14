/**
 * LazyCharts - 预定义的懒加载图表组件
 * 用于工作台页面的图表懒加载
 */
import { createLazyChart } from "./LazyChart";

// 基础图表组件
export const LazyLineChart = createLazyChart(() =>
  import("../charts/LineChart").then((m) => ({ default: m.LineChart }))
);

export const LazyBarChart = createLazyChart(() =>
  import("../charts/BarChart").then((m) => ({ default: m.BarChart }))
);

export const LazyPieChart = createLazyChart(() =>
  import("../charts/PieChart").then((m) => ({ default: m.PieChart }))
);

export const LazyAreaChart = createLazyChart(() =>
  import("../charts/AreaChart").then((m) => ({ default: m.AreaChart }))
);

export const LazyGaugeChart = createLazyChart(() =>
  import("../charts/GaugeChart").then((m) => ({ default: m.GaugeChart }))
);

export const LazyDualAxesChart = createLazyChart(() =>
  import("../charts/DualAxesChart").then((m) => ({ default: m.DualAxesChart }))
);

export const LazyFunnelChart = createLazyChart(() =>
  import("../charts/FunnelChart").then((m) => ({ default: m.FunnelChart }))
);

// 业务图表组件
export const LazyProjectHealthChart = createLazyChart(() =>
  import("../charts/business/ProjectHealthChart").then((m) => ({
    default: m.ProjectHealthChart,
  }))
);

export const LazyCostAnalysisChart = createLazyChart(() =>
  import("../charts/business/CostAnalysisChart").then((m) => ({
    default: m.CostAnalysisChart,
  }))
);

export const LazyDeliveryRateChart = createLazyChart(() =>
  import("../charts/business/DeliveryRateChart").then((m) => ({
    default: m.DeliveryRateChart,
  }))
);

export const LazyUtilizationChart = createLazyChart(() =>
  import("../charts/business/UtilizationChart").then((m) => ({
    default: m.UtilizationChart,
  }))
);
