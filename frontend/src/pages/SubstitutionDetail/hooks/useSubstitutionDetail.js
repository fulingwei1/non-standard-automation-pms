import { useState, useCallback, useEffect } from 'react';
import { substitutionApi } from '../../../services/api';

export function useSubstitutionDetail(substitutionId) {
    const [substitution, setSubstitution] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadSubstitution = useCallback(async () => {
        if (!substitutionId) return;
        try {
            setLoading(true);
            const response = await substitutionApi.get(substitutionId);
            setSubstitution(response.data || response);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [substitutionId]);

    const approve = useCallback(async () => {
        try { await substitutionApi.approve(substitutionId); await loadSubstitution(); return { success: true }; }
        catch (err) { return { success: false, error: err.message }; }
    }, [substitutionId, loadSubstitution]);

    useEffect(() => { loadSubstitution(); }, [loadSubstitution]);
    return { substitution, loading, loadSubstitution, approve };
}
