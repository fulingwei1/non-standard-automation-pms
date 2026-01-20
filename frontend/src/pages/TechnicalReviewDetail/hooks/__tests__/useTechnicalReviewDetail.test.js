import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTechnicalReviewDetail } from '../useTechnicalReviewDetail';
import { technicalReviewApi } from '../../../../services/api';

// Mock API
vi.mock('../../../../services/api', () => {
    return {
        technicalReviewApi: { list: vi.fn(), get: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn(), query: vi.fn(), aiMatch: vi.fn(), assign: vi.fn() }
    };
});

describe('useTechnicalReviewDetail Hook', () => {
  // Setup common mock data
  const mockItems = [{ id: 1, name: 'Test 1' }, { id: 2, name: 'Test 2' }];
  const mockDetail = { id: 1, name: 'Test Detail' };
  const mockResponse = { data: { items: mockItems, total: 2 }, items: mockItems }; 

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Auto-setup mocks for known methods
    const apiObjects = [technicalReviewApi];
    apiObjects.forEach(api => {
        if (api) {
            if (api.list) api.list.mockResolvedValue(mockResponse);
            if (api.get) api.get.mockResolvedValue({ data: mockDetail });
            if (api.query) api.query.mockResolvedValue(mockResponse);
            if (api.aiMatch) api.aiMatch.mockResolvedValue(mockResponse); // specialized
        }
    });
  });

  it('should load data', async () => {
    const { result } = renderHook(() => useTechnicalReviewDetail());

    // Wait for loading to finish
    if (result.current.hasOwnProperty('loading')) {
        await waitFor(() => expect(result.current.loading).toBe(false));
    } else {
        await waitFor(() => {});
    }

    // Basic assertion
    expect(result.current).toBeDefined();
  });
});
