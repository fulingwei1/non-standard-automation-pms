import { useState, useCallback, useEffect, useMemo } from 'react';
import { api } from '../../../services/api/client';

/**
 * 审批中心标签页类型
 */
export const APPROVAL_TABS = {
  PENDING: 'pending',      // 待我审批
  INITIATED: 'initiated',  // 我发起的
  CC: 'cc',                // 抄送我的
  PROCESSED: 'processed',  // 已处理
};

/**
 * 标签页对应的 API 端点
 */
const TAB_ENDPOINTS = {
  [APPROVAL_TABS.PENDING]: '/approvals/pending/mine',
  [APPROVAL_TABS.INITIATED]: '/approvals/pending/initiated',
  [APPROVAL_TABS.CC]: '/approvals/pending/cc',
  [APPROVAL_TABS.PROCESSED]: '/approvals/pending/processed',
};

/**
 * 审批中心数据 Hook
 *
 * 接入统一审批系统 API，支持四个标签页：
 * - 待我审批 (pending)
 * - 我发起的 (initiated)
 * - 抄送我的 (cc)
 * - 已处理 (processed)
 */
export function useApprovalCenter() {
  // 数据状态
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 分页状态
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    pages: 0,
  });

  // 筛选状态
  const [filters, setFilters] = useState({
    urgency: 'all',      // 紧急程度: all / NORMAL / URGENT / CRITICAL
    templateId: null,    // 审批模板 ID
    keyword: '',         // 搜索关键词
  });

  // 当前标签页
  const [activeTab, setActiveTab] = useState(APPROVAL_TABS.PENDING);

  // 统计数据
  const [counts, setCounts] = useState({
    pending: 0,
    initiated_pending: 0,
    unread_cc: 0,
    urgent: 0,
    total: 0,
  });

  /**
   * 加载统计数据
   */
  const loadCounts = useCallback(async () => {
    try {
      const response = await api.get('/approvals/pending/counts');
      const data = response.data?.data || response.data || {};
      setCounts({
        pending: data.pending || 0,
        initiated_pending: data.initiated_pending || 0,
        unread_cc: data.unread_cc || 0,
        urgent: data.urgent || 0,
        total: data.total || 0,
      });
    } catch (err) {
      console.error('加载统计数据失败:', err);
    }
  }, []);

  /**
   * 加载列表数据
   */
  const loadItems = useCallback(async (options = {}) => {
    const {
      page = pagination.page,
      pageSize = pagination.pageSize,
      tab = activeTab,
    } = options;

    setLoading(true);
    setError(null);

    try {
      const endpoint = TAB_ENDPOINTS[tab];
      const params = {
        page,
        page_size: pageSize,
      };

      // 添加筛选参数
      if (filters.urgency && filters.urgency !== 'all') {
        params.urgency = filters.urgency;
      }
      if (filters.templateId) {
        params.template_id = filters.templateId;
      }

      // 抄送我的标签页特殊处理：筛选未读/已读
      if (tab === APPROVAL_TABS.CC && filters.isRead !== undefined) {
        params.is_read = filters.isRead;
      }

      const response = await api.get(endpoint, { params });
      const data = response.data;

      // 处理响应数据（统一响应格式）
      const responseData = data.data || data;
      const itemsList = responseData.items || responseData || [];

      setItems(itemsList);
      setPagination({
        page: responseData.page || page,
        pageSize: responseData.page_size || pageSize,
        total: responseData.total || 0,
        pages: responseData.pages || Math.ceil((responseData.total || 0) / pageSize),
      });

    } catch (err) {
      console.error('加载审批列表失败:', err);
      setError(err.response?.data?.detail || err.message || '加载失败');
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [activeTab, filters, pagination.page, pagination.pageSize]);

  /**
   * 切换标签页
   */
  const switchTab = useCallback((tab) => {
    setActiveTab(tab);
    setPagination(prev => ({ ...prev, page: 1 }));
  }, []);

  /**
   * 更新筛选条件
   */
  const updateFilters = useCallback((newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    setPagination(prev => ({ ...prev, page: 1 }));
  }, []);

  /**
   * 切换页码
   */
  const changePage = useCallback((page) => {
    setPagination(prev => ({ ...prev, page }));
  }, []);

  /**
   * 审批通过
   */
  const approve = useCallback(async (taskId, comment = '') => {
    try {
      await api.post(`/tasks/${taskId}/approve`, {
        comment: comment || '同意',
      });
      // 刷新数据
      await Promise.all([loadItems(), loadCounts()]);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || '操作失败';
      return { success: false, error: message };
    }
  }, [loadItems, loadCounts]);

  /**
   * 审批驳回
   */
  const reject = useCallback(async (taskId, comment = '') => {
    try {
      await api.post(`/tasks/${taskId}/reject`, {
        comment: comment || '驳回',
      });
      // 刷新数据
      await Promise.all([loadItems(), loadCounts()]);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || '操作失败';
      return { success: false, error: message };
    }
  }, [loadItems, loadCounts]);

  /**
   * 标记抄送为已读
   */
  const markCcAsRead = useCallback(async (ccId) => {
    try {
      await api.post(`/pending/cc/${ccId}/read`);
      // 刷新数据
      await Promise.all([loadItems(), loadCounts()]);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || err.message || '操作失败';
      return { success: false, error: message };
    }
  }, [loadItems, loadCounts]);

  /**
   * 刷新数据
   */
  const refresh = useCallback(async () => {
    await Promise.all([loadItems(), loadCounts()]);
  }, [loadItems, loadCounts]);

  // 初始加载
  useEffect(() => {
    loadCounts();
  }, [loadCounts]);

  // 标签页或筛选条件变化时重新加载
  useEffect(() => {
    loadItems();
  }, [activeTab, filters, pagination.page]);

  // 计算当前标签页的 badge 数量
  const tabBadges = useMemo(() => ({
    [APPROVAL_TABS.PENDING]: counts.pending,
    [APPROVAL_TABS.INITIATED]: counts.initiated_pending,
    [APPROVAL_TABS.CC]: counts.unread_cc,
    [APPROVAL_TABS.PROCESSED]: 0,
  }), [counts]);

  return {
    // 数据
    items,
    loading,
    error,
    pagination,
    counts,
    tabBadges,

    // 状态
    activeTab,
    filters,

    // 操作
    switchTab,
    updateFilters,
    changePage,
    refresh,
    approve,
    reject,
    markCcAsRead,
  };
}

export default useApprovalCenter;
