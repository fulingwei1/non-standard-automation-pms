import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCustomerManagement } from '../useCustomerManagement';
import { customerApi } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
    customerApi: {
        list: vi.fn(),
        get: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
        get360: vi.fn()
    }
}));

describe('useCustomerManagement Hook', () => {
    const mockCustomers = [
        { id: 1, customer_name: 'Customer A', industry: 'Tech' },
        { id: 2, customer_name: 'Customer B', industry: 'Finance' }
    ];

    beforeEach(() => {
        vi.clearAllMocks();
        customerApi.list.mockResolvedValue({
            data: { items: mockCustomers, total: 2 }
        });
    });

    it('should load customers on mount', async () => {
        const { result } = renderHook(() => useCustomerManagement());

        expect(result.current.loading).toBe(true);

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(customerApi.list).toHaveBeenCalled();
        expect(result.current.customers).toHaveLength(2);
        expect(result.current.total).toBe(2);
    });

    it('should handle create customer', async () => {
        customerApi.create.mockResolvedValue({ data: { id: 3 } });
        const { result } = renderHook(() => useCustomerManagement());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        await act(async () => {
            await result.current.handleCreate({ customer_name: 'New Customer' });
        });

        expect(customerApi.create).toHaveBeenCalled();
        expect(result.current.showCreateDialog).toBe(false);
    });

    it('should extract industries from customers', async () => {
        const { result } = renderHook(() => useCustomerManagement());

        await waitFor(() => {
            expect(result.current.industries).toEqual(['Finance', 'Tech']);
        });
    });

    it('should handle filtering', async () => {
        const { result } = renderHook(() => useCustomerManagement());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        act(() => {
            result.current.setFilterIndustry('Tech');
        });

        await waitFor(() => {
            expect(customerApi.list).toHaveBeenCalledWith(
                expect.objectContaining({ industry: 'Tech' })
            );
        });
    });
});
