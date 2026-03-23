import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import ProjectCostFilter from '../ProjectCostFilter';

describe('ProjectCostFilter', () => {
  const mockOnFilterChange = vi.fn();
  const mockOnExport = vi.fn();

  const defaultFilters = {
    includeCost: false,
    overrunOnly: false,
    sort: 'created_at_desc',
  };

  // 保存原始 Switch 全局 fallback
  let origSwitch;

  beforeEach(() => {
    mockOnFilterChange.mockClear();
    mockOnExport.mockClear();

    // 保存并覆盖全局 Switch，使其具有 role="switch" 和 onClick 调用 onCheckedChange
    origSwitch = globalThis.Switch;
    globalThis.Switch = ({ checked, onCheckedChange, className, ...props }) => (
      React.createElement('button', {
        role: 'switch',
        'aria-checked': String(!!checked),
        className,
        onClick: () => onCheckedChange && onCheckedChange(!checked),
        ...props,
      })
    );
  });

  afterEach(() => {
    globalThis.Switch = origSwitch;
  });

  describe('Basic Rendering', () => {
    it('renders with default filters', () => {
      render(
        <ProjectCostFilter
          filters={defaultFilters}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={false}
        />
      );
      expect(screen.getByText('显示成本')).toBeInTheDocument();
    });

    it('renders cost switch', () => {
      render(
        <ProjectCostFilter
          filters={defaultFilters}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={false}
        />
      );
      const switches = screen.getAllByRole('switch');
      expect(switches.length).toBeGreaterThan(0);
    });

    it('shows overrun filter when showCost is true', () => {
      render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );
      expect(screen.getByText('仅超支项目')).toBeInTheDocument();
    });

    it('hides overrun filter when showCost is false', () => {
      render(
        <ProjectCostFilter
          filters={defaultFilters}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={false}
        />
      );
      expect(screen.queryByText('仅超支项目')).not.toBeInTheDocument();
    });
  });

  describe('Filter Interactions', () => {
    it('toggles cost display', () => {
      render(
        <ProjectCostFilter
          filters={defaultFilters}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={false}
        />
      );

      const switches = screen.getAllByRole('switch');
      fireEvent.click(switches[0]);

      expect(mockOnFilterChange).toHaveBeenCalledWith({
        ...defaultFilters,
        includeCost: true,
      });
    });

    it('toggles overrun filter', () => {
      render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );

      const switches = screen.getAllByRole('switch');
      fireEvent.click(switches[1]);

      expect(mockOnFilterChange).toHaveBeenCalledWith({
        ...defaultFilters,
        includeCost: true,
        overrunOnly: true,
      });
    });

    it('handles export action', () => {
      render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );

      // 导出按钮仅在 showCost 为 true 时显示
      const exportButton = screen.getByText('导出Excel').closest('button');
      if (exportButton) {
        fireEvent.click(exportButton);
        expect(mockOnExport).toHaveBeenCalled();
      }
    });
  });

  describe('Active Filters State', () => {
    it('shows active filters badge when includeCost is true', () => {
      render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );
      // "显示成本" 同时出现在 switch label 和 badge 中
      const elements = screen.getAllByText('显示成本');
      expect(elements.length).toBeGreaterThanOrEqual(2);
    });

    it('shows active filters when overrunOnly is true', () => {
      render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true, overrunOnly: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );
      // "仅超支项目" 同时在 switch 和 badge 中
      const elements = screen.getAllByText('仅超支项目');
      expect(elements.length).toBeGreaterThanOrEqual(2);
    });

    it('handles filter clear action', () => {
      render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true, overrunOnly: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );

      const clearButton = screen.getByText('清除筛选').closest('button');
      if (clearButton) {
        fireEvent.click(clearButton);
        expect(mockOnFilterChange).toHaveBeenCalledWith({
          includeCost: false,
          overrunOnly: false,
          sort: 'created_at_desc',
        });
      }
    });
  });

  describe('Snapshot', () => {
    it('matches snapshot with default props', () => {
      const { container } = render(
        <ProjectCostFilter
          filters={defaultFilters}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={false}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('matches snapshot with all filters active', () => {
      const { container } = render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true, overrunOnly: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});
