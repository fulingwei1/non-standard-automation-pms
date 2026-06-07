import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import SalesTeamCenter from '../SalesTeamCenter';

const permissionMock = vi.hoisted(() => ({
  hasPermission: vi.fn(() => false),
  isSuperuser: false,
  isLoading: false,
}));

vi.mock('../../hooks/usePermission', () => ({
  usePermission: () => permissionMock,
}));

vi.mock('../../components/layout/TabbedCenterPage', () => ({
  default: ({ title, tabs }) => (
    <div data-testid="tabbed-center">
      <h1>{title}</h1>
      {(tabs || []).map((tab) => (
        <span key={tab.value}>{tab.label}</span>
      ))}
    </div>
  ),
}));

vi.mock('../SalesTeam', () => ({
  default: () => <div>团队管理内容</div>,
}));

vi.mock('../SalesAI/PerformanceIncentive', () => ({
  default: () => <div>奖金激励内容</div>,
}));

function renderSalesTeamCenter() {
  return render(
    <MemoryRouter initialEntries={['/sales/team-center']}>
      <Routes>
        <Route path="/sales/team-center" element={<SalesTeamCenter />} />
        <Route path="/sales/workstation" element={<div>销售工作站落地页</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('SalesTeamCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    permissionMock.hasPermission.mockReturnValue(false);
    permissionMock.isSuperuser = false;
    permissionMock.isLoading = false;
  });

  it('redirects sales users without team permission back to the sales workstation', () => {
    renderSalesTeamCenter();

    expect(screen.getByText('销售工作站落地页')).toBeInTheDocument();
    expect(screen.queryByTestId('tabbed-center')).not.toBeInTheDocument();
  });

  it('keeps the team center available for users with sales team permission', () => {
    permissionMock.hasPermission.mockImplementation((code) => code === 'sales_team:read');

    renderSalesTeamCenter();

    expect(screen.getByTestId('tabbed-center')).toHaveTextContent('销售团队');
    expect(screen.getByText('团队管理')).toBeInTheDocument();
    expect(screen.getByText('奖金激励')).toBeInTheDocument();
  });
});
