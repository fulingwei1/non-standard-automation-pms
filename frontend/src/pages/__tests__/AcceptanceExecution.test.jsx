/**
 * AcceptanceExecution 页面测试
 * 只校验页面编排逻辑，底层数据细节交给 hook / 子组件各自测试。
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import AcceptanceExecution from '../AcceptanceExecution';
import { useAcceptanceExecutionPage } from '../AcceptanceExecution/hooks/useAcceptanceExecutionPage';

const mockNavigate = vi.fn();
const mockUseAcceptanceExecutionPage = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../AcceptanceExecution/hooks/useAcceptanceExecutionPage', () => ({
  useAcceptanceExecutionPage: (...args) => mockUseAcceptanceExecutionPage(...args),
}));

vi.mock('../../components/layout', () => ({
  PageHeader: ({ title, description }) => (
    <div>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  ),
}));

vi.mock('../AcceptanceExecution/ExecutionSummaryCards', () => ({
  ExecutionSummaryCards: ({ totalItems, passedCount, failedCount, totalChecked }) => (
    <div data-testid="summary-cards">
      <span>总项数:{totalItems}</span>
      <span>通过:{passedCount}</span>
      <span>不通过:{failedCount}</span>
      <span>已检查:{totalChecked}</span>
    </div>
  ),
}));

vi.mock('../AcceptanceExecution/CheckItemsPanel', () => ({
  CheckItemsPanel: ({ itemsByCategory, onItemClick, onAddIssue }) => (
    <div data-testid="check-items-panel">
      <button onClick={onAddIssue}>上报问题</button>
      {Object.entries(itemsByCategory || {}).map(([category, items]) => (
        <div key={category}>
          <div>{category}</div>
          {(items || []).map((item) => (
            <button key={item.id} onClick={() => onItemClick(item)}>
              {item.item_name}
            </button>
          ))}
        </div>
      ))}
    </div>
  ),
}));

vi.mock('../AcceptanceExecution/IssuesPanel', () => ({
  IssuesPanel: ({ issues }) => (
    <div data-testid="issues-panel">
      {(issues || []).map((issue) => (
        <div key={issue.id}>{issue.description}</div>
      ))}
    </div>
  ),
}));

vi.mock('../AcceptanceExecution/UpdateItemDialog', () => ({
  UpdateItemDialog: ({ open }) => open ? <div data-testid="update-item-dialog">update-dialog</div> : null,
}));

vi.mock('../AcceptanceExecution/CreateIssueDialog', () => ({
  CreateIssueDialog: ({ open }) => open ? <div data-testid="create-issue-dialog">create-issue-dialog</div> : null,
}));

vi.mock('../AcceptanceExecution/CompleteDialog', () => ({
  CompleteDialog: ({ open }) => open ? <div data-testid="complete-dialog">complete-dialog</div> : null,
}));

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/acceptance/execution/1']}>
      <Routes>
        <Route path="/acceptance/execution/:id" element={<AcceptanceExecution />} />
      </Routes>
    </MemoryRouter>
  );
}

function buildHookState(overrides = {}) {
  return {
    loading: false,
    order: {
      id: 1,
      order_no: 'ACC-2024-001',
      status: 'IN_PROGRESS',
    },
    items: [
      { id: 1, item_name: '用户登录功能', result_status: 'PENDING' },
      { id: 2, item_name: '系统响应时间', result_status: 'PASSED' },
    ],
    issues: [
      { id: 1, description: 'Safari浏览器下拉菜单无法正常显示' },
    ],
    itemsByCategory: {
      功能测试: [{ id: 1, item_name: '用户登录功能', result_status: 'PENDING' }],
      性能测试: [{ id: 2, item_name: '系统响应时间', result_status: 'PASSED' }],
    },
    passedCount: 1,
    failedCount: 0,
    totalChecked: 1,
    showItemDialog: false,
    setShowItemDialog: vi.fn(),
    showIssueDialog: false,
    setShowIssueDialog: vi.fn(),
    showCompleteDialog: false,
    setShowCompleteDialog: vi.fn(),
    selectedItem: null,
    itemResult: { result_status: 'PASSED', actual_value: '', deviation: '', remark: '' },
    setItemResult: vi.fn(),
    newIssue: { item_id: null, category: '', severity: 'MINOR', description: '', photos: [] },
    setNewIssue: vi.fn(),
    completeData: { overall_result: 'PASS', conclusion: '', conditions: '' },
    setCompleteData: vi.fn(),
    refreshAll: vi.fn(),
    openItemDialog: vi.fn(),
    handleUpdateItem: vi.fn(),
    handleCreateIssue: vi.fn(),
    handleComplete: vi.fn(),
    ...overrides,
  };
}

describe('AcceptanceExecution', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAcceptanceExecutionPage.mockReturnValue(buildHookState());
  });

  it('renders loading state', () => {
    mockUseAcceptanceExecutionPage.mockReturnValue(buildHookState({ loading: true }));

    renderPage();

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('renders not-found state when order is missing', () => {
    mockUseAcceptanceExecutionPage.mockReturnValue(
      buildHookState({ loading: false, order: null })
    );

    renderPage();

    expect(screen.getByText('验收单不存在')).toBeInTheDocument();
  });

  it('renders page content from hook state', () => {
    renderPage();

    expect(useAcceptanceExecutionPage).toBeDefined();
    expect(screen.getByText('验收执行 - ACC-2024-001')).toBeInTheDocument();
    expect(screen.getByText('验收检查项执行、问题管理')).toBeInTheDocument();
    expect(screen.getByTestId('summary-cards')).toBeInTheDocument();
    expect(screen.getByText('用户登录功能')).toBeInTheDocument();
    expect(screen.getByText('系统响应时间')).toBeInTheDocument();
    expect(screen.getByText('Safari浏览器下拉菜单无法正常显示')).toBeInTheDocument();
  });

  it('calls navigate when clicking back button', () => {
    renderPage();

    fireEvent.click(screen.getByRole('button', { name: /返回列表/i }));

    expect(mockNavigate).toHaveBeenCalledWith('/acceptance-orders');
  });

  it('calls refreshAll when clicking refresh button', () => {
    const state = buildHookState();
    mockUseAcceptanceExecutionPage.mockReturnValue(state);

    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /刷新/i }));

    expect(state.refreshAll).toHaveBeenCalledTimes(1);
  });

  it('opens complete dialog when clicking complete button', () => {
    const state = buildHookState();
    mockUseAcceptanceExecutionPage.mockReturnValue(state);

    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /完成验收/i }));

    expect(state.setShowCompleteDialog).toHaveBeenCalledWith(true);
  });

  it('does not show complete button when order is not in progress', () => {
    mockUseAcceptanceExecutionPage.mockReturnValue(
      buildHookState({ order: { id: 1, order_no: 'ACC-2024-001', status: 'COMPLETED' } })
    );

    renderPage();

    expect(screen.queryByRole('button', { name: /完成验收/i })).not.toBeInTheDocument();
  });

  it('opens issue dialog from check-items panel', () => {
    const state = buildHookState();
    mockUseAcceptanceExecutionPage.mockReturnValue(state);

    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '上报问题' }));

    expect(state.setShowIssueDialog).toHaveBeenCalledWith(true);
  });

  it('opens item dialog when clicking an item', () => {
    const state = buildHookState();
    mockUseAcceptanceExecutionPage.mockReturnValue(state);

    renderPage();
    fireEvent.click(screen.getByRole('button', { name: '用户登录功能' }));

    expect(state.openItemDialog).toHaveBeenCalledWith(
      expect.objectContaining({ id: 1, item_name: '用户登录功能' })
    );
  });

  it('passes dialog open state through to child dialogs', () => {
    mockUseAcceptanceExecutionPage.mockReturnValue(
      buildHookState({
        showItemDialog: true,
        showIssueDialog: true,
        showCompleteDialog: true,
      })
    );

    renderPage();

    expect(screen.getByTestId('update-item-dialog')).toBeInTheDocument();
    expect(screen.getByTestId('create-issue-dialog')).toBeInTheDocument();
    expect(screen.getByTestId('complete-dialog')).toBeInTheDocument();
  });
});
