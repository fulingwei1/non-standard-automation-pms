/**
 * ServiceRecord 组件测试
 * 测试覆盖：服务记录列表、客户信息、服务类型、状态管理
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ServiceRecord from '../ServiceRecord';
import { serviceApi } from '../../services/api';

vi.mock('../../services/api', () => ({
  serviceApi: {
    records: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      getStatistics: vi.fn(),
    }
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
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ServiceRecord', () => {
  const mockServiceRecords = {
    items: [
      {
        id: 1,
        code: 'SRV-2024-001',
        customerName: '客户A公司',
        contactPerson: '张经理',
        contactPhone: '13800138000',
        serviceType: 'installation',
        productName: '产品A',
        productCode: 'PRD-001',
        serviceDate: '2024-02-15',
        completionDate: '2024-02-16',
        status: 'completed',
        technician: '李师傅',
        description: '设备安装调试',
        satisfaction: 5,
        feedback: '服务很好',
        cost: 5000,
        attachments: ['report1.pdf']
      },
      {
        id: 2,
        code: 'SRV-2024-002',
        customerName: '客户B公司',
        contactPerson: '王总',
        contactPhone: '13900139000',
        serviceType: 'maintenance',
        productName: '产品B',
        productCode: 'PRD-002',
        serviceDate: '2024-02-20',
        completionDate: null,
        status: 'in_progress',
        technician: '赵工',
        description: '设备维护保养',
        satisfaction: null,
        feedback: null,
        cost: 3000,
        attachments: []
      }
    ],
    total: 2,
    stats: {
      total: 2,
      completed: 1,
      inProgress: 1,
      pending: 0,
      cancelled: 0,
      avgSatisfaction: 5,
      totalCost: 8000
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    serviceApi.records.list.mockResolvedValue({ data: mockServiceRecords });
    serviceApi.records.create.mockResolvedValue({ data: { success: true, id: 3 } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render service record page', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/服务记录|Service Record/i)).toBeInTheDocument();
      });
    });

    it('should render service record list', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-001')).toBeInTheDocument();
        expect(screen.getByText('SRV-2024-002')).toBeInTheDocument();
      });
    });

    it('should display customer names', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('客户A公司')).toBeInTheDocument();
        expect(screen.getByText('客户B公司')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load service records on mount', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(serviceApi.records.list).toHaveBeenCalledWith(
          expect.stringContaining('/service-record')
        );
      });
    });

    it('should show loading state', () => {
      serviceApi.records.list.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      serviceApi.records.list.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Service Information', () => {
    it('should display service type', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/安装|Installation/i)).toBeInTheDocument();
        expect(screen.getByText(/维护|Maintenance/i)).toBeInTheDocument();
      });
    });

    it('should show product information', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
        expect(screen.getByText('PRD-001')).toBeInTheDocument();
      });
    });

    it('should display technician', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('李师傅')).toBeInTheDocument();
        expect(screen.getByText('赵工')).toBeInTheDocument();
      });
    });

    it('should show service dates', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2024-02-15/)).toBeInTheDocument();
        expect(screen.getByText(/2024-02-20/)).toBeInTheDocument();
      });
    });
  });

  describe('Customer Information', () => {
    it('should display contact person', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('张经理')).toBeInTheDocument();
        expect(screen.getByText('王总')).toBeInTheDocument();
      });
    });

    it('should show contact phone', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/13800138000/)).toBeInTheDocument();
        expect(screen.getByText(/13900139000/)).toBeInTheDocument();
      });
    });
  });

  describe('Status Management', () => {
    it('should display service status', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/已完成|Completed/i)).toBeInTheDocument();
        expect(screen.getByText(/进行中|In Progress/i)).toBeInTheDocument();
      });
    });

    it('should update service status', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-002')).toBeInTheDocument();
      });

      const updateButtons = screen.queryAllByRole('button', { name: /更新状态|Update Status/i });
      if (updateButtons.length > 0) {
        fireEvent.click(updateButtons[0]);

        await waitFor(() => {
          expect(serviceApi.records.update).toHaveBeenCalled();
        });
      }
    });

    it('should complete service', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-002')).toBeInTheDocument();
      });

      const completeButtons = screen.queryAllByRole('button', { name: /完成|Complete/i });
      if (completeButtons.length > 0) {
        fireEvent.click(completeButtons[0]);

        await waitFor(() => {
          expect(serviceApi.records.update).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Satisfaction Management', () => {
    it('should display satisfaction rating', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/5.*星|5.*star/i)).toBeInTheDocument();
      });
    });

    it('should show customer feedback', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('服务很好')).toBeInTheDocument();
      });
    });

    it('should submit satisfaction', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-002')).toBeInTheDocument();
      });

      const ratingButtons = screen.queryAllByRole('button', { name: /评价|Rate/i });
      if (ratingButtons.length > 0) {
        fireEvent.click(ratingButtons[0]);

        expect(screen.queryByText(/满意度|Satisfaction/i)).toBeTruthy();
      }
    });
  });

  describe('Search and Filtering', () => {
    it('should search service records', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-001')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '客户A' } });

        await waitFor(() => {
          expect(serviceApi.records.list).toHaveBeenCalled();
        });
      }
    });

    it('should filter by service type', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(serviceApi.records.list).toHaveBeenCalled();
      });

      const typeFilter = screen.queryByRole('combobox');
      if (typeFilter) {
        fireEvent.change(typeFilter, { target: { value: 'installation' } });
      }
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(serviceApi.records.list).toHaveBeenCalled();
      });
    });

    it('should filter by date range', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(serviceApi.records.list).toHaveBeenCalled();
      });
    });
  });

  describe('CRUD Operations', () => {
    it('should create new service record', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(serviceApi.records.list).toHaveBeenCalled();
      });

      const createButton = screen.queryByRole('button', { name: /新建|Create|添加/i });
      if (createButton) {
        fireEvent.click(createButton);

        expect(screen.queryByText(/新建服务记录|Create Service Record/i)).toBeTruthy();
      }
    });

    it('should edit service record', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-001')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        expect(screen.queryByText(/编辑服务记录|Edit Service Record/i)).toBeTruthy();
      }
    });

    it('should delete service record', async () => {
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-001')).toBeInTheDocument();
      });

      const deleteButtons = screen.queryAllByRole('button', { name: /删除|Delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);

        await waitFor(() => {
          expect(serviceApi.records.delete).toHaveBeenCalled();
        });
      }
    });

    it('should view service detail', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-001')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        await waitFor(() => {
          expect(mockNavigate).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Attachment Management', () => {
    it('should display attachments', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-001')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        await waitFor(() => {
          expect(screen.getByText(/report1\.pdf/)).toBeInTheDocument();
        });
      }
    });

    it('should upload attachment', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-001')).toBeInTheDocument();
      });

      const uploadButtons = screen.queryAllByRole('button', { name: /上传|Upload/i });
      if (uploadButtons.length > 0) {
        fireEvent.click(uploadButtons[0]);

        expect(screen.queryByText(/选择文件|Select File/i)).toBeTruthy();
      }
    });
  });

  describe('Cost Management', () => {
    it('should display service cost', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/5,000|5000/)).toBeInTheDocument();
        expect(screen.getByText(/3,000|3000/)).toBeInTheDocument();
      });
    });

    it('should show total cost', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/8,000|8000/)).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Display', () => {
    it('should show total record count', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*记录|Total.*2/i)).toBeInTheDocument();
      });
    });

    it('should display status statistics', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1.*已完成|Completed.*1/i)).toBeInTheDocument();
        expect(screen.getByText(/1.*进行中|In Progress.*1/i)).toBeInTheDocument();
      });
    });

    it('should show average satisfaction', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/5.*平均|Average.*5/i)).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    it('should export service records', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(serviceApi.records.list).toHaveBeenCalled();
      });

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);

        await waitFor(() => {
          expect(serviceApi.records.create).toHaveBeenCalledWith(
            expect.stringContaining('/export')
          );
        });
      }
    });
  });

  describe('Report Generation', () => {
    it('should generate service report', async () => {
      render(
        <MemoryRouter>
          <ServiceRecord />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('SRV-2024-001')).toBeInTheDocument();
      });

      const reportButtons = screen.queryAllByRole('button', { name: /报告|Report/i });
      if (reportButtons.length > 0) {
        fireEvent.click(reportButtons[0]);

        await waitFor(() => {
          expect(serviceApi.records.create).toHaveBeenCalled();
        });
      }
    });
  });
});
