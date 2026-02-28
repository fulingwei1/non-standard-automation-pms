import { useState, useCallback, useEffect } from 'react';
import { qualificationApi } from '../../../services/api';

/**
 * 资质管理数据 Hook
 */
export function useQualificationData() {
    const [qualifications, setQualifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ type: '', status: '' });

    const loadQualifications = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.status && filters.status !== 'all') params.status = filters.status;

            const response = await qualificationApi.list(params);
            setQualifications(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const createQualification = useCallback(async (data) => {
        try {
            await qualificationApi.create(data);
            await loadQualifications();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadQualifications]);

    const renewQualification = useCallback(async (id, data) => {
        try {
            await qualificationApi.renew(id, data);
            await loadQualifications();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadQualifications]);

    useEffect(() => { loadQualifications(); }, [loadQualifications]);

    return { qualifications, loading, error, filters, setFilters, loadQualifications, createQualification, renewQualification };
}
