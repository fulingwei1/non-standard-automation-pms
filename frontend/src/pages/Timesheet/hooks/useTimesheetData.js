import { useState, useCallback, useEffect } from 'react';
import { timesheetApi } from '../../../services/api';

/**
 * 工时数据管理 Hook
 */
export function useTimesheetData() {
    const [timesheets, setTimesheets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [viewMode, setViewMode] = useState('week'); // day, week, month

    // 加载工时记录
    const loadTimesheets = useCallback(async () => {
        try {
            setLoading(true);
            const params = {
                date: selectedDate.toISOString().split('T')[0],
                view: viewMode,
            };

            const response = await timesheetApi.list(params);
            const data = response.data || response;
            setTimesheets(data.items || data || []);
        } catch (err) {
            console.error('Failed to load timesheets:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [selectedDate, viewMode]);

    // 创建工时记录
    const createTimesheet = useCallback(async (data) => {
        try {
            await timesheetApi.create(data);
            await loadTimesheets();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadTimesheets]);

    // 更新工时记录
    const updateTimesheet = useCallback(async (id, data) => {
        try {
            await timesheetApi.update(id, data);
            await loadTimesheets();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadTimesheets]);

    // 删除工时记录
    const deleteTimesheet = useCallback(async (id) => {
        try {
            await timesheetApi.delete(id);
            await loadTimesheets();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadTimesheets]);

    // 提交审批
    const submitForApproval = useCallback(async (ids) => {
        try {
            await timesheetApi.submitForApproval(ids);
            await loadTimesheets();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadTimesheets]);

    useEffect(() => {
        loadTimesheets();
    }, [loadTimesheets]);

    return {
        timesheets,
        loading,
        error,
        selectedDate,
        setSelectedDate,
        viewMode,
        setViewMode,
        loadTimesheets,
        createTimesheet,
        updateTimesheet,
        deleteTimesheet,
        submitForApproval,
    };
}
