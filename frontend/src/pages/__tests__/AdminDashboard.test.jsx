import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { mockApiGet, mockNavigate, consoleErrorMock, scrollToMock } = vi.hoisted(() => ({
  mockApiGet: vi.fn(),
  mockNavigate: vi.fn(),
  consoleErrorMock: vi.fn(),
  scrollToMock: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  default: {
    get: mockApiGet,
  },
}));

vi.mock('framer-motion', () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const Tag = typeof tag === 'string' ? tag : 'div';
        const filteredProps = Object.fromEntries(
          Object.entries(props).filter(
            ([key]) =>
              ![
                'initial',
                'animate',
                'exit',
                'variants',
                'transition',
                'whileHover',
                'whileTap',
                'whileInView',
                'layout',
                'layoutId',
                'drag',
                'dragConstraints',
                'onDragEnd',
              ].includes(key),
          ),
        );
        return <Tag {...filteredProps}>{children}</Tag>;
      },
    },
  ),
}));

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../../components/layout', () => ({
  PageHeader: ({ title, subtitle }) => (
    <div>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  ),
}));

vi.mock('../../components/ui', () => ({
  Card: ({ children }) => <div>{children}</div>,
  CardHeader: ({ children }) => <div>{children}</div>,
  CardContent: ({ children }) => <div>{children}</div>,
  CardTitle: ({ children }) => <h2>{children}</h2>,
  Progress: ({ value }) => <div role="progressbar" aria-valuenow={value} />,
  ApiIntegrationError: ({ error, apiEndpoint, onRetry }) => (
    <div>
      <p>接口异常：{error?.message || String(error)}</p>
      <p>{apiEndpoint}</p>
      <button type="button" onClick={onRetry}>
        重试
      </button>
    </div>
  ),
}));

vi.mock('../../components/common/StatCard', () => ({
  default: ({ title, value, subtitle, onClick }) => (
    <button type="button" onClick={onClick}>
      <span>{title}</span>
      <span>{String(value)}</span>
      {subtitle ? <span>{subtitle}</span> : null}
    </button>
  ),
}));

import AdminDashboard from '../AdminDashboard';

const statsData = {
  totalUsers: 151,
  activeUsers: 121,
  inactiveUsers: 30,
  newUsersThisMonth: 17,
  usersWithRoles: 140,
  usersWithoutRoles: 11,
  totalRoles: 8,
  systemRoles: 5,
  customRoles: 3,
  activeRoles: 7,
  inactiveRoles: 1,
  totalPermissions: 53,
  assignedPermissions: 45,
  unassignedPermissions: 8,
  systemUptime: 97.7,
  databaseSize: 12.8,
  storageUsed: 68,
  apiResponseTime: 187,
  errorRate: 0.3,
  loginCountToday: 29,
  loginCountThisWeek: 206,
  lastBackup: '2026-04-06 23:00',
  auditLogsToday: 41,
  auditLogsThisWeek: 311,
};

describe('AdminDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(consoleErrorMock);
    vi.spyOn(window, 'scrollTo').mockImplementation(scrollToMock);

    mockApiGet.mockResolvedValue({
      data: {
        data: statsData,
      },
    });
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <AdminDashboard />
      </MemoryRouter>,
    );
  }

  it('默认加载管理员统计并渲染核心卡片', async () => {
    renderPage();

    expect(screen.getByText('加载中...')).toBeInTheDocument();

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith('/admin/stats');
    });

    expect(screen.getByText('管理员工作台')).toBeInTheDocument();
    expect(screen.getByText('系统配置、用户管理、权限分配、系统维护')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /总用户数/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /角色总数/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /权限总数/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /系统可用性/i })).toBeInTheDocument();
    expect(screen.getByText('快捷操作')).toBeInTheDocument();
    expect(screen.getByText('系统健康状态')).toBeInTheDocument();
    expect(screen.getByText('系统提醒')).toBeInTheDocument();
    expect(screen.getByText('151')).toBeInTheDocument();
    expect(screen.getByText('53')).toBeInTheDocument();
    expect(screen.getAllByText('97.7%').length).toBeGreaterThanOrEqual(1);
  });

  it('点击统计卡片会跳转到对应管理页面', async () => {
    renderPage();

    await screen.findByRole('button', { name: /总用户数/i });

    fireEvent.click(screen.getByRole('button', { name: /总用户数/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/user-management');

    fireEvent.click(screen.getByRole('button', { name: /角色总数/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/role-management');

    fireEvent.click(screen.getByRole('button', { name: /权限总数/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/permission-management');

    fireEvent.click(screen.getByRole('button', { name: /系统可用性/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/settings');
  });

  it('顶部导航按钮支持滚动和页面跳转', async () => {
    renderPage();

    await screen.findByText('系统概览');

    fireEvent.click(screen.getByRole('button', { name: '系统概览' }));
    expect(scrollToMock).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' });

    fireEvent.click(screen.getByRole('button', { name: '用户管理' }));
    expect(mockNavigate).toHaveBeenCalledWith('/user-management');

    fireEvent.click(screen.getByRole('button', { name: '角色权限' }));
    expect(mockNavigate).toHaveBeenCalledWith('/role-management');

    fireEvent.click(screen.getByRole('button', { name: '系统监控' }));
    expect(mockNavigate).toHaveBeenCalledWith('/scheduler-monitoring');

    fireEvent.click(screen.getByRole('button', { name: '活动日志' }));
    expect(mockNavigate).toHaveBeenCalledWith('/scheduler-monitoring');
  });

  it('渲染系统健康和运行数据摘要', async () => {
    renderPage();

    await screen.findByText('系统健康状态');

    expect(screen.getByText('存储使用率')).toBeInTheDocument();
    expect(screen.getByText('数据库大小')).toBeInTheDocument();
    expect(screen.getByText('API 平均响应时间')).toBeInTheDocument();
    expect(screen.getByText('错误率')).toBeInTheDocument();
    expect(screen.getByText('68%')).toBeInTheDocument();
    expect(screen.getByText('12.8 GB')).toBeInTheDocument();
    expect(screen.getByText('187 ms')).toBeInTheDocument();
    expect(screen.getByText('0.3%')).toBeInTheDocument();
    expect(screen.getByText('今日登录')).toBeInTheDocument();
    expect(screen.getByText('今日审计日志')).toBeInTheDocument();
    expect(screen.getByText('最后备份')).toBeInTheDocument();
    expect(screen.getByText('2026-04-06 23:00')).toBeInTheDocument();
    expect(screen.getAllByRole('progressbar')).toHaveLength(2);
  });

  it('接口失败时显示错误态并支持重试', async () => {
    mockApiGet
      .mockRejectedValueOnce(new Error('Load failed'))
      .mockResolvedValueOnce({
        data: {
          data: statsData,
        },
      });

    renderPage();

    expect(await screen.findByText('接口异常：Load failed')).toBeInTheDocument();
    expect(screen.getByText('/api/v1/admin/stats')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '重试' }));

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledTimes(2);
    });

    expect(await screen.findByRole('button', { name: /总用户数/i })).toBeInTheDocument();
  });
});
