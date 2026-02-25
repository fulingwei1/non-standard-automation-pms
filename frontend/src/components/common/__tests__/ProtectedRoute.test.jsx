import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import {
  ProtectedRoute,
  ProcurementProtectedRoute,
  FinanceProtectedRoute,
} from '../ProtectedRoute';

// Mock the role and permission utils
vi.mock('../../../lib/roleConfig', () => ({
  hasProcurementAccess: vi.fn((role, isSuperuser) => {
    if (isSuperuser) return true;
    return role === 'PURCHASE' || role === 'PURCHASE_MGR';
  }),
  hasFinanceAccess: vi.fn((role, isSuperuser) => {
    if (isSuperuser) return true;
    return role === 'FINANCE' || role === 'CFO';
  }),
  hasProductionAccess: vi.fn(() => false),
  hasProjectReviewAccess: vi.fn(() => false),
  hasStrategyAccess: vi.fn(() => false),
}));

vi.mock('../../../lib/permissionUtils', () => ({
  hasPermission: vi.fn((permission) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user.permissions?.includes(permission) || false;
  }),
  hasAnyPurchasePermission: vi.fn(() => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user.permissions?.some(p => p.startsWith('purchase:')) || false;
  }),
}));

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
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

    it('handles invalid user data in localStorage', () => {
      localStorage.setItem('user', 'invalid json');

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(localStorage.getItem('user')).toBeNull();
    });
  });

  describe('Superuser Access', () => {
    it('allows superuser to access without permission check', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: true,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('handles isSuperuser alternative field name', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        isSuperuser: true,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Admin Access', () => {
    it('allows admin role to bypass permission checks', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'admin',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('allows super_admin role to bypass permission checks', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'super_admin',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('handles Chinese admin role names', () => {
      localStorage.setItem('user', JSON.stringify({
        role: '管理员',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Permission Check', () => {
    it('shows access denied when permission check fails', () => {
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

    it('uses default permission check when not provided', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Access Denied UI', () => {
    it('displays lock icon', () => {
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
    });

    it('displays back button', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('返回上一页')).toBeInTheDocument();
    });

    it('uses custom permission name in error message', () => {
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

    it('uses default permission name when not provided', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.getByText('您没有权限访问此功能')).toBeInTheDocument();
    });
  });

  describe('ProcurementProtectedRoute', () => {
    it('allows procurement role to access', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'PURCHASE',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProcurementProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProcurementProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('denies access to non-procurement roles', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProcurementProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProcurementProtectedRoute>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
      expect(screen.getByText('无权限访问')).toBeInTheDocument();
    });

    it('uses fine-grained permission check when requiredPermission provided', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
        permissions: ['purchase:order:read'],
      }));

      renderWithRouter(
        <ProcurementProtectedRoute requiredPermission="purchase:order:read">
          <div data-testid="protected-content">Protected Content</div>
        </ProcurementProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('checks any purchase permission when no specific permission required', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
        permissions: ['purchase:order:read'],
      }));

      renderWithRouter(
        <ProcurementProtectedRoute useFineGrained={true}>
          <div data-testid="protected-content">Protected Content</div>
        </ProcurementProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('FinanceProtectedRoute', () => {
    it('allows finance role to access', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'FINANCE',
        is_superuser: false,
      }));

      renderWithRouter(
        <FinanceProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </FinanceProtectedRoute>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('denies access to non-finance roles', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: false,
      }));

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

    it('handles empty user object', () => {
      localStorage.setItem('user', JSON.stringify({}));

      renderWithRouter(
        <ProtectedRoute checkPermission={() => false}>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      );

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('renders multiple children when authorized', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'admin',
        is_superuser: false,
      }));

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="child-1">Child 1</div>
          <div data-testid="child-2">Child 2</div>
        </ProtectedRoute>
      );

      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
    });
  });
});
