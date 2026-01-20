import { useState, useCallback, useEffect } from 'react';
import { purchaseRequestApi, projectApi } from '../../../services/api';

/**
 * 采购申请新建数据 Hook
 */
export function usePurchaseRequestNew() {
    const [projects, setProjects] = useState([]);
    const [materials, setMaterials] = useState([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    const loadProjects = useCallback(async () => {
        try {
            const response = await projectApi.list({ status: 'active', page_size: 100 });
            setProjects(response.data?.items || response.data || []);
        } catch (err) {
            console.error('Failed to load projects:', err);
        }
    }, []);

    const loadMaterials = useCallback(async (projectId) => {
        if (!projectId) return;
        try {
            setLoading(true);
            const response = await purchaseRequestApi.getMaterials(projectId);
            setMaterials(response.data || response || []);
        } catch (err) {
            console.error('Failed to load materials:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createRequest = useCallback(async (data) => {
        try {
            setSubmitting(true);
            await purchaseRequestApi.create(data);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        } finally {
            setSubmitting(false);
        }
    }, []);

    useEffect(() => { loadProjects(); }, [loadProjects]);

    return { projects, materials, loading, submitting, loadProjects, loadMaterials, createRequest };
}
