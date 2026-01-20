import { useState, useCallback, useEffect } from 'react';
import { customerApi } from '../../../services/api';

/**
 * 客户数据管理 Hook
 */
export function useCustomerData() {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pagination, setPagination] = useState({
        page: 1,
        pageSize: 20,
        total: 0,
    });
    const [filters, setFilters] = useState({
        keyword: '',
        level: '',
        industry: '',
    });

    // 加载客户列表
    const loadCustomers = useCallback(async () => {
        try {
            setLoading(true);
            const params = {
                page: pagination.page,
                page_size: pagination.pageSize,
            };

            if (filters.keyword) params.keyword = filters.keyword;
            if (filters.level && filters.level !== 'all') params.level = filters.level;
            if (filters.industry && filters.industry !== 'all') params.industry = filters.industry;

            const response = await customerApi.list(params);
            const data = response.data || response;

            setCustomers(data.items || data || []);
            if (data.total !== undefined) {
                setPagination(prev => ({ ...prev, total: data.total }));
            }
        } catch (err) {
            console.error('Failed to load customers:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    // 创建客户
    const createCustomer = useCallback(async (data) => {
        try {
            await customerApi.create(data);
            await loadCustomers();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadCustomers]);

    // 更新客户
    const updateCustomer = useCallback(async (id, data) => {
        try {
            await customerApi.update(id, data);
            await loadCustomers();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadCustomers]);

    // 删除客户
    const deleteCustomer = useCallback(async (id) => {
        try {
            await customerApi.delete(id);
            await loadCustomers();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadCustomers]);

    // 获取客户详情
    const getCustomerDetail = useCallback(async (id) => {
        try {
            const response = await customerApi.get(id);
            return response.data || response;
        } catch (err) {
            throw err;
        }
    }, []);

    useEffect(() => {
        loadCustomers();
    }, [loadCustomers]);

    return {
        customers,
        loading,
        error,
        pagination,
        setPagination,
        filters,
        setFilters,
        loadCustomers,
        createCustomer,
        updateCustomer,
        deleteCustomer,
        getCustomerDetail,
    };
}
