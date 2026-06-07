import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import usePresaleTickets from '../usePresaleTickets';
import { presaleApi } from '../../../services/api';

vi.mock('../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    presaleApi: {
      tickets: {
        getBoard: vi.fn(),
        list: vi.fn(),
        update: vi.fn(),
        accept: vi.fn(),
        updateProgress: vi.fn(),
        complete: vi.fn(),
      },
    },
  };
});

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

describe('usePresaleTickets', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    presaleApi.tickets.list.mockResolvedValue({ data: { items: [] } });
  });

  it('loads REVIEW tickets from the board reviewing column', async () => {
    presaleApi.tickets.getBoard.mockResolvedValue({
      data: {
        pending: [],
        accepted: [],
        in_progress: [],
        reviewing: [
          {
            id: 91,
            ticket_no: 'TICKET-REVIEW-001',
            title: '方案评审工单',
            ticket_type: 'SOLUTION_REVIEW',
            urgency: 'HIGH',
            status: 'REVIEW',
            customer_name: '华东客户',
            applicant_name: '销售一部',
          },
        ],
        completed: [],
      },
    });

    const { result } = renderHook(() => usePresaleTickets());

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.tickets).toHaveLength(1);
    expect(result.current.tickets[0]).toMatchObject({
      ticketNo: 'TICKET-REVIEW-001',
      status: 'REVIEWING',
      ticketTypeLabel: '方案评审',
    });
    expect(result.current.groupedByStatus.REVIEWING).toHaveLength(1);
    expect(result.current.stats.reviewing).toBe(1);
    expect(presaleApi.tickets.list).not.toHaveBeenCalled();
  });
});
