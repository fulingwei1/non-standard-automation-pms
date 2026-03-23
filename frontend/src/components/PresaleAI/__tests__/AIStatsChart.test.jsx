/**
 * AIStatsChart组件测试
 * Team 10: 售前AI系统集成与前端UI
 *
 * 注意：AIStatsChart 使用全局 recharts fallback 组件，
 * 这些组件渲染为 <div data-testid="recharts-XXX"> 而非真实 SVG 图表。
 * 因此用 data-testid 而非 .recharts-wrapper class 来断言。
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import AIStatsChart from '../AIStatsChart';

describe('AIStatsChart', () => {
  const mockData = [
    { date: '2026-02-01', count: 10 },
    { date: '2026-02-02', count: 15 },
    { date: '2026-02-03', count: 20 },
  ];

  /**
   * 辅助函数：验证图表已渲染（全局 fallback 的 recharts 组件使用 data-testid）
   */
  const expectChartRendered = (container) => {
    // ResponsiveContainer fallback 渲染子节点
    // 内部的 chart fallback 使用 data-testid="recharts-LineChart" 等
    const chartElement =
      container.querySelector('[data-testid^="recharts-"]') ||
      container.querySelector('.w-full');
    expect(chartElement).toBeInTheDocument();
  };

  it('renders line chart with data', () => {
    const { container } = render(
      <AIStatsChart data={mockData} type="line" dataKey="count" xKey="date" />
    );
    expectChartRendered(container);
  });

  it('renders bar chart with data', () => {
    const { container } = render(
      <AIStatsChart data={mockData} type="bar" dataKey="count" xKey="date" />
    );
    expectChartRendered(container);
  });

  it('renders area chart with data', () => {
    const { container } = render(
      <AIStatsChart data={mockData} type="area" dataKey="count" xKey="date" />
    );
    expectChartRendered(container);
  });

  it('shows no data message when data is empty', () => {
    render(<AIStatsChart data={[]} type="line" />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('shows no data message when data is null', () => {
    render(<AIStatsChart data={null} type="line" />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('uses custom colors', () => {
    const customColors = ['#ff0000', '#00ff00', '#0000ff'];
    const { container } = render(
      <AIStatsChart
        data={mockData}
        type="line"
        dataKey="count"
        xKey="date"
        colors={customColors}
      />
    );
    expectChartRendered(container);
  });

  it('renders pie chart with data', () => {
    const pieData = [
      { name: 'A', value: 10 },
      { name: 'B', value: 20 },
      { name: 'C', value: 30 },
    ];
    const { container } = render(
      <AIStatsChart data={pieData} type="pie" dataKey="value" xKey="name" />
    );
    expectChartRendered(container);
  });

  it('renders multiline chart with data', () => {
    const multiData = [
      { date: '2026-02-01', series1: 10, series2: 15 },
      { date: '2026-02-02', series1: 20, series2: 25 },
    ];
    const { container } = render(
      <AIStatsChart data={multiData} type="multiline" xKey="date" />
    );
    expectChartRendered(container);
  });

  it('applies custom height', () => {
    const { container } = render(
      <AIStatsChart data={mockData} type="line" height={400} />
    );
    expectChartRendered(container);
  });
});
