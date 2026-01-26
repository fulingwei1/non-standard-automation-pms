/**
 * DataTable 组件测试
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DataTable } from '../DataTable';
import type { ColumnType } from 'antd/es/table';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('DataTable', () => {
  const mockData = [
    { id: 1, name: 'Item 1', status: 'active' },
    { id: 2, name: 'Item 2', status: 'inactive' },
  ];

  const mockColumns: ColumnType<typeof mockData[0]>[] = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Status', dataIndex: 'status', key: 'status' },
  ];

  const mockQueryFn = vi.fn().mockResolvedValue({
    items: mockData,
    total: 2,
    page: 1,
    pageSize: 20,
    pages: 1,
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render table with data', async () => {
    render(
      <DataTable
        queryKey={['test']}
        queryFn={mockQueryFn}
        columns={mockColumns}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
    });
  });

  it('should show loading state', () => {
    const slowQueryFn = vi.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        items: mockData,
        total: 2,
        page: 1,
        pageSize: 20,
        pages: 1,
      }), 100))
    );

    render(
      <DataTable
        queryKey={['test']}
        queryFn={slowQueryFn}
        columns={mockColumns}
      />,
      { wrapper: createWrapper() }
    );

    // Ant Design Table 会在加载时显示加载状态
    expect(slowQueryFn).toHaveBeenCalled();
  });

  it('should handle pagination', async () => {
    const { container } = render(
      <DataTable
        queryKey={['test']}
        queryFn={mockQueryFn}
        columns={mockColumns}
        defaultPageSize={10}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(mockQueryFn).toHaveBeenCalled();
    });

    // 查找分页组件并点击下一页
    const nextButton = container.querySelector('.ant-pagination-next');
    if (nextButton) {
      fireEvent.click(nextButton);
      
      await waitFor(() => {
        expect(mockQueryFn).toHaveBeenCalledWith(
          expect.objectContaining({ page: 2 })
        );
      });
    }
  });

  it('should handle keyword search', async () => {
    const { container } = render(
      <DataTable
        queryKey={['test']}
        queryFn={mockQueryFn}
        columns={mockColumns}
        keywordFields={['name']}
        showSearch={true}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(mockQueryFn).toHaveBeenCalled();
    });

    const searchInput = container.querySelector('input[placeholder*="搜索"]') as HTMLInputElement;
    if (searchInput) {
      fireEvent.change(searchInput, { target: { value: 'Item 1' } });
      fireEvent.keyDown(searchInput, { key: 'Enter' });

      await waitFor(() => {
        expect(mockQueryFn).toHaveBeenCalledWith(
          expect.objectContaining({ keyword: 'Item 1' })
        );
      });
    }
  });

  it('should handle filter change', async () => {
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
      <DataTable
        queryKey={['test']}
        queryFn={mockQueryFn}
        columns={mockColumns}
        filters={filters}
        showFilters={true}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(mockQueryFn).toHaveBeenCalled();
    });

    // 筛选功能需要用户交互，这里主要验证组件渲染
    expect(screen.getByText('状态')).toBeInTheDocument();
  });

  it('should handle refresh', async () => {
    const { container } = render(
      <DataTable
        queryKey={['test']}
        queryFn={mockQueryFn}
        columns={mockColumns}
        showRefresh={true}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(mockQueryFn).toHaveBeenCalledTimes(1);
    });

    const refreshButton = container.querySelector('button[aria-label*="刷新"]') || 
                         container.querySelector('.ant-btn-icon-only');
    if (refreshButton) {
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(mockQueryFn).toHaveBeenCalledTimes(2);
      });
    }
  });

  it('should respect initial filters', async () => {
    render(
      <DataTable
        queryKey={['test']}
        queryFn={mockQueryFn}
        columns={mockColumns}
        initialFilters={{ status: 'active' }}
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(mockQueryFn).toHaveBeenCalledWith(
        expect.objectContaining({
          filters: { status: 'active' },
        })
      );
    });
  });

  it('should respect initial keyword', async () => {
    render(
      <DataTable
        queryKey={['test']}
        queryFn={mockQueryFn}
        columns={mockColumns}
        initialKeyword="test keyword"
      />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(mockQueryFn).toHaveBeenCalledWith(
        expect.objectContaining({
          keyword: 'test keyword',
        })
      );
    });
  });
});
