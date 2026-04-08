import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TrendingUp } from 'lucide-react';
import DashboardStatCard from '../DashboardStatCard';

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(
        Object.entries(props).filter(
          ([key]) => !['whileHover', 'whileTap', 'initial', 'animate', 'exit', 'transition', 'variants'].includes(key)
        )
      );
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    },
  }),
}));

describe('DashboardStatCard', () => {
  const mockOnClick = vi.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  it('renders label, value and icon', () => {
    const { container } = render(
      <DashboardStatCard icon={TrendingUp} label="测试标签" value="100" />
    );

    expect(screen.getByText('测试标签')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('renders change and description when provided', () => {
    const { container } = render(
      <DashboardStatCard
        icon={TrendingUp}
        label="增长"
        value="100"
        change="+10%"
        trend="up"
        description="这是描述文本"
      />
    );

    expect(container.textContent).toContain('+10%');
    expect(screen.getByText('这是描述文本')).toBeInTheDocument();
  });

  it('falls back to unknown when value is empty string', () => {
    render(
      <DashboardStatCard icon={TrendingUp} label="空值" value="" />
    );

    expect(screen.getByText('空值')).toBeInTheDocument();
    expect(screen.getByText('unknown')).toBeInTheDocument();
  });

  it('falls back to unknown when value is zero', () => {
    render(
      <DashboardStatCard icon={TrendingUp} label="零值" value={0} />
    );

    expect(screen.getByText('零值')).toBeInTheDocument();
    expect(screen.getByText('unknown')).toBeInTheDocument();
  });

  it('shows loading skeleton instead of label text when loading', () => {
    const { container } = render(
      <DashboardStatCard icon={TrendingUp} label="加载中" value="100" loading />
    );

    expect(screen.queryByText('加载中')).not.toBeInTheDocument();
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('calls onClick when card is clicked', () => {
    render(
      <DashboardStatCard
        icon={TrendingUp}
        label="可点击"
        value="100"
        onClick={mockOnClick}
      />
    );

    fireEvent.click(screen.getByText('100'));
    expect(mockOnClick).toHaveBeenCalledTimes(1);
  });

  it('applies custom className to card', () => {
    const { container } = render(
      <DashboardStatCard
        icon={TrendingUp}
        label="自定义"
        value="100"
        className="custom-class"
      />
    );

    expect(container.querySelector('.custom-class')).toBeInTheDocument();
  });
});
