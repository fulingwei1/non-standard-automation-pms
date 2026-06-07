import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSearchParams } from 'react-router-dom';
import { usePurchaseOrders } from '../usePurchaseOrders';
import { purchaseApi, supplierApi, projectApi } from '../../../../services/api';

vi.mock('../../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    purchaseApi: {
    list: vi.fn(),
    get: vi.fn(),
    query: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    aiMatch: vi.fn(),
    getOverdue: vi.fn(),
    getAging: vi.fn(),
    getSummary: vi.fn(),
    batch: vi.fn(),
    export: vi.fn(),
    submit: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    start: vi.fn(),
    complete: vi.fn(),
    cancel: vi.fn(),
  },
  supplierApi: {
    list: vi.fn(),
    get: vi.fn(),
    query: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    aiMatch: vi.fn(),
    getOverdue: vi.fn(),
    getAging: vi.fn(),
    getSummary: vi.fn(),
    batch: vi.fn(),
    export: vi.fn(),
    submit: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    start: vi.fn(),
    complete: vi.fn(),
    cancel: vi.fn(),
  },
  projectApi: {
    list: vi.fn(),
    get: vi.fn(),
    query: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    aiMatch: vi.fn(),
    getOverdue: vi.fn(),
    getAging: vi.fn(),
    getSummary: vi.fn(),
    batch: vi.fn(),
    export: vi.fn(),
    submit: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    start: vi.fn(),
    complete: vi.fn(),
    cancel: vi.fn(),
  },
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
    defaults: { baseURL: '/api' },
  },
  };
});

vi.mock('react-router-dom', () => ({
    useSearchParams: vi.fn()
}));

describe('usePurchaseOrders Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
        purchaseApi.list.mockResolvedValue({ data: { items: [] } });
        supplierApi.list.mockResolvedValue({ data: { items: [] } });
        projectApi.list.mockResolvedValue({ data: { items: [] } });
    });

    it('should initialize with default state', async () => {
        const { result } = renderHook(() => usePurchaseOrders());

        await waitFor(() => {
            expect(purchaseApi.list).toHaveBeenCalled();
            expect(projectApi.list).toHaveBeenCalled();
            expect(supplierApi.list).toHaveBeenCalled();
        });

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

    it('should handle modal state', async () => {
        const { result } = renderHook(() => usePurchaseOrders());

        await waitFor(() => {
            expect(purchaseApi.list).toHaveBeenCalled();
            expect(projectApi.list).toHaveBeenCalled();
            expect(supplierApi.list).toHaveBeenCalled();
        });

        act(() => {
            result.current.setShowCreateModal(true);
        });

        expect(result.current.showCreateModal).toBe(true);
    });

    it('scopes purchase orders and defaults new orders by project context', async () => {
        useSearchParams.mockReturnValue([
            new URLSearchParams('project_id=42'),
            vi.fn()
        ]);

        const { result } = renderHook(() => usePurchaseOrders());

        await waitFor(() => {
            expect(purchaseApi.list).toHaveBeenCalledWith(
                expect.objectContaining({
                    page_size: 1000,
                    project_id: '42'
                })
            );
        });

        expect(result.current.newOrder.project_id).toBe('42');
    });
});
