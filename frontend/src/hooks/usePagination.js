import { useState, useCallback, useMemo } from 'react';

/**
 * 分页 Hook
 * 
 * @param {Object} options - 配置选项
 * @param {number} options.initialPage - 初始页码
 * @param {number} options.initialPageSize - 初始每页条数
 * @param {number} options.total - 总条数
 * 
 * @example
 * const pagination = usePagination({ total: 100 });
 * 
 * // 获取当前分页参数
 * const params = { page: pagination.page, page_size: pagination.pageSize };
 * 
 * // 渲染分页器
 * <Pagination
 *   current={pagination.page}
 *   total={pagination.total}
 *   onChange={pagination.setPage}
 * />
 */
export function usePagination(options = {}) {
    const {
        initialPage = 1,
        initialPageSize = 20,
        total: initialTotal = 0,
    } = options;

    const [page, setPage] = useState(initialPage);
    const [pageSize, setPageSize] = useState(initialPageSize);
    const [total, setTotal] = useState(initialTotal);

    // 总页数
    const totalPages = useMemo(() => {
        return Math.ceil(total / pageSize) || 1;
    }, [total, pageSize]);

    // 是否有上一页/下一页
    const hasPrev = page > 1;
    const hasNext = page < totalPages;

    // 分页参数
    const params = useMemo(() => ({
        page,
        page_size: pageSize,
        offset: (page - 1) * pageSize,
    }), [page, pageSize]);

    // 跳转到指定页
    const goToPage = useCallback((newPage) => {
        const validPage = Math.max(1, Math.min(newPage, totalPages));
        setPage(validPage);
    }, [totalPages]);

    // 上一页
    const prevPage = useCallback(() => {
        if (hasPrev) {
            setPage(p => p - 1);
        }
    }, [hasPrev]);

    // 下一页
    const nextPage = useCallback(() => {
        if (hasNext) {
            setPage(p => p + 1);
        }
    }, [hasNext]);

    // 重置分页
    const reset = useCallback(() => {
        setPage(initialPage);
    }, [initialPage]);

    // 更新分页信息（从API响应中）
    const updateFromResponse = useCallback((response) => {
        if (response.total !== undefined) {
            setTotal(response.total);
        }
        if (response.page !== undefined) {
            setPage(response.page);
        }
    }, []);

    return {
        // 状态
        page,
        pageSize,
        total,
        totalPages,
        hasPrev,
        hasNext,
        params,

        // 操作
        setPage: goToPage,
        setPageSize,
        setTotal,
        prevPage,
        nextPage,
        reset,
        updateFromResponse,
    };
}
