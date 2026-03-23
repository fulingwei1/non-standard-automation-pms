/**
 * MainLayout 组件测试
 *
 * MainLayout 使用全局变量（Sidebar, Header, ToastContainer, AnimatePresence）
 * 这些在 setupTests.js 中定义为 fallback，不渲染 children。
 * 此处在 beforeEach 中覆盖全局变量，使其按预期渲染。
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { MainLayout } from '../MainLayout';

// Mock useToast（来自 ../ui，是真实的 import）
vi.mock('../../ui', () => ({
  ToastContainer: ({ toasts, onClose }) => (
    <div data-testid="toast-container">
      {(toasts || []).map((toast, i) => (
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

  // 保存原始全局值
  let origSidebar;
  let origHeader;
  let origToastContainer;
  let origAnimatePresence;

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();

    // 保存原始全局 fallback
    origSidebar = globalThis.Sidebar;
    origHeader = globalThis.Header;
    origToastContainer = globalThis.ToastContainer;
    origAnimatePresence = globalThis.AnimatePresence;

    // 覆盖全局 Sidebar：渲染含交互按钮的 mock
    globalThis.Sidebar = ({ collapsed, onToggle, onLogout }) => (
      React.createElement('div', { 'data-testid': 'sidebar' },
        React.createElement('div', null, `Sidebar Collapsed: ${String(collapsed)}`),
        React.createElement('button', { onClick: onToggle }, 'Toggle Sidebar'),
        React.createElement('button', { onClick: onLogout }, 'Logout')
      )
    );

    // 覆盖全局 Header：渲染用户信息和登出按钮
    globalThis.Header = ({ sidebarCollapsed, user, onLogout }) => (
      React.createElement('div', { 'data-testid': 'header' },
        React.createElement('div', null, `Header Collapsed: ${String(sidebarCollapsed)}`),
        React.createElement('div', null, `User: ${user?.username || 'none'}`),
        React.createElement('button', { onClick: onLogout }, 'Logout Header')
      )
    );

    // 覆盖全局 ToastContainer：渲染 toast 列表
    globalThis.ToastContainer = ({ toasts, onClose }) => (
      React.createElement('div', { 'data-testid': 'toast-container' },
        (toasts || []).map((toast, i) =>
          React.createElement('div', { key: i, 'data-testid': `toast-${i}` },
            toast.message,
            React.createElement('button', { onClick: () => onClose(toast.id) }, 'Close')
          )
        )
      )
    );

    // AnimatePresence 只渲染 children
    globalThis.AnimatePresence = ({ children }) => React.createElement(React.Fragment, null, children);
  });

  afterEach(() => {
    // 恢复原始全局值
    globalThis.Sidebar = origSidebar;
    globalThis.Header = origHeader;
    globalThis.ToastContainer = origToastContainer;
    globalThis.AnimatePresence = origAnimatePresence;
  });

  const renderWithRouter = (ui) => {
    return render(React.createElement(BrowserRouter, null, ui));
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

      const mockUser = {
        id: 1,
        username: 'newuser',
        real_name: '新用户',
      };

      act(() => {
        localStorage.setItem('user', JSON.stringify(mockUser));
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
      expect(mainElement).toHaveClass('pl-60');
    });

    it('sidebar折叠时main应该调整padding', () => {
      const { container } = renderWithRouter(
        <MainLayout onLogout={mockOnLogout}>Content</MainLayout>
      );

      const toggleButton = screen.getByText('Toggle Sidebar');
      fireEvent.click(toggleButton);

      const mainElement = container.querySelector('main');
      expect(mainElement).toHaveClass('pl-[72px]');
    });
  });

  describe('动画效果', () => {
    it('应该包含AnimatePresence用于内容切换', () => {
      renderWithRouter(
        <MainLayout onLogout={mockOnLogout}>
          <div>Animated Content</div>
        </MainLayout>
      );

      expect(screen.getByText('Animated Content')).toBeInTheDocument();
    });
  });
});
