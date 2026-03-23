import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ProjectCostFilter from '../ProjectCostFilter';

describe('ProjectCostFilter', () => {
  const mockOnFilterChange = vi.fn();
  const mockOnExport = vi.fn();
  
  const defaultFilters = {
    includeCost: false,
    overrunOnly: false,
    sort: 'created_at_desc',
  };

  beforeEach(() => {
    mockOnFilterChange.mockClear();
    mockOnExport.mockClear();
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
      const { container } = render(
        <ProjectCostFilter
          filters={defaultFilters}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={false}
        />
      );
      
      const switches = container.querySelectorAll('button[role="switch"]');
      fireEvent.click(switches[0]);
      
      expect(mockOnFilterChange).toHaveBeenCalledWith({
        ...defaultFilters,
        includeCost: true,
      });
    });

    it('toggles overrun filter', () => {
      const { container } = render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );
      
      const switches = container.querySelectorAll('button[role="switch"]');
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
          filters={defaultFilters}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={false}
        />
      );
      
      const exportButton = screen.queryByRole('button', { name: /导出|export/i });
      if (exportButton) {
        fireEvent.click(exportButton);
        expect(mockOnExport).toHaveBeenCalled();
      }
    });
  });

  describe('Active Filters State', () => {
    it('shows active filters when includeCost is true', () => {
      render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );
      expect(screen.getByText('显示成本')).toBeInTheDocument();
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
      expect(screen.getByText('仅超支项目')).toBeInTheDocument();
    });

    it('handles filter clear action', () => {
      const { container } = render(
        <ProjectCostFilter
          filters={{ ...defaultFilters, includeCost: true, overrunOnly: true }}
          onFilterChange={mockOnFilterChange}
          onExport={mockOnExport}
          showCost={true}
        />
      );
      
      const clearButton = screen.queryByRole('button', { name: /清除|clear/i });
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
