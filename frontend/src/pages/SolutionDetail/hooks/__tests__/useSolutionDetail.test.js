import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSolutionDetail } from '../useSolutionDetail';
import { presaleApi } from '../../../../services/api';
import { useParams } from 'react-router-dom';

vi.mock('react-router-dom', () => ({
    useParams: vi.fn()
}));

vi.mock('../../../../services/api', () => ({
    presaleApi: {
        solutions: {
            get: vi.fn(),
            getCost: vi.fn()
        }
    }
}));

describe('useSolutionDetail Hook', () => {
    const mockSolution = {
        id: 1,
        solution_no: 'SOL-1',
        name: 'Test Solution',
        customer_name: 'Test Customer',
        version: 'V1.0',
        status: 'draft',
        progress: 50,
        estimated_cost: 1000000,
        tags: ['tag1'],
        description: 'desc',
        tech_specs: {
            productInfo: {},
            capacity: {},
            testItems: [],
            testStandards: [],
            environment: {}
        },
        equipment: {
            main: [],
            auxiliary: [],
            software: [],
            fixtures: []
        },
        deliverables: []
    };
    const mockCost = {
        total_cost: 1000,
        gross_margin: 20
    };

    beforeEach(() => {
        vi.clearAllMocks();
        useParams.mockReturnValue({ id: '1' });
        presaleApi.solutions.get.mockResolvedValue({ data: mockSolution });
        presaleApi.solutions.getCost.mockResolvedValue({ data: mockCost });
    });

    it('should load solution and cost', async () => {
        const { result } = renderHook(() => useSolutionDetail());

        expect(result.current.loading).toBe(true);
        await waitFor(() => expect(result.current.loading).toBe(false));

        expect(presaleApi.solutions.get).toHaveBeenCalledWith('1');
        expect(presaleApi.solutions.getCost).toHaveBeenCalledWith('1');

        expect(result.current.solution.name).toBe('Test Solution');
        expect(result.current.costEstimate).toEqual(mockCost);
    });

    it('should handle load error', async () => {
        presaleApi.solutions.get.mockRejectedValue({ message: 'Error' });

        const { result } = renderHook(() => useSolutionDetail());
        await waitFor(() => expect(result.current.loading).toBe(false));

        expect(result.current.error).toBeTruthy();
    });

    it('should switch tabs', () => {
        const { result } = renderHook(() => useSolutionDetail());
        act(() => {
            result.current.setActiveTab('cost');
        });
        expect(result.current.activeTab).toBe('cost');
    });
});
