import { useState, useCallback, useEffect } from 'react';
import { timesheetApi } from '../../../services/api';

export function useTimesheetBatchOperations() {
    const [timesheets, setTimesheets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedIds, setSelectedIds] = useState([]);

    const loadTimesheets = useCallback(async () => {
        try {
            setLoading(true);
            const response = await timesheetApi.listPending();
            setTimesheets(response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, []);

    const approveBatch = useCallback(async (ids) => {
        try { await timesheetApi.batchApprove(ids); await loadTimesheets(); setSelectedIds([]); return { success: true }; }
        catch (err) { return { success: false, error: err.message }; }
    }, [loadTimesheets]);

    useEffect(() => { loadTimesheets(); }, [loadTimesheets]);
    return { timesheets, loading, selectedIds, setSelectedIds, loadTimesheets, approveBatch };
}
