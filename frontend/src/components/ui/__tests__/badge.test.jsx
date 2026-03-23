import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '../badge';

describe('Badge', () => {
  describe('Basic Rendering', () => {
    it('renders with text content', () => {
      render(<Badge>测试标签</Badge>);
      expect(screen.getByText('测试标签')).toBeInTheDocument();
    });

    it('renders as span element', () => {
      const { container } = render(<Badge>标签</Badge>);
      const badge = container.querySelector('span');
      expect(badge).toBeInTheDocument();
    });

    it('renders with children', () => {
      render(
        <Badge>
          <span>图标</span>
          文本
        </Badge>
      );
      expect(screen.getByText('图标')).toBeInTheDocument();
      expect(screen.getByText('文本')).toBeInTheDocument();
    });
  });

  describe('Variant Styles', () => {
    it('renders default variant', () => {
      const { container } = render(<Badge variant="default">默认</Badge>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders secondary variant', () => {
      const { container } = render(<Badge variant="secondary">次要</Badge>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders success variant', () => {
      const { container } = render(<Badge variant="success">成功</Badge>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders warning variant', () => {
      const { container } = render(<Badge variant="warning">警告</Badge>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders danger variant', () => {
      const { container } = render(<Badge variant="danger">危险</Badge>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders info variant', () => {
      const { container } = render(<Badge variant="info">信息</Badge>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders outline variant', () => {
      const { container } = render(<Badge variant="outline">轮廓</Badge>);
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <Badge className="custom-badge">自定义</Badge>
      );
      expect(container.querySelector('.custom-badge')).toBeInTheDocument();
    });

    it('merges custom className with variant classes', () => {
      const { container } = render(
        <Badge variant="success" className="my-custom-class">
          合并
        </Badge>
      );
      expect(
        container.querySelector('.my-custom-class')
      ).toBeInTheDocument();
    });

    it('has base rounded-full class', () => {
      const { container } = render(<Badge>圆角</Badge>);
      const badge = container.querySelector('span');
      expect(badge).toHaveClass('rounded-full');
    });

    it('has inline-flex display', () => {
      const { container } = render(<Badge>布局</Badge>);
      const badge = container.querySelector('span');
      expect(badge).toHaveClass('inline-flex');
    });
  });

  describe('Additional Props', () => {
    it('spreads additional props to span element', () => {
      render(<Badge data-testid="test-badge">属性</Badge>);
      expect(screen.getByTestId('test-badge')).toBeInTheDocument();
    });

    it('supports onClick handler', () => {
      const handleClick = vi.fn();
      const { container } = render(<Badge onClick={handleClick}>点击</Badge>);

      const badge = container.querySelector('span');
      badge.click();

      expect(handleClick).toHaveBeenCalled();
    });

    it('supports aria attributes', () => {
      render(<Badge aria-label="状态标签">状态</Badge>);
      const badge = screen.getByLabelText('状态标签');
      expect(badge).toBeInTheDocument();
    });
  });

  describe('Content Variations', () => {
    it('renders with empty content', () => {
      const { container } = render(<Badge></Badge>);
      expect(container.querySelector('span')).toBeInTheDocument();
    });

    it('renders with number', () => {
      render(<Badge>42</Badge>);
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('renders with icon', () => {
      render(
        <Badge>
          <svg data-testid="icon">
            <circle />
          </svg>
          图标标签
        </Badge>
      );
      expect(screen.getByTestId('icon')).toBeInTheDocument();
    });

    it('renders with long text', () => {
      render(<Badge>这是一个很长的标签文本内容</Badge>);
      expect(screen.getByText('这是一个很长的标签文本内容')).toBeInTheDocument();
    });
  });

  describe('Size and Spacing', () => {
    it('has correct padding classes', () => {
      const { container } = render(<Badge>填充</Badge>);
      const badge = container.querySelector('span');
      expect(badge).toHaveClass('px-2.5');
      expect(badge).toHaveClass('py-0.5');
    });

    it('has correct text size', () => {
      const { container } = render(<Badge>文本</Badge>);
      const badge = container.querySelector('span');
      expect(badge).toHaveClass('text-xs');
    });

    it('has font-medium weight', () => {
      const { container } = render(<Badge>字重</Badge>);
      const badge = container.querySelector('span');
      expect(badge).toHaveClass('font-medium');
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default badge', () => {
      const { container } = render(<Badge>默认标签</Badge>);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for all variants', () => {
      const variants = [
        'default',
        'secondary',
        'success',
        'warning',
        'danger',
        'info',
        'outline',
      ];

      variants.forEach((variant) => {
        const { container } = render(
          <Badge variant={variant}>{variant}</Badge>
        );
        expect(container).toMatchSnapshot();
      });
    });

    it('matches snapshot with icon', () => {
      const { container } = render(
        <Badge variant="success">
          <svg className="icon">
            <circle />
          </svg>
          完成
        </Badge>
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom className', () => {
      const { container } = render(
        <Badge className="custom-styles">自定义样式</Badge>
      );
      expect(container).toMatchSnapshot();
    });
  });
});
