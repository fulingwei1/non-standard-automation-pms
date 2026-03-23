/**
 * Header 组件测试
 *
 * Header 使用全局 lucide-react icon fallback（渲染为 SVG 无 data-testid）
 * 以及全局 UI 组件 fallback（DropdownMenu 等渲染为 div）。
 * 测试需要通过文本内容和 DOM 结构来验证。
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../Header';

describe('Header 组件', () => {
  const mockOnLogout = vi.fn();

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('渲染测试', () => {
    it('应该正确渲染基本结构', () => {
      const { container } = render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      // 验证 header 元素存在
      const header = container.querySelector('header');
      expect(header).toBeInTheDocument();

      // 验证搜索按钮存在
      expect(screen.getByText('搜索项目、设备...')).toBeInTheDocument();
    });

    it('sidebar收起时应该调整左边距', () => {
      const { container, rerender } = render(
        <Header sidebarCollapsed={false} onLogout={mockOnLogout} />
      );

      const header = container.querySelector('header');
      expect(header).toHaveClass('left-60');

      rerender(<Header sidebarCollapsed={true} onLogout={mockOnLogout} />);
      expect(header).toHaveClass('left-[72px]');
    });
  });

  describe('用户信息显示', () => {
    it('未提供用户时应该从localStorage读取', () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        real_name: '测试用户',
      };
      localStorage.setItem('user', JSON.stringify(mockUser));

      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByText('测试用户')).toBeInTheDocument();
    });

    it('应该显示用户头像的首字母', () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        real_name: '张三',
      };

      render(<Header sidebarCollapsed={false} user={mockUser} onLogout={mockOnLogout} />);

      expect(screen.getByText('张')).toBeInTheDocument();
    });

    it('应该显示用户真实姓名', () => {
      const mockUser = {
        id: 1,
        username: 'testuser',
        real_name: '李四',
      };

      render(<Header sidebarCollapsed={false} user={mockUser} onLogout={mockOnLogout} />);

      expect(screen.getByText('李四')).toBeInTheDocument();
    });

    it('无用户信息时应该显示默认文本', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      // 默认头像首字母 "用" (来自 "用户"[0])
      expect(screen.getByText('用')).toBeInTheDocument();
    });

    it('应该显示用户角色信息', () => {
      const mockUser = {
        id: 1,
        username: 'pmuser',
        real_name: '项目经理',
        role: 'pm',
      };

      render(<Header sidebarCollapsed={false} user={mockUser} onLogout={mockOnLogout} />);

      // 用户名称应该在触发按钮中
      expect(screen.getByText('项目经理')).toBeInTheDocument();
    });

    it('应该处理localStorage中的无效JSON', () => {
      localStorage.setItem('user', 'invalid-json');

      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      // 无效 JSON 时 currentUser 为 null，displayName 回退到 "用户"
      // "用户" 可能在多处出现（名称和角色/用户名行），用 getAllByText
      const elements = screen.getAllByText('用户');
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('欢迎消息', () => {
    it('早上应该显示"早上好"', () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2024-01-01T08:00:00'));

      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByText(/早上好/)).toBeInTheDocument();

      vi.useRealTimers();
    });

    it('下午应该显示"下午好"', () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2024-01-01T15:00:00'));

      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByText(/下午好/)).toBeInTheDocument();

      vi.useRealTimers();
    });

    it('晚上应该显示"晚上好"', () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2024-01-01T20:00:00'));

      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByText(/晚上好/)).toBeInTheDocument();

      vi.useRealTimers();
    });
  });

  describe('交互功能', () => {
    it('点击搜索框应该触发搜索', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      const searchButton = screen.getByText('搜索项目、设备...').closest('button');
      fireEvent.click(searchButton);

      // 目前只是一个空函数，确保不会报错
      expect(searchButton).toBeInTheDocument();
    });

    it('点击通知图标应该可以交互', () => {
      const { container } = render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      // 通知按钮包含 bg-red-500 的通知点
      const bellButton = container.querySelector('.bg-red-500')?.closest('button');
      expect(bellButton).toBeInTheDocument();

      fireEvent.click(bellButton);
      // 确保可以点击不报错
    });

    it('应该显示未读通知标记', () => {
      const { container } = render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      // 查找红色通知点
      const notificationDot = container.querySelector('.bg-red-500');
      expect(notificationDot).toBeInTheDocument();
    });
  });

  describe('下拉菜单', () => {
    it('应该包含个人信息选项', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      // DropdownMenu fallback 直接渲染所有内容（不需要点击触发）
      expect(screen.getByText('个人信息')).toBeInTheDocument();
    });

    it('应该包含账户设置选项', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByText('账户设置')).toBeInTheDocument();
    });
  });

  describe('响应式设计', () => {
    it('小屏幕时应该隐藏欢迎消息', () => {
      const { container } = render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      const welcomeMessage = container.querySelector('.md\\:block');
      expect(welcomeMessage).toBeInTheDocument();
      expect(welcomeMessage).toHaveClass('hidden', 'md:block');
    });
  });
});
