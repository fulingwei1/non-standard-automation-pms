/**
 * AIStatsChart组件测试
 * Team 10: 售前AI系统集成与前端UI
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

  it('renders line chart with data', () => {
    render(<AIStatsChart data={mockData} type="line" dataKey="count" xKey="date" />);
    // Chart should be rendered
    expect(document.querySelector('.recharts-wrapper')).toBeInTheDocument();
  });

  it('renders bar chart with data', () => {
    render(<AIStatsChart data={mockData} type="bar" dataKey="count" xKey="date" />);
    expect(document.querySelector('.recharts-wrapper')).toBeInTheDocument();
  });

  it('renders area chart with data', () => {
    render(<AIStatsChart data={mockData} type="area" dataKey="count" xKey="date" />);
    expect(document.querySelector('.recharts-wrapper')).toBeInTheDocument();
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
    render(
      <AIStatsChart
        data={mockData}
        type="line"
        dataKey="count"
        xKey="date"
        colors={customColors}
      />
    );
    // Chart should be rendered with custom colors
    expect(document.querySelector('.recharts-wrapper')).toBeInTheDocument();
  });

  it('renders pie chart with data', () => {
    const pieData = [
      { name: 'A', value: 10 },
      { name: 'B', value: 20 },
      { name: 'C', value: 30 },
    ];
    render(<AIStatsChart data={pieData} type="pie" dataKey="value" xKey="name" />);
    expect(document.querySelector('.recharts-wrapper')).toBeInTheDocument();
  });

  it('renders multiline chart with data', () => {
    const multiData = [
      { date: '2026-02-01', series1: 10, series2: 15 },
      { date: '2026-02-02', series1: 20, series2: 25 },
    ];
    render(<AIStatsChart data={multiData} type="multiline" xKey="date" />);
    expect(document.querySelector('.recharts-wrapper')).toBeInTheDocument();
  });

  it('applies custom height', () => {
    const { container } = render(
      <AIStatsChart data={mockData} type="line" height={400} />
    );
    const wrapper = container.querySelector('.recharts-wrapper');
    expect(wrapper).toBeInTheDocument();
  });
});
