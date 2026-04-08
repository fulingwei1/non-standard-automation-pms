/**
 * Header 组件测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Header } from '../Header';

vi.mock('lucide-react', () => ({
  Search: () => <div data-testid="search-icon">Search</div>,
  Bell: () => <div data-testid="bell-icon">Bell</div>,
  ChevronDown: () => <div data-testid="chevron-down">ChevronDown</div>,
  Settings: () => <div data-testid="settings-icon">Settings</div>,
  User: () => <div data-testid="user-icon">User</div>,
  LogOut: () => <div data-testid="logout-icon">LogOut</div>,
  Command: () => <div data-testid="command-icon">Command</div>,
}));

vi.mock('../../ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }) => <div data-testid="dropdown-menu">{children}</div>,
  DropdownMenuTrigger: ({ children, asChild }) => (asChild ? children : <div>{children}</div>),
  DropdownMenuContent: ({ children }) => <div data-testid="dropdown-content">{children}</div>,
  DropdownMenuItem: ({ children, onClick, className }) => (
    <button type="button" onClick={onClick} className={className}>
      {children}
    </button>
  ),
  DropdownMenuSeparator: () => <div data-testid="dropdown-separator" />,
}));

vi.mock('../../ui/avatar', () => ({
  Avatar: ({ children, className }) => <div data-testid="avatar" className={className}>{children}</div>,
  AvatarImage: ({ src }) => <img data-testid="avatar-image" src={src} alt="avatar" />,
  AvatarFallback: ({ children, className }) => <div data-testid="avatar-fallback" className={className}>{children}</div>,
}));

vi.mock('../../lib/roleConfig', () => ({
  getRoleInfo: (role) => ({
    name: role === 'pm' ? '项目经理' : role === 'unknown' ? '用户' : role,
  }),
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
      expect(screen.getByText('搜索项目、设备...')).toBeInTheDocument();
    });

    it('sidebar收起时应该调整左边距', () => {
      const { container, rerender } = render(
        <Header sidebarCollapsed={false} onLogout={mockOnLogout} />
      );

      expect(container.querySelector('header')).toHaveClass('left-60');

      rerender(<Header sidebarCollapsed={true} onLogout={mockOnLogout} />);
      expect(container.querySelector('header')).toHaveClass('left-[72px]');
    });
  });

  describe('用户信息显示', () => {
    it('未提供用户时应该从localStorage读取', () => {
      localStorage.setItem(
        'user',
        JSON.stringify({ id: 1, username: 'testuser', real_name: '测试用户' })
      );

      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByText('测试用户')).toBeInTheDocument();
    });

    it('应该显示用户头像的首字母', () => {
      render(
        <Header
          sidebarCollapsed={false}
          user={{ id: 1, username: 'testuser', real_name: '张三' }}
          onLogout={mockOnLogout}
        />
      );

      expect(screen.getByText('张')).toBeInTheDocument();
    });

    it('无用户信息时应该显示默认文本', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getAllByText('用户').length).toBeGreaterThan(0);
      expect(screen.getByText('用')).toBeInTheDocument();
    });

    it('应该显示用户角色信息', () => {
      render(
        <Header
          sidebarCollapsed={false}
          user={{ id: 1, username: 'pmuser', real_name: '项目经理', role: 'pm' }}
          onLogout={mockOnLogout}
        />
      );

      expect(screen.getAllByText('项目经理').length).toBeGreaterThan(0);
    });

    it('应该处理localStorage中的无效JSON', () => {
      localStorage.setItem('user', 'invalid-json');
      const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getAllByText('用户').length).toBeGreaterThan(0);
      warnSpy.mockRestore();
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
    it('点击搜索区域不会报错', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      const searchButton = screen.getByText('搜索项目、设备...').closest('button');
      expect(() => fireEvent.click(searchButton)).not.toThrow();
    });

    it('通知按钮和未读标记存在', () => {
      const { container } = render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByTestId('bell-icon')).toBeInTheDocument();
      expect(container.querySelector('.bg-red-500')).toBeInTheDocument();
    });

    it('点击退出登录应该调用onLogout', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      fireEvent.click(screen.getByText('退出登录'));
      expect(mockOnLogout).toHaveBeenCalledTimes(1);
    });
  });

  describe('下拉菜单', () => {
    it('应该包含个人信息和账户设置选项', () => {
      render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      expect(screen.getByText('个人信息')).toBeInTheDocument();
      expect(screen.getByText('账户设置')).toBeInTheDocument();
      expect(screen.getByText('退出登录')).toBeInTheDocument();
    });
  });

  describe('响应式设计', () => {
    it('小屏幕时欢迎消息容器应带 hidden md:block', () => {
      const { container } = render(<Header sidebarCollapsed={false} onLogout={mockOnLogout} />);

      const welcomeMessage = container.querySelector('.md\\:block');
      expect(welcomeMessage).toBeInTheDocument();
      expect(welcomeMessage).toHaveClass('hidden', 'md:block');
    });
  });
});
