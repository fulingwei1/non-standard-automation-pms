/**
 * Header 组件测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../Header';

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Search: () => <div data-testid="search-icon">Search</div>,
  Bell: () => <div data-testid="bell-icon">Bell</div>,
  ChevronDown: () => <div data-testid="chevron-down">ChevronDown</div>,
  Settings: () => <div data-testid="settings-icon">Settings</div>,
  User: () => <div data-testid="user-icon">User</div>,
  LogOut: () => <div data-testid="logout-icon">LogOut</div>,
  Command: () => <div data-testid="command-icon">Command</div>,
}));

describe('Header 组件', () => {
  const mockOnLogout = vi.fn();

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('渲染测试', () => {
    it('应该正确渲染基本结构', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByTestId('search-icon')).toBeInTheDocument();
      expect(screen.getByTestId('bell-icon')).toBeInTheDocument();
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

      expect(screen.getByText('用')).toBeInTheDocument(); // 默认头像文字
    });

    it('应该显示用户角色信息', () => {
      const mockUser = {
        id: 1,
        username: 'pmuser',
        real_name: '项目经理',
        role: 'pm',
      };

      render(<Header sidebarCollapsed={false} user={mockUser} onLogout={mockOnLogout} />);

      // 角色应该显示在第二行
      const userInfo = screen.getByText('项目经理').closest('button');
      expect(userInfo).toBeInTheDocument();
    });

    it('应该处理localStorage中的无效JSON', () => {
      localStorage.setItem('user', 'invalid-json');

      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      // 应该显示默认值
      expect(screen.getByText('用户')).toBeInTheDocument();
    });
  });

  describe('欢迎消息', () => {
    it('早上应该显示"早上好"', () => {
      // Mock Date
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
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      const bellIcon = screen.getByTestId('bell-icon').closest('button');
      expect(bellIcon).toBeInTheDocument();

      fireEvent.click(bellIcon);
      // 确保可以点击
    });

    it('点击退出登录应该调用onLogout', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      // 打开用户菜单
      const userButton = screen.getByTestId('chevron-down').closest('button');
      fireEvent.click(userButton);

      // 点击退出登录
      const logoutButton = screen.getByText('退出登录');
      fireEvent.click(logoutButton);

      expect(mockOnLogout).toHaveBeenCalled();
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

      const userButton = screen.getByTestId('chevron-down').closest('button');
      fireEvent.click(userButton);

      expect(screen.getByText('个人信息')).toBeInTheDocument();
    });

    it('应该包含账户设置选项', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      const userButton = screen.getByTestId('chevron-down').closest('button');
      fireEvent.click(userButton);

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
