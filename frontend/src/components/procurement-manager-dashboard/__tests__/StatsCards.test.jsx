import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatsCards from '../StatsCards';

describe('StatsCards', () => {
  const mockStats = {
    pendingApprovals: 12,
    inTransitOrders: 8,
    shortageAlerts: 5,
    activeSuppliers: 48,
  };

  it('renders all stat card titles', () => {
    render(<StatsCards stats={mockStats} />);

    expect(screen.getByText('待审批订单')).toBeInTheDocument();
    expect(screen.getByText('在途订单')).toBeInTheDocument();
    expect(screen.getByText('缺料预警')).toBeInTheDocument();
    expect(screen.getByText('在用供应商')).toBeInTheDocument();
  });

  it('displays correct stat values', () => {
    render(<StatsCards stats={mockStats} />);

    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('8')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('48')).toBeInTheDocument();
  });

  it('renders fixed helper texts', () => {
    render(<StatsCards stats={mockStats} />);

    expect(screen.getByText('3 项紧急')).toBeInTheDocument();
    expect(screen.getByText('+5 本周')).toBeInTheDocument();
    expect(screen.getByText('-2 较上周')).toBeInTheDocument();
    expect(screen.getByText('+2 本月')).toBeInTheDocument();
  });

  it('falls back to zero when stats are missing', () => {
    render(<StatsCards stats={undefined} />);

    expect(screen.getAllByText('0')).toHaveLength(4);
  });

  it('renders responsive grid layout', () => {
    const { container } = render(<StatsCards stats={mockStats} />);

    const grid = container.querySelector('.grid');
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4');
  });
});
