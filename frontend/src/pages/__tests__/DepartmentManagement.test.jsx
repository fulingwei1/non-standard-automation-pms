import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { orgApiMock, alertMock } = vi.hoisted(() => ({
  orgApiMock: {
    departments: vi.fn(),
    departmentTree: vi.fn(),
    createDepartment: vi.fn(),
    updateDepartment: vi.fn(),
    getDepartment: vi.fn(),
  },
  alertMock: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  orgApi: orgApiMock,
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

vi.mock('../../components/ui/card', () => ({
  Card: ({ children }) => <div>{children}</div>,
  CardContent: ({ children }) => <div>{children}</div>,
  CardHeader: ({ children }) => <div>{children}</div>,
  CardTitle: ({ children }) => <h2>{children}</h2>,
}));

vi.mock('../../components/ui/button', () => ({
  Button: ({ children, onClick, type = 'button', ...props }) => (
    <button type={type} onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('../../components/ui/input', () => ({
  Input: ({ className, ...props }) => <input className={className} {...props} />,
}));

vi.mock('../../components/ui/badge', () => ({
  Badge: ({ children }) => <span>{children}</span>,
}));

vi.mock('../../components/ui/label', () => ({
  Label: ({ children, htmlFor, className }) => (
    <label htmlFor={htmlFor} className={className}>
      {children}
    </label>
  ),
}));

vi.mock('../../lib/utils', () => ({
  cn: (...values) => values.filter(Boolean).join(' '),
}));

vi.mock('../../lib/animations', () => ({
  fadeIn: {},
  staggerContainer: {},
}));

vi.mock('../../components/ui/dialog', () => ({
  Dialog: ({ open, children }) => (open ? <div>{children}</div> : null),
  DialogContent: ({ children, ...props }) => <div {...props}>{children}</div>,
  DialogHeader: ({ children }) => <div>{children}</div>,
  DialogTitle: ({ children }) => <h2>{children}</h2>,
  DialogFooter: ({ children }) => <div>{children}</div>,
}));

vi.mock('../../components/ui/select', () => ({
  Select: ({ children }) => <div>{children}</div>,
  SelectContent: ({ children }) => <div>{children}</div>,
  SelectItem: ({ children, value }) => <div data-value={value}>{children}</div>,
  SelectTrigger: ({ children, className }) => <div className={className}>{children}</div>,
  SelectValue: ({ placeholder }) => <span>{placeholder}</span>,
}));

import DepartmentManagement from '../DepartmentManagement';

const treeDepartments = [
  {
    id: 1,
    dept_code: 'RD',
    dept_name: '研发部',
    manager_name: '张三',
    children: [],
  },
  {
    id: 2,
    dept_code: 'SALES',
    dept_name: '销售部',
    manager_name: '李四',
    children: [],
  },
];

const listDepartments = [
  {
    id: 1,
    dept_code: 'RD',
    dept_name: '研发部',
    level: 1,
    is_active: true,
    manager: { name: '张三' },
  },
  {
    id: 2,
    dept_code: 'SALES',
    dept_name: '销售部',
    level: 1,
    is_active: false,
    manager: { name: '李四' },
  },
];

const departmentDetail = {
  id: 1,
  dept_code: 'RD',
  dept_name: '研发部',
  parent_id: null,
  sort_order: 10,
  is_active: true,
  level: 1,
  manager: { name: '张三' },
};

describe('DepartmentManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('alert', alertMock);

    orgApiMock.departmentTree.mockResolvedValue({
      data: { items: treeDepartments },
    });
    orgApiMock.departments.mockResolvedValue({
      data: { items: listDepartments },
    });
    orgApiMock.getDepartment.mockResolvedValue({
      data: departmentDetail,
    });
    orgApiMock.createDepartment.mockResolvedValue({ data: { success: true } });
    orgApiMock.updateDepartment.mockResolvedValue({ data: { success: true } });
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <DepartmentManagement />
      </MemoryRouter>,
    );
  }

  it('默认加载树形视图并请求部门树', async () => {
    renderPage();

    await waitFor(() => {
      expect(orgApiMock.departmentTree).toHaveBeenCalledWith({ is_active: true });
    });

    expect(screen.getByText('部门管理')).toBeInTheDocument();
    expect(screen.getByText('管理系统部门信息，包括创建、编辑、查看部门树等操作。')).toBeInTheDocument();
    expect(screen.getByText('部门树')).toBeInTheDocument();
    expect(screen.getByText('研发部')).toBeInTheDocument();
    expect(screen.getByText('销售部')).toBeInTheDocument();
    expect(screen.getByText('张三')).toBeInTheDocument();
  });

  it('切到列表视图后会请求部门列表并渲染表格', async () => {
    renderPage();

    await screen.findByText('研发部');
    fireEvent.click(screen.getByRole('button', { name: /列表视图/i }));

    await waitFor(() => {
      expect(orgApiMock.departments).toHaveBeenCalledWith({ skip: 0, limit: 1000 });
    });

    expect(screen.getByText('部门列表')).toBeInTheDocument();
    expect(screen.getAllByText('RD').length).toBeGreaterThan(0);
    expect(screen.getAllByText('SALES').length).toBeGreaterThan(0);
    expect(screen.getByText('启用')).toBeInTheDocument();
    expect(screen.getByText('禁用')).toBeInTheDocument();
  });

  it('可以打开新增部门弹窗并提交创建', async () => {
    renderPage();

    await screen.findByText('研发部');
    fireEvent.click(screen.getByRole('button', { name: /新增部门/i }));

    expect(await screen.findByRole('heading', { name: '新增部门' })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/部门编码/), { target: { value: 'QA' } });
    fireEvent.change(screen.getByLabelText(/部门名称/), { target: { value: '质量部' } });
    fireEvent.change(screen.getByLabelText(/排序/), { target: { value: '3' } });
    fireEvent.click(screen.getAllByRole('button', { name: '保存' })[0]);

    await waitFor(() => {
      expect(orgApiMock.createDepartment).toHaveBeenCalledWith({
        dept_code: 'QA',
        dept_name: '质量部',
        parent_id: null,
        manager_id: null,
        sort_order: '3',
        is_active: true,
      });
    });
  });

  it('点击查看会请求详情并打开详情弹窗', async () => {
    renderPage();

    await screen.findByText('研发部');
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[3]);

    await waitFor(() => {
      expect(orgApiMock.getDepartment).toHaveBeenCalledWith(1);
    });

    expect(screen.getByText('部门详情')).toBeInTheDocument();
    expect(screen.getAllByText('研发部').length).toBeGreaterThan(0);
    expect(screen.getAllByText('RD').length).toBeGreaterThan(0);
  });

  it('点击编辑会加载详情并提交更新', async () => {
    renderPage();

    await screen.findByText('研发部');
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[4]);

    expect(await screen.findByText('编辑部门')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/部门名称/), { target: { value: '研发中心' } });
    fireEvent.click(screen.getAllByRole('button', { name: '保存' })[0]);

    await waitFor(() => {
      expect(orgApiMock.updateDepartment).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          dept_name: '研发中心',
          parent_id: null,
        }),
      );
    });
  });

  it('加载部门树失败时会弹出错误提示', async () => {
    orgApiMock.departmentTree.mockRejectedValueOnce(new Error('Load failed'));

    renderPage();

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith('加载部门树失败: Load failed');
    });
  });
});
