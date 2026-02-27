/**
 * useMonthlySummary Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMonthlySummary } from '../useMonthlySummary';
import { performanceApi } from '../../services/api';

// Mock API
vi.mock('../../services/api', async (importOriginal) => {
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

// Mock utils
vi.mock('../../utils/monthlySummaryUtils', () => ({
  getCurrentPeriod: vi.fn(() => ({
    period: '2024-01',
    year: 2024,
    month: 1
  }))
}));

// Mock confirmAction - always confirms
vi.mock('@/lib/confirmAction', () => ({
  confirmAction: vi.fn().mockResolvedValue(true)
}));

// Mock alert
globalThis.alert = vi.fn();

describe('useMonthlySummary', () => {
  const mockHistory = [
    { id: 1, period: '2024-01', submit_date: '2024-01-28', status: 'COMPLETED' },
    { id: 2, period: '2023-12', submit_date: '2023-12-28', status: 'DRAFT' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    performanceApi.getMonthlySummaryHistory.mockResolvedValue({ data: mockHistory });
    performanceApi.saveMonthlySummaryDraft.mockResolvedValue({ success: true });
    performanceApi.createMonthlySummary.mockResolvedValue({ success: true });
  });

  it('should initialize with default form data', () => {
    const { result } = renderHook(() => useMonthlySummary());
    expect(result.current.formData.period).toBe('2024-01');
    expect(result.current.formData.workContent).toBe('');
    expect(result.current.formData.selfEvaluation).toBe('');
    expect(result.current.isDraft).toBe(true);
  });

  it('should handle input change', () => {
    const { result } = renderHook(() => useMonthlySummary());
    act(() => {
      result.current.handleInputChange('workContent', 'New work content');
    });
    expect(result.current.formData.workContent).toBe('New work content');
    expect(result.current.isDraft).toBe(true);
  });

  it('should handle multiple field changes', () => {
    const { result } = renderHook(() => useMonthlySummary());
    act(() => {
      result.current.handleInputChange('workContent', 'Work');
      result.current.handleInputChange('selfEvaluation', 'Evaluation');
      result.current.handleInputChange('highlights', 'Highlights');
    });
    expect(result.current.formData.workContent).toBe('Work');
    expect(result.current.formData.selfEvaluation).toBe('Evaluation');
    expect(result.current.formData.highlights).toBe('Highlights');
  });

  it('should load history successfully', async () => {
    const { result } = renderHook(() => useMonthlySummary());
    await act(async () => {
      await result.current.loadHistory();
    });
    expect(result.current.history).toEqual(mockHistory);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should handle history loading error with fallback', async () => {
    performanceApi.getMonthlySummaryHistory.mockRejectedValue(new Error('Failed to load'));
    const { result } = renderHook(() => useMonthlySummary());
    await act(async () => {
      await result.current.loadHistory();
    });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.history.length).toBeGreaterThan(0);
  });

  it('should toggle show history', () => {
    const { result } = renderHook(() => useMonthlySummary());
    expect(result.current.showHistory).toBe(false);
    act(() => { result.current.setShowHistory(true); });
    expect(result.current.showHistory).toBe(true);
    act(() => { result.current.setShowHistory(false); });
    expect(result.current.showHistory).toBe(false);
  });

  it('should save draft successfully', async () => {
    const { result } = renderHook(() => useMonthlySummary());
    act(() => {
      result.current.handleInputChange('workContent', 'Draft work');
    });
    await act(async () => {
      await result.current.handleSaveDraft();
    });
    expect(performanceApi.saveMonthlySummaryDraft).toHaveBeenCalledWith(
      '2024-01',
      expect.objectContaining({ work_content: 'Draft work' })
    );
    expect(result.current.isSaving).toBe(false);
    expect(result.current.isDraft).toBe(false);
  });

  it('should handle draft save error', async () => {
    performanceApi.saveMonthlySummaryDraft.mockRejectedValue(new Error('Save failed'));
    const { result } = renderHook(() => useMonthlySummary());
    await act(async () => {
      await result.current.handleSaveDraft();
    });
    expect(result.current.isSaving).toBe(false);
    expect(result.current.error).toBeTruthy();
  });

  it('should submit summary successfully', async () => {
    const mockNavigate = vi.fn();
    const { result } = renderHook(() => useMonthlySummary());
    act(() => {
      result.current.handleInputChange('workContent', 'Completed work');
      result.current.handleInputChange('selfEvaluation', 'Good performance');
    });
    await act(async () => {
      await result.current.handleSubmit(mockNavigate);
    });
    expect(performanceApi.createMonthlySummary).toHaveBeenCalledWith(
      expect.objectContaining({
        period: '2024-01',
        work_content: 'Completed work',
        self_evaluation: 'Good performance'
      })
    );
    expect(result.current.isSubmitting).toBe(false);
    expect(mockNavigate).toHaveBeenCalledWith('/personal/my-performance');
  });

  it('should validate required fields before submit', async () => {
    const mockNavigate = vi.fn();
    const { result } = renderHook(() => useMonthlySummary());
    // Don't fill required fields
    await act(async () => {
      await result.current.handleSubmit(mockNavigate);
    });
    expect(performanceApi.createMonthlySummary).not.toHaveBeenCalled();
    expect(globalThis.alert).toHaveBeenCalledWith('请填写本月工作内容');
  });

  it('should handle submit error', async () => {
    performanceApi.createMonthlySummary.mockRejectedValue(new Error('Submit failed'));
    const mockNavigate = vi.fn();
    const { result } = renderHook(() => useMonthlySummary());
    act(() => {
      result.current.handleInputChange('workContent', 'Work');
      result.current.handleInputChange('selfEvaluation', 'Eval');
    });
    await act(async () => {
      await result.current.handleSubmit(mockNavigate);
    });
    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.error).toBeTruthy();
  });

  it('should provide all form fields', () => {
    const { result } = renderHook(() => useMonthlySummary());
    expect(result.current.formData).toHaveProperty('period');
    expect(result.current.formData).toHaveProperty('workContent');
    expect(result.current.formData).toHaveProperty('selfEvaluation');
    expect(result.current.formData).toHaveProperty('highlights');
    expect(result.current.formData).toHaveProperty('problems');
    expect(result.current.formData).toHaveProperty('nextMonthPlan');
  });

  it('should provide all necessary methods', () => {
    const { result } = renderHook(() => useMonthlySummary());
    expect(typeof result.current.handleInputChange).toBe('function');
    expect(typeof result.current.handleSaveDraft).toBe('function');
    expect(typeof result.current.handleSubmit).toBe('function');
    expect(typeof result.current.loadHistory).toBe('function');
    expect(typeof result.current.setShowHistory).toBe('function');
  });

  it('should expose currentPeriod', () => {
    const { result } = renderHook(() => useMonthlySummary());
    expect(result.current.currentPeriod).toEqual({
      period: '2024-01',
      year: 2024,
      month: 1
    });
  });
});
