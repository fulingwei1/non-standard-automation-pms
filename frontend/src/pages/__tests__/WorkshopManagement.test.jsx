import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WorkshopManagement from '../WorkshopManagement';

const mockUseWorkshopManagement = vi.fn();

vi.mock('../WorkshopManagement/hooks/useWorkshopManagement', () => ({
  useWorkshopManagement: (...args) => mockUseWorkshopManagement(...args),
}));

vi.mock('../../components/layout', () => ({
  PageHeader: ({ title, description }) => (
    <div>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  ),
}));

vi.mock('../WorkshopManagement/WorkshopFilters', () => ({
  WorkshopFilters: ({ searchKeyword, setSearchKeyword }) => (
    <div data-testid="workshop-filters">
      <input
        aria-label="搜索车间"
        value={searchKeyword}
        onChange={(e) => setSearchKeyword(e.target.value)}
      />
    </div>
  ),
}));

vi.mock('../WorkshopManagement/WorkshopTable', () => ({
  WorkshopTable: ({ loading, filteredWorkshops, onViewDetail, onEditClick }) => (
    <div data-testid="workshop-table">
      {loading ? (
        <div>加载中...</div>
      ) : filteredWorkshops.length === 0 ? (
        <div>暂无车间</div>
      ) : (
        filteredWorkshops.map((workshop) => (
          <div key={workshop.id}>
            <span>{workshop.workshop_code}</span>
            <span>{workshop.workshop_name}</span>
            <button onClick={() => onViewDetail(workshop.id)}>查看详情</button>
            <button onClick={() => onEditClick(workshop)}>编辑车间</button>
          </div>
        ))
      )}
    </div>
  ),
}));

vi.mock('../WorkshopManagement/WorkshopFormDialog', () => ({
  WorkshopFormDialog: ({ mode, open, onSubmit }) =>
    open ? <button onClick={onSubmit}>{mode}-dialog-submit</button> : null,
}));

vi.mock('../WorkshopManagement/WorkshopDetailDialog', () => ({
  WorkshopDetailDialog: ({ open, selectedWorkshop, onEditClick }) =>
    open ? (
      <div data-testid="workshop-detail-dialog">
        <span>{selectedWorkshop?.workshop_name}</span>
        <button onClick={() => onEditClick(selectedWorkshop)}>详情里编辑</button>
      </div>
    ) : null,
}));

function buildHookState(overrides = {}) {
  return {
    loading: false,
    filteredWorkshops: [
      {
        id: 1,
        workshop_code: 'WS-001',
        workshop_name: '装配车间A',
        workshop_type: 'ASSEMBLY',
        manager_name: '张主管',
        is_active: true,
      },
    ],
    managers: [{ id: 7, name: '张主管' }],
    selectedWorkshop: {
      id: 1,
      workshop_code: 'WS-001',
      workshop_name: '装配车间A',
    },
    searchKeyword: '',
    setSearchKeyword: vi.fn(),
    filterType: '',
    setFilterType: vi.fn(),
    filterActive: '',
    setFilterActive: vi.fn(),
    showCreateDialog: false,
    setShowCreateDialog: vi.fn(),
    showEditDialog: false,
    setShowEditDialog: vi.fn(),
    showDetailDialog: false,
    setShowDetailDialog: vi.fn(),
    workshopForm: { workshop_code: '', workshop_name: '' },
    setWorkshopForm: vi.fn(),
    handleCreate: vi.fn(),
    handleEdit: vi.fn(),
    handleViewDetail: vi.fn(),
    handleEditClick: vi.fn(),
    ...overrides,
  };
}

describe('WorkshopManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseWorkshopManagement.mockReturnValue(buildHookState());
  });

  it('renders page title and workshop list', () => {
    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>
    );

    expect(screen.getByText('车间管理')).toBeInTheDocument();
    expect(screen.getByText('车间列表、创建、编辑、工位管理')).toBeInTheDocument();
    expect(screen.getByTestId('workshop-filters')).toBeInTheDocument();
    expect(screen.getByTestId('workshop-table')).toBeInTheDocument();
    expect(screen.getByText('WS-001')).toBeInTheDocument();
    expect(screen.getByText('装配车间A')).toBeInTheDocument();
  });

  it('opens create dialog when clicking new workshop button', () => {
    const state = buildHookState();
    mockUseWorkshopManagement.mockReturnValue(state);

    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /新建车间/i }));
    expect(state.setShowCreateDialog).toHaveBeenCalledWith(true);
  });

  it('passes filter changes back to the hook', () => {
    const state = buildHookState();
    mockUseWorkshopManagement.mockReturnValue(state);

    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText('搜索车间'), { target: { value: '装配' } });
    expect(state.setSearchKeyword).toHaveBeenCalledWith('装配');
  });

  it('forwards table actions to hook handlers', () => {
    const state = buildHookState();
    mockUseWorkshopManagement.mockReturnValue(state);

    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: '查看详情' }));
    expect(state.handleViewDetail).toHaveBeenCalledWith(1);

    fireEvent.click(screen.getByRole('button', { name: '编辑车间' }));
    expect(state.handleEditClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: 1, workshop_name: '装配车间A' })
    );
  });

  it('renders loading state from table props', () => {
    mockUseWorkshopManagement.mockReturnValue(buildHookState({ loading: true }));

    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>
    );

    expect(screen.getByText('加载中...')).toBeInTheDocument();
  });

  it('renders empty state when there are no workshops', () => {
    mockUseWorkshopManagement.mockReturnValue(buildHookState({ filteredWorkshops: [] }));

    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>
    );

    expect(screen.getByText('暂无车间')).toBeInTheDocument();
  });

  it('renders create, edit, and detail dialogs based on hook state', () => {
    const state = buildHookState({
      showCreateDialog: true,
      showEditDialog: true,
      showDetailDialog: true,
    });
    mockUseWorkshopManagement.mockReturnValue(state);

    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: 'create-dialog-submit' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'edit-dialog-submit' })).toBeInTheDocument();
    expect(screen.getByTestId('workshop-detail-dialog')).toBeInTheDocument();
  });

  it('forwards create and edit submits to hook handlers', () => {
    const state = buildHookState({
      showCreateDialog: true,
      showEditDialog: true,
    });
    mockUseWorkshopManagement.mockReturnValue(state);

    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: 'create-dialog-submit' }));
    fireEvent.click(screen.getByRole('button', { name: 'edit-dialog-submit' }));

    expect(state.handleCreate).toHaveBeenCalledTimes(1);
    expect(state.handleEdit).toHaveBeenCalledTimes(1);
  });
});
