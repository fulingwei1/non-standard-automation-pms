/**
 * useTable Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTable } from '../useTable';

describe('useTable', () => {
  const mockData = [
    { id: 1, name: 'Item 1' },
    { id: 2, name: 'Item 2' },
    { id: 3, name: 'Item 3' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useTable({ data: mockData }));

    expect(result.current.selectedRowKeys).toEqual([]);
    expect(result.current.selectedRows).toEqual([]);
  });

  it('should initialize with default selected keys', () => {
    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        defaultSelectedRowKeys: [1, 2],
      })
    );

    expect(result.current.selectedRowKeys).toEqual([1, 2]);
    expect(result.current.selectedRows).toHaveLength(2);
  });

  it('should get row key correctly', () => {
    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        rowKey: 'id',
      })
    );

    expect(result.current.getRowKey(mockData[0], 0)).toBe(1);
    expect(result.current.getRowKey(mockData[1], 1)).toBe(2);
  });

  it('should get row key using function', () => {
    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        rowKey: (record) => `key-${record.id}`,
      })
    );

    expect(result.current.getRowKey(mockData[0], 0)).toBe('key-1');
  });

  it('should handle select', () => {
    const mockOnSelectionChange = vi.fn();

    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        rowKey: 'id',
        onSelectionChange: mockOnSelectionChange,
      })
    );

    act(() => {
      result.current.handleSelect(mockData[0], true);
    });

    expect(result.current.selectedRowKeys).toEqual([1]);
    expect(result.current.selectedRows).toEqual([mockData[0]]);
    expect(mockOnSelectionChange).toHaveBeenCalledWith([1], [mockData[0]]);
  });

  it('should handle deselect', () => {
    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        rowKey: 'id',
      })
    );

    act(() => {
      result.current.handleSelect(mockData[0], true);
      result.current.handleSelect(mockData[1], true);
    });

    expect(result.current.selectedRowKeys).toEqual([1, 2]);

    act(() => {
      result.current.handleSelect(mockData[0], false);
    });

    expect(result.current.selectedRowKeys).toEqual([2]);
    expect(result.current.selectedRows).toEqual([mockData[1]]);
  });

  it('should handle select all', () => {
    const mockOnSelectionChange = vi.fn();

    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        rowKey: 'id',
        onSelectionChange: mockOnSelectionChange,
      })
    );

    act(() => {
      result.current.handleSelectAll(true);
    });

    expect(result.current.selectedRowKeys).toEqual([1, 2, 3]);
    expect(result.current.selectedRows).toEqual(mockData);
    expect(mockOnSelectionChange).toHaveBeenCalledWith([1, 2, 3], mockData);
  });

  it('should handle deselect all', () => {
    const mockOnSelectionChange = vi.fn();

    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        rowKey: 'id',
        onSelectionChange: mockOnSelectionChange,
      })
    );

    act(() => {
      result.current.handleSelectAll(true);
      result.current.handleSelectAll(false);
    });

    expect(result.current.selectedRowKeys).toEqual([]);
    expect(result.current.selectedRows).toEqual([]);
    expect(mockOnSelectionChange).toHaveBeenCalledWith([], []);
  });

  it('should clear selection', () => {
    const mockOnSelectionChange = vi.fn();

    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        rowKey: 'id',
        onSelectionChange: mockOnSelectionChange,
      })
    );

    act(() => {
      result.current.handleSelectAll(true);
      result.current.clearSelection();
    });

    expect(result.current.selectedRowKeys).toEqual([]);
    expect(result.current.selectedRows).toEqual([]);
    expect(mockOnSelectionChange).toHaveBeenCalledWith([], []);
  });

  it('should provide rowSelection config for Ant Design', () => {
    const mockOnSelectionChange = vi.fn();

    const { result } = renderHook(() =>
      useTable({
        data: mockData,
        rowKey: 'id',
        onSelectionChange: mockOnSelectionChange,
      })
    );

    expect(result.current.rowSelection).toHaveProperty('selectedRowKeys');
    expect(result.current.rowSelection).toHaveProperty('onChange');
    expect(result.current.rowSelection).toHaveProperty('onSelectAll');

    act(() => {
      result.current.rowSelection.onChange([1, 2] as React.Key[]);
    });

    expect(result.current.selectedRowKeys).toEqual([1, 2]);
    expect(mockOnSelectionChange).toHaveBeenCalled();
  });

  it('should update selected rows when data changes', () => {
    const { result, rerender } = renderHook(
      ({ data }) => useTable({ data, rowKey: 'id' }),
      { initialProps: { data: mockData } }
    );

    act(() => {
      result.current.handleSelectAll(true);
    });

    expect(result.current.selectedRows).toHaveLength(3);

    const newData = [{ id: 1, name: 'Item 1' }];
    rerender({ data: newData });

    expect(result.current.selectedRows).toHaveLength(1);
  });
});
