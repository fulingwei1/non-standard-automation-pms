import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDepartmentManagement } from '../useDepartmentManagement';
import { departmentApi } from '../../../../services/api';

vi.mock('../../../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    default: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      defaults: { baseURL: '/api' },
    },
  };
});

describe('useDepartmentManagement Hook', () => {
    const mockDepartments = [
        { id: 1, name: 'HR', type: 'admin' },
        { id: 2, name: 'Tech', type: 'rd' },
    ];

    beforeEach(() => {
        vi.clearAllMocks();
        departmentApi.list.mockResolvedValue({ data: mockDepartments });
    });

    it('should list departments on mount', async () => {
        const { result } = renderHook(() => useDepartmentManagement());

        expect(result.current.loading).toBe(true);
        await waitFor(() => expect(result.current.loading).toBe(false));

        expect(result.current.departments).toEqual(mockDepartments);
        expect(departmentApi.list).toHaveBeenCalledTimes(1);
    });

    it('should create a department', async () => {
        const { result } = renderHook(() => useDepartmentManagement());
        await waitFor(() => expect(result.current.loading).toBe(false));

        departmentApi.create.mockResolvedValue({ id: 3 });

        let opResult;
        await act(async () => {
            opResult = await result.current.createDepartment({ name: 'Sales', type: 'sales' });
        });

        expect(opResult.success).toBe(true);
        expect(departmentApi.create).toHaveBeenCalledWith({ name: 'Sales', type: 'sales' });
        // Should reload
        expect(departmentApi.list).toHaveBeenCalledTimes(2);
    });

    it('should handle create error', async () => {
        const { result } = renderHook(() => useDepartmentManagement());
        await waitFor(() => expect(result.current.loading).toBe(false));

        departmentApi.create.mockRejectedValue(new Error('API Error'));

        let opResult;
        await act(async () => {
            opResult = await result.current.createDepartment({ name: 'Sales' });
        });

        expect(opResult.success).toBe(false);
        expect(opResult.error).toBe('API Error');
    });
});
