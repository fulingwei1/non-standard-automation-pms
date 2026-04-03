import { useState, useCallback, useEffect, useMemo, useRef } from 'react';

/**
 * 通用数据管理 Hook
 * 封装加载、过滤、分页、CRUD 的公共模式
 *
 * 解决的重复模式（来自 WorkOrderManagement / WorkshopManagement /
 * ProductionExceptionList 等页面 hook）：
 *   - useState for loading / data / error
 *   - useCallback for fetch（setLoading → build params → call API → normalise response → finally clear loading）
 *   - useMemo for client-side filtering
 *   - useEffect for auto-init
 *
 * @param {Function} fetchFn
 *   接收当前 filters 对象并返回 Promise 的 API 函数。
 *   返回值应为以下任一形式：
 *     - { data: { items: [], total: N } }
 *     - { data: [] }
 *     - []
 *
 * @param {Object}   options                    配置项
 * @param {Object}   options.defaultFilters     初始过滤条件（默认 {}）
 * @param {Function} options.filterFn           客户端二次过滤函数 (item, filters) => boolean
 *                                              用于在 API 已返回数据后做本地关键字过滤等
 * @param {boolean}  options.autoLoad           是否在 mount / filter 变化时自动调用 fetchFn（默认 true）
 * @param {Object}   options.defaultPagination  初始分页配置（默认 { page: 1, pageSize: 20, total: 0 }）
 *
 * @returns {{
 *   data:          any[],
 *   filteredData:  any[],
 *   loading:       boolean,
 *   error:         string|null,
 *   filters:       Object,
 *   setFilters:    Function,
 *   pagination:    { page: number, pageSize: number, total: number },
 *   setPagination: Function,
 *   reload:        Function,
 *   mutate:        Function,
 *   clearError:    Function,
 * }}
 *
 * @example
 * // 基础用法 ──────────────────────────────────────────────────────────────────
 * const { filteredData, loading, error, filters, setFilters, reload } =
 *   useDataManagement(
 *     (filters) => productionApi.workshops.list({
 *       workshop_type: filters.type || undefined,
 *       is_active:     filters.active !== '' ? filters.active === 'true' : undefined,
 *       search:        filters.search || undefined,
 *     }),
 *     {
 *       defaultFilters: { type: '', active: '', search: '' },
 *       filterFn: (item, { search }) =>
 *         !search ||
 *         item.workshop_code?.toLowerCase().includes(search.toLowerCase()) ||
 *         item.workshop_name?.toLowerCase().includes(search.toLowerCase()),
 *     }
 *   );
 *
 * // CRUD 封装 ─────────────────────────────────────────────────────────────────
 * const { mutate } = useDataManagement(...);
 * const handleCreate = async (form) => {
 *   const result = await mutate(() => productionApi.workshops.create(form));
 *   if (result.success) setShowDialog(false);
 * };
 */
export function useDataManagement(fetchFn, options = {}) {
  const {
    defaultFilters = {},
    filterFn = null,
    autoLoad = true,
    defaultPagination = { page: 1, pageSize: 20, total: 0 },
  } = options;

  // ── Core state ──────────────────────────────────────────────────────────────
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(autoLoad); // start true when auto-loading
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(defaultFilters);
  const [pagination, setPagination] = useState(defaultPagination);

  // Keep a stable ref to fetchFn so the useCallback below doesn't need it as a
  // dependency (avoids infinite re-render when callers pass an inline function).
  const fetchFnRef = useRef(fetchFn);
  useEffect(() => {
    fetchFnRef.current = fetchFn;
  });

  // ── Primary fetch ───────────────────────────────────────────────────────────
  /**
   * reload() re-fetches using the current filters + pagination.
   * It is safe to call at any time (e.g. after a mutation).
   */
  const reload = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetchFnRef.current(filters, pagination);

      // Normalise the three response shapes produced by the existing API layer:
      //   { data: { items: [], total: N } }  → server-paginated list
      //   { data: [] }                        → flat array wrapped in axios shape
      //   []                                  → raw array (rare but handled)
      const payload = response?.data ?? response;
      const items = payload?.items ?? (Array.isArray(payload) ? payload : []);
      const total = payload?.total ?? items.length;

      setData(items);
      setPagination((prev) => ({ ...prev, total }));
    } catch (err) {
      const message =
        err?.response?.data?.detail ?? err?.message ?? 'Unknown error';
      setError(message);
      console.error('[useDataManagement] fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }, [filters, pagination.page, pagination.pageSize]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Auto-load ───────────────────────────────────────────────────────────────
  useEffect(() => {
    if (autoLoad) {
      reload();
    }
    // reload identity changes when filters / pagination change, so this also
    // handles "re-fetch when filter changes" without extra plumbing.
  }, [reload, autoLoad]);

  // ── Client-side filter (useMemo) ────────────────────────────────────────────
  /**
   * filteredData applies an optional client-side predicate on top of whatever
   * the server returned. This mirrors the useMemo pattern present in
   * WorkshopManagement and ProductionExceptionList where a keyword search is
   * applied locally after the API call (avoids extra round trips for small
   * datasets already fully loaded).
   */
  const filteredData = useMemo(() => {
    if (!filterFn) return data;
    return data.filter((item) => filterFn(item, filters));
  }, [data, filters, filterFn]);

  // ── Mutation helper ─────────────────────────────────────────────────────────
  /**
   * mutate() wraps any write operation (create / update / delete) so callers
   * don't have to repeat try/catch + reload boilerplate.
   *
   * @param {Function} actionFn  async () => any
   * @param {Object}   opts
   * @param {boolean}  opts.reloadAfter  re-fetch after success (default true)
   * @returns {{ success: boolean, data?: any, error?: string }}
   */
  const mutate = useCallback(
    async (actionFn, { reloadAfter = true } = {}) => {
      try {
        const result = await actionFn();
        if (reloadAfter) await reload();
        return { success: true, data: result };
      } catch (err) {
        const message =
          err?.response?.data?.detail ?? err?.message ?? 'Unknown error';
        console.error('[useDataManagement] mutation failed:', err);
        return { success: false, error: message };
      }
    },
    [reload],
  );

  // ── Helpers ─────────────────────────────────────────────────────────────────
  const clearError = useCallback(() => setError(null), []);

  return {
    // Data
    data,
    filteredData,
    // Status
    loading,
    error,
    clearError,
    // Filters
    filters,
    setFilters,
    // Pagination
    pagination,
    setPagination,
    // Actions
    reload,
    mutate,
  };
}
