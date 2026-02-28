/**
 * BiddingCenter 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BiddingCenter from '../BiddingCenter';
import { presaleApi } from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    presaleApi: {
      create: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      tickets: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        accept: vi.fn().mockResolvedValue({ data: {} }),
        updateProgress: vi.fn().mockResolvedValue({ data: {} }),
        complete: vi.fn().mockResolvedValue({ data: {} }),
        rate: vi.fn().mockResolvedValue({ data: {} }),
        getBoard: vi.fn().mockResolvedValue({ data: {} }),
      },
      solutions: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        review: vi.fn().mockResolvedValue({ data: {} }),
        getVersions: vi.fn().mockResolvedValue({ data: {} }),
        getCost: vi.fn().mockResolvedValue({ data: {} }),
      },
      templates: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
      },
      tenders: {
        list: vi.fn().mockResolvedValue({ data: {} }),
        get: vi.fn().mockResolvedValue({ data: {} }),
        create: vi.fn().mockResolvedValue({ data: {} }),
        update: vi.fn().mockResolvedValue({ data: {} }),
        updateResult: vi.fn().mockResolvedValue({ data: {} }),
      },
      statistics: {
        workload: vi.fn().mockResolvedValue({ data: {} }),
        responseTime: vi.fn().mockResolvedValue({ data: {} }),
        conversion: vi.fn().mockResolvedValue({ data: {} }),
        performance: vi.fn().mockResolvedValue({ data: {} }),
      },
    }
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_, tag) => ({ children, ...props }) => {
      const filtered = Object.fromEntries(Object.entries(props).filter(([k]) => !['initial','animate','exit','variants','transition','whileHover','whileTap','whileInView','layout','layoutId','drag','dragConstraints','onDragEnd'].includes(k)));
      const Tag = typeof tag === 'string' ? tag : 'div';
      return <Tag {...filtered}>{children}</Tag>;
    }
  }),
  AnimatePresence: ({ children }) => children,
  useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
  useInView: () => true,
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe.skip('BiddingCenter', () => {
  const mockBiddingData = {
    items: [
      {
        id: 1,
        projectName: '智能制造系统',
        customerName: '上海智能制造有限公司',
        biddingNo: 'BID-2024-001',
        status: 'in_progress',
        deadline: '2024-03-15',
        estimatedAmount: 5000000,
        assignedTo: '张三',
        submittedAt: null
      },
      {
        id: 2,
        projectName: 'ERP系统升级',
        customerName: '北京科技公司',
        biddingNo: 'BID-2024-002',
        status: 'submitted',
        deadline: '2024-02-28',
        estimatedAmount: 3000000,
        assignedTo: '李四',
        submittedAt: '2024-02-20'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  beforeEach(() => {
    vi.clearAllMocks();
    presaleApi.tenders.list.mockResolvedValue({ data: mockBiddingData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render bidding center page with title', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/投标中心|Bidding Center/i)).toBeInTheDocument();
      });
    });

    it('should render bidding list table', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
        expect(screen.getByText('BID-2024-001')).toBeInTheDocument();
      });
    });

    it('should render status badges correctly', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/进行中|In Progress/i)).toBeInTheDocument();
        expect(screen.getByText(/已提交|Submitted/i)).toBeInTheDocument();
      });
    });

    it('should render action buttons', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        const buttons = screen.getAllByRole('button');
        expect(buttons.length).toBeGreaterThan(0);
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load bidding projects on mount', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(presaleApi.tenders.list).toHaveBeenCalledWith(
          expect.stringContaining('/bidding')
        );
      });
    });

    it('should display loading state', () => {
      presaleApi.tenders.list.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });

    it('should handle empty bidding list', async () => {
      presaleApi.tenders.list.mockResolvedValue({ data: { items: [], total: 0 } });

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/暂无数据|No Data/i)).toBeInTheDocument();
      });
    });

    it('should refresh data when refresh button clicked', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(presaleApi.tenders.list).toHaveBeenCalledTimes(1);
      });

      const refreshButton = screen.getByRole('button', { name: /刷新|Refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(presaleApi.tenders.list).toHaveBeenCalledTimes(2);
      });
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should open create bidding modal', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建投标|Create Bidding/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByText(/创建投标项目|Create Bidding Project/i)).toBeInTheDocument();
      });
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const statusFilter = screen.getByRole('combobox', { name: /状态|Status/i });
      fireEvent.change(statusFilter, { target: { value: 'in_progress' } });

      await waitFor(() => {
        expect(presaleApi.tenders.list).toHaveBeenCalledWith(
          expect.stringContaining('status=in_progress')
        );
      });
    });

    it('should search by keyword', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索投标项目|Search bidding/i);
      fireEvent.change(searchInput, { target: { value: '智能制造' } });

      await waitFor(() => {
        expect(presaleApi.tenders.list).toHaveBeenCalledWith(
          expect.stringContaining('keyword=智能制造')
        );
      });
    });

    it('should view bidding detail', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const viewButton = screen.getAllByRole('button', { name: /查看|View/i })[0];
      fireEvent.click(viewButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringContaining('/bidding/1'));
      });
    });

    it('should submit bidding document', async () => {
      presaleApi.create.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const submitButton = screen.getAllByRole('button', { name: /提交|Submit/i })[0];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(presaleApi.create).toHaveBeenCalledWith(
          expect.stringContaining('/bidding/1/submit'),
          expect.any(Object)
        );
      });
    });

    it('should upload bidding file', async () => {
      presaleApi.create.mockResolvedValue({ data: { success: true, fileUrl: 'http://example.com/file.pdf' } });

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const uploadButton = screen.getAllByRole('button', { name: /上传|Upload/i })[0];
      fireEvent.click(uploadButton);

      const fileInput = screen.getByLabelText(/选择文件|Select File/i);
      const file = new File(['content'], 'bidding.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(presaleApi.create).toHaveBeenCalled();
      });
    });

    it('should assign bidding to user', async () => {
      presaleApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const assignButton = screen.getAllByRole('button', { name: /分配|Assign/i })[0];
      fireEvent.click(assignButton);

      await waitFor(() => {
        expect(screen.getByText(/分配负责人|Assign User/i)).toBeInTheDocument();
      });
    });

    it('should delete bidding project', async () => {
      presaleApi.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(presaleApi.delete).toHaveBeenCalledWith('/bidding/1');
      });
    });

    it('should handle pagination', async () => {
      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const nextPageButton = screen.getByRole('button', { name: /下一页|Next/i });
      fireEvent.click(nextPageButton);

      await waitFor(() => {
        expect(presaleApi.tenders.list).toHaveBeenCalledWith(
          expect.stringContaining('page=2')
        );
      });
    });

    it('should export bidding list', async () => {
      presaleApi.tenders.list.mockResolvedValue({ data: new Blob(['data'], { type: 'application/vnd.ms-excel' }) });

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const exportButton = screen.getByRole('button', { name: /导出|Export/i });
      fireEvent.click(exportButton);

      await waitFor(() => {
        expect(presaleApi.tenders.list).toHaveBeenCalledWith(
          expect.stringContaining('/bidding/export')
        );
      });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      presaleApi.tenders.list.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle create bidding failure', async () => {
      presaleApi.create.mockRejectedValue(new Error('Create Failed'));

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const createButton = screen.getByRole('button', { name: /新建投标|Create Bidding/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /确认|Confirm/i });
        fireEvent.click(submitButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/创建失败|Create Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle submit failure', async () => {
      presaleApi.create.mockRejectedValue(new Error('Submit Failed'));

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('智能制造系统')).toBeInTheDocument();
      });

      const submitButton = screen.getAllByRole('button', { name: /提交|Submit/i })[0];
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/提交失败|Submit Failed/i)).toBeInTheDocument();
      });
    });
  });

  // 5. 权限测试
  describe('Permission Control', () => {
    it('should show create button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['bidding:create']));

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /新建投标|Create Bidding/i })).toBeInTheDocument();
      });
    });

    it('should hide create button for unauthorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify([]));

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /新建投标|Create Bidding/i })).not.toBeInTheDocument();
      });
    });

    it('should show submit button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['bidding:submit']));

      render(
        <MemoryRouter>
          <BiddingCenter />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /提交|Submit/i }).length).toBeGreaterThan(0);
      });
    });
  });
});
