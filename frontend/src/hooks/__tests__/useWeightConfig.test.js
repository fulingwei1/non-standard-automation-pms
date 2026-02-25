/**
 * useWeightConfig Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useWeightConfig } from '../useWeightConfig';
import { performanceApi } from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  performanceApi: {
    getWeightConfig: vi.fn(),
    updateWeightConfig: vi.fn()
  }
}));

// Mock utils
vi.mock('../../utils/weightConfigUtils', () => ({
  defaultWeights: {
    deptManager: 50,
    projectManager: 50
  }
}));

// Mock confirmAction - always confirms
vi.mock('@/lib/confirmAction', () => ({
  confirmAction: vi.fn().mockResolvedValue(true)
}));

// Mock alert
globalThis.alert = vi.fn();

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
    performanceApi.getWeightConfig.mockResolvedValue(mockWeightResponse);
    performanceApi.updateWeightConfig.mockResolvedValue({ success: true });
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
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.configHistory.length).toBeGreaterThan(0);
    const historyItem = result.current.configHistory[0];
    expect(historyItem).toHaveProperty('id');
    expect(historyItem).toHaveProperty('date');
    expect(historyItem).toHaveProperty('operator');
  });

  it('should update weight value via handleWeightChange', () => {
    const { result } = renderHook(() => useWeightConfig());
    act(() => {
      result.current.handleWeightChange('dept', 70);
    });
    expect(result.current.weights.deptManager).toBe(70);
    expect(result.current.weights.projectManager).toBe(30);
    expect(result.current.isDirty).toBe(true);
  });

  it('should ensure weights sum to 100', () => {
    const { result } = renderHook(() => useWeightConfig());
    act(() => {
      result.current.handleWeightChange('dept', 75);
    });
    expect(result.current.weights.deptManager + result.current.weights.projectManager).toBe(100);
  });

  it('should mark as dirty when weights change', async () => {
    const { result } = renderHook(() => useWeightConfig());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    expect(result.current.isDirty).toBe(false);
    act(() => {
      result.current.handleWeightChange('dept', 65);
    });
    expect(result.current.isDirty).toBe(true);
  });

  it('should save weight configuration', async () => {
    const { result } = renderHook(() => useWeightConfig());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    act(() => {
      result.current.handleWeightChange('dept', 70);
    });
    await act(async () => {
      await result.current.handleSave();
    });
    expect(performanceApi.updateWeightConfig).toHaveBeenCalledWith(
      expect.objectContaining({
        dept_manager_weight: 70,
        project_manager_weight: 30
      })
    );
  });

  it('should set saving state during save', async () => {
    let resolveSave;
    performanceApi.updateWeightConfig.mockReturnValue(new Promise(resolve => { resolveSave = resolve; }));
    const { result } = renderHook(() => useWeightConfig());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    let savePromise;
    act(() => {
      savePromise = result.current.handleSave();
    });

    // Saving state should be true while promise is pending
    await waitFor(() => {
      expect(result.current.isSaving).toBe(true);
    });

    await act(async () => {
      resolveSave({ success: true });
      await savePromise;
    });

    expect(result.current.isSaving).toBe(false);
  });

  it('should reset dirty flag after save', async () => {
    const { result } = renderHook(() => useWeightConfig());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    act(() => {
      result.current.handleWeightChange('dept', 65);
    });
    expect(result.current.isDirty).toBe(true);
    await act(async () => {
      await result.current.handleSave();
    });
    expect(result.current.isDirty).toBe(false);
  });

  it('should handle save error', async () => {
    performanceApi.updateWeightConfig.mockRejectedValue(new Error('Save failed'));
    const { result } = renderHook(() => useWeightConfig());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    await act(async () => {
      await result.current.handleSave();
    });
    // alert should have been called with error message
    expect(globalThis.alert).toHaveBeenCalledWith(expect.stringContaining('保存失败'));
  });

  it('should handle load error with fallback data', async () => {
    performanceApi.getWeightConfig.mockRejectedValue(new Error('Load failed'));
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

  it('should reject negative weights', () => {
    const { result } = renderHook(() => useWeightConfig());
    act(() => {
      result.current.handleWeightChange('dept', -10);
    });
    // Should not change (invalid value rejected)
    expect(result.current.weights.deptManager).toBeGreaterThanOrEqual(0);
  });

  it('should reject weights over 100', () => {
    const { result } = renderHook(() => useWeightConfig());
    act(() => {
      result.current.handleWeightChange('dept', 150);
    });
    expect(result.current.weights.deptManager).toBeLessThanOrEqual(100);
  });

  it('should support reset to default', async () => {
    const { result } = renderHook(() => useWeightConfig());
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    act(() => {
      result.current.handleWeightChange('dept', 80);
    });
    expect(result.current.isDirty).toBe(true);

    await act(async () => {
      await result.current.handleReset();
    });

    expect(result.current.weights).toEqual({
      deptManager: 50,
      projectManager: 50
    });
  });

  it('should update project weight when changing project type', () => {
    const { result } = renderHook(() => useWeightConfig());
    act(() => {
      result.current.handleWeightChange('project', 70);
    });
    expect(result.current.weights.projectManager).toBe(70);
    expect(result.current.weights.deptManager).toBe(30);
  });
});
