/**
 * Mock @ant-design/plots 图表组件
 * 用于测试环境中避免真实图表渲染
 */

// Mock 所有图表组件，返回简单的 div 用于测试
const createMockChart = (chartType) => {
  return function MockChart({ data = [], ..._props }) {
    return (
      <div
        data-testid={`${chartType}-chart`}
        data-chart-type={chartType}
        data-points={data.length}
      >
        {chartType} Chart ({data.length} data points)
      </div>
    );
  };
};

export const Line = createMockChart('line');
export const Bar = createMockChart('bar');
export const Area = createMockChart('area');
export const Pie = createMockChart('pie');
export const Column = createMockChart('column');
export const Scatter = createMockChart('scatter');
export const Rose = createMockChart('rose');
export const Radar = createMockChart('radar');
export const DualAxes = createMockChart('dual-axes');
export const Gauge = createMockChart('gauge');
export const Liquid = createMockChart('liquid');
export const Bullet = createMockChart('bullet');
export const Funnel = createMockChart('funnel');
export const Waterfall = createMockChart('waterfall');
export const WordCloud = createMockChart('word-cloud');
export const Sunburst = createMockChart('sunburst');
export const Treemap = createMockChart('treemap');
export const Heatmap = createMockChart('heatmap');
export const Box = createMockChart('box');
export const Violin = createMockChart('violin');
export const Stock = createMockChart('stock');
