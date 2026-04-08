import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const {
  mockProjectList,
  mockDocumentList,
  mockDocumentCreate,
  toastSuccessMock,
  toastErrorMock,
  windowOpenMock,
  consoleErrorMock,
} = vi.hoisted(() => ({
  mockProjectList: vi.fn(),
  mockDocumentList: vi.fn(),
  mockDocumentCreate: vi.fn(),
  toastSuccessMock: vi.fn(),
  toastErrorMock: vi.fn(),
  windowOpenMock: vi.fn(),
  consoleErrorMock: vi.fn(),
}));

vi.mock('../../services/api', () => ({
  projectApi: {
    list: mockProjectList,
  },
  documentApi: {
    list: mockDocumentList,
    create: mockDocumentCreate,
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

vi.mock('../../components/layout', () => ({
  PageHeader: ({ title, actions }) => (
    <div>
      <h1>{title}</h1>
      <div>{actions}</div>
    </div>
  ),
}));

vi.mock('../../components/ui/card', () => ({
  Card: ({ children }) => <div>{children}</div>,
  CardContent: ({ children }) => <div>{children}</div>,
}));

vi.mock('../../components/ui/button', () => ({
  Button: ({ children, onClick, disabled, type = 'button' }) => (
    <button type={type} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

vi.mock('../../components/ui/input', () => ({
  Input: ({ value, onChange, placeholder, className }) => (
    <input
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      className={className}
    />
  ),
}));

vi.mock('../../components/ui/badge', () => ({
  Badge: ({ children }) => <span>{children}</span>,
}));

vi.mock('../../components/ui/select', async () => {
  const React = await import('react');
  const SelectContext = React.createContext(() => {});

  return {
    Select: ({ value, onValueChange, children }) => (
      <SelectContext.Provider value={onValueChange}>
        <div data-testid="mock-select" data-value={value}>
          {children}
        </div>
      </SelectContext.Provider>
    ),
    SelectTrigger: ({ children }) => <div>{children}</div>,
    SelectValue: ({ placeholder }) => <span>{placeholder}</span>,
    SelectContent: ({ children }) => <div>{children}</div>,
    SelectItem: ({ value, children }) => {
      const onValueChange = React.useContext(SelectContext);
      return (
        <button type="button" onClick={() => onValueChange?.(value)}>
          {children}
        </button>
      );
    },
  };
});

vi.mock('../../components/ui/dialog', () => ({
  Dialog: ({ open, children }) => (open ? <div>{children}</div> : null),
  DialogContent: ({ children }) => <div>{children}</div>,
  DialogHeader: ({ children }) => <div>{children}</div>,
  DialogTitle: ({ children }) => <h2>{children}</h2>,
  DialogBody: ({ children }) => <div>{children}</div>,
  DialogFooter: ({ children }) => <div>{children}</div>,
}));

vi.mock('../../components/ui/toast', () => ({
  toast: {
    success: toastSuccessMock,
    error: toastErrorMock,
  },
}));

vi.mock('../../components/common', () => ({
  LoadingCard: ({ rows }) => <div>加载中骨架-{rows}</div>,
  ErrorMessage: ({ error, onRetry }) => (
    <div>
      <p>{error}</p>
      <button type="button" onClick={onRetry}>
        重试
      </button>
    </div>
  ),
  EmptyState: ({ title, description }) => (
    <div>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  ),
}));

vi.mock('../../lib/utils', () => ({
  cn: (...classes) => classes.filter(Boolean).join(' '),
  formatDate: (value) => `日期:${value}`,
}));

vi.mock('../../lib/animations', () => ({
  fadeIn: {},
  staggerContainer: {},
}));

import Documents from '../Documents';

const projects = [
  { id: 'project-1', project_name: '项目A' },
  { id: 'project-2', project_name: '项目B' },
  { id: 'project-3', project_name: '项目C' },
];

const docsByProject = {
  'project-1': [
    {
      id: 'doc-1',
      file_name: '需求文档.pdf',
      file_type: 'pdf',
      file_size: 1024,
      created_at: '2026-04-01',
      project_id: 'project-1',
      uploaded_by: '张三',
      description: '项目A需求说明',
      download_url: 'https://files.example.com/doc-1.pdf',
    },
  ],
  'project-2': [
    {
      id: 'doc-2',
      file_name: '现场照片.png',
      file_type: 'png',
      file_size: 2048,
      created_at: '2026-04-02',
      project_id: 'project-2',
      uploaded_by: '李四',
      description: '项目B现场照片',
      file_url: 'https://files.example.com/doc-2.png',
    },
  ],
  'project-3': [
    {
      id: 'doc-3',
      file_name: '测试记录.xlsx',
      file_type: 'xlsx',
      file_size: 4096,
      created_at: '2026-04-03',
      project_id: 'project-3',
      uploaded_by: '王五',
      description: '项目C测试记录',
    },
  ],
};

describe('Documents', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(console, 'error').mockImplementation(consoleErrorMock);
    vi.spyOn(window, 'open').mockImplementation(windowOpenMock);

    mockProjectList.mockResolvedValue({
      data: {
        items: projects,
      },
    });

    mockDocumentList.mockImplementation((projectId) =>
      Promise.resolve({
        data: docsByProject[projectId] || [],
      }),
    );

    mockDocumentCreate.mockResolvedValue({ data: { success: true } });
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <Documents />
      </MemoryRouter>,
    );
  }

  it('默认加载项目并聚合全部项目文档', async () => {
    renderPage();

    await waitFor(() => {
      expect(mockProjectList).toHaveBeenCalledWith({ page_size: 1000 });
    });

    await waitFor(() => {
      expect(mockDocumentList).toHaveBeenCalledWith('project-1');
      expect(mockDocumentList).toHaveBeenCalledWith('project-2');
      expect(mockDocumentList).toHaveBeenCalledWith('project-3');
    });

    expect(screen.getByText('文件管理')).toBeInTheDocument();
    expect(await screen.findByText('需求文档.pdf')).toBeInTheDocument();
    expect(screen.getByText('现场照片.png')).toBeInTheDocument();
    expect(screen.getByText('测试记录.xlsx')).toBeInTheDocument();
    expect(screen.getAllByText('项目A').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('项目B').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('项目C').length).toBeGreaterThanOrEqual(2);
  });

  it('支持本地搜索过滤当前文档列表', async () => {
    renderPage();

    await screen.findByText('需求文档.pdf');

    fireEvent.change(screen.getByPlaceholderText('搜索文档名称、描述...'), {
      target: { value: '现场' },
    });

    expect(screen.getByText('现场照片.png')).toBeInTheDocument();
    expect(screen.queryByText('需求文档.pdf')).not.toBeInTheDocument();
    expect(screen.queryByText('测试记录.xlsx')).not.toBeInTheDocument();
    expect(screen.getByText('项目B现场照片')).toBeInTheDocument();
  });

  it('切换项目后按选中项目单独加载文档，失败后可重试恢复', async () => {
    renderPage();

    await screen.findByText('需求文档.pdf');

    mockDocumentList.mockRejectedValueOnce(new Error('加载项目文档失败'));
    fireEvent.click(screen.getByRole('button', { name: '项目C' }));

    expect(await screen.findByText('加载项目文档失败')).toBeInTheDocument();

    mockDocumentList.mockResolvedValueOnce({
      data: [docsByProject['project-3'][0]],
    });
    fireEvent.click(screen.getByRole('button', { name: '重试' }));

    await waitFor(() => {
      expect(mockDocumentList).toHaveBeenLastCalledWith('project-3');
    });

    expect(await screen.findByText('测试记录.xlsx')).toBeInTheDocument();
    expect(screen.queryByText('需求文档.pdf')).not.toBeInTheDocument();
  });

  it('支持上传文件并提交真实 FormData 字段', async () => {
    renderPage();

    await screen.findByText('需求文档.pdf');

    fireEvent.click(screen.getByRole('button', { name: /上传文件/i }));

    expect(screen.getByRole('heading', { name: '上传文件' })).toBeInTheDocument();

    const uploadSelect = screen.getAllByTestId('mock-select')[1];
    fireEvent.click(within(uploadSelect).getByRole('button', { name: '项目B' }));

    const fileInput = document.getElementById('file-upload');
    const file = new File(['hello'], '上传资料.pdf', { type: 'application/pdf' });
    fireEvent.change(fileInput, {
      target: { files: [file] },
    });

    const descriptionInput = screen.getByPlaceholderText('输入文件描述...');
    fireEvent.change(descriptionInput, {
      target: { value: '补充说明' },
    });

    const uploadDialog = screen.getByRole('heading', { name: '上传文件' }).parentElement?.parentElement;
    fireEvent.click(within(uploadDialog).getByRole('button', { name: '上传' }));

    await waitFor(() => {
      expect(mockDocumentCreate).toHaveBeenCalledTimes(1);
    });

    const formData = mockDocumentCreate.mock.calls[0][0];
    expect(formData).toBeInstanceOf(FormData);
    expect(formData.get('project_id')).toBe('project-2');
    expect(formData.get('description')).toBe('补充说明');
    expect(formData.get('file')).toBe(file);
    expect(toastSuccessMock).toHaveBeenCalledWith('文件上传成功');
  });

  it('下载按钮优先使用现成链接，没有链接时走兜底下载地址', async () => {
    renderPage();

    await screen.findByText('需求文档.pdf');

    const firstDownloadButton = screen.getAllByRole('button', { name: '下载' })[0];
    fireEvent.click(firstDownloadButton);

    expect(windowOpenMock).toHaveBeenCalledWith(
      'https://files.example.com/doc-1.pdf',
      '_blank',
    );

    fireEvent.click(screen.getByRole('button', { name: '项目C' }));

    await waitFor(() => {
      expect(mockDocumentList).toHaveBeenLastCalledWith('project-3');
    });

    fireEvent.click(screen.getByRole('button', { name: '下载' }));

    expect(windowOpenMock).toHaveBeenCalledWith(
      '/api/v1/documents/doc-3/download',
      '_blank',
    );
  });
});
