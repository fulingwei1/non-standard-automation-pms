import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePresalesTasks } from '../usePresalesTasks';
import { presaleApi } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  presaleApi: {
    tickets: {
      list: vi.fn(),
      accept: vi.fn(),
      updateProgress: vi.fn(),
      complete: vi.fn(),
    },
  },
}));

describe('usePresalesTasks Hook', () => {
  const mockItems = [{ id: 1, title: 'Test 1' }, { id: 2, title: 'Test 2' }];

  beforeEach(() => {
    vi.clearAllMocks();
    presaleApi.tickets.list.mockResolvedValue({ data: { items: mockItems, total: 2 } });
    presaleApi.tickets.accept.mockResolvedValue({ data: { success: true } });
    presaleApi.tickets.updateProgress.mockResolvedValue({ data: { success: true } });
    presaleApi.tickets.complete.mockResolvedValue({ data: { success: true } });
  });

  it('should load tasks with mapped filters', async () => {
    const { result } = renderHook(() => usePresalesTasks());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.tasks).toEqual(mockItems);
    expect(presaleApi.tickets.list).toHaveBeenCalledWith({ page_size: 50 });

    await act(async () => {
      result.current.setFilters({ status: 'PENDING', type: 'SOLUTION' });
    });

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenLastCalledWith({
        page_size: 50,
        status: 'PENDING',
        ticket_type: 'SOLUTION',
      });
    });
  });

  it('should accept task when updating status to ACCEPTED', async () => {
    const { result } = renderHook(() => usePresalesTasks());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      const response = await result.current.updateTaskStatus(12, 'ACCEPTED');
      expect(response).toEqual({ success: true });
    });

    expect(presaleApi.tickets.accept).toHaveBeenCalledWith(12, {});
    expect(presaleApi.tickets.list).toHaveBeenCalledTimes(2);
  });

  it('should complete task with normalized actual hours payload', async () => {
    const { result } = renderHook(() => usePresalesTasks());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      const response = await result.current.completeTask(8, { actualHours: 6.5 });
      expect(response).toEqual({ success: true });
    });

    expect(presaleApi.tickets.complete).toHaveBeenCalledWith(8, { actual_hours: 6.5 });
    expect(presaleApi.tickets.list).toHaveBeenCalledTimes(2);
  });
});
