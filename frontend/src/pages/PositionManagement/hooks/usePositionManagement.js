import { useState, useCallback, useEffect } from 'react';
import { positionApi } from '../../../services/api';

/**
 * 职位管理数据 Hook
 */
export function usePositionManagement() {
    const [positions, setPositions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadPositions = useCallback(async () => {
        try {
            setLoading(true);
            const response = await positionApi.list({ page_size: 100 });
            setPositions(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const createPosition = useCallback(async (data) => {
        try {
            await positionApi.create(data);
            await loadPositions();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadPositions]);

    const updatePosition = useCallback(async (id, data) => {
        try {
            await positionApi.update(id, data);
            await loadPositions();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadPositions]);

    const deletePosition = useCallback(async (id) => {
        try {
            await positionApi.delete(id);
            await loadPositions();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadPositions]);

    useEffect(() => { loadPositions(); }, [loadPositions]);

    return { positions, loading, error, loadPositions, createPosition, updatePosition, deletePosition };
}
