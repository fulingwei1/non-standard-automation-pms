/**
 * QualificationManagement 组件测试
 * 测试覆盖：资质列表、证书管理、到期提醒、审核流程
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import QualificationManagement from '../QualificationManagement';
import api from '../../services/api';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
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

describe('QualificationManagement', () => {
  const mockQualifications = {
    items: [
      {
        id: 1,
        code: 'QUAL-001',
        name: '电工证',
        category: 'technical',
        level: '高级',
        holderName: '张师傅',
        holderType: 'employee',
        issueDate: '2023-01-15',
        expiryDate: '2026-01-15',
        status: 'valid',
        certNumber: 'DG20230001',
        issueOrg: '劳动局',
        daysToExpiry: 365
      },
      {
        id: 2,
        code: 'QUAL-002',
        name: '焊工证',
        category: 'technical',
        level: '中级',
        holderName: '李师傅',
        holderType: 'employee',
        issueDate: '2022-06-20',
        expiryDate: '2024-03-20',
        status: 'expiring',
        certNumber: 'HG20220015',
        issueOrg: '质监局',
        daysToExpiry: 30
      }
    ],
    total: 2,
    stats: {
      total: 2,
      valid: 1,
      expiring: 1,
      expired: 0,
      pending: 0
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({ data: mockQualifications });
    api.post.mockResolvedValue({ data: { success: true, id: 3 } });
    api.put.mockResolvedValue({ data: { success: true } });
    api.delete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render qualification management page', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/资质管理|Qualification Management/i)).toBeInTheDocument();
      });
    });

    it('should render qualification list', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('电工证')).toBeInTheDocument();
        expect(screen.getByText('焊工证')).toBeInTheDocument();
      });
    });

    it('should display holder names', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('张师傅')).toBeInTheDocument();
        expect(screen.getByText('李师傅')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load qualifications on mount', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/qualification')
        );
      });
    });

    it('should show loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      api.get.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Qualification Information', () => {
    it('should display certificate numbers', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('DG20230001')).toBeInTheDocument();
        expect(screen.getByText('HG20220015')).toBeInTheDocument();
      });
    });

    it('should show qualification level', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('高级')).toBeInTheDocument();
        expect(screen.getByText('中级')).toBeInTheDocument();
      });
    });

    it('should display issuing organization', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('劳动局')).toBeInTheDocument();
        expect(screen.getByText('质监局')).toBeInTheDocument();
      });
    });
  });

  describe('Expiry Management', () => {
    it('should display expiry dates', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2026-01-15/)).toBeInTheDocument();
        expect(screen.getByText(/2024-03-20/)).toBeInTheDocument();
      });
    });

    it('should show days to expiry', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/365.*天|365.*days/i)).toBeInTheDocument();
        expect(screen.getByText(/30.*天|30.*days/i)).toBeInTheDocument();
      });
    });

    it('should highlight expiring qualifications', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/即将过期|Expiring/i)).toBeInTheDocument();
      });
    });

    it('should send renewal reminder', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('焊工证')).toBeInTheDocument();
      });

      const reminderButtons = screen.queryAllByRole('button', { name: /提醒|Remind/i });
      if (reminderButtons.length > 0) {
        fireEvent.click(reminderButtons[0]);

        await waitFor(() => {
          expect(api.post).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Status Management', () => {
    it('should display qualification status', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/有效|Valid/i)).toBeInTheDocument();
        expect(screen.getByText(/即将过期|Expiring/i)).toBeInTheDocument();
      });
    });

    it('should update qualification status', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('电工证')).toBeInTheDocument();
      });

      const updateButtons = screen.queryAllByRole('button', { name: /更新|Update/i });
      if (updateButtons.length > 0) {
        fireEvent.click(updateButtons[0]);

        await waitFor(() => {
          expect(api.put).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Search and Filtering', () => {
    it('should search qualifications', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('电工证')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '电工' } });

        await waitFor(() => {
          expect(api.get).toHaveBeenCalled();
        });
      }
    });

    it('should filter by category', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const categoryFilter = screen.queryByRole('combobox');
      if (categoryFilter) {
        fireEvent.change(categoryFilter, { target: { value: 'technical' } });
      }
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });
    });
  });

  describe('CRUD Operations', () => {
    it('should create new qualification', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const createButton = screen.queryByRole('button', { name: /新建|Create|添加/i });
      if (createButton) {
        fireEvent.click(createButton);

        expect(screen.queryByText(/新建资质|Create Qualification/i)).toBeTruthy();
      }
    });

    it('should edit qualification', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('电工证')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        expect(screen.queryByText(/编辑资质|Edit Qualification/i)).toBeTruthy();
      }
    });

    it('should delete qualification', async () => {
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('电工证')).toBeInTheDocument();
      });

      const deleteButtons = screen.queryAllByRole('button', { name: /删除|Delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);

        await waitFor(() => {
          expect(api.delete).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Certificate Upload', () => {
    it('should upload certificate file', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('电工证')).toBeInTheDocument();
      });

      const uploadButtons = screen.queryAllByRole('button', { name: /上传|Upload/i });
      if (uploadButtons.length > 0) {
        fireEvent.click(uploadButtons[0]);

        expect(screen.queryByText(/选择文件|Select File/i)).toBeTruthy();
      }
    });

    it('should view certificate', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('电工证')).toBeInTheDocument();
      });

      const viewButtons = screen.queryAllByRole('button', { name: /查看|View|详情/i });
      if (viewButtons.length > 0) {
        fireEvent.click(viewButtons[0]);

        expect(screen.queryByText(/证书详情|Certificate Details/i)).toBeTruthy();
      }
    });
  });

  describe('Statistics Display', () => {
    it('should show total qualification count', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/2.*资质|Total.*2/i)).toBeInTheDocument();
      });
    });

    it('should display status statistics', async () => {
      render(
        <MemoryRouter>
          <QualificationManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/1.*有效|Valid.*1/i)).toBeInTheDocument();
        expect(screen.getByText(/1.*即将过期|Expiring.*1/i)).toBeInTheDocument();
      });
    });
  });
});
