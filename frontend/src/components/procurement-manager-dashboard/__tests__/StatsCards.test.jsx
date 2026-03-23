import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatsCards from '../StatsCards';

describe('StatsCards', () => {
  const mockStats = {
    pendingApprovals: 12,
    inTransitOrders: 8,
    lowStockWarnings: 5,
    activeSuppliers: 48,
  };

  describe('Basic Rendering', () => {
    it('renders all stat cards', () => {
      render(<StatsCards stats={mockStats} />);
      expect(screen.getByText('待审批订单')).toBeInTheDocument();
      expect(screen.getByText('在途订单')).toBeInTheDocument();
      expect(screen.getByText('缺料预警')).toBeInTheDocument();
      expect(screen.getByText('活跃供应商')).toBeInTheDocument();
    });

    it('displays correct stat values', () => {
      render(<StatsCards stats={mockStats} />);
      expect(screen.getByText('12')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('48')).toBeInTheDocument();
    });

    it('displays icons for each card', () => {
      const { container } = render(<StatsCards stats={mockStats} />);
      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(4);
    });
  });

  describe('Empty Stats', () => {
    it('handles undefined stats', () => {
      render(<StatsCards stats={undefined} />);
      expect(screen.getByText('待审批订单')).toBeInTheDocument();
      expect(screen.getAllByText('0')).toHaveLength(4);
    });

    it('handles null stats', () => {
      render(<StatsCards stats={null} />);
      expect(screen.getAllByText('0')).toHaveLength(4);
    });

    it('handles empty object stats', () => {
      render(<StatsCards stats={{}} />);
      expect(screen.getAllByText('0')).toHaveLength(4);
    });

    it('handles partial stats', () => {
      render(<StatsCards stats={{ pendingApprovals: 5 }} />);
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getAllByText('0')).toHaveLength(3);
    });
  });

  describe('Additional Information', () => {
    it('displays urgent items indicator', () => {
      render(<StatsCards stats={mockStats} />);
      expect(screen.getByText(/紧急/)).toBeInTheDocument();
    });

    it('displays trend indicators', () => {
      render(<StatsCards stats={mockStats} />);
      expect(screen.getByText(/本周/)).toBeInTheDocument();
    });
  });

  describe('Layout', () => {
    it('renders cards in grid layout', () => {
      const { container } = render(<StatsCards stats={mockStats} />);
      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('applies responsive grid classes', () => {
      const { container } = render(<StatsCards stats={mockStats} />);
      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-4');
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot with stats', () => {
      const { container } = render(<StatsCards stats={mockStats} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot without stats', () => {
      const { container } = render(<StatsCards />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
