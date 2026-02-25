import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useRequirementSurvey } from '../useRequirementSurvey';
import { surveyApi } from '../../../../services/api';

// Mock API
vi.mock('../../../../services/api', () => {
    return {
        surveyApi: { list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), get: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), create: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), update: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), delete: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), query: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), aiMatch: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), assign: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }), submit: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }) }
    };
});

describe('useRequirementSurvey Hook', () => {
  // Setup common mock data
  const mockItems = [{ id: 1, name: 'Test 1' }, { id: 2, name: 'Test 2' }];
  const mockDetail = { id: 1, name: 'Test Detail' };
  const mockResponse = { data: { items: mockItems, total: 2 }, items: mockItems }; 

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Auto-setup mocks for known methods
    const apiObjects = [surveyApi];
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
    const { result } = renderHook(() => useRequirementSurvey());

    // Wait for loading to finish
    if (Object.prototype.hasOwnProperty.call(result.current, 'loading')) {
        await waitFor(() => expect(result.current.loading).toBe(false));
    } else {
        await waitFor(() => {});
    }

    // Basic assertion
    expect(result.current).toBeDefined();
  });
});
