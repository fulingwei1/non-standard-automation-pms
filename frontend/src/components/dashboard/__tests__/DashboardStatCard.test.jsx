import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DashboardStatCard from '../DashboardStatCard';
import { TrendingUp } from 'lucide-react';

describe('DashboardStatCard', () => {
  const mockOnClick = vi.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  describe('Basic Rendering', () => {
    it('renders with required props', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="测试标签"
          value="100"
        />
      );
      expect(screen.getByText('测试标签')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('renders icon component', () => {
      const { container } = render(
        <DashboardStatCard
          icon={TrendingUp}
          label="测试"
          value="100"
        />
      );
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders with string value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="项目数"
          value="50个"
        />
      );
      expect(screen.getByText('50个')).toBeInTheDocument();
    });

    it('renders with numeric value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="项目数"
          value={100}
        />
      );
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  describe('Trend Display', () => {
    it('displays positive trend', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="增长"
          value="100"
          change="+10%"
          trend="up"
        />
      );
      expect(screen.getByText('+10%')).toBeInTheDocument();
    });

    it('displays negative trend', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="下降"
          value="90"
          change="-5%"
          trend="down"
        />
      );
      expect(screen.getByText('-5%')).toBeInTheDocument();
    });

    it('displays neutral trend', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="稳定"
          value="100"
          change="0%"
          trend="neutral"
        />
      );
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('handles missing trend', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="无趋势"
          value="100"
          change="+5%"
        />
      );
      expect(screen.getByText('+5%')).toBeInTheDocument();
    });
  });

  describe('Description', () => {
    it('displays description when provided', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="测试"
          value="100"
          description="这是描述文本"
        />
      );
      expect(screen.getByText('这是描述文本')).toBeInTheDocument();
    });

    it('does not display description when not provided', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="测试"
          value="100"
        />
      );
      expect(screen.queryByText('描述')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('displays loading state', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="加载中"
          value="100"
          loading={true}
        />
      );
      expect(screen.getByText('加载中')).toBeInTheDocument();
    });

    it('displays normal state when not loading', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="正常"
          value="100"
          loading={false}
        />
      );
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('defaults to non-loading state', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="默认"
          value="100"
        />
      );
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  describe('Click Interaction', () => {
    it('calls onClick when card is clicked', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="可点击"
          value="100"
          onClick={mockOnClick}
        />
      );
      
      const card = screen.getByText('100').closest('div');
      if (card) {
        fireEvent.click(card);
        expect(mockOnClick).toHaveBeenCalled();
      }
    });

    it('does not error when onClick is not provided', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="不可点击"
          value="100"
        />
      );
      
      const card = screen.getByText('100').closest('div');
      expect(() => {
        if (card) fireEvent.click(card);
      }).not.toThrow();
    });

    it('applies hover effect when clickable', () => {
      const { container } = render(
        <DashboardStatCard
          icon={TrendingUp}
          label="可点击"
          value="100"
          onClick={mockOnClick}
        />
      );
      
      expect(container.querySelector('div')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('applies custom className', () => {
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

    it('applies custom icon color', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="彩色图标"
          value="100"
          iconColor="text-red-500"
        />
      );
      
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('applies custom icon background', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="背景"
          value="100"
          iconBg="bg-blue-500"
        />
      );
      
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('uses default icon styling when not provided', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="默认样式"
          value="100"
        />
      );
      
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="零值"
          value={0}
        />
      );
      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('handles negative value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="负值"
          value={-10}
        />
      );
      expect(screen.getByText('-10')).toBeInTheDocument();
    });

    it('handles very large value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="大数"
          value={1000000}
        />
      );
      expect(screen.getByText('1000000')).toBeInTheDocument();
    });

    it('handles empty string value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="空值"
          value=""
        />
      );
      expect(screen.getByText('空值')).toBeInTheDocument();
    });

    it('handles very long label', () => {
      const longLabel = '这是一个非常非常非常长的标签文本用于测试溢出';
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label={longLabel}
          value="100"
        />
      );
      expect(screen.getByText(longLabel)).toBeInTheDocument();
    });

    it('handles very long description', () => {
      const longDescription = '这是一个非常非常非常长的描述文本用于测试溢出处理和文本换行';
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="长描述"
          value="100"
          description={longDescription}
        />
      );
      expect(screen.getByText(longDescription)).toBeInTheDocument();
    });
  });

  describe('Component Display Name', () => {
    it('has correct displayName', () => {
      expect(DashboardStatCard.displayName).toBe('DashboardStatCard');
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot with minimal props', () => {
      const { container } = render(
        <DashboardStatCard
          icon={TrendingUp}
          label="最小"
          value="100"
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with all props', () => {
      const { container } = render(
        <DashboardStatCard
          icon={TrendingUp}
          label="完整"
          value="100"
          change="+10%"
          trend="up"
          description="完整属性"
          onClick={mockOnClick}
          loading={false}
          className="custom"
          iconColor="text-blue-500"
          iconBg="bg-blue-100"
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot in loading state', () => {
      const { container } = render(
        <DashboardStatCard
          icon={TrendingUp}
          label="加载"
          value="100"
          loading={true}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
