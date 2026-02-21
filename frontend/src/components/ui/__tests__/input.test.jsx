import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '../input';
import { Search } from 'lucide-react';

describe('Input', () => {
  describe('Basic Rendering', () => {
    it('renders input element', () => {
      render(<Input placeholder="输入文本" />);
      expect(screen.getByPlaceholderText('输入文本')).toBeInTheDocument();
    });

    it('renders with value', () => {
      render(<Input value="测试文本" onChange={() => {}} />);
      const input = screen.getByDisplayValue('测试文本');
      expect(input).toBeInTheDocument();
    });

    it('renders with placeholder', () => {
      render(<Input placeholder="请输入..." />);
      expect(screen.getByPlaceholderText('请输入...')).toBeInTheDocument();
    });

    it('renders with default empty value', () => {
      const { container } = render(<Input />);
      const input = container.querySelector('input');
      expect(input.value).toBe('');
    });
  });

  describe('Input Types', () => {
    it('renders text input by default', () => {
      const { container } = render(<Input />);
      const input = container.querySelector('input');
      expect(input.type).toBe('text');
    });

    it('renders password input', () => {
      const { container } = render(<Input type="password" />);
      const input = container.querySelector('input');
      expect(input.type).toBe('password');
    });

    it('renders email input', () => {
      const { container } = render(<Input type="email" />);
      const input = container.querySelector('input');
      expect(input.type).toBe('email');
    });

    it('renders number input', () => {
      const { container } = render(<Input type="number" />);
      const input = container.querySelector('input');
      expect(input.type).toBe('number');
    });

    it('renders tel input', () => {
      const { container } = render(<Input type="tel" />);
      const input = container.querySelector('input');
      expect(input.type).toBe('tel');
    });
  });

  describe('Icon Support', () => {
    it('renders with icon', () => {
      const { container } = render(<Input icon={Search} />);
      expect(container.querySelector('svg')).toBeInTheDocument();
    });

    it('applies left padding when icon is present', () => {
      const { container } = render(<Input icon={Search} />);
      const input = container.querySelector('input');
      expect(input).toHaveClass('pl-10');
    });

    it('does not apply icon padding when no icon', () => {
      const { container } = render(<Input />);
      const input = container.querySelector('input');
      expect(input).toHaveClass('px-4');
      expect(input).not.toHaveClass('pl-10');
    });
  });

  describe('Error State', () => {
    it('applies error styles when error prop is true', () => {
      const { container } = render(<Input error={true} />);
      const input = container.querySelector('input');
      expect(input).toHaveClass('border-red-500/50');
    });

    it('does not apply error styles by default', () => {
      const { container } = render(<Input />);
      const input = container.querySelector('input');
      expect(input).not.toHaveClass('border-red-500/50');
    });
  });

  describe('Disabled State', () => {
    it('disables input when disabled prop is true', () => {
      render(<Input disabled placeholder="禁用输入框" />);
      const input = screen.getByPlaceholderText('禁用输入框');
      expect(input).toBeDisabled();
    });

    it('applies disabled styles', () => {
      const { container } = render(<Input disabled />);
      const input = container.querySelector('input');
      expect(input).toHaveClass('disabled:opacity-50');
      expect(input).toHaveClass('disabled:cursor-not-allowed');
    });

    it('does not trigger onChange when disabled', () => {
      const handleChange = vi.fn();
      render(<Input disabled onChange={handleChange} />);

      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: '测试' } });

      expect(handleChange).not.toHaveBeenCalled();
    });
  });

  describe('User Interactions', () => {
    it('calls onChange when value changes', () => {
      const handleChange = vi.fn();
      render(<Input onChange={handleChange} />);

      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: '新文本' } });

      expect(handleChange).toHaveBeenCalled();
    });

    it('updates value on user input', () => {
      const { rerender } = render(
        <Input value="初始值" onChange={() => {}} />
      );
      expect(screen.getByDisplayValue('初始值')).toBeInTheDocument();

      rerender(<Input value="新值" onChange={() => {}} />);
      expect(screen.getByDisplayValue('新值')).toBeInTheDocument();
    });

    it('handles focus event', () => {
      const handleFocus = vi.fn();
      render(<Input onFocus={handleFocus} />);

      const input = screen.getByRole('textbox');
      fireEvent.focus(input);

      expect(handleFocus).toHaveBeenCalled();
    });

    it('handles blur event', () => {
      const handleBlur = vi.fn();
      render(<Input onBlur={handleBlur} />);

      const input = screen.getByRole('textbox');
      fireEvent.blur(input);

      expect(handleBlur).toHaveBeenCalled();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<Input className="custom-input" />);
      const input = container.querySelector('input');
      expect(input).toHaveClass('custom-input');
    });

    it('merges custom className with default classes', () => {
      const { container } = render(<Input className="my-custom-class" />);
      const input = container.querySelector('input');
      expect(input).toHaveClass('my-custom-class');
      expect(input).toHaveClass('rounded-xl');
    });
  });

  describe('Ref Forwarding', () => {
    it('forwards ref to input element', () => {
      const ref = { current: null };
      render(<Input ref={ref} />);

      expect(ref.current).toBeInstanceOf(HTMLInputElement);
    });

    it('allows programmatic focus via ref', () => {
      const ref = { current: null };
      render(<Input ref={ref} />);

      ref.current.focus();
      expect(document.activeElement).toBe(ref.current);
    });
  });

  describe('Accessibility', () => {
    it('is keyboard accessible', () => {
      render(<Input />);
      const input = screen.getByRole('textbox');

      input.focus();
      expect(document.activeElement).toBe(input);
    });

    it('supports aria-label', () => {
      render(<Input aria-label="搜索框" />);
      expect(screen.getByLabelText('搜索框')).toBeInTheDocument();
    });

    it('supports aria-describedby', () => {
      render(<Input aria-describedby="help-text" />);
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'help-text');
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined value', () => {
      const { container } = render(<Input value={undefined} />);
      const input = container.querySelector('input');
      expect(input.value).toBe('');
    });

    it('handles null value', () => {
      const { container } = render(<Input value={null} />);
      const input = container.querySelector('input');
      expect(input.value).toBe('');
    });

    it('handles empty string value', () => {
      render(<Input value="" onChange={() => {}} />);
      const input = screen.getByRole('textbox');
      expect(input.value).toBe('');
    });

    it('handles long text values', () => {
      const longText = 'A'.repeat(1000);
      render(<Input value={longText} onChange={() => {}} />);
      const input = screen.getByRole('textbox');
      expect(input.value).toBe(longText);
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for basic input', () => {
      const { container } = render(<Input placeholder="基础输入框" />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with icon', () => {
      const { container } = render(
        <Input icon={Search} placeholder="搜索..." />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with error', () => {
      const { container } = render(<Input error={true} value="错误文本" />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot when disabled', () => {
      const { container } = render(<Input disabled value="禁用" />);
      expect(container).toMatchSnapshot();
    });
  });
});
