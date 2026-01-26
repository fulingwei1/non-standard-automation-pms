/**
 * 通用表格Hook
 * 统一处理表格状态、选择、排序
 */

import { useState, useCallback, useMemo } from 'react';

export interface UseTableOptions<T> {
  data: T[];
  rowKey?: string | ((record: T) => string);
  defaultSelectedRowKeys?: (string | number)[];
  onSelectionChange?: (selectedRowKeys: (string | number)[], selectedRows: T[]) => void;
}

/**
 * 通用表格Hook
 * 
 * @example
 * ```tsx
 * const {
 *   selectedRowKeys,
 *   selectedRows,
 *   rowSelection,
 *   handleSelect,
 *   handleSelectAll,
 *   clearSelection
 * } = useTable({
 *   data: projects,
 *   rowKey: 'id',
 *   onSelectionChange: (keys, rows) => {
 *     console.log('选中:', keys, rows);
 *   }
 * });
 * ```
 */
export function useTable<T extends Record<string, any>>(
  options: UseTableOptions<T>
) {
  const {
    data,
    rowKey = 'id',
    defaultSelectedRowKeys = [],
    onSelectionChange,
  } = options;

  const [selectedRowKeys, setSelectedRowKeys] = useState<(string | number)[]>(
    defaultSelectedRowKeys
  );

  // 获取行的key
  const getRowKey = useCallback((record: T, index: number): string | number => {
    if (typeof rowKey === 'function') {
      return rowKey(record);
    }
    return record[rowKey] ?? index;
  }, [rowKey]);

  // 选中的行数据
  const selectedRows = useMemo(() => {
    return data.filter(item => {
      const key = getRowKey(item, 0);
      return selectedRowKeys.includes(key);
    });
  }, [data, selectedRowKeys, getRowKey]);

  // 选择变更处理
  const handleSelect = useCallback((record: T, selected: boolean) => {
    const key = getRowKey(record, 0);
    
    setSelectedRowKeys(prev => {
      const newKeys = selected
        ? [...prev, key]
        : prev.filter(k => k !== key);
      
      const newRows = data.filter(item => {
        const itemKey = getRowKey(item, 0);
        return newKeys.includes(itemKey);
      });
      
      onSelectionChange?.(newKeys, newRows);
      
      return newKeys;
    });
  }, [data, getRowKey, onSelectionChange]);

  // 全选/取消全选
  const handleSelectAll = useCallback((selected: boolean) => {
    if (selected) {
      const allKeys = data.map((item, index) => getRowKey(item, index));
      setSelectedRowKeys(allKeys);
      onSelectionChange?.(allKeys, data);
    } else {
      setSelectedRowKeys([]);
      onSelectionChange?.([], []);
    }
  }, [data, getRowKey, onSelectionChange]);

  // 清除选择
  const clearSelection = useCallback(() => {
    setSelectedRowKeys([]);
    onSelectionChange?.([], []);
  }, [onSelectionChange]);

  // 行选择配置（用于Ant Design Table）
  const rowSelection = useMemo(() => ({
    selectedRowKeys,
    onChange: (keys: React.Key[]) => {
      setSelectedRowKeys(keys as (string | number)[]);
      const selectedRows = data.filter(item => {
        const key = getRowKey(item, 0);
        return keys.includes(key);
      });
      onSelectionChange?.(keys as (string | number)[], selectedRows);
    },
    onSelectAll: (selected: boolean, selectedRows: T[], changeRows: T[]) => {
      handleSelectAll(selected);
    },
  }), [selectedRowKeys, data, getRowKey, onSelectionChange, handleSelectAll]);

  return {
    selectedRowKeys,
    selectedRows,
    rowSelection,
    handleSelect,
    handleSelectAll,
    clearSelection,
    getRowKey,
  };
}
