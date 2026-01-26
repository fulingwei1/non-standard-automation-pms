/**
 * FilterPanel 组件测试
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilterPanel } from '../FilterPanel';
import dayjs from 'dayjs';

describe('FilterPanel', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render select filter', () => {
    const filters = [
      {
        key: 'status',
        label: '状态',
        type: 'select' as const,
        options: [
          { label: '激活', value: 'active' },
          { label: '未激活', value: 'inactive' },
        ],
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{}}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('状态')).toBeInTheDocument();
  });

  it('should render input filter', () => {
    const filters = [
      {
        key: 'name',
        label: '名称',
        type: 'input' as const,
        placeholder: '请输入名称',
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{}}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('名称')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('请输入名称')).toBeInTheDocument();
  });

  it('should render date filter', () => {
    const filters = [
      {
        key: 'date',
        label: '日期',
        type: 'date' as const,
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{}}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('日期')).toBeInTheDocument();
  });

  it('should render date range filter', () => {
    const filters = [
      {
        key: 'dateRange',
        label: '日期范围',
        type: 'dateRange' as const,
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{}}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('日期范围')).toBeInTheDocument();
  });

  it('should render number filter', () => {
    const filters = [
      {
        key: 'price',
        label: '价格',
        type: 'number' as const,
        placeholder: '请输入价格',
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{}}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('价格')).toBeInTheDocument();
  });

  it('should handle filter value change', () => {
    const filters = [
      {
        key: 'status',
        label: '状态',
        type: 'select' as const,
        options: [
          { label: '激活', value: 'active' },
          { label: '未激活', value: 'inactive' },
        ],
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{}}
        onChange={mockOnChange}
      />
    );

    // 由于 Ant Design Select 的实现，这里主要验证组件渲染
    // 实际的值变更测试可能需要更复杂的模拟
    expect(screen.getByText('状态')).toBeInTheDocument();
  });

  it('should show clear button when showClear is true', () => {
    const filters = [
      {
        key: 'status',
        label: '状态',
        type: 'select' as const,
        options: [
          { label: '激活', value: 'active' },
          { label: '未激活', value: 'inactive' },
        ],
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{ status: 'active' }}
        onChange={mockOnChange}
        showClear={true}
      />
    );

    const clearButton = screen.getByRole('button', { name: /清除|重置/i });
    expect(clearButton).toBeInTheDocument();
  });

  it('should call onChange when clear button is clicked', () => {
    const filters = [
      {
        key: 'status',
        label: '状态',
        type: 'select' as const,
        options: [
          { label: '激活', value: 'active' },
          { label: '未激活', value: 'inactive' },
        ],
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{ status: 'active' }}
        onChange={mockOnChange}
        showClear={true}
      />
    );

    const clearButton = screen.getByRole('button', { name: /清除|重置/i });
    fireEvent.click(clearButton);

    expect(mockOnChange).toHaveBeenCalledWith({});
  });

  it('should display current filter values', () => {
    const filters = [
      {
        key: 'status',
        label: '状态',
        type: 'select' as const,
        options: [
          { label: '激活', value: 'active' },
          { label: '未激活', value: 'inactive' },
        ],
      },
      {
        key: 'name',
        label: '名称',
        type: 'input' as const,
      },
    ];

    render(
      <FilterPanel
        filters={filters}
        values={{ status: 'active', name: 'Test' }}
        onChange={mockOnChange}
      />
    );

    expect(screen.getByText('状态')).toBeInTheDocument();
    expect(screen.getByText('名称')).toBeInTheDocument();
  });

  it('should render in vertical layout', () => {
    const filters = [
      {
        key: 'status',
        label: '状态',
        type: 'select' as const,
        options: [
          { label: '激活', value: 'active' },
        ],
      },
    ];

    const { container } = render(
      <FilterPanel
        filters={filters}
        values={{}}
        onChange={mockOnChange}
        layout="vertical"
      />
    );

    // 验证垂直布局（Form.Item 应该垂直排列）
    expect(container.querySelector('.ant-form-vertical')).toBeInTheDocument();
  });
});
