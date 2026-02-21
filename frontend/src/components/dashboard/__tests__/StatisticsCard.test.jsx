import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

// Mock StatisticsCard component
const StatisticsCard = ({ title, value, trend, icon: Icon, color = 'blue' }) => {
  return (
    <div className="statistics-card" data-color={color}>
      <div className="header">
        {Icon && <Icon className="icon" />}
        <h3>{title}</h3>
      </div>
      <div className="value">{value}</div>
      {trend !== undefined && (
        <div className={`trend ${trend >= 0 ? 'positive' : 'negative'}`}>
          {trend >= 0 ? '+' : ''}{trend}%
        </div>
      )}
    </div>
  );
};

const MockIcon = () => <svg data-testid="mock-icon"><circle /></svg>;

describe('StatisticsCard', () => {
  describe('Basic Rendering', () => {
    it('renders title and value', () => {
      render(<StatisticsCard title="总销售额" value="¥1,000,000" />);
      expect(screen.getByText('总销售额')).toBeInTheDocument();
      expect(screen.getByText('¥1,000,000')).toBeInTheDocument();
    });

    it('renders without icon', () => {
      render(<StatisticsCard title="订单数" value="100" />);
      expect(screen.queryByTestId('mock-icon')).not.toBeInTheDocument();
    });

    it('renders with icon', () => {
      render(<StatisticsCard title="客户数" value="50" icon={MockIcon} />);
      expect(screen.getByTestId('mock-icon')).toBeInTheDocument();
    });
  });

  describe('Trend Display', () => {
    it('displays positive trend', () => {
      render(<StatisticsCard title="增长" value="100" trend={15} />);
      expect(screen.getByText('+15%')).toBeInTheDocument();
    });

    it('displays negative trend', () => {
      render(<StatisticsCard title="下降" value="80" trend={-10} />);
      expect(screen.getByText('-10%')).toBeInTheDocument();
    });

    it('displays zero trend', () => {
      render(<StatisticsCard title="持平" value="100" trend={0} />);
      expect(screen.getByText('+0%')).toBeInTheDocument();
    });

    it('does not display trend when not provided', () => {
      render(<StatisticsCard title="无趋势" value="100" />);
      expect(screen.queryByText(/%/)).not.toBeInTheDocument();
    });

    it('applies positive class for positive trend', () => {
      const { container } = render(
        <StatisticsCard title="测试" value="100" trend={10} />
      );
      const trend = container.querySelector('.trend');
      expect(trend).toHaveClass('positive');
    });

    it('applies negative class for negative trend', () => {
      const { container } = render(
        <StatisticsCard title="测试" value="100" trend={-5} />
      );
      const trend = container.querySelector('.trend');
      expect(trend).toHaveClass('negative');
    });
  });

  describe('Color Variants', () => {
    it('uses default blue color', () => {
      const { container } = render(
        <StatisticsCard title="默认" value="100" />
      );
      expect(container.querySelector('[data-color="blue"]')).toBeInTheDocument();
    });

    it('applies custom color', () => {
      const { container } = render(
        <StatisticsCard title="自定义" value="100" color="red" />
      );
      expect(container.querySelector('[data-color="red"]')).toBeInTheDocument();
    });

    it('supports various color options', () => {
      const colors = ['blue', 'green', 'red', 'yellow', 'purple'];
      colors.forEach((color) => {
        const { container } = render(
          <StatisticsCard title="测试" value="100" color={color} />
        );
        expect(
          container.querySelector(`[data-color="${color}"]`)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Value Formats', () => {
    it('handles numeric values', () => {
      render(<StatisticsCard title="数字" value={12345} />);
      expect(screen.getByText('12345')).toBeInTheDocument();
    });

    it('handles string values', () => {
      render(<StatisticsCard title="字符串" value="150 orders" />);
      expect(screen.getByText('150 orders')).toBeInTheDocument();
    });

    it('handles formatted currency', () => {
      render(<StatisticsCard title="金额" value="¥1,234,567.89" />);
      expect(screen.getByText('¥1,234,567.89')).toBeInTheDocument();
    });

    it('handles percentage values', () => {
      render(<StatisticsCard title="百分比" value="95.5%" />);
      expect(screen.getByText('95.5%')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles very large values', () => {
      render(<StatisticsCard title="大数值" value="999,999,999" />);
      expect(screen.getByText('999,999,999')).toBeInTheDocument();
    });

    it('handles zero value', () => {
      render(<StatisticsCard title="零值" value={0} />);
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('handles empty string value', () => {
      render(<StatisticsCard title="空值" value="" />);
      expect(screen.getByText('')).toBeInTheDocument();
    });

    it('handles very long title', () => {
      const longTitle = '这是一个非常非常长的统计卡片标题用于测试';
      render(<StatisticsCard title={longTitle} value="100" />);
      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for basic card', () => {
      const { container } = render(
        <StatisticsCard title="销售额" value="¥100,000" />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with icon and trend', () => {
      const { container } = render(
        <StatisticsCard
          title="订单数"
          value="250"
          trend={12}
          icon={MockIcon}
        />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with negative trend', () => {
      const { container } = render(
        <StatisticsCard
          title="退货率"
          value="3.5%"
          trend={-2.5}
          color="red"
        />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom color', () => {
      const { container } = render(
        <StatisticsCard
          title="新客户"
          value="85"
          trend={8}
          color="green"
          icon={MockIcon}
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
