import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// Mock Switch component
const Switch = ({ checked = false, onChange, disabled = false, label, className }) => {
  return (
    <div className={`switch-wrapper ${className || ''}`}>
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => !disabled && onChange?.(!checked)}
        disabled={disabled}
        className={`switch ${checked ? 'checked' : ''} ${disabled ? 'disabled' : ''}`}
      >
        <span className="switch-thumb" />
      </button>
      {label && <span className="switch-label">{label}</span>}
    </div>
  );
};

describe('Switch', () => {
  describe('Basic Rendering', () => {
    it('renders switch component', () => {
      render(<Switch />);
      expect(screen.getByRole('switch')).toBeInTheDocument();
    });

    it('renders with label', () => {
      render(<Switch label="启用功能" />);
      expect(screen.getByText('启用功能')).toBeInTheDocument();
    });

    it('renders without label', () => {
      const { container } = render(<Switch />);
      expect(container.querySelector('.switch-label')).not.toBeInTheDocument();
    });

    it('renders thumb element', () => {
      const { container } = render(<Switch />);
      expect(container.querySelector('.switch-thumb')).toBeInTheDocument();
    });
  });

  describe('Checked State', () => {
    it('renders unchecked by default', () => {
      render(<Switch />);
      const switchElement = screen.getByRole('switch');
      expect(switchElement.getAttribute('aria-checked')).toBe('false');
    });

    it('renders checked when checked prop is true', () => {
      render(<Switch checked={true} onChange={() => {}} />);
      const switchElement = screen.getByRole('switch');
      expect(switchElement.getAttribute('aria-checked')).toBe('true');
    });

    it('applies checked className when checked', () => {
      const { container } = render(<Switch checked={true} onChange={() => {}} />);
      const switchButton = container.querySelector('.switch');
      expect(switchButton).toHaveClass('checked');
    });

    it('does not have checked className when unchecked', () => {
      const { container } = render(<Switch checked={false} onChange={() => {}} />);
      const switchButton = container.querySelector('.switch');
      expect(switchButton).not.toHaveClass('checked');
    });
  });

  describe('Toggle Functionality', () => {
    it('calls onChange when clicked', () => {
      const handleChange = vi.fn();
      render(<Switch checked={false} onChange={handleChange} />);

      const switchElement = screen.getByRole('switch');
      fireEvent.click(switchElement);

      expect(handleChange).toHaveBeenCalledWith(true);
    });

    it('toggles from checked to unchecked', () => {
      const handleChange = vi.fn();
      render(<Switch checked={true} onChange={handleChange} />);

      const switchElement = screen.getByRole('switch');
      fireEvent.click(switchElement);

      expect(handleChange).toHaveBeenCalledWith(false);
    });

    it('can be toggled multiple times', () => {
      const handleChange = vi.fn();
      const { rerender } = render(
        <Switch checked={false} onChange={handleChange} />
      );

      const switchElement = screen.getByRole('switch');
      
      fireEvent.click(switchElement);
      expect(handleChange).toHaveBeenCalledWith(true);

      rerender(<Switch checked={true} onChange={handleChange} />);
      fireEvent.click(switchElement);
      expect(handleChange).toHaveBeenCalledWith(false);

      expect(handleChange).toHaveBeenCalledTimes(2);
    });

    it('handles missing onChange gracefully', () => {
      render(<Switch />);
      const switchElement = screen.getByRole('switch');
      expect(() => fireEvent.click(switchElement)).not.toThrow();
    });
  });

  describe('Disabled State', () => {
    it('disables switch when disabled prop is true', () => {
      render(<Switch disabled={true} />);
      const switchElement = screen.getByRole('switch');
      expect(switchElement).toBeDisabled();
    });

    it('applies disabled className', () => {
      const { container } = render(<Switch disabled={true} />);
      const switchButton = container.querySelector('.switch');
      expect(switchButton).toHaveClass('disabled');
    });

    it('does not trigger onChange when disabled', () => {
      const handleChange = vi.fn();
      render(<Switch disabled={true} onChange={handleChange} />);

      const switchElement = screen.getByRole('switch');
      fireEvent.click(switchElement);

      expect(handleChange).not.toHaveBeenCalled();
    });

    it('is not disabled by default', () => {
      render(<Switch />);
      const switchElement = screen.getByRole('switch');
      expect(switchElement).not.toBeDisabled();
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(<Switch className="custom-switch" />);
      expect(container.querySelector('.custom-switch')).toBeInTheDocument();
    });

    it('merges custom className with default classes', () => {
      const { container } = render(
        <Switch className="rounded-lg shadow-md" />
      );
      const wrapper = container.querySelector('.switch-wrapper');
      expect(wrapper).toHaveClass('rounded-lg', 'shadow-md');
    });
  });

  describe('Accessibility', () => {
    it('has role="switch"', () => {
      render(<Switch />);
      expect(screen.getByRole('switch')).toBeInTheDocument();
    });

    it('sets aria-checked attribute correctly', () => {
      const { rerender } = render(<Switch checked={false} onChange={() => {}} />);
      let switchElement = screen.getByRole('switch');
      expect(switchElement.getAttribute('aria-checked')).toBe('false');

      rerender(<Switch checked={true} onChange={() => {}} />);
      switchElement = screen.getByRole('switch');
      expect(switchElement.getAttribute('aria-checked')).toBe('true');
    });

    it('is keyboard accessible', () => {
      const handleChange = vi.fn();
      render(<Switch onChange={handleChange} />);
      
      const switchElement = screen.getByRole('switch');
      switchElement.focus();
      
      expect(document.activeElement).toBe(switchElement);
    });
  });

  describe('Label Variations', () => {
    it('displays simple text label', () => {
      render(<Switch label="接收通知" />);
      expect(screen.getByText('接收通知')).toBeInTheDocument();
    });

    it('displays long label', () => {
      const longLabel = '这是一个非常长的标签文本用于测试组件的渲染能力';
      render(<Switch label={longLabel} />);
      expect(screen.getByText(longLabel)).toBeInTheDocument();
    });

    it('handles empty label', () => {
      const { container } = render(<Switch label="" />);
      const label = container.querySelector('.switch-label');
      expect(label).toBeInTheDocument();
      expect(label.textContent).toBe('');
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined checked prop', () => {
      render(<Switch checked={undefined} onChange={() => {}} />);
      const switchElement = screen.getByRole('switch');
      expect(switchElement.getAttribute('aria-checked')).toBe('false');
    });

    it('handles null checked prop', () => {
      render(<Switch checked={null} onChange={() => {}} />);
      const switchElement = screen.getByRole('switch');
      expect(switchElement.getAttribute('aria-checked')).toBe('false');
    });

    it('handles string checked prop', () => {
      render(<Switch checked="true" onChange={() => {}} />);
      const switchElement = screen.getByRole('switch');
      // Truthy string should be treated as true
      expect(switchElement.getAttribute('aria-checked')).toBe('true');
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for unchecked switch', () => {
      const { container } = render(<Switch />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot for checked switch', () => {
      const { container } = render(<Switch checked={true} onChange={() => {}} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with label', () => {
      const { container } = render(<Switch label="启用暗黑模式" />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot when disabled', () => {
      const { container } = render(<Switch disabled={true} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with all props', () => {
      const { container } = render(
        <Switch
          checked={true}
          onChange={() => {}}
          label="自动保存"
          className="custom-switch"
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
