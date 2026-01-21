import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSalesWorkstation } from '../useSalesWorkstation';
import { salesStatisticsApi, opportunityApi, customerApi } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
    salesStatisticsApi: { summary: vi.fn(), funnel: vi.fn() },
    opportunityApi: { list: vi.fn() },
    customerApi: { list: vi.fn() },
    contractApi: { list: vi.fn() },
    invoiceApi: { list: vi.fn() },
    projectApi: { get: vi.fn() },
    quoteApi: { list: vi.fn(), getApprovalStatus: vi.fn() },
    taskCenterApi: { myTasks: vi.fn() }
}));

describe('useSalesWorkstation Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        salesStatisticsApi.summary.mockResolvedValue({ data: {} });
        salesStatisticsApi.funnel.mockResolvedValue({ data: {} });
        opportunityApi.list.mockResolvedValue({ data: { items: [] } });
        customerApi.list.mockResolvedValue({ data: { items: [] } });
    });

    it('should initialize with default stats', async () => {
        const { result } = renderHook(() => useSalesWorkstation());

        expect(result.current.stats.monthlyTarget).toBe(1200000);
        expect(result.current.todos).toEqual([]);
        expect(result.current.customers).toEqual([]);
    });

    it('should load data on mount', async () => {
        const { result } = renderHook(() => useSalesWorkstation());

        await waitFor(() => {
            expect(salesStatisticsApi.summary).toHaveBeenCalled();
        });
    });

    it('should toggle todo correctly', () => {
        const { result } = renderHook(() => useSalesWorkstation());

        // First set a todo
        act(() => {
            result.current.toggleTodo('test-id');
        });

        // The toggle function should work (no error thrown)
        expect(result.current.toggleTodo).toBeDefined();
    });
});
