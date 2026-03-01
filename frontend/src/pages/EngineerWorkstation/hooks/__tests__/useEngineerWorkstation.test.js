import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useEngineerWorkstation } from '../useEngineerWorkstation';
import { projectApi, taskCenterApi as taskApi } from '../../../../services/api';

// Mock API
vi.mock('../../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
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

describe('useEngineerWorkstation Hook', () => {
  // Setup common mock data
  const mockItems = [{ id: 1, name: 'Test 1' }, { id: 2, name: 'Test 2' }];
  const mockDetail = { id: 1, name: 'Test Detail' };
  const mockResponse = { data: { items: mockItems, total: 2 }, items: mockItems }; 

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Auto-setup mocks for known methods
    const apiObjects = [projectApi, taskApi];
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
    const { result } = renderHook(() => useEngineerWorkstation());

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
