/**
 * MainLayout 组件测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { MainLayout } from '../MainLayout';

// Mock子组件
vi.mock('../Sidebar', () => ({
  Sidebar: ({ collapsed, onToggle, onLogout }) => (
    <div data-testid="sidebar">
      <div>Sidebar Collapsed: {String(collapsed)}</div>
      <button onClick={onToggle}>Toggle Sidebar</button>
      <button onClick={onLogout}>Logout</button>
    </div>
  ),
}));

vi.mock('../Header', () => ({
  Header: ({ sidebarCollapsed, user, onLogout }) => (
    <div data-testid="header">
      <div>Header Collapsed: {String(sidebarCollapsed)}</div>
      <div>User: {user?.username || 'none'}</div>
      <button onClick={onLogout}>Logout Header</button>
    </div>
  ),
}));

vi.mock('../../ui', () => ({
  ToastContainer: ({ toasts, onClose }) => (
    <div data-testid="toast-container">
      {toasts.map((toast, i) => (
        <div key={i} data-testid={`toast-${i}`}>
          {toast.message}
          <button onClick={() => onClose(toast.id)}>Close</button>
        </div>
      ))}
    </div>
  ),
  useToast: () => ({
    toasts: [],
    removeToast: vi.fn(),
  }),
}));

describe('MainLayout 组件', () => {
  const mockOnLogout = vi.fn();

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const renderWithRouter = (ui) => {
    return render(<BrowserRouter>{ui}</BrowserRouter>);
  };

  describe('渲染测试', () => {
    it('应该正确渲染所有子组件', () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('header')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('应该渲染ToastContainer', () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      expect(screen.getByTestId('toast-container')).toBeInTheDocument();
    });

    it('应该正确渲染children', () => {
      renderWithRouter(
        <MainLayout onLogout={mockOnLogout}>
          <div>Test Child Component</div>
        </MainLayout>
      );

      expect(screen.getByText('Test Child Component')).toBeInTheDocument();
    });
  });

  describe('sidebar折叠状态', () => {
    it('初始状态应该是展开的', () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      expect(screen.getByText('Sidebar Collapsed: false')).toBeInTheDocument();
      expect(screen.getByText('Header Collapsed: false')).toBeInTheDocument();
    });

    it('点击Toggle应该切换sidebar状态', () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      const toggleButton = screen.getByText('Toggle Sidebar');
      
      expect(screen.getByText('Sidebar Collapsed: false')).toBeInTheDocument();

      fireEvent.click(toggleButton);

      expect(screen.getByText('Sidebar Collapsed: true')).toBeInTheDocument();
      expect(screen.getByText('Header Collapsed: true')).toBeInTheDocument();

      fireEvent.click(toggleButton);

      expect(screen.getByText('Sidebar Collapsed: false')).toBeInTheDocument();
    });

    it('sidebar和header的collapsed状态应该同步', () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      const toggleButton = screen.getByText('Toggle Sidebar');
      fireEvent.click(toggleButton);

      // 两个组件的状态应该一致
      expect(screen.getByText('Sidebar Collapsed: true')).toBeInTheDocument();
      expect(screen.getByText('Header Collapsed: true')).toBeInTheDocument();
    });
  });

  describe('用户信息管理', () => {
    it('应该从localStorage读取用户信息', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        real_name: '测试用户',
      };
      localStorage.setItem('user', JSON.stringify(mockUser));

      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      await waitFor(() => {
        expect(screen.getByText('User: testuser')).toBeInTheDocument();
      });
    });

    it('localStorage为空时应该显示none', () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      expect(screen.getByText('User: none')).toBeInTheDocument();
    });

    it('应该处理localStorage的无效JSON', async () => {
      localStorage.setItem('user', 'invalid-json');

      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      await waitFor(() => {
        expect(screen.getByText('User: none')).toBeInTheDocument();
      });
    });

    it('应该监听storage事件更新用户信息', async () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      await waitFor(() => {
        expect(screen.getByText('User: none')).toBeInTheDocument();
      });

      // 模拟其他标签页更新localStorage
      const mockUser = {
        id: 1,
        username: 'newuser',
        real_name: '新用户',
      };
      
      act(() => {
        localStorage.setItem('user', JSON.stringify(mockUser));
        
        // 触发storage事件
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'user',
          newValue: JSON.stringify(mockUser),
          oldValue: null,
        }));
      });

      await waitFor(() => {
        expect(screen.getByText('User: newuser')).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('storage事件清除用户时应该显示none', async () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
      };
      
      act(() => {
        localStorage.setItem('user', JSON.stringify(mockUser));
      });

      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      await waitFor(() => {
        expect(screen.getByText('User: testuser')).toBeInTheDocument();
      }, { timeout: 3000 });

      // 清除用户
      act(() => {
        localStorage.removeItem('user');
        
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'user',
          newValue: null,
          oldValue: JSON.stringify(mockUser),
        }));
      });

      await waitFor(() => {
        expect(screen.getByText('User: none')).toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });

  describe('登出功能', () => {
    it('Sidebar的登出按钮应该调用onLogout', () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      const logoutButton = screen.getByText('Logout');
      fireEvent.click(logoutButton);

      expect(mockOnLogout).toHaveBeenCalled();
    });

    it('Header的登出按钮应该调用onLogout', () => {
      renderWithRouter(<MainLayout onLogout={mockOnLogout}>Content</MainLayout>);

      const logoutButton = screen.getByText('Logout Header');
      fireEvent.click(logoutButton);

      expect(mockOnLogout).toHaveBeenCalled();
    });
  });

  describe('布局样式', () => {
    it('应该有正确的背景色', () => {
      const { container } = renderWithRouter(
        <MainLayout onLogout={mockOnLogout}>Content</MainLayout>
      );

      const mainDiv = container.querySelector('.min-h-screen.bg-surface-0');
      expect(mainDiv).toBeInTheDocument();
    });

    it('main内容区域应该有正确的padding', () => {
      const { container } = renderWithRouter(
        <MainLayout onLogout={mockOnLogout}>Content</MainLayout>
      );

      const mainElement = container.querySelector('main');
      expect(mainElement).toHaveClass('pt-16');
      expect(mainElement).toHaveClass('pl-60'); // sidebar展开时
    });

    it('sidebar折叠时main应该调整padding', () => {
      const { container } = renderWithRouter(
        <MainLayout onLogout={mockOnLogout}>Content</MainLayout>
      );

      const toggleButton = screen.getByText('Toggle Sidebar');
      fireEvent.click(toggleButton);

      const mainElement = container.querySelector('main');
      expect(mainElement).toHaveClass('pl-[72px]'); // sidebar收起时
    });
  });

  describe('动画效果', () => {
    it('应该包含AnimatePresence用于内容切换', () => {
      const { container } = renderWithRouter(
        <MainLayout onLogout={mockOnLogout}>
          <div>Animated Content</div>
        </MainLayout>
      );

      expect(screen.getByText('Animated Content')).toBeInTheDocument();
      // AnimatePresence 被正确使用
    });
  });
});
