import { useState, useCallback, useEffect } from 'react';
import { adminApi as settingsApi } from '../../../services/api';

/**
 * 系统设置数据 Hook
 */
export function useSettings() {
    const [settings, setSettings] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    const loadSettings = useCallback(async () => {
        try {
            setLoading(true);
            const response = await settingsApi.get();
            setSettings(response.data || response || {});
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const updateSettings = useCallback(async (data) => {
        try {
            setSaving(true);
            await settingsApi.update(data);
            await loadSettings();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        } finally {
            setSaving(false);
        }
    }, [loadSettings]);

    const resetSettings = useCallback(async (category) => {
        try {
            setSaving(true);
            await settingsApi.reset(category);
            await loadSettings();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        } finally {
            setSaving(false);
        }
    }, [loadSettings]);

    useEffect(() => { loadSettings(); }, [loadSettings]);

    return { settings, loading, saving, error, loadSettings, updateSettings, resetSettings };
}
