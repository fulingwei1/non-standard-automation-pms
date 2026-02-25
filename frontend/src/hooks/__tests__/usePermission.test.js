/**
 * usePermission Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { usePermission } from '../usePermission';
import { usePermissionContext } from '../../context/PermissionContext';
import { ReactNode } from 'react';

// Mock PermissionContext
const mockPermissionContext = {
  permissions: ['project:create', 'project:read', 'project:update'],
  menus: [
    { code: 'project-list' },
    { code: 'project-create' },
    { code: 'dashboard' }
  ],
  dataScopes: ['own', 'department'],
  isSuperuser: false,
  isLoading: false,
  error: null
};

vi.mock('../../context/PermissionContext', () => ({
  usePermissionContext: vi.fn(() => mockPermissionContext)
}));

describe('usePermission', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    usePermissionContext.mockReturnValue(mockPermissionContext);
  });

  it('should check if user has permission', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.hasPermission('project:create')).toBe(true);
    expect(result.current.hasPermission('project:read')).toBe(true);
    expect(result.current.hasPermission('project:delete')).toBe(false);
  });

  it('should check if user has any permission', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.hasAnyPermission(['project:create', 'project:delete'])).toBe(true);
    expect(result.current.hasAnyPermission(['project:delete', 'user:delete'])).toBe(false);
  });

  it('should check if user has all permissions', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.hasAllPermissions(['project:create', 'project:read'])).toBe(true);
    expect(result.current.hasAllPermissions(['project:create', 'project:delete'])).toBe(false);
  });

  it('should return true for superuser', () => {

    usePermissionContext.mockReturnValue({
      ...mockPermissionContext,
      isSuperuser: true
    });

    const { result } = renderHook(() => usePermission());

    expect(result.current.hasPermission('any:permission')).toBe(true);
    expect(result.current.hasAnyPermission(['any:permission'])).toBe(true);
    expect(result.current.hasAllPermissions(['any:permission'])).toBe(true);
  });

  it('should handle null permissions', () => {

    usePermissionContext.mockReturnValue({
      ...mockPermissionContext,
      permissions: null
    });

    const { result } = renderHook(() => usePermission());

    expect(result.current.hasPermission('project:create')).toBe(false);
    expect(result.current.hasAnyPermission(['project:create'])).toBe(false);
    expect(result.current.hasAllPermissions(['project:create'])).toBe(false);
  });

  it('should handle empty permissions array', () => {

    usePermissionContext.mockReturnValue({
      ...mockPermissionContext,
      permissions: []
    });

    const { result } = renderHook(() => usePermission());

    expect(result.current.hasPermission('project:create')).toBe(false);
  });

  it('should check menu access', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.canAccessMenu('project-list')).toBe(true);
    expect(result.current.canAccessMenu('dashboard')).toBe(true);
    expect(result.current.canAccessMenu('admin-panel')).toBe(false);
  });

  it('should handle invalid permission codes', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.hasPermission(null)).toBe(false);
    expect(result.current.hasPermission(undefined)).toBe(false);
    expect(result.current.hasPermission('')).toBe(false);
  });

  it('should handle invalid permission arrays', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.hasAnyPermission(null)).toBe(false);
    expect(result.current.hasAnyPermission(undefined)).toBe(false);
    expect(result.current.hasAnyPermission([])).toBe(false);
  });

  it('should return true for hasAllPermissions with empty array', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.hasAllPermissions([])).toBe(true);
  });

  it('should provide loading and error states', () => {

    usePermissionContext.mockReturnValue({
      ...mockPermissionContext,
      isLoading: true,
      error: 'Failed to load permissions'
    });

    const { result } = renderHook(() => usePermission());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.error).toBe('Failed to load permissions');
  });

  it('should memoize permission check functions', () => {
    const { result, rerender } = renderHook(() => usePermission());

    const firstHasPermission = result.current.hasPermission;
    const firstHasAnyPermission = result.current.hasAnyPermission;
    const firstHasAllPermissions = result.current.hasAllPermissions;

    rerender();

    expect(result.current.hasPermission).toBe(firstHasPermission);
    expect(result.current.hasAnyPermission).toBe(firstHasAnyPermission);
    expect(result.current.hasAllPermissions).toBe(firstHasAllPermissions);
  });

  it('should handle data scopes', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.dataScopes).toEqual(['own', 'department']);
  });

  it('should check case-sensitive permissions', () => {
    const { result } = renderHook(() => usePermission());

    expect(result.current.hasPermission('project:create')).toBe(true);
    expect(result.current.hasPermission('PROJECT:CREATE')).toBe(false);
  });
});
