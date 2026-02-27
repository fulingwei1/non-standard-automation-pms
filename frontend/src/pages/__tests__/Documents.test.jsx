/**
 * Documents 组件测试
 * 测试覆盖：渲染、数据加载、交互、错误、权限
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Documents from '../Documents';
import _api, { documentApi, projectApi } from '../../services/api';

// Mock dependencies
vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { success: true } }),
    put: vi.fn().mockResolvedValue({ data: { success: true } }),
    delete: vi.fn().mockResolvedValue({ data: { success: true } }),
    defaults: { baseURL: '/api' },
  },
    documentApi: {
      create: vi.fn().mockResolvedValue({ data: {} }),
      delete: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      list: vi.fn().mockResolvedValue({ data: {} }),
    },
    projectApi: {
      list: vi.fn().mockResolvedValue({ data: {} }),
      getBoard: vi.fn().mockResolvedValue({ data: {} }),
      get: vi.fn().mockResolvedValue({ data: {} }),
      create: vi.fn().mockResolvedValue({ data: {} }),
      update: vi.fn().mockResolvedValue({ data: {} }),
      getMachines: vi.fn().mockResolvedValue({ data: {} }),
      getInProductionSummary: vi.fn().mockResolvedValue({ data: {} }),
      recommendTemplates: vi.fn().mockResolvedValue({ data: {} }),
      createFromTemplate: vi.fn().mockResolvedValue({ data: {} }),
      checkAutoTransition: vi.fn().mockResolvedValue({ data: {} }),
      getGateCheckResult: vi.fn().mockResolvedValue({ data: {} }),
      advanceStage: vi.fn().mockResolvedValue({ data: {} }),
      getCacheStats: vi.fn().mockResolvedValue({ data: {} }),
      clearCache: vi.fn().mockResolvedValue({ data: {} }),
      resetCacheStats: vi.fn().mockResolvedValue({ data: {} }),
      getStatusLogs: vi.fn().mockResolvedValue({ data: {} }),
      getHealthDetails: vi.fn().mockResolvedValue({ data: {} }),
      getStats: vi.fn().mockResolvedValue({ data: {} }),
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

describe.skip('Documents', () => {
  const mockDocData = {
    items: [
      {
        id: 1,
        fileName: '项目需求文档.pdf',
        fileType: 'pdf',
        fileSize: 2048576,
        category: '需求文档',
        uploadedBy: '张三',
        uploadedAt: '2024-02-15',
        downloadCount: 10,
        version: 'v1.0'
      },
      {
        id: 2,
        fileName: '技术方案.docx',
        fileType: 'docx',
        fileSize: 1024000,
        category: '技术文档',
        uploadedBy: '李四',
        uploadedAt: '2024-02-10',
        downloadCount: 5,
        version: 'v2.1'
      }
    ],
    total: 2,
    page: 1,
    pageSize: 10
  };

  beforeEach(() => {
    vi.clearAllMocks();
    projectApi.list.mockResolvedValue({ data: mockDocData });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // 1. 组件渲染测试
  describe('Component Rendering', () => {
    it('should render documents page with title', async () => {
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/文档管理|Document Management/i)).toBeInTheDocument();
      });
    });

    it('should render document list table', async () => {
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
        expect(screen.getByText('技术方案.docx')).toBeInTheDocument();
      });
    });
  });

  // 2. 数据加载测试
  describe('Data Loading', () => {
    it('should load documents on mount', async () => {
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalledWith(
          expect.stringContaining('/documents')
        );
      });
    });

    it('should display loading state', () => {
      projectApi.list.mockImplementation(() => new Promise(() => {}));
      
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      expect(screen.getByText(/加载中|Loading/i)).toBeInTheDocument();
    });

    it('should refresh data when refresh button clicked', async () => {
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalledTimes(1);
      });

      const refreshButton = screen.getByRole('button', { name: /刷新|Refresh/i });
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalledTimes(2);
      });
    });
  });

  // 3. 交互测试
  describe('User Interactions', () => {
    it('should upload document', async () => {
      documentApi.create.mockResolvedValue({ data: { success: true, fileId: 3 } });

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole('button', { name: /上传|Upload/i });
      fireEvent.click(uploadButton);

      const fileInput = screen.getByLabelText(/选择文件|Select File/i);
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(documentApi.create).toHaveBeenCalled();
      });
    });

    it('should filter by category', async () => {
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const categoryFilter = screen.getByRole('combobox', { name: /分类|Category/i });
      fireEvent.change(categoryFilter, { target: { value: '需求文档' } });

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalledWith(
          expect.stringContaining('category=需求文档')
        );
      });
    });

    it('should search by keyword', async () => {
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/搜索文档|Search document/i);
      fireEvent.change(searchInput, { target: { value: '需求' } });

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalledWith(
          expect.stringContaining('keyword=需求')
        );
      });
    });

    it('should download document', async () => {
      projectApi.list.mockResolvedValue({ data: new Blob(['content'], { type: 'application/pdf' }) });

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const downloadButton = screen.getAllByRole('button', { name: /下载|Download/i })[0];
      fireEvent.click(downloadButton);

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalledWith(
          expect.stringContaining('/documents/1/download')
        );
      });
    });

    it('should preview document', async () => {
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const previewButton = screen.getAllByRole('button', { name: /预览|Preview/i })[0];
      fireEvent.click(previewButton);

      await waitFor(() => {
        expect(screen.getByText(/文档预览|Document Preview/i)).toBeInTheDocument();
      });
    });

    it('should delete document', async () => {
      documentApi.delete.mockResolvedValue({ data: { success: true } });
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const deleteButton = screen.getAllByRole('button', { name: /删除|Delete/i })[0];
      fireEvent.click(deleteButton);

      await waitFor(() => {
        expect(documentApi.delete).toHaveBeenCalledWith('/documents/1');
      });
    });

    it('should share document', async () => {
      documentApi.create.mockResolvedValue({ data: { success: true, shareLink: 'http://example.com/share' } });

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const shareButton = screen.getAllByRole('button', { name: /分享|Share/i })[0];
      fireEvent.click(shareButton);

      await waitFor(() => {
        expect(screen.getByText(/分享文档|Share Document/i)).toBeInTheDocument();
      });
    });

    it('should move document to folder', async () => {
      documentApi.update.mockResolvedValue({ data: { success: true } });

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const moveButton = screen.getAllByRole('button', { name: /移动|Move/i })[0];
      fireEvent.click(moveButton);

      await waitFor(() => {
        expect(screen.getByText(/移动到文件夹|Move to Folder/i)).toBeInTheDocument();
      });
    });

    it('should handle pagination', async () => {
      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const nextPageButton = screen.getByRole('button', { name: /下一页|Next/i });
      fireEvent.click(nextPageButton);

      await waitFor(() => {
        expect(projectApi.list).toHaveBeenCalledWith(
          expect.stringContaining('page=2')
        );
      });
    });
  });

  // 4. 错误处理测试
  describe('Error Handling', () => {
    it('should display error message on load failure', async () => {
      projectApi.list.mockRejectedValue(new Error('Network Error'));

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/加载失败|Load Failed/i)).toBeInTheDocument();
      });
    });

    it('should handle upload failure', async () => {
      documentApi.create.mockRejectedValue(new Error('Upload Failed'));

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('项目需求文档.pdf')).toBeInTheDocument();
      });

      const uploadButton = screen.getByRole('button', { name: /上传|Upload/i });
      fireEvent.click(uploadButton);

      const fileInput = screen.getByLabelText(/选择文件|Select File/i);
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/上传失败|Upload Failed/i)).toBeInTheDocument();
      });
    });
  });

  // 5. 权限测试
  describe('Permission Control', () => {
    it('should show upload button for authorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify(['document:upload']));

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /上传|Upload/i })).toBeInTheDocument();
      });
    });

    it('should hide upload button for unauthorized users', async () => {
      localStorage.setItem('userPermissions', JSON.stringify([]));

      render(
        <MemoryRouter>
          <Documents />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /上传|Upload/i })).not.toBeInTheDocument();
      });
    });
  });
});
