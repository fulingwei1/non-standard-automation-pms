import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { StatCard } from '../StatCard';
import { DollarSign } from 'lucide-react';

describe('StatCard', () => {
  describe('Basic Rendering', () => {
    it('renders with required props', () => {
      render(<StatCard title="测试标题" value="1000" />);
      expect(screen.getByText('测试标题')).toBeInTheDocument();
      expect(screen.getByText('1000')).toBeInTheDocument();
    });

    it('renders subtitle when provided', () => {
      render(<StatCard title="标题" value="100" subtitle="副标题" />);
      expect(screen.getByText('副标题')).toBeInTheDocument();
    });

    it('renders icon when provided', () => {
      const { container } = render(
        <StatCard title="标题" value="100" icon={DollarSign} />
      );
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('renders children when provided', () => {
      render(
        <StatCard title="标题" value="100">
          <div data-testid="child">子内容</div>
        </StatCard>
      );
      expect(screen.getByTestId('child')).toBeInTheDocument();
    });

    it('renders header slot when provided', () => {
      const headerSlot = <div data-testid="header">头部</div>;
      render(<StatCard title="标题" value="100" headerSlot={headerSlot} />);
      expect(screen.getByTestId('header')).toBeInTheDocument();
    });
  });

  describe('Trend Display', () => {
    it('displays positive trend with up arrow', () => {
      const { container } = render(
        <StatCard title="标题" value="100" trend={10} />
      );
      expect(screen.getByText('+10%')).toBeInTheDocument();
      expect(screen.getByText('vs 上月')).toBeInTheDocument();
    });

    it('displays negative trend with down arrow', () => {
      const { container } = render(
        <StatCard title="标题" value="100" trend={-5} />
      );
      expect(screen.getByText('-5%')).toBeInTheDocument();
    });

    it('displays zero trend correctly', () => {
      const { container } = render(
        <StatCard title="标题" value="100" trend={0} />
      );
      expect(screen.queryByText('0%')).not.toBeInTheDocument();
    });

    it('uses custom trend suffix', () => {
      render(
        <StatCard title="标题" value="100" trend={10} trendSuffix="单位" />
      );
      expect(screen.getByText('+10单位')).toBeInTheDocument();
    });

    it('uses custom trend label', () => {
      render(
        <StatCard title="标题" value="100" trend={10} trendLabel="与上周比" />
      );
      expect(screen.getByText('与上周比')).toBeInTheDocument();
    });

    it('hides trend sign when trendShowSign is false', () => {
      render(
        <StatCard title="标题" value="100" trend={10} trendShowSign={false} />
      );
      expect(screen.getByText('10%')).toBeInTheDocument();
      expect(screen.queryByText('+10%')).not.toBeInTheDocument();
    });
  });

  describe('Layout Variants', () => {
    it('renders default layout', () => {
      const { container } = render(
        <StatCard title="标题" value="100" layout="default" />
      );
      expect(container.firstChild).toHaveClass('relative');
    });

    it('renders compact layout', () => {
      render(
        <StatCard title="标题" value="100" layout="compact" icon={DollarSign} />
      );
      expect(screen.getByText('标题')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('renders row layout', () => {
      render(
        <StatCard title="标题" value="100" layout="row" icon={DollarSign} />
      );
      expect(screen.getByText('标题')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('renders normal size by default', () => {
      const { container } = render(<StatCard title="标题" value="100" />);
      const valueElement = screen.getByText('100');
      expect(valueElement).toHaveClass('text-2xl');
    });

    it('renders large size', () => {
      const { container } = render(
        <StatCard title="标题" value="100" size="large" />
      );
      const valueElement = screen.getByText('100');
      expect(valueElement).toHaveClass('text-3xl');
    });

    it('renders small size', () => {
      const { container } = render(
        <StatCard title="标题" value="100" size="small" />
      );
      const valueElement = screen.getByText('100');
      expect(valueElement).toHaveClass('text-xl');
    });
  });

  describe('Styling and Customization', () => {
    it('applies custom className', () => {
      const { container } = render(
        <StatCard title="标题" value="100" cardClassName="custom-class" />
      );
      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('applies custom title className', () => {
      render(
        <StatCard title="标题" value="100" titleClassName="custom-title" />
      );
      const titleElement = screen.getByText('标题');
      expect(titleElement).toHaveClass('custom-title');
    });

    it('applies custom value className', () => {
      render(
        <StatCard title="标题" value="100" valueClassName="custom-value" />
      );
      const valueElement = screen.getByText('100');
      expect(valueElement).toHaveClass('custom-value');
    });

    it('applies custom color', () => {
      const { container } = render(
        <StatCard title="标题" value="100" color="text-blue-500" />
      );
      const valueElement = screen.getByText('100');
      expect(valueElement).toHaveClass('text-blue-500');
    });

    it('applies custom background', () => {
      const { container } = render(
        <StatCard title="标题" value="100" bg="bg-red-800" icon={DollarSign} />
      );
      expect(container.querySelector('.bg-red-800')).toBeInTheDocument();
    });

    it('hides decoration when showDecoration is false', () => {
      const { container } = render(
        <StatCard title="标题" value="100" showDecoration={false} />
      );
      expect(container.querySelector('.blur-2xl')).not.toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onClick when clicked', () => {
      const handleClick = vi.fn();
      render(<StatCard title="标题" value="100" onClick={handleClick} />);

      const card = screen.getByText('标题').closest('div');
      fireEvent.click(card);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('has cursor-pointer when onClick is provided', () => {
      const { container } = render(
        <StatCard title="标题" value="100" onClick={() => {}} />
      );
      expect(container.firstChild).toHaveClass('cursor-pointer');
    });

    it('does not have cursor-pointer when onClick is not provided', () => {
      const { container } = render(<StatCard title="标题" value="100" />);
      expect(container.firstChild).not.toHaveClass('cursor-pointer');
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default layout', () => {
      const { container } = render(
        <StatCard title="销售额" value="¥100,000" subtitle="本月" trend={12} />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for compact layout', () => {
      const { container } = render(
        <StatCard
          title="订单数"
          value="150"
          layout="compact"
          icon={DollarSign}
          trend={-5}
        />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for row layout', () => {
      const { container } = render(
        <StatCard
          title="客户数"
          value="250"
          layout="row"
          icon={DollarSign}
          subtitle="活跃客户"
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
