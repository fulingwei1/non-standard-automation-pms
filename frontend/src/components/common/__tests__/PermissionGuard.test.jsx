import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PermissionGuard, useHasPermission } from '../PermissionGuard';

// Mock the usePermission hook
vi.mock('../../../hooks/usePermission', () => ({
  usePermission: vi.fn(() => ({
    hasPermission: vi.fn((perm) => perm === 'test:read'),
    hasAnyPermission: vi.fn((perms) => perms.some(p => p === 'test:read')),
    hasAllPermissions: vi.fn((perms) => perms.every(p => p === 'test:read')),
  })),
  PermissionGuard: ({ permission, children, fallback, requireAll }) => {
    const mockUser = JSON.parse(localStorage.getItem('user') || '{}');
    const permissions = mockUser.permissions || [];
    
    const hasAccess = mockUser.is_superuser
      ? true
      : Array.isArray(permission)
        ? (requireAll 
            ? permission.every(p => permissions.includes(p))
            : permission.some(p => permissions.includes(p)))
        : permissions.includes(permission);

    if (!hasAccess) {
      return fallback || null;
    }
    
    return children;
  },
}));

describe('PermissionGuard', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('Basic Rendering', () => {
    it('renders children when user has permission', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:read'],
      }));

      render(
        <PermissionGuard permission="test:read">
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.getByTestId('guarded-content')).toBeInTheDocument();
    });

    it('does not render children when user lacks permission', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: [],
      }));

      render(
        <PermissionGuard permission="test:read">
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
    });

    it('renders fallback when permission denied', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: [],
      }));

      render(
        <PermissionGuard
          permission="test:read"
          fallback={<div data-testid="fallback">No Access</div>}
        >
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
      expect(screen.getByTestId('fallback')).toBeInTheDocument();
    });

    it('renders nothing when no fallback provided and permission denied', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: [],
      }));

      const { container } = render(
        <PermissionGuard permission="test:read">
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
      expect(container.firstChild).toBeNull();
    });
  });

  describe('Superuser Access', () => {
    it('allows superuser to access without permission check', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        is_superuser: true,
        permissions: [],
      }));

      render(
        <PermissionGuard permission="test:read">
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.getByTestId('guarded-content')).toBeInTheDocument();
    });
  });

  describe('Multiple Permissions', () => {
    it('grants access when user has any of the required permissions', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:read'],
      }));

      render(
        <PermissionGuard permission={['test:read', 'test:write']}>
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.getByTestId('guarded-content')).toBeInTheDocument();
    });

    it('denies access when user has none of the required permissions', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['other:read'],
      }));

      render(
        <PermissionGuard permission={['test:read', 'test:write']}>
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
    });

    it('requires all permissions when requireAll is true', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:read'],
      }));

      render(
        <PermissionGuard
          permission={['test:read', 'test:write']}
          requireAll={true}
        >
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
    });

    it('grants access when user has all required permissions', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:read', 'test:write'],
      }));

      render(
        <PermissionGuard
          permission={['test:read', 'test:write']}
          requireAll={true}
        >
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.getByTestId('guarded-content')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles missing user in localStorage', () => {
      render(
        <PermissionGuard permission="test:read">
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
    });

    it('handles invalid user data in localStorage', () => {
      localStorage.setItem('user', 'invalid json');

      const { container } = render(
        <PermissionGuard permission="test:read">
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
    });

    it('handles user without permissions array', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
      }));

      render(
        <PermissionGuard permission="test:read">
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
    });

    it('renders multiple children when authorized', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:read'],
      }));

      render(
        <PermissionGuard permission="test:read">
          <div data-testid="child-1">Child 1</div>
          <div data-testid="child-2">Child 2</div>
        </PermissionGuard>
      );

      expect(screen.getByTestId('child-1')).toBeInTheDocument();
      expect(screen.getByTestId('child-2')).toBeInTheDocument();
    });

    it('handles empty permission string', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: [''],
      }));

      render(
        <PermissionGuard permission="">
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.getByTestId('guarded-content')).toBeInTheDocument();
    });

    it('handles empty permissions array', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:read'],
      }));

      render(
        <PermissionGuard permission={[]}>
          <div data-testid="guarded-content">Guarded Content</div>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('guarded-content')).not.toBeInTheDocument();
    });
  });

  describe('useHasPermission Hook', () => {
    it('returns true when permission exists', () => {
      const TestComponent = () => {
        const hasPermission = useHasPermission('test:read');
        return <div data-testid="has-perm">{hasPermission ? 'Yes' : 'No'}</div>;
      };

      render(<TestComponent />);
      expect(screen.getByTestId('has-perm')).toHaveTextContent('Yes');
    });

    it('handles array of permissions', () => {
      const TestComponent = () => {
        const hasPermission = useHasPermission(['test:read', 'test:write']);
        return <div data-testid="has-perm">{hasPermission ? 'Yes' : 'No'}</div>;
      };

      render(<TestComponent />);
      expect(screen.getByTestId('has-perm')).toHaveTextContent('Yes');
    });

    it('handles requireAll parameter', () => {
      const TestComponent = () => {
        const hasPermission = useHasPermission(['test:read', 'test:write'], true);
        return <div data-testid="has-perm">{hasPermission ? 'Yes' : 'No'}</div>;
      };

      render(<TestComponent />);
      expect(screen.getByTestId('has-perm')).toHaveTextContent('Yes');
    });

    it('returns true when permission is null or undefined', () => {
      const TestComponent = () => {
        const hasPermission = useHasPermission(null);
        return <div data-testid="has-perm">{hasPermission ? 'Yes' : 'No'}</div>;
      };

      render(<TestComponent />);
      expect(screen.getByTestId('has-perm')).toHaveTextContent('Yes');
    });
  });

  describe('Complex Permission Scenarios', () => {
    it('handles nested permission checks', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:read', 'test:write'],
      }));

      render(
        <PermissionGuard permission="test:read">
          <PermissionGuard permission="test:write">
            <div data-testid="nested-content">Nested Content</div>
          </PermissionGuard>
        </PermissionGuard>
      );

      expect(screen.getByTestId('nested-content')).toBeInTheDocument();
    });

    it('denies access in nested guards when inner permission missing', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:read'],
      }));

      render(
        <PermissionGuard permission="test:read">
          <PermissionGuard permission="test:write">
            <div data-testid="nested-content">Nested Content</div>
          </PermissionGuard>
        </PermissionGuard>
      );

      expect(screen.queryByTestId('nested-content')).not.toBeInTheDocument();
    });

    it('handles wildcard-like permissions', () => {
      localStorage.setItem('user', JSON.stringify({
        role: 'USER',
        permissions: ['test:*'],
      }));

      render(
        <PermissionGuard permission="test:*">
          <div data-testid="wildcard-content">Wildcard Content</div>
        </PermissionGuard>
      );

      expect(screen.getByTestId('wildcard-content')).toBeInTheDocument();
    });
  });
});
