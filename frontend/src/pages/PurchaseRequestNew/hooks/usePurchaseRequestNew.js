import { useState, useCallback, useEffect } from 'react';
import { purchaseApi as purchaseRequestApi, projectApi } from '../../../services/api';

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
            setLoading(true);
            const response = await projectApi.list({ status: 'active', page_size: 100 });
            // 防御性处理：确保 projects 始终为数组
            setProjects(Array.isArray(response.data?.items) ? response.data.items : Array.isArray(response.data) ? response.data : []);
        } catch (_err) {
          // 非关键操作失败时静默降级
        } finally {
            setLoading(false);
        }
    }, []);

    const loadMaterials = useCallback(async (projectId) => {
        if (!projectId) return;
        try {
            setLoading(true);
            const response = await purchaseRequestApi.getMaterials(projectId);
            // 防御性处理：确保 materials 始终为数组
            setMaterials(Array.isArray(response.data?.items) ? response.data.items : Array.isArray(response.data) ? response.data : []);
        } catch (_err) {
          // 非关键操作失败时静默降级
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
