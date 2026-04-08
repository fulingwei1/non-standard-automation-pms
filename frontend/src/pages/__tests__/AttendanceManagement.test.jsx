import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { useState } from 'react';

const { adminApiMock, consoleLogMock } = vi.hoisted(() => ({
  adminApiMock: {
    attendance: {
      list: vi.fn(),
    },
  },
  consoleLogMock: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  adminApi: adminApiMock,
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

vi.mock('../../components/layout', () => ({
  PageHeader: ({ title, description, actions }) => (
    <div>
      <h1>{title}</h1>
      <p>{description}</p>
      <div>{actions}</div>
    </div>
  ),
}));

vi.mock('../../lib/utils', () => ({
  cn: (...values) => values.filter(Boolean).join(' '),
}));

vi.mock('../../lib/animations', () => ({
  staggerContainer: {},
}));

vi.mock('../../components/ui', async () => {
  const React = await import('react');
  const TabsContext = React.createContext({ value: '', setValue: () => {} });

  function Tabs({ children, defaultValue }) {
    const [value, setValue] = useState(defaultValue);
    return <TabsContext.Provider value={{ value, setValue }}>{children}</TabsContext.Provider>;
  }

  function TabsTrigger({ children, value }) {
    const tabs = React.useContext(TabsContext);
    return (
      <button type="button" onClick={() => tabs.setValue(value)}>
        {children}
      </button>
    );
  }

  function TabsContent({ children, value }) {
    const tabs = React.useContext(TabsContext);
    return tabs.value === value ? <div>{children}</div> : null;
  }

  return {
    Card: ({ children }) => <div>{children}</div>,
    CardContent: ({ children }) => <div>{children}</div>,
    CardHeader: ({ children }) => <div>{children}</div>,
    CardTitle: ({ children }) => <h2>{children}</h2>,
    Button: ({ children, onClick, type = 'button', ...props }) => (
      <button type={type} onClick={onClick} {...props}>
        {children}
      </button>
    ),
    Badge: ({ children }) => <span>{children}</span>,
    Tabs,
    TabsList: ({ children }) => <div>{children}</div>,
    TabsTrigger,
    TabsContent,
    Progress: ({ value }) => <div role="progressbar" aria-valuenow={value} />, 
  };
});

import AttendanceManagement from '../AttendanceManagement';

const departmentStats = [
  {
    department: '研发部',
    total: 10,
    present: 8,
    leave: 1,
    late: 1,
    attendanceRate: 80,
    earlyLeave: 0,
    absence: 1,
  },
  {
    department: '测试部',
    total: 5,
    present: 5,
    leave: 0,
    late: 0,
    attendanceRate: 100,
    earlyLeave: 0,
    absence: 0,
  },
];

describe('AttendanceManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'log').mockImplementation(consoleLogMock);

    adminApiMock.attendance.list.mockResolvedValue({
      data: { items: departmentStats },
    });
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <AttendanceManagement />
      </MemoryRouter>,
    );
  }

  it('默认加载考勤统计并渲染页头和汇总卡片', async () => {
    renderPage();

    await waitFor(() => {
      expect(adminApiMock.attendance.list).toHaveBeenCalledWith({ date: 'today' });
    });

    expect(screen.getByText('员工考勤管理')).toBeInTheDocument();
    expect(screen.getByText('员工考勤记录、统计分析、请假管理、加班管理')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /导出报表/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /统计分析/i })).toBeInTheDocument();

    expect(screen.getByText('总人数')).toBeInTheDocument();
    expect(screen.getAllByText('出勤').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('请假').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('迟到').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('出勤率').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('13')).toBeInTheDocument();
    expect(screen.getByText('86.7%')).toBeInTheDocument();
  });

  it('渲染部门统计列表和对应出勤率', async () => {
    renderPage();

    expect(await screen.findByText('研发部')).toBeInTheDocument();
    expect(screen.getByText('测试部')).toBeInTheDocument();
    expect(screen.getByText('总人数: 10')).toBeInTheDocument();
    expect(screen.getByText('总人数: 5')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    expect(screen.getByText('100.0%')).toBeInTheDocument();
    expect(screen.getAllByRole('progressbar')).toHaveLength(2);
  });

  it('支持 data 直接为数组的返回形状', async () => {
    adminApiMock.attendance.list.mockResolvedValueOnce({
      data: departmentStats,
    });

    renderPage();

    expect(await screen.findByText('研发部')).toBeInTheDocument();
    expect(screen.getByText('测试部')).toBeInTheDocument();
  });

  it('可以切换到考勤记录、请假管理和加班管理标签页', async () => {
    renderPage();

    await screen.findByText('研发部');

    fireEvent.click(screen.getByRole('button', { name: '考勤记录' }));
    expect(screen.getByText('暂无考勤明细记录（当前仅展示部门考勤统计）')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '请假管理' }));
    expect(screen.getByText('请假申请')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '加班管理' }));
    expect(screen.getByText('暂无加班申请数据')).toBeInTheDocument();
  });

  it('接口失败时会记录降级日志并保持空态汇总', async () => {
    adminApiMock.attendance.list.mockRejectedValueOnce(new Error('API Error'));

    renderPage();

    await waitFor(() => {
      expect(consoleLogMock).toHaveBeenCalledWith('Attendance API unavailable, using mock data');
    });

    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(4);
    expect(screen.getByText('0.0%')).toBeInTheDocument();
    expect(screen.queryByText('研发部')).not.toBeInTheDocument();
  });
});
