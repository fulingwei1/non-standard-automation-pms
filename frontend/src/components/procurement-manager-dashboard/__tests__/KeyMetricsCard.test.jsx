import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KeyMetricsCard from '../KeyMetricsCard';

describe('KeyMetricsCard', () => {
  describe('Basic Rendering', () => {
    it('renders card title', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('关键指标')).toBeInTheDocument();
    });

    it('renders view details button', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('查看详情')).toBeInTheDocument();
    });

    it('renders all four metric sections', () => {
      render(<KeyMetricsCard />);

      expect(screen.getByText('本月订单数')).toBeInTheDocument();
      expect(screen.getByText('供应商评分')).toBeInTheDocument();
      expect(screen.getByText('成本节省率')).toBeInTheDocument();
      expect(screen.getByText('订单完成率')).toBeInTheDocument();
    });
  });

  describe('Metric Values', () => {
    it('displays order count', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('92')).toBeInTheDocument();
    });

    it('displays supplier rating', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('4.55')).toBeInTheDocument();
    });

    it('displays cost savings rate', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('4.2%')).toBeInTheDocument();
    });

    it('displays order completion rate', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('96.8%')).toBeInTheDocument();
    });
  });

  describe('Trend Indicators', () => {
    it('displays positive trend for orders', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('+8 较上月')).toBeInTheDocument();
    });

    it('displays positive trend for rating', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('+0.12 较上月')).toBeInTheDocument();
    });

    it('displays positive trend for savings', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('+0.5% 较上月')).toBeInTheDocument();
    });

    it('displays positive trend for completion', () => {
      render(<KeyMetricsCard />);
      expect(screen.getByText('+1.2% 较上月')).toBeInTheDocument();
    });

    it('shows trending up icons for all metrics', () => {
      const { container } = render(<KeyMetricsCard />);
      const trendIcons = container.querySelectorAll('.text-emerald-400');
      expect(trendIcons.length).toBeGreaterThan(0);
    });
  });

  describe('Layout', () => {
    it('uses grid layout for metrics', () => {
      const { container } = render(<KeyMetricsCard />);
      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('displays metrics in centered text format', () => {
      const { container } = render(<KeyMetricsCard />);
      const textCenters = container.querySelectorAll('.text-center');
      expect(textCenters.length).toBe(4);
    });
  });

  describe('Styling', () => {
    it('has proper card background', () => {
      const { container } = render(<KeyMetricsCard />);
      const card = container.querySelector('.bg-surface-50');
      expect(card).toBeInTheDocument();
    });

    it('displays icon with primary color', () => {
      const { container } = render(<KeyMetricsCard />);
      const icon = container.querySelector('.text-primary');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot', () => {
      const { container } = render(<KeyMetricsCard />);
      expect(container).toMatchSnapshot();
    });
  });
});
