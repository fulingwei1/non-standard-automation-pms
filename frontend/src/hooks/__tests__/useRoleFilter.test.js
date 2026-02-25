/**
 * useRoleFilter Hook 测试
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useRoleFilter } from '../useRoleFilter';

// Mock constants
vi.mock('../../lib/constants', () => ({
  PROJECT_STAGES: [
    { key: 'design', name: '方案设计', roles: ['admin', 'pm', 'te'] },
    { key: 'procurement', name: '采购备料', roles: ['admin', 'procurement'] },
    { key: 'assembly', name: '装配调试', roles: ['admin', 'worker'] },
    { key: 'testing', name: '测试验收' }, // 无 roles 限制
    { key: 'delivery', name: '交付' }
  ]
}));

describe('useRoleFilter', () => {
  const mockProjects = [
    { 
      id: 1, 
      name: 'Project 1',
      pm_id: 1,
      te_id: 2,
      sales_id: 3,
      members: [{ user_id: 4 }]
    },
    { 
      id: 2, 
      name: 'Project 2',
      pm_id: 5,
      te_id: 6,
      sales_id: 1,
      members: [{ user_id: 7 }]
    },
    { 
      id: 3, 
      name: 'Project 3',
      pm_id: 8,
      te_id: 1,
      sales_id: 9,
      members: []
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return all stages for admin', () => {
    const user = { id: 1, role: 'admin' };
    const { result } = renderHook(() => useRoleFilter(user));

    expect(result.current.relevantStages).toHaveLength(5);
  });

  it('should return all stages for pmc', () => {
    const user = { id: 1, role: 'pmc' };
    const { result } = renderHook(() => useRoleFilter(user));

    expect(result.current.relevantStages).toHaveLength(5);
  });

  it('should filter stages by role', () => {
    const user = { id: 1, role: 'procurement' };
    const { result } = renderHook(() => useRoleFilter(user));

    // procurement 只能看到 procurement 阶段和没有 roles 限制的阶段
    const stageKeys = result.current.relevantStages.map(s => s.key);
    expect(stageKeys).toContain('procurement');
    expect(stageKeys).toContain('testing');
    expect(stageKeys).toContain('delivery');
  });

  it('should return user projects as PM', () => {
    const user = { id: 1, role: 'pm' };
    const { result } = renderHook(() => 
      useRoleFilter(user, mockProjects)
    );

    // user id=1 is PM of project 1, sales of project 2, TE of project 3
    expect(result.current.myProjects).toHaveLength(3);
  });

  it('should return user projects as TE', () => {
    // user id=2 is TE of project 1 only
    const user = { id: 2, role: 'te' };
    const { result } = renderHook(() => 
      useRoleFilter(user, mockProjects)
    );

    expect(result.current.myProjects).toHaveLength(1);
    expect(result.current.myProjects[0].id).toBe(1);
  });

  it('should return user projects as sales', () => {
    // user id=3 is sales of project 1 only
    const user = { id: 3, role: 'sales' };
    const { result } = renderHook(() => 
      useRoleFilter(user, mockProjects)
    );

    expect(result.current.myProjects).toHaveLength(1);
    expect(result.current.myProjects[0].id).toBe(1);
  });

  it('should return user projects as member', () => {
    const user = { id: 4, role: 'engineer' };
    const { result } = renderHook(() => 
      useRoleFilter(user, mockProjects)
    );

    expect(result.current.myProjects).toHaveLength(1);
    expect(result.current.myProjects[0].id).toBe(1);
  });

  it('should return empty array when no projects match', () => {
    const user = { id: 999, role: 'engineer' };
    const { result } = renderHook(() => 
      useRoleFilter(user, mockProjects)
    );

    expect(result.current.myProjects).toHaveLength(0);
  });

  it('should return relevant stage keys', () => {
    const user = { id: 1, role: 'pm' };
    const { result } = renderHook(() => useRoleFilter(user));

    expect(result.current.relevantStageKeys).toContain('design');
    expect(result.current.relevantStageKeys).toContain('testing');
  });

  it('should check if project is relevant', () => {
    const user = { id: 1, role: 'pm' };
    const { result } = renderHook(() => 
      useRoleFilter(user, mockProjects)
    );

    expect(result.current.isProjectRelevant(1)).toBe(true);
    expect(result.current.isProjectRelevant(2)).toBe(true);
    expect(result.current.isProjectRelevant(3)).toBe(true); // te_id=1 matches
    expect(result.current.isProjectRelevant(999)).toBe(false);
  });

  it('should check if stage is relevant', () => {
    const user = { id: 1, role: 'pm' };
    const { result } = renderHook(() => useRoleFilter(user));

    expect(result.current.isStageRelevant('design')).toBe(true);
    expect(result.current.isStageRelevant('testing')).toBe(true);
  });

  it('should handle missing user gracefully', () => {
    const { result } = renderHook(() => 
      useRoleFilter(null, mockProjects)
    );

    expect(result.current.myProjects).toHaveLength(3);
  });

  it('should handle empty projects array', () => {
    const user = { id: 1, role: 'pm' };
    const { result } = renderHook(() => useRoleFilter(user, []));

    expect(result.current.myProjects).toHaveLength(0);
  });

  it('should memoize results', () => {
    const user = { id: 1, role: 'pm' };
    const { result, rerender } = renderHook(() => 
      useRoleFilter(user, mockProjects)
    );

    const firstMyProjects = result.current.myProjects;
    const firstRelevantStages = result.current.relevantStages;

    rerender();

    expect(result.current.myProjects).toBe(firstMyProjects);
    expect(result.current.relevantStages).toBe(firstRelevantStages);
  });

  it('should update when user changes', () => {
    const { result, rerender } = renderHook(
      ({ user, projects }) => useRoleFilter(user, projects),
      { initialProps: { user: { id: 1, role: 'pm' }, projects: mockProjects } }
    );

    expect(result.current.myProjects).toHaveLength(3); // pm_id=1, sales_id=1, te_id=1

    rerender({ user: { id: 5, role: 'pm' }, projects: mockProjects });

    expect(result.current.myProjects).toHaveLength(1);
    expect(result.current.myProjects[0].pm_id).toBe(5);
  });
});
