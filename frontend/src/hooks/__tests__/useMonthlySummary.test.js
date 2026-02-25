/**
 * useMonthlySummary Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useMonthlySummary } from '../useMonthlySummary';
import { performanceApi } from '../../services/api';

// Mock API
vi.mock('../../services/api', () => ({
  performanceApi: {
    getMonthlySummaryHistory: vi.fn(),
    saveDraft: vi.fn(),
    submitSummary: vi.fn()
  }
}));

// Mock utils
vi.mock('../../utils/monthlySummaryUtils', () => ({
  getCurrentPeriod: vi.fn(() => ({
    period: '2024-01',
    year: 2024,
    month: 1
  }))
}));

// Mock confirmAction
vi.mock('@/lib/confirmAction', () => ({
  confirmAction: vi.fn((message, callback) => callback())
}));

describe('useMonthlySummary', () => {
  const mockHistory = [
    {
      id: 1,
      period: '2024-01',
      submit_date: '2024-01-28',
      status: 'COMPLETED',
      workContent: 'Work done',
      selfEvaluation: 'Good'
    },
    {
      id: 2,
      period: '2023-12',
      submit_date: '2023-12-28',
      status: 'DRAFT',
      workContent: 'Draft work',
      selfEvaluation: 'Draft eval'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();

    performanceApi.getMonthlySummaryHistory.mockResolvedValue({
      data: mockHistory
    });
    performanceApi.saveDraft.mockResolvedValue({ success: true });
    performanceApi.submitSummary.mockResolvedValue({ success: true });
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

  it('should handle history loading error', async () => {

    performanceApi.getMonthlySummaryHistory.mockRejectedValue(
      new Error('Failed to load')
    );

    const { result } = renderHook(() => useMonthlySummary());

    await act(async () => {
      await result.current.loadHistory();
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.history.length).toBeGreaterThan(0); // fallback data
  });

  it('should toggle show history', () => {
    const { result } = renderHook(() => useMonthlySummary());

    expect(result.current.showHistory).toBe(false);

    act(() => {
      result.current.setShowHistory(true);
    });

    expect(result.current.showHistory).toBe(true);

    act(() => {
      result.current.setShowHistory(false);
    });

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

    expect(performanceApi.saveDraft).toHaveBeenCalledWith(
      expect.objectContaining({
        workContent: 'Draft work'
      })
    );
    expect(result.current.isSaving).toBe(false);
  });

  it('should set saving state during draft save', async () => {

    let resolveSave;
    const promise = new Promise(resolve => {
      resolveSave = resolve;
    });
    performanceApi.saveDraft.mockReturnValue(promise);

    const { result } = renderHook(() => useMonthlySummary());

    const savePromise = act(async () => {
      await result.current.handleSaveDraft();
    });

    expect(result.current.isSaving).toBe(true);

    resolveSave({ success: true });
    await savePromise;

    expect(result.current.isSaving).toBe(false);
  });

  it('should submit summary successfully', async () => {

    const { result } = renderHook(() => useMonthlySummary());

    act(() => {
      result.current.handleInputChange('workContent', 'Completed work');
    });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(performanceApi.submitSummary).toHaveBeenCalledWith(
      expect.objectContaining({
        workContent: 'Completed work'
      })
    );
    expect(result.current.isSubmitting).toBe(false);
  });

  it('should set submitting state during submit', async () => {

    let resolveSubmit;
    const promise = new Promise(resolve => {
      resolveSubmit = resolve;
    });
    performanceApi.submitSummary.mockReturnValue(promise);

    const { result } = renderHook(() => useMonthlySummary());

    const submitPromise = act(async () => {
      await result.current.handleSubmit();
    });

    expect(result.current.isSubmitting).toBe(true);

    resolveSubmit({ success: true });
    await submitPromise;

    expect(result.current.isSubmitting).toBe(false);
  });

  it('should mark as not draft after submit', async () => {
    const { result } = renderHook(() => useMonthlySummary());

    expect(result.current.isDraft).toBe(true);

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(result.current.isDraft).toBe(false);
  });

  it('should handle submit error', async () => {

    performanceApi.submitSummary.mockRejectedValue(
      new Error('Submit failed')
    );

    const { result } = renderHook(() => useMonthlySummary());

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(result.current.isSubmitting).toBe(false);
  });

  it('should update period in form data', () => {

    getCurrentPeriod.mockReturnValue({
      period: '2024-02',
      year: 2024,
      month: 2
    });

    const { result } = renderHook(() => useMonthlySummary());

    expect(result.current.formData.period).toBe('2024-02');
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
});
