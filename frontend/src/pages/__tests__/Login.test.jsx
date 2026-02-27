/**
 * Login 页面测试
 * 测试登录页面的表单交互、验证和API调用
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../Login';
import { authApi } from '../../services/api';

// Mock authApi
// Mock motion components
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}));

// Mock diagnose
vi.mock('../../utils/diagnose', () => ({
  diagnoseLogin: vi.fn(),
}));

// Mock logger
vi.mock('../../utils/logger', () => ({
  logger: {
    error: vi.fn(),
    debug: vi.fn(),
    warn: vi.fn(),
  },
}));

describe('Login 页面', () => {
  const mockOnLoginSuccess = vi.fn();

  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  describe('基本渲染', () => {
    it('应该正确渲染登录表单', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      expect(screen.getByText('欢迎回来')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('请输入用户名')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('请输入密码')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /登录/ })).toBeInTheDocument();
    });

    it('应该显示品牌信息', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      expect(screen.getByText(/让每个项目/)).toBeInTheDocument();
      expect(screen.getByText(/尽在掌控/)).toBeInTheDocument();
    });

    it('应该显示功能特性', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      expect(screen.getByText('实时进度追踪')).toBeInTheDocument();
      expect(screen.getByText('智能工时管理')).toBeInTheDocument();
      expect(screen.getByText('团队高效协作')).toBeInTheDocument();
      expect(screen.getByText('AI 智能预警')).toBeInTheDocument();
    });

    it('应该显示快捷登录按钮', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      expect(screen.getByText('郑汝才')).toBeInTheDocument();
      expect(screen.getByText('骆奕兴')).toBeInTheDocument();
      expect(screen.getByText('符凌维')).toBeInTheDocument();
    });
  });

  describe('表单输入', () => {
    it('应该能够输入用户名', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      fireEvent.change(usernameInput, { target: { value: 'testuser' } });

      expect(usernameInput.value).toBe('testuser');
    });

    it('应该能够输入密码', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const passwordInput = screen.getByPlaceholderText('请输入密码');
      fireEvent.change(passwordInput, { target: { value: 'password123' } });

      expect(passwordInput.value).toBe('password123');
    });

    it('密码输入框默认应该是password类型', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const passwordInput = screen.getByPlaceholderText('请输入密码');
      expect(passwordInput.type).toBe('password');
    });

    it('点击眼睛图标应该切换密码可见性', () => {
      const { container } = render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const toggleButton = container.querySelector('button[type="button"]');

      expect(passwordInput.type).toBe('password');

      fireEvent.click(toggleButton);
      expect(passwordInput.type).toBe('text');

      fireEvent.click(toggleButton);
      expect(passwordInput.type).toBe('password');
    });
  });

  describe('记住我功能', () => {
    it('默认应该勾选记住我', () => {
      const { container } = render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const checkbox = container.querySelector('input[type="checkbox"]');
      expect(checkbox.checked).toBe(true);
    });

    it('应该能够切换记住我状态', () => {
      const { container } = render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const checkbox = container.querySelector('input[type="checkbox"]');
      
      fireEvent.click(checkbox);
      expect(checkbox.checked).toBe(false);

      fireEvent.click(checkbox);
      expect(checkbox.checked).toBe(true);
    });
  });

  describe('表单提交', () => {
    it('空表单提交应该被HTML5验证阻止', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const form = screen.getByRole('button', { name: /登录/ }).closest('form');
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
      
      form.dispatchEvent(submitEvent);

      // HTML5验证会阻止空表单提交
      expect(authApi.login).not.toHaveBeenCalled();
    });

    it('成功登录应该调用API并保存token', async () => {
      const mockUserData = {
        id: 1,
        username: 'testuser',
        real_name: '测试用户',
        roles: ['pm'],
        permissions: ['project:view'],
      };

      authApi.login.mockResolvedValue({
        data: { access_token: 'test-token-123' },
      });

      authApi.me.mockResolvedValue({
        data: mockUserData,
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(authApi.login).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(localStorage.getItem('token')).toBe('test-token-123');
        expect(mockOnLoginSuccess).toHaveBeenCalled();
      });
    });

    it('登录失败应该显示错误信息', async () => {
      authApi.login.mockRejectedValue({
        response: {
          status: 401,
          data: { detail: '用户名或密码错误' },
        },
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'wronguser' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/用户名或密码错误/)).toBeInTheDocument();
      });

      expect(mockOnLoginSuccess).not.toHaveBeenCalled();
    });

    it('网络错误应该显示相应提示', async () => {
      authApi.login.mockRejectedValue({
        request: {},
        message: 'Network Error',
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'password' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/无法连接到服务器/)).toBeInTheDocument();
      });
    });

    it('提交时应该显示loading状态', async () => {
      authApi.login.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'password' } });
      fireEvent.click(loginButton);

      // 应该显示加载动画
      await waitFor(() => {
        const spinner = screen.getByRole('button', { name: /登录/ }).querySelector('svg.animate-spin');
        expect(spinner).toBeInTheDocument();
      });
    });

    it('loading时按钮应该被禁用', async () => {
      authApi.login.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'password' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(loginButton).toBeDisabled();
      });
    });
  });

  describe('快捷登录', () => {
    it('点击快捷登录应该填充用户名和密码', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const quickLoginButton = screen.getByText('郑汝才').closest('button');
      fireEvent.click(quickLoginButton);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');

      expect(usernameInput.value).toBe('zhengrucai');
      expect(passwordInput.value).toBe('123456');
    });

    it('所有快捷登录按钮都应该可用', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const quickLogins = [
        { name: '郑汝才', username: 'zhengrucai' },
        { name: '骆奕兴', username: 'luoyixing' },
        { name: '符凌维', username: 'fulingwei' },
        { name: '宋魁', username: 'songkui' },
      ];

      quickLogins.forEach(({ name, username }) => {
        const button = screen.getByText(name).closest('button');
        fireEvent.click(button);

        const usernameInput = screen.getByPlaceholderText('请输入用户名');
        expect(usernameInput.value).toBe(username);
      });
    });
  });

  describe('错误处理', () => {
    it('用户未找到应该显示特定错误', async () => {
      authApi.login.mockRejectedValue({
        response: {
          status: 401,
          data: {
            detail: {
              error_code: 'USER_NOT_FOUND',
              message: '该员工尚未开通系统账号',
            },
          },
        },
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'newuser' } });
      fireEvent.change(passwordInput, { target: { value: 'password' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/该员工尚未开通系统账号/)).toBeInTheDocument();
      });
    });

    it('账号已禁用应该显示特定错误', async () => {
      authApi.login.mockRejectedValue({
        response: {
          status: 401,
          data: {
            detail: {
              error_code: 'USER_DISABLED',
              message: '账号已被禁用',
            },
          },
        },
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'disabled' } });
      fireEvent.change(passwordInput, { target: { value: 'password' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/账号已被禁用/)).toBeInTheDocument();
      });
    });

    it('获取用户信息失败应该清除token', async () => {
      authApi.login.mockResolvedValue({
        data: { access_token: 'test-token' },
      });

      authApi.me.mockRejectedValue({
        response: { status: 500 },
        message: 'Server Error',
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'testuser' } });
      fireEvent.change(passwordInput, { target: { value: 'password' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/系统错误/)).toBeInTheDocument();
      });

      expect(localStorage.getItem('token')).toBeNull();
      expect(mockOnLoginSuccess).not.toHaveBeenCalled();
    });

    it('用户无角色应该显示错误并清除token', async () => {
      authApi.login.mockResolvedValue({
        data: { access_token: 'test-token' },
      });

      authApi.me.mockResolvedValue({
        data: {
          id: 1,
          username: 'norole',
          real_name: '无角色用户',
          is_superuser: false,
          roles: [], // 无角色
          permissions: [],
        },
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'norole' } });
      fireEvent.change(passwordInput, { target: { value: 'password' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/尚未分配角色/)).toBeInTheDocument();
      });

      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  describe('角色映射', () => {
    it('应该正确映射超级管理员角色', async () => {
      authApi.login.mockResolvedValue({
        data: { access_token: 'admin-token' },
      });

      authApi.me.mockResolvedValue({
        data: {
          id: 1,
          username: 'admin',
          is_superuser: true,
          roles: [],
          permissions: [],
        },
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'admin' } });
      fireEvent.change(passwordInput, { target: { value: 'admin' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        const savedUser = JSON.parse(localStorage.getItem('user'));
        expect(savedUser.role).toBe('super_admin');
      });
    });

    it('应该正确映射项目经理角色', async () => {
      authApi.login.mockResolvedValue({
        data: { access_token: 'pm-token' },
      });

      authApi.me.mockResolvedValue({
        data: {
          id: 1,
          username: 'pm',
          real_name: '项目经理',
          is_superuser: false,
          roles: ['PM'],
          permissions: [],
        },
      });

      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      const usernameInput = screen.getByPlaceholderText('请输入用户名');
      const passwordInput = screen.getByPlaceholderText('请输入密码');
      const loginButton = screen.getByRole('button', { name: /登录/ });

      fireEvent.change(usernameInput, { target: { value: 'pm' } });
      fireEvent.change(passwordInput, { target: { value: 'password' } });
      fireEvent.click(loginButton);

      await waitFor(() => {
        const savedUser = JSON.parse(localStorage.getItem('user'));
        expect(savedUser.role).toBe('pm');
      });
    });
  });

  describe('UI交互', () => {
    it('应该显示忘记密码链接', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      expect(screen.getByText('忘记密码？')).toBeInTheDocument();
    });

    it('底部应该显示版权信息', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      expect(screen.getByText(/© 2026 项目进度管理系统/)).toBeInTheDocument();
    });

    it('应该显示快捷登录提示文本', () => {
      render(<Login onLoginSuccess={mockOnLoginSuccess} />);

      expect(screen.getByText(/点击上方按钮自动填充账号/)).toBeInTheDocument();
    });
  });
});
