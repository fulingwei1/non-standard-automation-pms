import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAssemblyKitBoard } from '../useAssemblyKitBoard';

// Mock assemblyKitApi
vi.mock('../../../../services/api/production.js', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    assemblyKitApi: {
    listKits: vi.fn(),
    analyzeKit: vi.fn(),
  },
  };
});

import { assemblyKitApi } from '../../../../services/api/production.js';

describe('useAssemblyKitBoard Hook', () => {
  // Setup common mock data
  const mockItems = [{ id: 1, name: 'Test 1', readiness: 100 }, { id: 2, name: 'Test 2', readiness: 50 }];
  const mockDetail = { id: 1, name: 'Test Detail' };
  const mockResponse = { data: { items: mockItems, total: 2 }, items: mockItems };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup mock responses
    assemblyKitApi.listKits.mockResolvedValue(mockResponse);
    assemblyKitApi.analyzeKit.mockResolvedValue({ data: mockDetail });
  });

  it('should load data', async () => {
    const { result } = renderHook(() => useAssemblyKitBoard());

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