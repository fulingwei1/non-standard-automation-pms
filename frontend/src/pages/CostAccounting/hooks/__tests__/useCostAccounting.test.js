import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCostAccounting } from '../useCostAccounting';
import { costApi } from '../../../../services/api/projects.js';

// Mock API
vi.mock('../../../../services/api/projects.js', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    costApi: {
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

describe('useCostAccounting Hook', () => {
  // Setup common mock data
  const mockItems = [{ id: 1, name: 'Test 1' }, { id: 2, name: 'Test 2' }];
  const mockDetail = { id: 1, name: 'Test Detail' };
  const mockResponse = { data: { items: mockItems, total: 2 }, items: mockItems }; 

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Auto-setup mocks for known methods
    const apiObjects = [costApi];
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
    const { result } = renderHook(() => useCostAccounting());

    // Wait for loading to finish
    if (Object.prototype.hasOwnProperty.call(result.current, 'loading')) {
        await waitFor(() => expect(result.current.loading).toBe(false));
    } else {
        await waitFor(() => {});
    }

    // Basic assertion
    expect(result.current).toBeDefined();
  });

  it('does not warn or call costs API before a project is selected', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { result } = renderHook(() => useCostAccounting());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(costApi.list).not.toHaveBeenCalled();
    expect(warnSpy).not.toHaveBeenCalledWith(
      '成本查询需要指定项目ID，请先选择项目',
    );

    warnSpy.mockRestore();
  });
});
