import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePurchaseOrders } from '../usePurchaseOrders';
import { purchaseApi, supplierApi, projectApi } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
    purchaseApi: {
        list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
        create: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
        update: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
        delete: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
        submitApproval: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
        receiveGoods: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } })
    },
    supplierApi: { list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }) },
    projectApi: { list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }) }
}));

vi.mock('react-router-dom', () => ({
    useSearchParams: () => [new URLSearchParams()]
}));

describe('usePurchaseOrders Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        purchaseApi.list.mockResolvedValue({ data: { items: [] } });
        supplierApi.list.mockResolvedValue({ data: { items: [] } });
        projectApi.list.mockResolvedValue({ data: { items: [] } });
    });

    it('should initialize with default state', async () => {
        const { result } = renderHook(() => usePurchaseOrders());

        expect(result.current.statusFilter).toBe('all');
        expect(result.current.showCreateModal).toBe(false);
        expect(result.current.orders).toEqual([]);
    });

    it('should load orders on mount', async () => {
        renderHook(() => usePurchaseOrders());

        await waitFor(() => {
            expect(purchaseApi.list).toHaveBeenCalled();
        });
    });

    it('should handle modal state', () => {
        const { result } = renderHook(() => usePurchaseOrders());

        act(() => {
            result.current.setShowCreateModal(true);
        });

        expect(result.current.showCreateModal).toBe(true);
    });
});
