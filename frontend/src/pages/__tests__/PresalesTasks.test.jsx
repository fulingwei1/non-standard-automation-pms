import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PresalesTasks from '../PresalesTasks';
import { presaleApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  presaleApi: {
    tickets: {
      list: vi.fn(),
      accept: vi.fn(),
      updateProgress: vi.fn(),
      complete: vi.fn(),
    },
  },
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => {
      const Tag = typeof tag === 'string' ? tag : 'div';
      return ({ children, ...props }) => {
        const motionProps = new Set([
          'initial',
          'animate',
          'exit',
          'variants',
          'transition',
          'whileHover',
          'whileTap',
          'layout',
        ]);
        const domProps = Object.fromEntries(
          Object.entries(props).filter(([key]) => !motionProps.has(key)),
        );
        return <Tag {...domProps}>{children}</Tag>;
      };
    },
  }),
  AnimatePresence: ({ children }) => children,
}));

const ticketItems = [
  {
    id: 11,
    title: '技术方案编写',
    ticket_type: 'SOLUTION_DESIGN',
    status: 'PENDING',
    urgency: 'HIGH',
    customer_name: '华东制造',
    applicant_name: '宋魁',
    deadline: '2026-06-30',
    description: '输出非标自动化方案',
    estimated_hours: 12,
    actual_hours: 0,
  },
  {
    id: 12,
    title: '投标成本核算',
    ticket_type: 'COST_ESTIMATE',
    status: 'IN_PROGRESS',
    urgency: 'MEDIUM',
    customer_name: '苏州装备',
    applicant_name: '郑琴',
    deadline: '2026-07-05',
    progress: 40,
    description: '核算关键部件成本',
    estimated_hours: 8,
    actual_hours: 3,
  },
];

function renderPage(initialEntry = '/presales-tasks') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <PresalesTasks />
    </MemoryRouter>,
  );
}

describe('PresalesTasks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, 'alert').mockImplementation(() => {});
    presaleApi.tickets.list.mockResolvedValue({
      data: { items: ticketItems, total: ticketItems.length },
    });
    presaleApi.tickets.accept.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders technical task cards from presale tickets', async () => {
    renderPage();

    expect(screen.getByText('技术任务中心')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('技术方案编写')).toBeInTheDocument();
    });
    expect(screen.getByText('华东制造')).toBeInTheDocument();
    expect(screen.getByText('销售：宋魁')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('搜索任务...')).toHaveValue('');
    expect(presaleApi.tickets.list).toHaveBeenCalledWith({ page: 1, page_size: 100 });
  });

  it('requests backend status filters using current ticket API parameters', async () => {
    renderPage();

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenCalledTimes(1);
    });

    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'in_progress' },
    });

    await waitFor(() => {
      expect(presaleApi.tickets.list).toHaveBeenLastCalledWith({
        page: 1,
        page_size: 100,
        status: 'ACCEPTED,IN_PROGRESS,PROCESSING',
      });
    });
  });

  it('opens details and accepts the selected ticket id', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('技术方案编写')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('技术方案编写'));
    expect(screen.getByText('任务详情')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /接单处理/ }));

    await waitFor(() => {
      expect(presaleApi.tickets.accept).toHaveBeenCalledWith(11, {});
    });
  });
});
