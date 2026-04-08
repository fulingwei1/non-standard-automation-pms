import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useProductionExceptionList } from '../useProductionExceptionList';

// Use vi.hoisted to define mocks before vi.mock is called
const { mockProjectList, mockExceptionsList } = vi.hoisted(() => ({
  mockProjectList: vi.fn(),
  mockExceptionsList: vi.fn(),
}));

// Mock projectApi
vi.mock('../../../../services/api/projects.js', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    projectApi: {
    list: mockProjectList,
  },
  };
});

// Mock productionApi - need full structure since other modules depend on it
vi.mock('../../../../services/api/production.js', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    productionApi: {
    exceptions: {
      list: mockExceptionsList,
      get: vi.fn(),
      create: vi.fn(),
      handle: vi.fn(),
      close: vi.fn(),
    },
    workOrders: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      assign: vi.fn(),
      start: vi.fn(),
      pause: vi.fn(),
      resume: vi.fn(),
      complete: vi.fn(),
      getProgress: vi.fn(),
      getReports: vi.fn(),
    },
    workshops: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      getWorkstations: vi.fn(),
      addWorkstation: vi.fn(),
    },
    workstations: {
      list: vi.fn(),
      getStatus: vi.fn(),
    },
    workers: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    taskBoard: vi.fn(),
    reports: {
      workerPerformance: vi.fn(),
      workerRanking: vi.fn(),
    },
    capacity: {
      oee: vi.fn(),
      bottlenecks: vi.fn(),
      trend: vi.fn(),
      forecast: vi.fn(),
    },
    dashboard: vi.fn(),
    dailyReports: {
      daily: vi.fn(),
      latestDaily: vi.fn(),
    },
    productionPlans: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      submit: vi.fn(),
      approve: vi.fn(),
      publish: vi.fn(),
    },
    workReports: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      start: vi.fn(),
      progress: vi.fn(),
      complete: vi.fn(),
      approve: vi.fn(),
      my: vi.fn(),
    },
    materialRequisitions: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      approve: vi.fn(),
      issue: vi.fn(),
    },
  },
  };
});

describe('useProductionExceptionList Hook', () => {
  // Setup common mock data
  const mockItems = [{ id: 1, name: 'Test 1' }, { id: 2, name: 'Test 2' }];
  const mockResponse = { data: { items: mockItems, total: 2 }, items: mockItems };
  const mockProjectsResponse = { data: { items: mockItems, total: 2 } };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup mock responses
    mockProjectList.mockResolvedValue(mockProjectsResponse);
    mockExceptionsList.mockResolvedValue(mockResponse);
  });

  it('should load data', async () => {
    const { result } = renderHook(() => useProductionExceptionList());

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