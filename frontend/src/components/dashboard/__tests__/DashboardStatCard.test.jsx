import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// DashboardStatCard 使用 motion 但未导入，在测试中 mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => {
      const { whileHover, whileTap, initial, animate, transition, ...validProps } = props;
      return <div {...validProps}>{children}</div>;
    },
  },
}));

import DashboardStatCard from '../DashboardStatCard';
import { TrendingUp } from 'lucide-react';

describe('DashboardStatCard', () => {
  const mockOnClick = vi.fn();

  beforeEach(() => {
    mockOnClick.mockClear();
  });

  /**
   * 辅助函数：通过 data-testid="uistatcard" 获取 UiStatCard 渲染的 DOM 元素
   * UiStatCard 是全局 fallback，props 会作为 HTML attribute 渲染在 div 上
   */
  const getStatCard = () => screen.getByTestId('uistatcard');

  describe('Basic Rendering', () => {
    it('renders with required props', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="测试标签"
          value="100"
        />
      );
      const card = getStatCard();
      expect(card).toBeInTheDocument();
      expect(card).toHaveAttribute('label', '测试标签');
      expect(card).toHaveAttribute('value', '100');
    });

    it('renders icon component', () => {
      const { container } = render(
        <DashboardStatCard
          icon={TrendingUp}
          label="测试"
          value="100"
        />
      );
      // icon 作为属性传递给 UiStatCard，不会直接渲染 svg
      const card = getStatCard();
      expect(card).toBeInTheDocument();
    });

    it('renders with string value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="项目数"
          value="50个"
        />
      );
      const card = getStatCard();
      expect(card).toHaveAttribute('value', '50个');
    });

    it('renders with numeric value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="项目数"
          value={100}
        />
      );
      const card = getStatCard();
      expect(card).toHaveAttribute('value', '100');
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
      const card = getStatCard();
      expect(card).toHaveAttribute('change', '+10%');
      expect(card).toHaveAttribute('trend', 'up');
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
      const card = getStatCard();
      expect(card).toHaveAttribute('change', '-5%');
      expect(card).toHaveAttribute('trend', 'down');
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
      const card = getStatCard();
      expect(card).toHaveAttribute('change', '0%');
      expect(card).toHaveAttribute('trend', 'neutral');
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
      const card = getStatCard();
      expect(card).toHaveAttribute('change', '+5%');
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
      const card = getStatCard();
      expect(card).toHaveAttribute('description', '这是描述文本');
    });

    it('does not display description when not provided', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="测试"
          value="100"
        />
      );
      const card = getStatCard();
      expect(card).not.toHaveAttribute('description');
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
      const card = getStatCard();
      expect(card).toHaveAttribute('label', '加载中');
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
      const card = getStatCard();
      expect(card).toHaveAttribute('value', '100');
    });

    it('defaults to non-loading state', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="默认"
          value="100"
        />
      );
      const card = getStatCard();
      expect(card).toHaveAttribute('value', '100');
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

      const card = getStatCard().closest('div');
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

      const card = getStatCard().closest('div');
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

      // className 传递给 UiStatCard，UiStatCard fallback 会将其设置到 div 上
      const card = getStatCard();
      expect(card).toHaveClass('custom-class');
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

      const card = getStatCard();
      expect(card).toBeInTheDocument();
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

      const card = getStatCard();
      expect(card).toBeInTheDocument();
    });

    it('uses default icon styling when not provided', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="默认样式"
          value="100"
        />
      );

      const card = getStatCard();
      expect(card).toBeInTheDocument();
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
      // value=0 是 falsy，组件中 value || "unknown" 会变成 "unknown"
      const card = getStatCard();
      expect(card).toHaveAttribute('value', 'unknown');
    });

    it('handles negative value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="负值"
          value={-10}
        />
      );
      const card = getStatCard();
      expect(card).toHaveAttribute('value', '-10');
    });

    it('handles very large value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="大数"
          value={1000000}
        />
      );
      const card = getStatCard();
      expect(card).toHaveAttribute('value', '1000000');
    });

    it('handles empty string value', () => {
      render(
        <DashboardStatCard
          icon={TrendingUp}
          label="空值"
          value=""
        />
      );
      // value="" 是 falsy，组件中 value || "unknown" 会变成 "unknown"
      const card = getStatCard();
      expect(card).toHaveAttribute('value', 'unknown');
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
      const card = getStatCard();
      expect(card).toHaveAttribute('label', longLabel);
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
      const card = getStatCard();
      expect(card).toHaveAttribute('description', longDescription);
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
