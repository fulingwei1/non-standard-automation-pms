import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import {
  ProtectedRoute,
  ProcurementProtectedRoute,
  FinanceProtectedRoute,
} from '../ProtectedRoute';

// Mock usePermission and useModuleAccess hooks
const mockUsePermission = {
  hasPermission: vi.fn(() => false),
  hasAnyPermission: vi.fn(() => false),
  hasAllPermissions: vi.fn(() => false),
  canAccessMenu: vi.fn(() => false),
  getDataScope: vi.fn(() => null),
  canAccessData: vi.fn(() => false),
  isSuperuser: false,
  isLoading: false,
  error: null,
  permissions: [],
  menus: [],
  dataScopes: {},
};

vi.mock('../../../hooks/usePermission', () => ({
  usePermission: () => mockUsePermission,
}));

vi.mock('../../../context/PermissionContext', () => ({
  usePermissionContext: () => ({
    permissions: mockUsePermission.permissions,
    menus: mockUsePermission.menus,
    dataScopes: mockUsePermission.dataScopes,
    isSuperuser: mockUsePermission.isSuperuser,
    isLoading: mockUsePermission.isLoading,
    error: mockUsePermission.error,
    user: null,
    refreshPermissions: vi.fn(),
    clearPermissions: vi.fn(),
    updatePermission: vi.fn(),
  }),
}));

vi.mock('../../../lib/permission', () => ({
  useModuleAccess: () => ({
    hasModuleAccess: vi.fn((moduleKey) => {
      if (mockUsePermission.isSuperuser) return true;
      if (mockUsePermission.isLoading) return false;
      return mockUsePermission.hasAnyPermission([moduleKey]);
    }),
    checkPermission: vi.fn((code) => {
      if (mockUsePermission.isSuperuser) return true;
      return mockUsePermission.hasPermission(code);
    }),
    isSuperuser: mockUsePermission.isSuperuser,
    isLoading: mockUsePermission.isLoading,
    error: mockUsePermission.error,
    permissions: mockUsePermission.permissions,
  }),
}));

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

// Helper: configure the global localStorage mock to use a real backing store
function setupLocalStorageMock() {
  const store = {};
  localStorage.getItem.mockImplementation((key) => store[key] ?? null);
  localStorage.setItem.mockImplementation((key, value) => { store[key] = String(value); });
  localStorage.removeItem.mockImplementation((key) => { delete store[key]; });
  localStorage.clear.mockImplementation(() => { Object.keys(store).forEach((k) => delete store[k]); });
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupLocalStorageMock();
    // Reset mock state
    mockUsePermission.isSuperuser = false;
    mockUsePermission.isLoading = false;
    mockUsePermission.permissions = [];
    mockUsePermission.hasPermission.mockReturnValue(false);
    mockUsePermission.hasAnyPermission.mockReturnValue(false);
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Basic Authentication', () => {
    it('redirects to login when user is not authenticated', () => {
      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('renders children when user is authenticated and authorized', () => {
      localStorage.setItem('token', 'valid-token');
      localStorage.setItem('user', JSON.stringify({
        role: 'ADMIN',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => true}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Superuser Access', () => {
    it('allows superuser to access without permission check', () => {
      localStorage.setItem('token', 'valid-token');
      mockUsePermission.isSuperuser = true;

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Loading State (fail-closed)', () => {
    it('shows loading placeholder while permissions load', () => {
      localStorage.setItem('token', 'valid-token');
      mockUsePermission.isLoading = true;

      renderWithRouter(
        <ProtectedRoute checkPermission={() => true}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByText('权限验证中...')).toBeInTheDocument();
    });
  });

  describe('Permission Check', () => {
    it('shows access denied when permission check fails', () => {
      localStorage.setItem('token', 'valid-token');
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false} permissionName="测试功能">
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('无权限访问')).toBeInTheDocument();
      expect(screen.getByText('您没有权限访问测试功能')).toBeInTheDocument();
    });

    it('calls checkPermission with user role', () => {
      localStorage.setItem('token', 'valid-token');
      const mockCheckPermission = vi.fn(() => true);
      localStorage.setItem('user', JSON.stringify({
        role: 'TEST_ROLE',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={mockCheckPermission}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(mockCheckPermission).toHaveBeenCalledWith('TEST_ROLE');
    });
  });

  describe('Access Denied UI', () => {
    it('displays lock icon and back button', () => {
      localStorage.setItem('token', 'valid-token');
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('🔒')).toBeInTheDocument();
      expect(screen.getByText('返回上一页')).toBeInTheDocument();
    });

    it('uses custom permission name in error message', () => {
      localStorage.setItem('token', 'valid-token');
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false} permissionName="自定义模块">
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('您没有权限访问自定义模块')).toBeInTheDocument();
    });
  });

  describe('ProcurementProtectedRoute', () => {
    it('allows access when user has procurement permissions', () => {
      mockUsePermission.hasAnyPermission.mockReturnValue(true);

      renderWithRouter(
        <ProcurementProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProcurementProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('denies access when user lacks procurement permissions', () => {
      mockUsePermission.hasAnyPermission.mockReturnValue(false);

      renderWithRouter(
        <ProcurementProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProcurementProtectedRoute>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByText('无权限访问')).toBeInTheDocument();
    });

    it('checks specific permission when requiredPermission provided', () => {
      mockUsePermission.hasPermission.mockImplementation(
        (code) => code === 'purchase:order:read'
      );

      renderWithRouter(
        <ProcurementProtectedRoute requiredPermission="purchase:order:read">
          <div data-testid="protected-content">Protected Content</div>
        </ProcurementProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('superuser always has access', () => {
      mockUsePermission.isSuperuser = true;
      mockUsePermission.hasAnyPermission.mockReturnValue(false);

      renderWithRouter(
        <ProcurementProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProcurementProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('FinanceProtectedRoute', () => {
    it('allows access when user has finance permissions', () => {
      mockUsePermission.hasAnyPermission.mockReturnValue(true);

      renderWithRouter(
        <FinanceProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </FinanceProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('denies access when user lacks finance permissions', () => {
      mockUsePermission.hasAnyPermission.mockReturnValue(false);

      renderWithRouter(
        <FinanceProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </FinanceProtectedRoute>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing role field', () => {
      localStorage.setItem('token', 'valid-token');
      localStorage.setItem('user', JSON.stringify({
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });
  });
});
