import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../button';

describe('Button', () => {
  describe('Basic Rendering', () => {
    it('renders button with text', () => {
      render(<Button>点击我</Button>);
      expect(screen.getByText('点击我')).toBeInTheDocument();
    });

    it('renders as button element by default', () => {
      render(<Button>按钮</Button>);
      const button = screen.getByRole('button');
      expect(button.tagName).toBe('BUTTON');
    });

    it('renders children correctly', () => {
      render(
        <Button>
          <span>图标</span>
          <span>文本</span>
        </Button>
      );
      expect(screen.getByText('图标')).toBeInTheDocument();
      expect(screen.getByText('文本')).toBeInTheDocument();
    });
  });

  describe('Variant Styles', () => {
    it('renders default variant', () => {
      const { container } = render(<Button variant="default">默认</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders secondary variant', () => {
      const { container } = render(<Button variant="secondary">次要</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders outline variant', () => {
      const { container } = render(<Button variant="outline">轮廓</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders ghost variant', () => {
      const { container } = render(<Button variant="ghost">幽灵</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders destructive variant', () => {
      const { container } = render(<Button variant="destructive">删除</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders success variant', () => {
      const { container } = render(<Button variant="success">成功</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders link variant', () => {
      const { container } = render(<Button variant="link">链接</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('renders default size', () => {
      const { container } = render(<Button>默认大小</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders small size', () => {
      const { container } = render(<Button size="sm">小号</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders large size', () => {
      const { container } = render(<Button size="lg">大号</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });

    it('renders icon size', () => {
      const { container } = render(<Button size="icon">图标</Button>);
      expect(container.firstChild).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('renders disabled button', () => {
      render(<Button disabled>禁用按钮</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('does not trigger onClick when disabled', () => {
      const handleClick = vi.fn();
      render(
        <Button disabled onClick={handleClick}>
          禁用
        </Button>
      );

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('has reduced opacity when disabled', () => {
      render(<Button disabled>禁用</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('disabled:opacity-50');
    });
  });

  describe('Click Interactions', () => {
    it('calls onClick handler when clicked', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>点击</Button>);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('passes event to onClick handler', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>点击</Button>);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledWith(expect.any(Object));
    });

    it('can be clicked multiple times', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>多次点击</Button>);

      const button = screen.getByRole('button');
      fireEvent.click(button);
      fireEvent.click(button);
      fireEvent.click(button);

      expect(handleClick).toHaveBeenCalledTimes(3);
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <Button className="custom-button">自定义</Button>
      );
      expect(container.querySelector('.custom-button')).toBeInTheDocument();
    });

    it('merges custom className with variant classes', () => {
      const { container } = render(
        <Button variant="outline" className="my-custom-class">
          合并类名
        </Button>
      );
      expect(
        container.querySelector('.my-custom-class')
      ).toBeInTheDocument();
    });
  });

  describe('AsChild Prop', () => {
    it('renders as child element when asChild is true', () => {
      render(
        <Button asChild>
          <a href="/test">链接按钮</a>
        </Button>
      );

      const link = screen.getByText('链接按钮');
      expect(link.tagName).toBe('A');
      expect(link).toHaveAttribute('href', '/test');
    });
  });

  describe('Button Type', () => {
    it('renders with button type by default', () => {
      render(<Button>提交</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('type', 'button');
    });

    it('renders with submit type', () => {
      render(<Button type="submit">提交</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('type', 'submit');
    });

    it('renders with reset type', () => {
      render(<Button type="reset">重置</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('type', 'reset');
    });
  });

  describe('Accessibility', () => {
    it('is keyboard accessible', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>按钮</Button>);

      const button = screen.getByRole('button');
      button.focus();

      expect(document.activeElement).toBe(button);
    });

    it('has proper focus styles', () => {
      render(<Button>聚焦</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveClass('focus-visible:outline-none');
      expect(button).toHaveClass('focus-visible:ring-2');
    });

    it('supports aria-label', () => {
      render(<Button aria-label="关闭对话框">X</Button>);
      const button = screen.getByRole('button', { name: '关闭对话框' });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('renders with empty children', () => {
      const { container } = render(<Button></Button>);
      expect(container.querySelector('button')).toBeInTheDocument();
    });

    it('handles null children', () => {
      const { container } = render(<Button>{null}</Button>);
      expect(container.querySelector('button')).toBeInTheDocument();
    });

    it('renders with complex children', () => {
      render(
        <Button>
          <svg className="icon">
            <circle />
          </svg>
          <span>文本</span>
          <span className="badge">3</span>
        </Button>
      );

      expect(screen.getByText('文本')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for default button', () => {
      const { container } = render(<Button>默认按钮</Button>);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for all variants', () => {
      const variants = [
        'default',
        'secondary',
        'outline',
        'ghost',
        'destructive',
        'success',
        'link',
      ];

      variants.forEach((variant) => {
        const { container } = render(
          <Button variant={variant}>{variant}</Button>
        );
        expect(container).toMatchSnapshot();
      });
    });

    it('matches snapshot for disabled state', () => {
      const { container } = render(<Button disabled>禁用按钮</Button>);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with icon and text', () => {
      const { container } = render(
        <Button>
          <span>图标</span>
          确认
        </Button>
      );
      expect(container).toMatchSnapshot();
    });
  });
});
