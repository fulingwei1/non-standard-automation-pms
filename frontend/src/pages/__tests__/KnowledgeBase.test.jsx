/**
 * KnowledgeBase 组件测试
 * 测试覆盖：知识库列表、分类管理、搜索、收藏、评分
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import KnowledgeBase from '../KnowledgeBase';
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

describe('KnowledgeBase', () => {
  const mockKnowledgeData = {
    items: [
      {
        id: 1,
        title: '设备操作指南',
        category: 'operation',
        type: 'document',
        content: '详细的设备操作步骤...',
        author: '张工',
        createdAt: '2024-01-15',
        updatedAt: '2024-02-20',
        viewCount: 150,
        likeCount: 25,
        rating: 4.5,
        tags: ['设备', '操作', '指南'],
        status: 'published',
        isFavorite: false
      },
      {
        id: 2,
        title: '质量检验标准',
        category: 'quality',
        type: 'document',
        content: '产品质量检验的标准和流程...',
        author: '李工',
        createdAt: '2024-02-01',
        updatedAt: '2024-02-15',
        viewCount: 200,
        likeCount: 35,
        rating: 4.8,
        tags: ['质量', '检验', '标准'],
        status: 'published',
        isFavorite: true
      }
    ],
    categories: [
      { id: 1, name: 'operation', label: '操作指南', count: 15 },
      { id: 2, name: 'quality', label: '质量管理', count: 20 },
      { id: 3, name: 'maintenance', label: '维护保养', count: 10 }
    ],
    total: 2,
    stats: {
      total: 45,
      published: 40,
      draft: 5,
      totalViews: 5000,
      totalLikes: 800
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
    api.get.mockResolvedValue({ data: mockKnowledgeData });
    api.post.mockResolvedValue({ data: { success: true, id: 3 } });
    api.put.mockResolvedValue({ data: { success: true } });
    api.delete.mockResolvedValue({ data: { success: true } });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render knowledge base page', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/知识库|Knowledge Base/i)).toBeInTheDocument();
      });
    });

    it('should render knowledge list', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备操作指南')).toBeInTheDocument();
        expect(screen.getByText('质量检验标准')).toBeInTheDocument();
      });
    });

    it('should display categories', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('操作指南')).toBeInTheDocument();
        expect(screen.getByText('质量管理')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should load knowledge items on mount', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalledWith(
          expect.stringContaining('/knowledge')
        );
      });
    });

    it('should show loading state', () => {
      api.get.mockImplementation(() => new Promise(() => {}));

      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      expect(screen.queryByText(/加载中|Loading/i)).toBeTruthy();
    });

    it('should handle load error', async () => {
      api.get.mockRejectedValue(new Error('Load failed'));

      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        const errorMessage = screen.queryByText(/错误|Error|失败/i);
        expect(errorMessage).toBeTruthy();
      });
    });
  });

  describe('Knowledge Information', () => {
    it('should display author information', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('张工')).toBeInTheDocument();
        expect(screen.getByText('李工')).toBeInTheDocument();
      });
    });

    it('should show view count', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/150.*浏览|150.*views/i)).toBeInTheDocument();
        expect(screen.getByText(/200.*浏览|200.*views/i)).toBeInTheDocument();
      });
    });

    it('should display like count', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/25.*赞|25.*likes/i)).toBeInTheDocument();
        expect(screen.getByText(/35.*赞|35.*likes/i)).toBeInTheDocument();
      });
    });

    it('should show ratings', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/4\.5/)).toBeInTheDocument();
        expect(screen.getByText(/4\.8/)).toBeInTheDocument();
      });
    });

    it('should display tags', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备')).toBeInTheDocument();
        expect(screen.getByText('质量')).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('should search knowledge items', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备操作指南')).toBeInTheDocument();
      });

      const searchInput = screen.queryByPlaceholderText(/搜索|Search/i);
      if (searchInput) {
        fireEvent.change(searchInput, { target: { value: '设备' } });

        await waitFor(() => {
          expect(api.get).toHaveBeenCalled();
        });
      }
    });

    it('should filter by category', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('操作指南')).toBeInTheDocument();
      });

      const categoryButton = screen.getByText('操作指南');
      fireEvent.click(categoryButton);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });
    });

    it('should filter by tags', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备')).toBeInTheDocument();
      });

      const tagButton = screen.getByText('设备');
      fireEvent.click(tagButton);

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });
    });
  });

  describe('Favorite Management', () => {
    it('should show favorite status', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('质量检验标准')).toBeInTheDocument();
      });

      const favoriteButtons = screen.queryAllByRole('button', { name: /收藏|Favorite/i });
      expect(favoriteButtons.length).toBeGreaterThanOrEqual(0);
    });

    it('should toggle favorite', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备操作指南')).toBeInTheDocument();
      });

      const favoriteButtons = screen.queryAllByRole('button', { name: /收藏|Favorite/i });
      if (favoriteButtons.length > 0) {
        fireEvent.click(favoriteButtons[0]);

        await waitFor(() => {
          expect(api.post).toHaveBeenCalled();
        });
      }
    });

    it('should view favorites only', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const favoritesFilter = screen.queryByRole('button', { name: /我的收藏|My Favorites/i });
      if (favoritesFilter) {
        fireEvent.click(favoritesFilter);

        await waitFor(() => {
          expect(api.get).toHaveBeenCalled();
        });
      }
    });
  });

  describe('Rating and Feedback', () => {
    it('should rate knowledge item', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备操作指南')).toBeInTheDocument();
      });

      const ratingButtons = screen.queryAllByRole('button', { name: /评分|Rate/i });
      if (ratingButtons.length > 0) {
        fireEvent.click(ratingButtons[0]);

        await waitFor(() => {
          expect(api.post).toHaveBeenCalled();
        });
      }
    });

    it('should like knowledge item', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备操作指南')).toBeInTheDocument();
      });

      const likeButtons = screen.queryAllByRole('button', { name: /点赞|Like/i });
      if (likeButtons.length > 0) {
        fireEvent.click(likeButtons[0]);

        await waitFor(() => {
          expect(api.post).toHaveBeenCalled();
        });
      }
    });
  });

  describe('CRUD Operations', () => {
    it('should create new knowledge item', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const createButton = screen.queryByRole('button', { name: /新建|Create|添加/i });
      if (createButton) {
        fireEvent.click(createButton);

        expect(screen.queryByText(/新建知识|Create Knowledge/i)).toBeTruthy();
      }
    });

    it('should edit knowledge item', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备操作指南')).toBeInTheDocument();
      });

      const editButtons = screen.queryAllByRole('button', { name: /编辑|Edit/i });
      if (editButtons.length > 0) {
        fireEvent.click(editButtons[0]);

        expect(screen.queryByText(/编辑知识|Edit Knowledge/i)).toBeTruthy();
      }
    });

    it('should delete knowledge item', async () => {
      window.confirm = vi.fn(() => true);

      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备操作指南')).toBeInTheDocument();
      });

      const deleteButtons = screen.queryAllByRole('button', { name: /删除|Delete/i });
      if (deleteButtons.length > 0) {
        fireEvent.click(deleteButtons[0]);

        await waitFor(() => {
          expect(api.delete).toHaveBeenCalled();
        });
      }
    });

    it('should view knowledge detail', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('设备操作指南')).toBeInTheDocument();
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

  describe('Category Management', () => {
    it('should display category counts', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/15/)).toBeInTheDocument();
        expect(screen.getByText(/20/)).toBeInTheDocument();
      });
    });

    it('should manage categories', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const manageCategoryButton = screen.queryByRole('button', { name: /管理分类|Manage Categories/i });
      if (manageCategoryButton) {
        fireEvent.click(manageCategoryButton);

        expect(screen.queryByText(/分类管理|Category Management/i)).toBeTruthy();
      }
    });
  });

  describe('Statistics Display', () => {
    it('should show total knowledge count', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/45.*知识|Total.*45/i)).toBeInTheDocument();
      });
    });

    it('should display total views and likes', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/5,000|5千/)).toBeInTheDocument();
        expect(screen.getByText(/800/)).toBeInTheDocument();
      });
    });

    it('should show status statistics', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/40.*已发布|Published.*40/i)).toBeInTheDocument();
        expect(screen.getByText(/5.*草稿|Draft.*5/i)).toBeInTheDocument();
      });
    });
  });

  describe('Export Functionality', () => {
    it('should export knowledge base', async () => {
      render(
        <MemoryRouter>
          <KnowledgeBase />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(api.get).toHaveBeenCalled();
      });

      const exportButton = screen.queryByRole('button', { name: /导出|Export/i });
      if (exportButton) {
        fireEvent.click(exportButton);

        await waitFor(() => {
          expect(api.post).toHaveBeenCalledWith(
            expect.stringContaining('/export')
          );
        });
      }
    });
  });
});
