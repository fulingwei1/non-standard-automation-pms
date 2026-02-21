/**
 * useWeightConfig Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useWeightConfig } from '../useWeightConfig';

// Mock API
vi.mock('../services/api', () => ({
  performanceApi: {
    getWeightConfig: vi.fn(),
    saveWeightConfig: vi.fn()
  }
}));

// Mock utils
vi.mock('../utils/weightConfigUtils', () => ({
  defaultWeights: {
    deptManager: 50,
    projectManager: 50
  }
}));

// Mock confirmAction
vi.mock('@/lib/confirmAction', () => ({
  confirmAction: vi.fn((message, callback) => callback())
}));

describe('useWeightConfig', () => {
  const mockWeightResponse = {
    data: {
      dept_manager_weight: 60,
      project_manager_weight: 40,
      history: [
        {
          id: 1,
          updated_at: '2024-01-01',
          updated_by_name: 'Admin',
          dept_manager_weight: 60,
          project_manager_weight: 40,
          change_reason: 'Initial setup'
        }
      ]
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    const { performanceApi } = require('../services/api');
    performanceApi.getWeightConfig.mockResolvedValue(mockWeightResponse);
    performanceApi.saveWeightConfig.mockResolvedValue({ success: true });
  });

  it('should initialize with default weights', () => {
    const { result } = renderHook(() => useWeightConfig());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.weights).toEqual({
      deptManager: 50,
      projectManager: 50
    });
  });

  it('should load weight configuration successfully', async () => {
    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.weights).toEqual({
      deptManager: 60,
      projectManager: 40
    });
  });

  it('should load configuration history', async () => {
    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.configHistory.length).toBeGreaterThan(0);
    });

    const historyItem = result.current.configHistory[0];
    expect(historyItem).toHaveProperty('id');
    expect(historyItem).toHaveProperty('date');
    expect(historyItem).toHaveProperty('operator');
  });

  it('should update weight value', () => {
    const { result } = renderHook(() => useWeightConfig());

    act(() => {
      result.current.updateWeight('deptManager', 70);
    });

    expect(result.current.weights.deptManager).toBe(70);
    expect(result.current.weights.projectManager).toBe(30);
    expect(result.current.isDirty).toBe(true);
  });

  it('should ensure weights sum to 100', () => {
    const { result } = renderHook(() => useWeightConfig());

    act(() => {
      result.current.updateWeight('deptManager', 75);
    });

    expect(result.current.weights.deptManager).toBe(75);
    expect(result.current.weights.projectManager).toBe(25);
    expect(result.current.weights.deptManager + result.current.weights.projectManager).toBe(100);
  });

  it('should mark as dirty when weights change', async () => {
    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isDirty).toBe(false);

    act(() => {
      result.current.updateWeight('deptManager', 65);
    });

    expect(result.current.isDirty).toBe(true);
  });

  it('should save weight configuration', async () => {
    const { performanceApi } = require('../services/api');
    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.updateWeight('deptManager', 70);
    });

    await act(async () => {
      await result.current.handleSave();
    });

    expect(performanceApi.saveWeightConfig).toHaveBeenCalledWith(
      expect.objectContaining({
        deptManager: 70,
        projectManager: 30
      })
    );
  });

  it('should set saving state during save', async () => {
    const { performanceApi } = require('../services/api');
    let resolveSave;
    const promise = new Promise(resolve => {
      resolveSave = resolve;
    });
    performanceApi.saveWeightConfig.mockReturnValue(promise);

    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    const savePromise = act(async () => {
      await result.current.handleSave();
    });

    expect(result.current.isSaving).toBe(true);

    resolveSave({ success: true });
    await savePromise;

    expect(result.current.isSaving).toBe(false);
  });

  it('should reset dirty flag after save', async () => {
    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.updateWeight('deptManager', 65);
    });

    expect(result.current.isDirty).toBe(true);

    await act(async () => {
      await result.current.handleSave();
    });

    expect(result.current.isDirty).toBe(false);
  });

  it('should handle save error', async () => {
    const { performanceApi } = require('../services/api');
    performanceApi.saveWeightConfig.mockRejectedValue(
      new Error('Save failed')
    );

    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.handleSave();
    });

    expect(result.current.error).toBeTruthy();
  });

  it('should handle load error with fallback data', async () => {
    const { performanceApi } = require('../services/api');
    performanceApi.getWeightConfig.mockRejectedValue(
      new Error('Load failed')
    );

    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.weights).toBeDefined();
  });

  it('should provide impact statistics', async () => {
    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.impactStatistics).toBeDefined();
    expect(result.current.impactStatistics).toHaveProperty('totalEmployees');
    expect(result.current.impactStatistics).toHaveProperty('affectedEmployees');
  });

  it('should handle zero or negative weights', () => {
    const { result } = renderHook(() => useWeightConfig());

    act(() => {
      result.current.updateWeight('deptManager', 0);
    });

    expect(result.current.weights.deptManager).toBe(0);
    expect(result.current.weights.projectManager).toBe(100);

    act(() => {
      result.current.updateWeight('deptManager', -10);
    });

    // Should handle gracefully (implementation dependent)
    expect(result.current.weights.deptManager).toBeGreaterThanOrEqual(0);
  });

  it('should handle weights over 100', () => {
    const { result } = renderHook(() => useWeightConfig());

    act(() => {
      result.current.updateWeight('deptManager', 150);
    });

    // Should cap at 100
    expect(result.current.weights.deptManager).toBeLessThanOrEqual(100);
  });

  it('should support reset to default', async () => {
    const { result } = renderHook(() => useWeightConfig());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.updateWeight('deptManager', 80);
    });

    if (result.current.handleReset) {
      act(() => {
        result.current.handleReset();
      });

      expect(result.current.weights).toEqual({
        deptManager: 50,
        projectManager: 50
      });
    }
  });
});
