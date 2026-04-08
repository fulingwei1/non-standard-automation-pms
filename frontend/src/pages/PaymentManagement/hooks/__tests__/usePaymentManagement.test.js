import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePaymentManagement } from '../usePaymentManagement';
import { paymentApi, receivableApi } from '../../../../services/api';

vi.mock('../../../../services/api', async () => {
  return {
    __esModule: true,
    paymentApi: {
      list: vi.fn(),
      get: vi.fn(),
      getReminders: vi.fn(),
      getStatistics: vi.fn(),
    },
    receivableApi: {
      list: vi.fn(),
      get: vi.fn(),
      getAging: vi.fn(),
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

describe('usePaymentManagement Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        paymentApi.list.mockResolvedValue({ data: { items: [], total: 0 } });
        paymentApi.getReminders.mockResolvedValue({ data: { items: [] } });
        paymentApi.getStatistics.mockResolvedValue({data: { items: [] }});
        receivableApi.getAging.mockResolvedValue({data: { items: [] }});
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
