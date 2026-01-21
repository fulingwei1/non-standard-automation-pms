import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useManufacturingDirectorDashboard } from '../useManufacturingDirectorDashboard';

vi.mock('../../../../services/api', () => ({
    productionApi: { getStats: vi.fn(), getDailyReport: vi.fn(), getWorkshops: vi.fn() },
    shortageApi: { getDailyReport: vi.fn() },
    serviceApi: { getStats: vi.fn() },
    materialApi: { getStats: vi.fn() },
    businessSupportApi: { getPendingApprovals: vi.fn() }
}));

describe('useManufacturingDirectorDashboard Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should initialize with default state', () => {
        const { result } = renderHook(() => useManufacturingDirectorDashboard());

        expect(result.current.selectedTab).toBe('overview');
        expect(result.current.selectedDate).toBe('');
        expect(result.current.productionStats).toBe(null);
    });

    it('should handle tab changes', () => {
        const { result } = renderHook(() => useManufacturingDirectorDashboard());

        act(() => {
            result.current.setSelectedTab('production');
        });

        expect(result.current.selectedTab).toBe('production');
    });

    it('should handle date changes', () => {
        const { result } = renderHook(() => useManufacturingDirectorDashboard());

        act(() => {
            result.current.setSelectedDate('2024-01-15');
        });

        expect(result.current.selectedDate).toBe('2024-01-15');
    });
});
