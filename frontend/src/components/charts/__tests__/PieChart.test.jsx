import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import PieChart from '../PieChart';

vi.mock('@ant-design/plots', () => ({
  Pie: ({ onReady, ...props }) => {
    if (onReady) {
      const plot = { on: vi.fn() };
      onReady(plot);
    }
    return <div data-testid="ant-pie" data-props={JSON.stringify(props)} />;
  },
}));

describe('PieChart', () => {
  const mockData = [
    { type: '产品A', value: 300 },
    { type: '产品B', value: 200 },
    { type: '产品C', value: 150 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chart component with data', () => {
    render(<PieChart data={mockData} />);
    expect(screen.getByTestId('ant-pie')).toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(<PieChart data={mockData} title="销售分布" />);
    expect(screen.getByText('销售分布')).toBeInTheDocument();
  });

  it('does not render title when not provided', () => {
    render(<PieChart data={mockData} />);
    expect(screen.queryByText('销售分布')).not.toBeInTheDocument();
  });

  it('shows empty state for empty data', () => {
    render(<PieChart data={[]} />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
    expect(screen.queryByTestId('ant-pie')).not.toBeInTheDocument();
  });

  it('shows empty state for undefined data', () => {
    render(<PieChart data={undefined} />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('shows empty state for null data', () => {
    render(<PieChart data={null} />);
    expect(screen.getByText('暂无数据')).toBeInTheDocument();
  });

  it('uses default height', () => {
    render(<PieChart data={mockData} />);
    const props = JSON.parse(screen.getByTestId('ant-pie').getAttribute('data-props'));
    expect(props.height).toBe(300);
  });

  it('applies custom height', () => {
    render(<PieChart data={mockData} height={400} />);
    const props = JSON.parse(screen.getByTestId('ant-pie').getAttribute('data-props'));
    expect(props.height).toBe(400);
  });

  it('passes custom fields and donut config', () => {
    render(
      <PieChart
        data={mockData}
        angleField="amount"
        colorField="category"
        donut
        innerRadius={0.7}
      />
    );
    const props = JSON.parse(screen.getByTestId('ant-pie').getAttribute('data-props'));
    expect(props.angleField).toBe('amount');
    expect(props.colorField).toBe('category');
    expect(props.innerRadius).toBe(0.7);
  });

  it('disables labels when showLabel is false', () => {
    render(<PieChart data={mockData} showLabel={false} />);
    const props = JSON.parse(screen.getByTestId('ant-pie').getAttribute('data-props'));
    expect(props.label).toBe(false);
  });

  it('passes custom colors', () => {
    render(<PieChart data={mockData} colors={['#111111', '#222222']} />);
    const props = JSON.parse(screen.getByTestId('ant-pie').getAttribute('data-props'));
    expect(props.color).toEqual(['#111111', '#222222']);
  });

  it('renders donut statistic when provided', () => {
    render(
      <PieChart
        data={mockData}
        donut
        statistic={{ title: '总计', content: '650' }}
      />
    );
    const props = JSON.parse(screen.getByTestId('ant-pie').getAttribute('data-props'));
    expect(props.statistic.title.content).toBe('总计');
    expect(props.statistic.content.content).toBe('650');
  });

  it('matches snapshot for basic chart', () => {
    const { container } = render(<PieChart data={mockData} title="产品销售分布" />);
    expect(container).toMatchSnapshot();
  });

  it('matches snapshot for empty state', () => {
    const { container } = render(<PieChart data={[]} />);
    expect(container).toMatchSnapshot();
  });
});
