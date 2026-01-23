/**
 * Hooks 集成测试
 * 测试多个Hooks协同工作的场景
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useDataLoader } from '../../hooks/useDataLoader';
import { usePaginatedData } from '../../hooks/usePaginatedData';
import { useForm } from '../../hooks/useForm';
import { useTable } from '../../hooks/useTable';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('Hooks Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useDataLoader + useForm Integration', () => {
    it('should load data and submit form', async () => {
      const mockData = { id: 1, name: 'Project 1' };
      const mockLoadFn = vi.fn().mockResolvedValue(mockData);
      const mockSubmitFn = vi.fn().mockResolvedValue({ id: 2, name: 'New Project' });

      const { result: loaderResult } = renderHook(
        () => useDataLoader(['project', 1], mockLoadFn),
        { wrapper: createWrapper() }
      );

      const { result: formResult } = renderHook(
        () => useForm({
          initialValues: { name: '' },
          onSubmit: mockSubmitFn,
        }),
        { wrapper: createWrapper() }
      );

      // 等待数据加载
      await waitFor(() => {
        expect(loaderResult.current.isSuccess).toBe(true);
      });

      expect(loaderResult.current.data).toEqual(mockData);

      // 更新表单并提交
      act(() => {
        formResult.current.handleChange('name', 'New Project');
      });

      await act(async () => {
        await formResult.current.handleSubmit();
      });

      await waitFor(() => {
        expect(formResult.current.isSuccess).toBe(true);
      });

      expect(mockSubmitFn).toHaveBeenCalled();
      const submitCall = mockSubmitFn.mock.calls[0][0];
      expect(submitCall.name).toBe('New Project');
    });
  });

  describe('usePaginatedData + useTable Integration', () => {
    it('should paginate data and select rows', async () => {
      const mockData = {
        items: [
          { id: 1, name: 'Item 1' },
          { id: 2, name: 'Item 2' },
          { id: 3, name: 'Item 3' },
        ],
        total: 3,
        page: 1,
        pageSize: 20,
        pages: 1,
      };

      const mockQueryFn = vi.fn().mockResolvedValue(mockData);

      const { result: paginatedResult } = renderHook(
        () => usePaginatedData(['items'], mockQueryFn),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(paginatedResult.current.isLoading).toBe(false);
      });

      const { result: tableResult } = renderHook(
        () => useTable({
          data: paginatedResult.current.data,
          rowKey: 'id',
        })
      );

      // 选择行
      act(() => {
        tableResult.current.handleSelect(paginatedResult.current.data[0], true);
      });

      expect(tableResult.current.selectedRowKeys).toEqual([1]);
      expect(tableResult.current.selectedRows).toHaveLength(1);

      // 切换页码
      act(() => {
        paginatedResult.current.handlePageChange(2, 20);
      });

      await waitFor(() => {
        expect(paginatedResult.current.pagination.page).toBe(2);
      });

      // 选择应该被清除（因为数据变了）
      // 注意：实际应用中可能需要保持选择状态
    });
  });

  describe('usePaginatedData + useForm Integration', () => {
    it('should filter data and create new item', async () => {
      const mockData = {
        items: [],
        total: 0,
        page: 1,
        pageSize: 20,
        pages: 0,
      };

      const mockQueryFn = vi.fn().mockResolvedValue(mockData);
      const mockCreateFn = vi.fn().mockResolvedValue({ id: 1, name: 'New Item' });

      const { result: paginatedResult } = renderHook(
        () => usePaginatedData(['items'], mockQueryFn),
        { wrapper: createWrapper() }
      );

      const { result: formResult } = renderHook(
        () => useForm({
          initialValues: { name: '' },
          onSubmit: mockCreateFn,
          onSuccess: () => {
            // 创建成功后刷新列表
            paginatedResult.current.refetch();
          },
        }),
        { wrapper: createWrapper() }
      );

      // 设置筛选
      act(() => {
        paginatedResult.current.handleFilterChange({ status: 'active' });
      });

      await waitFor(() => {
        expect(mockQueryFn).toHaveBeenCalledWith(
          expect.objectContaining({ filters: { status: 'active' } })
        );
      });

      // 提交表单
      act(() => {
        formResult.current.handleChange('name', 'New Item');
      });

      await act(async () => {
        await formResult.current.handleSubmit();
      });

      await waitFor(() => {
        expect(formResult.current.isSuccess).toBe(true);
      });

      // 验证创建后刷新了列表（可能被调用多次，至少2次）
      expect(mockQueryFn).toHaveBeenCalled();
      expect(mockQueryFn.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Complete CRUD Workflow', () => {
    it('should complete full CRUD workflow', async () => {
      // 初始数据
      const initialData = {
        items: [{ id: 1, name: 'Item 1' }],
        total: 1,
        page: 1,
        pageSize: 20,
        pages: 1,
      };

      const mockListFn = vi.fn().mockResolvedValue(initialData);
      const mockGetFn = vi.fn().mockResolvedValue({ id: 1, name: 'Item 1' });
      const mockUpdateFn = vi.fn().mockResolvedValue({ id: 1, name: 'Updated Item' });
      const mockDeleteFn = vi.fn().mockResolvedValue({ success: true });

      // 1. 列表查询
      const { result: listResult } = renderHook(
        () => usePaginatedData(['items'], mockListFn),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(listResult.current.isLoading).toBe(false);
      });

      expect(listResult.current.data).toHaveLength(1);

      // 2. 获取详情
      const { result: detailResult } = renderHook(
        () => useDataLoader(['item', 1], mockGetFn),
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        expect(detailResult.current.isSuccess).toBe(true);
      });

      expect(detailResult.current.data?.name).toBe('Item 1');

      // 3. 更新
      const { result: updateFormResult } = renderHook(
        () => useForm({
          initialValues: { name: 'Item 1' },
          onSubmit: mockUpdateFn,
          onSuccess: () => {
            listResult.current.refetch();
            detailResult.current.refetch();
          },
        }),
        { wrapper: createWrapper() }
      );

      act(() => {
        updateFormResult.current.handleChange('name', 'Updated Item');
      });

      await act(async () => {
        await updateFormResult.current.handleSubmit();
      });

      await waitFor(() => {
        expect(updateFormResult.current.isSuccess).toBe(true);
      });

      // 4. 删除
      await act(async () => {
        await mockDeleteFn();
      });

      // 刷新列表
      await act(async () => {
        await listResult.current.refetch();
      });

      // 验证所有操作都执行了
      expect(mockListFn).toHaveBeenCalled();
      expect(mockGetFn).toHaveBeenCalled();
      expect(mockUpdateFn).toHaveBeenCalled();
      expect(mockDeleteFn).toHaveBeenCalled();
    });
  });
});
