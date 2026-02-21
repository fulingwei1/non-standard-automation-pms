/**
 * useEvaluationTasks Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useEvaluationTasks } from '../useEvaluationTasks';

// Mock API
vi.mock('../services/api', () => ({
  performanceApi: {
    getEvaluationTasks: vi.fn()
  }
}));

// Mock utils
vi.mock('../utils/evaluationTaskUtils', () => ({
  calculateTaskStatistics: vi.fn((tasks) => ({
    total: tasks.length,
    pending: tasks.filter(t => t.status === 'PENDING').length,
    completed: tasks.filter(t => t.status === 'COMPLETED').length
  })),
  filterTasks: vi.fn((tasks, searchTerm, typeFilter) => {
    let filtered = tasks;
    if (searchTerm) {
      filtered = filtered.filter(t => 
        t.name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    if (typeFilter && typeFilter !== 'all') {
      filtered = filtered.filter(t => t.type === typeFilter);
    }
    return filtered;
  })
}));

describe('useEvaluationTasks', () => {
  const mockTasks = [
    { id: 1, name: 'Task 1', status: 'PENDING', period: '2024-01', type: 'SELF' },
    { id: 2, name: 'Task 2', status: 'COMPLETED', period: '2024-01', type: 'PEER' },
    { id: 3, name: 'Task 3', status: 'PENDING', period: '2024-02', type: 'SELF' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    const { performanceApi } = require('../services/api');
    performanceApi.getEvaluationTasks.mockResolvedValue({
      data: { tasks: mockTasks }
    });
  });

  it('should initialize with default state', () => {
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', '', 'all', [])
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.error).toBe(null);
    expect(result.current.tasks).toEqual([]);
  });

  it('should load tasks successfully', async () => {
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', '', 'all', [])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.tasks).toEqual(mockTasks);
    expect(result.current.error).toBe(null);
  });

  it('should filter tasks by period', async () => {
    const { performanceApi } = require('../services/api');
    
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', '', 'all', [])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(performanceApi.getEvaluationTasks).toHaveBeenCalledWith({
      period: '2024-01',
      status_filter: undefined
    });
  });

  it('should filter tasks by status', async () => {
    const { performanceApi } = require('../services/api');
    
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'pending', '', 'all', [])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(performanceApi.getEvaluationTasks).toHaveBeenCalledWith({
      period: '2024-01',
      status_filter: 'PENDING'
    });
  });

  it('should calculate statistics', async () => {
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', '', 'all', [])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.statistics).toEqual({
      total: 3,
      pending: 2,
      completed: 1
    });
  });

  it('should filter tasks by search term', async () => {
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', 'Task 1', 'all', [])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.filteredTasks).toHaveLength(1);
    expect(result.current.filteredTasks[0].name).toBe('Task 1');
  });

  it('should filter tasks by type', async () => {
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', '', 'SELF', [])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.filteredTasks).toHaveLength(2);
  });

  it('should get available periods', async () => {
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', '', 'all', [])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.availablePeriods).toContain('2024-01');
    expect(result.current.availablePeriods).toContain('2024-02');
  });

  it('should handle API errors with fallback', async () => {
    const { performanceApi } = require('../services/api');
    const mockError = new Error('API Error');
    mockError.response = { data: { detail: 'Failed to load' } };
    performanceApi.getEvaluationTasks.mockRejectedValue(mockError);

    const mockFallback = [{ id: 99, name: 'Fallback Task' }];

    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', '', 'all', mockFallback)
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to load');
    expect(result.current.tasks).toEqual(mockFallback);
  });

  it('should support refetch', async () => {
    const { performanceApi } = require('../services/api');
    
    const { result } = renderHook(() => 
      useEvaluationTasks('2024-01', 'all', '', 'all', [])
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(performanceApi.getEvaluationTasks).toHaveBeenCalledTimes(1);

    await result.current.refetch();

    expect(performanceApi.getEvaluationTasks).toHaveBeenCalledTimes(2);
  });

  it('should reload when period changes', async () => {
    const { performanceApi } = require('../services/api');
    
    const { rerender } = renderHook(
      ({ period, status }) => useEvaluationTasks(period, status, '', 'all', []),
      { initialProps: { period: '2024-01', status: 'all' } }
    );

    await waitFor(() => {
      expect(performanceApi.getEvaluationTasks).toHaveBeenCalledTimes(1);
    });

    rerender({ period: '2024-02', status: 'all' });

    await waitFor(() => {
      expect(performanceApi.getEvaluationTasks).toHaveBeenCalledTimes(2);
    });
  });

  it('should reload when status filter changes', async () => {
    const { performanceApi } = require('../services/api');
    
    const { rerender } = renderHook(
      ({ period, status }) => useEvaluationTasks(period, status, '', 'all', []),
      { initialProps: { period: '2024-01', status: 'all' } }
    );

    await waitFor(() => {
      expect(performanceApi.getEvaluationTasks).toHaveBeenCalledTimes(1);
    });

    rerender({ period: '2024-01', status: 'pending' });

    await waitFor(() => {
      expect(performanceApi.getEvaluationTasks).toHaveBeenCalledTimes(2);
    });
  });
});
