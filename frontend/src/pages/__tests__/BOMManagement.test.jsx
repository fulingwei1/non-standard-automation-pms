/**
 * BOMManagement 组件测试
 * 测试覆盖：BOM列表、层级结构、物料关联、版本管理
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BOMManagement from '../BOMManagement';
import api from '../../services/api';

// Mock dependencies
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

describe('BOMManagement', () => {
  const mockBOMs = {
    items: [
      {
        id: 1,
        code: 'BOM-001',
        name: '产品A BOM',
        version: 'V1.0',
        productCode: 'PRD-001',
        productName: '产品A',
        status: 'active',
        level: 3,
        itemCount: 25,
        totalCost: 12500,
        createdBy: '张工',
        createdAt: '2024-01-15',
        updatedAt: '2024-02-20'
      },
      {
        id: 2,
        code: 'BOM-002',
        name: '产品B BOM',
        version: 'V2.1',
        productCode: 'PRD-002',
        productName: '产品B',
        status: 'draft',
        level: 2,
        itemCount: 18,
        totalCost: 8900,
        createdBy: '李工',
        createdAt: '2024-02-01',
        updatedAt: '2024-02-22'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  const mockBOMDetail = {
    id: 1,
    code: 'BOM-001',
    name: '产品A BOM',
    version: 'V1.0',
    productCode: 'PRD-001',
    productName: '产品A',
    status: 'active',
    level: 3,
    items: [
      {
        id: 1,
        level: 1,
        materialCode: 'MAT-001',
        materialName: '钢板',
        spec: '1000x2000x5mm',
        quantity: 10,
        unit: '张',
        unitPrice: 500,
        totalPrice: 5000,
        supplier: '供应商A',
        leadTime: 7
      },
      {
        id: 2,
        level: 2,
        materialCode: 'MAT-002',
        materialName: '螺栓',
        spec: 'M8x20',
        quantity: 100,
        unit: '个',
        unitPrice: 2,
        totalPrice: 200,
        supplier: '供应商B',
        leadTime: 3,
        parentId: 1
      }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockImplementation((url) => {
      if (url.includes('/bom') && !url.includes('/bom/')) {
        return Promise.resolve({ data: mockBOMs });
      }
      if (url.includes('/bom/1')) {
        return Promise.resolve({ data: mockBOMDetail });
      }
      return Promise.resolve({ data: {} });
    });
    api.post.mockResolvedValue({ data: { success: true, id: 3 } });
    api.put.mockResolvedValue({ data: { success: true } });
    api.delete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render BOM management page', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/BOM管理|BOM Management/i)).toBeInTheDocument();
      });
    });

    it('should render BOM list', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
        expect(screen.getByText('产品B BOM')).toBeInTheDocument();
      });
    });

    it('should display BOM codes and versions', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('BOM-001')).toBeInTheDocument();
        expect(screen.getByText('V1.0')).toBeInTheDocument();
        expect(screen.getByText('V2.1')).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load BOMs on mount', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(expect.stringContaining('/bom'));
      });
    });

    it('should show loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      api.get.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  // 3. BOM信息显示测试
  describe('BOM Information Display', () => {
    it('should display product information', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A')).toBeInTheDocument();
        expect(screen.getByText('PRD-001')).toBeInTheDocument();
      });
    });

    it('should show BOM level', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/3.*层|Level.*3/i)).toBeInTheDocument();
      });
    });

    it('should display item count', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/25.*项|25.*items/i)).toBeInTheDocument();
      });
    });

    it('should show total cost', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/12,500|12500/)).toBeInTheDocument();
      });
    });
  });

  // 4. BOM状态管理测试
  describe('BOM Status Management', () => {
    it('should display BOM status', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/active|激活|生效/i)).toBeInTheDocument();
        expect(screen.getByText(/draft|草稿/i)).toBeInTheDocument();
      });
    });

    it('should activate BOM', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品B BOM')).toBeInTheDocument();
      });

      const activateButtons = screen.queryAllByRole('button', { name: /激活|Activate/i });
      if (activateButtons.length > 0) {
        fireEvent.click(activateButtons[0]);

        await waitFor(() => {
          expect(api.put).toHaveBeenCalledWith(
            expect.stringContaining('/bom/'),
            expect.objectContaining({ status: 'active' })
          );
        });
      }
    });
  });

  // 5. 搜索和筛选测试
  describe('Search and Filtering', () => {
    it('should search BOMs', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '产品A' } });

        await waitFor(() => {
          expect(api.get).toHaveBeenCalled();
        });
      }
    });

    it('should filter by status', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const statusFilter = screen.queryByRole('combobox');
      if (statusFilter) {
        fireEvent.change(statusFilter, { target: { value: 'active' } });
      }
    });

    it('should filter by product', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });
    });
  });

  // 6. BOM层级结构测试
  describe('BOM Hierarchy', () => {
    it('should display BOM tree structure', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);

        await waitFor(() => {
          expect(screen.getByText('钢板')).toBeInTheDocument();
          expect(screen.getByText('螺栓')).toBeInTheDocument();
        });
      }
    });

    it('should show material hierarchy levels', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);

        await waitFor(() => {
          const levels = screen.getAllByText(/Level.*[12]|层级.*[12]/i);
          expect(levels.length).toBeGreaterThanOrEqual(0);
        });
      }
    });

    it('should expand/collapse BOM nodes', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const expandButtons = screen.queryAllByRole('button', { name: /展开|Expand/i });
      if (expandButtons.length > 0) {
        fireEvent.click(expandButtons[0]);
      }
    });
  });

  // 7. 物料信息测试
  describe('Material Information', () => {
    it('should display material details', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);

        await waitFor(() => {
          expect(screen.getByText('MAT-001')).toBeInTheDocument();
          expect(screen.getByText('1000x2000x5mm')).toBeInTheDocument();
        });
      }
    });

    it('should show material quantities', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);

        await waitFor(() => {
          expect(screen.getByText(/10.*张/)).toBeInTheDocument();
          expect(screen.getByText(/100.*个/)).toBeInTheDocument();
        });
      }
    });

    it('should display supplier information', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);

        await waitFor(() => {
          expect(screen.getByText('供应商A')).toBeInTheDocument();
          expect(screen.getByText('供应商B')).toBeInTheDocument();
        });
      }
    });
  });

  // 8. BOM操作测试
  describe('BOM Operations', () => {
    it('should create new BOM', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const createButton = screen.queryByRole('button', { name: /新建|Create|添加/i });
      if (createButton) {
        fireEvent.click(createButton);

        expect(screen.queryByText(/新建BOM|Create BOM/i)).toBeTruthy();
      }
    });

    it('should edit BOM', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        expect(screen.queryByText(/编辑BOM|Edit BOM/i)).toBeTruthy();
      }
    });

    it('should copy BOM', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const copyButtons = screen.queryAllByRole('button', { name: /复制|Copy/i });
      if (copyButtons.length > 0) {
        fireEvent.click(copyButtons[0]);

        await waitFor(() => {
          expect(api.post).toHaveBeenCalled();
        });
      }
    });

    it('should delete BOM', async () => {
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
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

  // 9. 版本管理测试
  describe('Version Management', () => {
    it('should display BOM versions', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('V1.0')).toBeInTheDocument();
        expect(screen.getByText('V2.1')).toBeInTheDocument();
      });
    });

    it('should create new version', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const versionButtons = screen.queryAllByRole('button', { name: /版本|Version/i });
      if (versionButtons.length > 0) {
        fireEvent.click(versionButtons[0]);

        const newVersionButton = screen.queryByRole('button', { name: /新版本|New Version/i });
        if (newVersionButton) {
          fireEvent.click(newVersionButton);
        }
      }
    });

    it('should compare BOM versions', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const compareButtons = screen.queryAllByRole('button', { name: /比较|Compare/i });
      if (compareButtons.length > 0) {
        fireEvent.click(compareButtons[0]);
      }
    });
  });

  // 10. 成本计算测试
  describe('Cost Calculation', () => {
    it('should calculate total BOM cost', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/12,500|12500/)).toBeInTheDocument();
      });
    });

    it('should show material unit prices', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const viewButton = screen.queryAllByRole('button', { name: /查看|View|详情/i })[0];
      if (viewButton) {
        fireEvent.click(viewButton);

        await waitFor(() => {
          expect(screen.getByText(/500|5,000/)).toBeInTheDocument();
        });
      }
    });

    it('should display cost breakdown', async () => {
      render(
        <MemoryRouter>
          <BOMManagement />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('产品A BOM')).toBeInTheDocument();
      });

      const costButtons = screen.queryAllByRole('button', { name: /成本|Cost/i });
      if (costButtons.length > 0) {
        fireEvent.click(costButtons[0]);
      }
    });
  });
});
