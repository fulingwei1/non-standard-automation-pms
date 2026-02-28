import { useState, useCallback, useEffect } from 'react';
import { communicationApi, customerApi } from '../../../services/api';

/**
 * 客户沟通数据 Hook
 */
export function useCustomerCommunication() {
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [customers, setCustomers] = useState([]);
    const [selectedCustomer, setSelectedCustomer] = useState(null);

    const loadRecords = useCallback(async (customerId = null) => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (customerId) params.customer_id = customerId;

            const response = await communicationApi.list(params);
            setRecords(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadCustomers = useCallback(async () => {
        try {
            const response = await customerApi.list({ page_size: 100 });
            setCustomers(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            console.error('Failed to load customers:', err);
        }
    }, []);

    const createRecord = useCallback(async (data) => {
        try {
            await communicationApi.create(data);
            await loadRecords(selectedCustomer?.id);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadRecords, selectedCustomer]);

    useEffect(() => { loadCustomers(); loadRecords(); }, [loadCustomers, loadRecords]);

    return { records, loading, error, customers, selectedCustomer, setSelectedCustomer, loadRecords, createRecord };
}
