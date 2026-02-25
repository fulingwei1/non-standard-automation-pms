import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePaymentManagement } from '../usePaymentManagement';
import { paymentApi, receivableApi } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
    paymentApi: { list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), getReminders: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), getStatistics: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }) },
    receivableApi: { getAging: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }) }
}));

describe('usePaymentManagement Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        paymentApi.list.mockResolvedValue({ data: { items: [], total: 0 } });
        paymentApi.getReminders.mockResolvedValue({ data: { items: [] } });
        paymentApi.getStatistics.mockResolvedValue({ data: {} });
        receivableApi.getAging.mockResolvedValue({ data: {} });
    });

    it('should initialize with default state', async () => {
        const { result } = renderHook(() => usePaymentManagement());

        expect(result.current.viewMode).toBe('list');
        expect(result.current.selectedStatus).toBe('all');
        expect(result.current.payments).toEqual([]);
    });

    it('should load payments on mount', async () => {
        renderHook(() => usePaymentManagement());

        await waitFor(() => {
            expect(paymentApi.list).toHaveBeenCalled();
        });
    });

    it('should handle filter state changes', () => {
        const { result } = renderHook(() => usePaymentManagement());

        act(() => {
            result.current.setSelectedStatus('paid');
        });

        expect(result.current.selectedStatus).toBe('paid');
    });
});
