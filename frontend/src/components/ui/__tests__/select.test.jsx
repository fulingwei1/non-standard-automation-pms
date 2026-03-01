import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

// Mock Select component
const Select = ({ value, onChange, options, placeholder = '请选择', disabled = false }) => {
  const safeOptions = options || [];
  return (
    <select
      value={value || "unknown"}
      onChange={(e) => !disabled && onChange?.(e.target.value)}
      disabled={disabled}
      className="select-component"
    >
      <option value="">{placeholder}</option>
      {safeOptions.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
};

describe('Select', () => {
  const mockOptions = [
    { value: '1', label: '选项1' },
    { value: '2', label: '选项2' },
    { value: '3', label: '选项3' },
  ];

  describe('Basic Rendering', () => {
    it('renders select element', () => {
      render(<Select options={mockOptions} />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('renders placeholder option', () => {
      render(<Select options={mockOptions} placeholder="选择一个选项" />);
      expect(screen.getByText('选择一个选项')).toBeInTheDocument();
    });

    it('renders all options', () => {
      render(<Select options={mockOptions} />);
      mockOptions.forEach((option) => {
        expect(screen.getByText(option.label)).toBeInTheDocument();
      });
    });

    it('renders with default placeholder', () => {
      render(<Select options={mockOptions} />);
      expect(screen.getByText('请选择')).toBeInTheDocument();
    });
  });

  describe('Value Selection', () => {
    it('displays selected value', () => {
      render(<Select options={mockOptions} value="2" onChange={() => {}} />);
      const select = screen.getByRole('combobox');
      expect(select.value).toBe('2');
    });

    it('calls onChange when option is selected', () => {
      const handleChange = vi.fn();
      render(<Select options={mockOptions} onChange={handleChange} />);

      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: '2' } });

      expect(handleChange).toHaveBeenCalledWith('2');
    });

    it('can change selection multiple times', () => {
      const handleChange = vi.fn();
      render(<Select options={mockOptions} onChange={handleChange} />);

      const select = screen.getByRole('combobox');
      
      fireEvent.change(select, { target: { value: '1' } });
      expect(handleChange).toHaveBeenCalledWith('1');

      fireEvent.change(select, { target: { value: '3' } });
      expect(handleChange).toHaveBeenCalledWith('3');

      expect(handleChange).toHaveBeenCalledTimes(2);
    });

    it('handles empty value', () => {
      render(<Select options={mockOptions} value="" onChange={() => {}} />);
      const select = screen.getByRole('combobox');
      expect(select.value).toBe('');
    });
  });

  describe('Disabled State', () => {
    it('disables select when disabled prop is true', () => {
      render(<Select options={mockOptions} disabled={true} />);
      const select = screen.getByRole('combobox');
      expect(select).toBeDisabled();
    });

    it('does not trigger onChange when disabled', () => {
      const handleChange = vi.fn();
      render(
        <Select options={mockOptions} disabled={true} onChange={handleChange} />
      );

      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: '1' } });

      expect(handleChange).not.toHaveBeenCalled();
    });

    it('is not disabled by default', () => {
      render(<Select options={mockOptions} />);
      const select = screen.getByRole('combobox');
      expect(select).not.toBeDisabled();
    });
  });

  describe('Options Configuration', () => {
    it('handles empty options array', () => {
      render(<Select options={[]} />);
      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
      expect(select.children.length).toBe(1); // Only placeholder
    });

    it('handles single option', () => {
      const singleOption = [{ value: 'only', label: '唯一选项' }];
      render(<Select options={singleOption} />);
      expect(screen.getByText('唯一选项')).toBeInTheDocument();
    });

    it('handles large number of options', () => {
      const manyOptions = Array.from({ length: 100 }, (_, i) => ({
        value: `${i}`,
        label: `选项${i}`,
      }));
      render(<Select options={manyOptions} />);
      const select = screen.getByRole('combobox');
      expect(select.children.length).toBe(101); // 100 options + placeholder
    });

    it('handles options with special characters', () => {
      const specialOptions = [
        { value: '1', label: '选项 & 符号' },
        { value: '2', label: '选项 < > 符号' },
        { value: '3', label: "选项 ' \" 引号" },
      ];
      render(<Select options={specialOptions} />);
      expect(screen.getByText('选项 & 符号')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined options', () => {
      render(<Select options={undefined} />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('handles null options', () => {
      render(<Select options={null} />);
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('handles undefined onChange', () => {
      render(<Select options={mockOptions} />);
      const select = screen.getByRole('combobox');
      expect(() => {
        fireEvent.change(select, { target: { value: '1' } });
      }).not.toThrow();
    });

    it('handles very long option labels', () => {
      const longOptions = [
        {
          value: '1',
          label: '这是一个非常非常非常非常长的选项标签用于测试组件的渲染能力',
        },
      ];
      render(<Select options={longOptions} />);
      expect(screen.getByText(/这是一个非常非常/)).toBeInTheDocument();
    });
  });

  describe('Snapshot Tests', () => {
    it('matches snapshot for basic select', () => {
      const { container } = render(<Select options={mockOptions} />);
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with selected value', () => {
      const { container } = render(
        <Select options={mockOptions} value="2" onChange={() => {}} />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot when disabled', () => {
      const { container } = render(
        <Select options={mockOptions} disabled={true} />
      );
      expect(container).toMatchSnapshot();
    });

    it('matches snapshot with custom placeholder', () => {
      const { container } = render(
        <Select options={mockOptions} placeholder="自定义占位符" />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
