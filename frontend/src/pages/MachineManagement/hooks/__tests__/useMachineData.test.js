import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useMachineData } from '../useMachineData';

// Mock the API module
vi.mock('../../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    machineApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
  projectApi: {
    get: vi.fn(),
  },
  };
});

import { machineApi, projectApi } from '../../../../services/api';

describe('useMachineData Hook', () => {
  // Setup common mock data
  const mockItems = [
    { id: 1, machine_code: 'MCH-001', machine_name: 'Test 1', status: 'running', health: 'good', progress: 50 },
    { id: 2, machine_code: 'MCH-002', machine_name: 'Test 2', status: 'idle', health: 'good', progress: 30 }
  ];
  const mockDetail = { id: 1, machine_code: 'MCH-001', machine_name: 'Test Detail', status: 'running', health: 'good', progress: 50 };
  const mockResponse = { data: { items: mockItems, total: 2 } };

  beforeEach(() => {
    vi.clearAllMocks();
    // Setup mock responses
    machineApi.list.mockResolvedValue(mockResponse);
    machineApi.get.mockResolvedValue({ data: mockDetail });
    projectApi.get.mockResolvedValue({ data: { project_name: 'Test Project' } });
  });

  it('should load data', async () => {
    const { result } = renderHook(() => useMachineData('proj-1'));

    // Wait for loading to finish
    await waitFor(() => expect(result.current.loading).toBe(false));

    // Basic assertion - verify hook returns data
    expect(result.current).toBeDefined();
    expect(result.current.machines).toBeDefined();
  });
});