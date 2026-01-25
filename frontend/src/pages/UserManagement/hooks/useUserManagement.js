import { useState, useCallback, useEffect } from 'react';
import { userApi } from '../../../services/api';

/**
 * 用户管理数据 Hook
 */
export function useUserManagement() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', role: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadUsers = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.role && filters.role !== 'all') params.role = filters.role;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await userApi.list(params);
            // 使用统一响应格式处理（API拦截器自动处理，添加formatted字段）
            const paginatedData = response.formatted || response.data;
            setUsers(paginatedData?.items || paginatedData || []);
            if (paginatedData?.total) setPagination(prev => ({ ...prev, total: paginatedData.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const createUser = useCallback(async (data) => {
        try {
            await userApi.create(data);
            await loadUsers();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadUsers]);

    const updateUser = useCallback(async (id, data) => {
        try {
            await userApi.update(id, data);
            await loadUsers();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadUsers]);

    const resetPassword = useCallback(async (id) => {
        try {
            await userApi.resetPassword(id);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, []);

    useEffect(() => { loadUsers(); }, [loadUsers]);

    return { users, loading, error, filters, setFilters, pagination, setPagination, loadUsers, createUser, updateUser, resetPassword };
}
