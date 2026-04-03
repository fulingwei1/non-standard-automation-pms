import { useState, useCallback, useMemo } from 'react';

/**
 * 批量选择 Hook
 *
 * @param {Array} items - 可选择的项目列表
 * @param {string} idKey - 项目唯一标识的字段名，默认 'id'
 *
 * @example
 * const { selectedIds, isSelected, toggle, toggleAll, clear, isAllSelected, selectedCount } = useSelection(projects);
 */
export function useSelection(items = [], idKey = 'id') {
  const [selectedIds, setSelectedIds] = useState(new Set());

  const toggle = useCallback((id) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const isSelected = useCallback((id) => {
    return selectedIds.has(id);
  }, [selectedIds]);

  const toggleAll = useCallback(() => {
    setSelectedIds((prev) => {
      if (prev.size === items.length && items.length > 0) {
        return new Set();
      }
      return new Set(items.map((item) => item[idKey]));
    });
  }, [items, idKey]);

  const clear = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const selectMultiple = useCallback((ids) => {
    setSelectedIds(new Set(ids));
  }, []);

  const isAllSelected = useMemo(() => {
    return items.length > 0 && selectedIds.size === items.length;
  }, [items.length, selectedIds.size]);

  const isPartialSelected = useMemo(() => {
    return selectedIds.size > 0 && selectedIds.size < items.length;
  }, [items.length, selectedIds.size]);

  const selectedCount = selectedIds.size;

  const selectedItems = useMemo(() => {
    return items.filter((item) => selectedIds.has(item[idKey]));
  }, [items, selectedIds, idKey]);

  return {
    selectedIds,
    selectedItems,
    selectedCount,
    isSelected,
    toggle,
    toggleAll,
    clear,
    selectMultiple,
    isAllSelected,
    isPartialSelected,
  };
}
