import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

const { useBOMManagementMock } = vi.hoisted(() => ({
  useBOMManagementMock: vi.fn(),
}));

vi.mock('../BOMManagement/hooks', () => ({
  useBOMManagement: useBOMManagementMock,
}));

vi.mock('../BOMManagement/BOMFilterBar', () => ({
  default: ({
    searchKeyword,
    setSearchKeyword,
    onProjectChange,
    setFilterMachine,
    setFilterStatus,
    projects,
    machines,
  }) => (
    <div data-testid="bom-filter-bar">
      <div>projects:{projects.length}</div>
      <div>machines:{machines.length}</div>
      <input
        aria-label="搜索BOM"
        value={searchKeyword}
        onChange={(e) => setSearchKeyword(e.target.value)}
      />
      <button onClick={() => onProjectChange('1')}>切项目</button>
      <button onClick={() => setFilterMachine('2')}>切机台</button>
      <button onClick={() => setFilterStatus('active')}>切状态</button>
    </div>
  ),
}));

vi.mock('../BOMManagement/BOMTable', () => ({
  default: ({ loading, filteredBoms, onViewDetail, onExport, onCreateNew }) => (
    <div data-testid="bom-table">
      <div>{loading ? 'loading' : `rows:${filteredBoms.length}`}</div>
      {filteredBoms.map((bom) => (
        <div key={bom.id}>{bom.bom_name}</div>
      ))}
      <button onClick={() => onViewDetail(filteredBoms[0]?.id)}>查看详情</button>
      <button onClick={() => onExport(filteredBoms[0]?.id)}>导出BOM</button>
      <button onClick={onCreateNew}>新建BOM</button>
    </div>
  ),
}));

vi.mock('../BOMManagement/BOMDetailDialog', () => ({
  default: ({
    open,
    selectedBom,
    versions,
    onOpenChange,
    onImport,
    onExport,
    onRelease,
    onViewVersion,
  }) =>
    open ? (
      <div data-testid="bom-detail-dialog">
        <div>detail:{selectedBom?.bom_name}</div>
        <button onClick={() => onOpenChange(false)}>关闭详情</button>
        <button onClick={onImport}>打开导入</button>
        <button onClick={() => onExport(selectedBom?.id)}>详情导出</button>
        <button onClick={onRelease}>打开发布</button>
        <button onClick={() => onViewVersion(versions[0])}>查看版本</button>
      </div>
    ) : null,
}));

vi.mock('../BOMManagement/CreateBOMDialog', () => ({
  default: ({ open }) => (open ? <div data-testid="create-bom-dialog">create-dialog</div> : null),
}));

vi.mock('../BOMManagement/ImportBOMDialog', () => ({
  default: ({ open }) => (open ? <div data-testid="import-bom-dialog">import-dialog</div> : null),
}));

vi.mock('../BOMManagement/ReleaseBOMDialog', () => ({
  default: ({ open }) => (open ? <div data-testid="release-bom-dialog">release-dialog</div> : null),
}));

import BOMManagement from '../BOMManagement';

function createHookState(overrides = {}) {
  return {
    loading: false,
    filteredBoms: [
      {
        id: 1,
        bom_no: 'BOM-001',
        bom_name: '产品A BOM',
        project_name: '产品A项目',
        machine_name: '机台A',
        version: 'V1.0',
        status: 'active',
        total_items: 25,
        total_amount: 12500,
      },
    ],
    projects: [{ id: 1, project_name: '产品A项目' }],
    machines: [{ id: 2, machine_name: '机台A' }],
    selectedBom: {
      id: 1,
      bom_no: 'BOM-001',
      bom_name: '产品A BOM',
      version: 'V1.0',
      status: 'APPROVED',
    },
    setSelectedBom: vi.fn(),
    bomItems: [{ id: 11, material_code: 'MAT-001' }],
    versions: [{ id: 9, version: 'V0.9', status: 'draft' }],
    searchKeyword: '',
    setSearchKeyword: vi.fn(),
    filterProject: '',
    filterMachine: '',
    setFilterMachine: vi.fn(),
    filterStatus: '',
    setFilterStatus: vi.fn(),
    handleFilterProjectChange: vi.fn(),
    showBomDetail: false,
    setShowBomDetail: vi.fn(),
    showCreateDialog: false,
    setShowCreateDialog: vi.fn(),
    showImportDialog: false,
    setShowImportDialog: vi.fn(),
    showReleaseDialog: false,
    setShowReleaseDialog: vi.fn(),
    newBom: { bom_name: '' },
    setNewBom: vi.fn(),
    importFile: null,
    setImportFile: vi.fn(),
    releaseNote: '',
    setReleaseNote: vi.fn(),
    fetchBOMDetail: vi.fn(),
    handleCreateBOM: vi.fn(),
    handleReleaseBOM: vi.fn(),
    handleImport: vi.fn(),
    handleExport: vi.fn(),
    handleCreateDialogProjectChange: vi.fn(),
    ...overrides,
  };
}

describe('BOMManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('按当前页面编排渲染页头、筛选区和表格', () => {
    useBOMManagementMock.mockReturnValue(createHookState());

    render(
      <MemoryRouter>
        <BOMManagement />
      </MemoryRouter>,
    );

    expect(screen.getByText('BOM管理')).toBeInTheDocument();
    expect(screen.getByText('物料清单管理，支持版本控制、导入导出、发布审批')).toBeInTheDocument();
    expect(screen.getByTestId('bom-filter-bar')).toHaveTextContent('projects:1');
    expect(screen.getByTestId('bom-table')).toHaveTextContent('rows:1');
    expect(screen.getByText('产品A BOM')).toBeInTheDocument();
  });

  it('筛选区操作会调用 hook 暴露的 setter 和 handler', () => {
    const state = createHookState({ searchKeyword: '旧关键字' });
    useBOMManagementMock.mockReturnValue(state);

    render(
      <MemoryRouter>
        <BOMManagement />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('搜索BOM'), { target: { value: '新BOM' } });
    fireEvent.click(screen.getByRole('button', { name: '切项目' }));
    fireEvent.click(screen.getByRole('button', { name: '切机台' }));
    fireEvent.click(screen.getByRole('button', { name: '切状态' }));

    expect(state.setSearchKeyword).toHaveBeenCalledWith('新BOM');
    expect(state.handleFilterProjectChange).toHaveBeenCalledWith('1');
    expect(state.setFilterMachine).toHaveBeenCalledWith('2');
    expect(state.setFilterStatus).toHaveBeenCalledWith('active');
  });

  it('表格操作会调用详情、导出和新建入口', () => {
    const state = createHookState();
    useBOMManagementMock.mockReturnValue(state);

    render(
      <MemoryRouter>
        <BOMManagement />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: '查看详情' }));
    fireEvent.click(screen.getByRole('button', { name: '导出BOM' }));
    fireEvent.click(screen.getByRole('button', { name: '新建BOM' }));

    expect(state.fetchBOMDetail).toHaveBeenCalledWith(1);
    expect(state.handleExport).toHaveBeenCalledWith(1);
    expect(state.setShowCreateDialog).toHaveBeenCalledWith(true);
  });

  it('详情弹窗里的版本、导入、发布动作会走页面编排回调', () => {
    const state = createHookState({
      showBomDetail: true,
      showCreateDialog: true,
      showImportDialog: true,
      showReleaseDialog: true,
    });
    useBOMManagementMock.mockReturnValue(state);

    render(
      <MemoryRouter>
        <BOMManagement />
      </MemoryRouter>,
    );

    expect(screen.getByTestId('bom-detail-dialog')).toHaveTextContent('detail:产品A BOM');
    expect(screen.getByTestId('create-bom-dialog')).toBeInTheDocument();
    expect(screen.getByTestId('import-bom-dialog')).toBeInTheDocument();
    expect(screen.getByTestId('release-bom-dialog')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: '关闭详情' }));
    fireEvent.click(screen.getByRole('button', { name: '打开导入' }));
    fireEvent.click(screen.getByRole('button', { name: '详情导出' }));
    fireEvent.click(screen.getByRole('button', { name: '打开发布' }));
    fireEvent.click(screen.getByRole('button', { name: '查看版本' }));

    expect(state.setShowBomDetail).toHaveBeenCalledWith(false);
    expect(state.setShowImportDialog).toHaveBeenCalledWith(true);
    expect(state.handleExport).toHaveBeenCalledWith(1);
    expect(state.setShowReleaseDialog).toHaveBeenCalledWith(true);
    expect(state.setSelectedBom).toHaveBeenCalledWith(state.versions[0]);
    expect(state.fetchBOMDetail).toHaveBeenCalledWith(9);
  });
});
