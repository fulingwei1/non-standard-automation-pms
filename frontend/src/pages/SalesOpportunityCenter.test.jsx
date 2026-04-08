import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SalesOpportunityCenter from './SalesOpportunityCenter';

vi.mock('./LeadManagement', () => ({
  default: () => <div data-testid="lead-management">线索管理组件</div>,
}));

vi.mock('./OpportunityManagement', () => ({
  default: ({ embedded }) => (
    <div data-testid="opportunity-management">商机管理组件-{embedded ? 'embedded' : 'standalone'}</div>
  ),
}));

vi.mock('../hooks/usePermission', () => ({
  usePermission: () => ({
    hasPermission: () => true,
    hasAnyPermission: () => true,
  }),
}));

vi.mock('../components/ui/tabs', () => ({
  Tabs: ({ children }) => <div data-testid="tabs-root">{children}</div>,
  TabsList: ({ children }) => <div data-testid="tabs-list">{children}</div>,
  TabsTrigger: ({ children, value }) => <button data-value={value}>{children}</button>,
  TabsContent: ({ children }) => <div>{children}</div>,
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <SalesOpportunityCenter />
    </MemoryRouter>,
  );
}

describe('SalesOpportunityCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the real center page title, description, and visible tabs', () => {
    renderPage();

    expect(screen.getByText('商机中心')).toBeInTheDocument();
    expect(screen.getByText('统一管理销售线索与商机推进')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '线索管理' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '商机管理' })).toBeInTheDocument();
  });

  it('renders the first tab content by default through TabbedCenterPage', () => {
    renderPage();

    expect(screen.getByTestId('lead-management')).toBeInTheDocument();
    expect(screen.queryByTestId('opportunity-management')).not.toBeInTheDocument();
  });
});
