import { useState, useCallback, useMemo } from 'react';

/**
 * 过滤器 Hook
 * 
 * @param {Object} initialFilters - 初始过滤条件
 * 
 * @example
 * const filters = useFilter({
 *   status: 'all',
 *   keyword: '',
 *   dateRange: null,
 * });
 * 
 * // 更新过滤条件
 * filters.set('status', 'active');
 * 
 * // 获取查询参数
 * const params = filters.toQueryParams();
 */
export function useFilter(initialFilters = {}) {
    const [filters, setFilters] = useState(initialFilters);

    // 设置单个过滤条件
    const set = useCallback((key, value) => {
        setFilters(prev => ({
            ...prev,
            [key]: value,
        }));
    }, []);

    // 批量设置过滤条件
    const setMultiple = useCallback((updates) => {
        setFilters(prev => ({
            ...prev,
            ...updates,
        }));
    }, []);

    // 重置所有过滤条件
    const reset = useCallback(() => {
        setFilters(initialFilters);
    }, [initialFilters]);

    // 重置单个过滤条件
    const resetOne = useCallback((key) => {
        setFilters(prev => ({
            ...prev,
            [key]: initialFilters[key],
        }));
    }, [initialFilters]);

    // 转换为查询参数（过滤空值）
    const toQueryParams = useCallback(() => {
        const params = {};

        for (const [key, value] of Object.entries(filters)) {
            // 跳过空值和 'all'
            if (value === null || value === undefined || value === '' || value === 'all') {
                continue;
            }
            params[key] = value;
        }

        return params;
    }, [filters]);

    // 过滤条件是否为空
    const isEmpty = useMemo(() => {
        return Object.values(filters).every(
            v => v === null || v === undefined || v === '' || v === 'all'
        );
    }, [filters]);

    // 活跃的过滤条件数量
    const activeCount = useMemo(() => {
        return Object.values(filters).filter(
            v => v !== null && v !== undefined && v !== '' && v !== 'all'
        ).length;
    }, [filters]);

    return {
        // 状态
        filters,
        isEmpty,
        activeCount,

        // 操作
        set,
        setMultiple,
        setFilters,
        reset,
        resetOne,
        toQueryParams,
    };
}
