import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTimesheet } from '../useTimesheet';
import { timesheetApi, projectApi } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
    timesheetApi: {
        getWeek: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
        batchCreate: vi.fn(),
        submit: vi.fn(),
    },
    projectApi: {
        list: vi.fn(),
    },
}));

describe('useTimesheet Hook', () => {
    const mockProjects = [
        { id: 1, project_name: 'Project A', project_code: 'PJ000000001' },
        { id: 2, project_name: 'Project B', project_code: 'PJ000000002' },
    ];

    const mockTimesheets = [
        {
            id: 1,
            project_id: 1,
            project_name: 'Project A',
            task_id: 101,
            task_name: 'Task 1',
            work_date: '2024-01-15',
            work_hours: 8,
            status: 'DRAFT',
        },
    ];

    beforeEach(() => {
        vi.clearAllMocks();
        projectApi.list.mockResolvedValue({
            data: { items: mockProjects },
        });
        timesheetApi.getWeek.mockResolvedValue({
            data: { data: { timesheets: mockTimesheets } },
        });
    });

    it('should load projects on mount', async () => {
        const { result } = renderHook(() => useTimesheet());

        await waitFor(() => {
            expect(result.current.loading).toBe(false);
        });

        expect(projectApi.list).toHaveBeenCalled();
        expect(result.current.projects).toHaveLength(2);
    });

    it('should have correct initial state', async () => {
        const { result } = renderHook(() => useTimesheet());

        expect(result.current.weekOffset).toBe(0);
        expect(result.current.isCurrentWeek).toBe(true);
        expect(result.current.showAddDialog).toBe(false);
        expect(typeof result.current.weeklyTotal).toBe('number');
    });

    it('should handle dialog state', () => {
        const { result } = renderHook(() => useTimesheet());

        expect(result.current.showAddDialog).toBe(false);

        act(() => {
            result.current.setShowAddDialog(true);
        });

        expect(result.current.showAddDialog).toBe(true);
    });

    it('should handle week offset changes', () => {
        const { result } = renderHook(() => useTimesheet());

        expect(result.current.weekOffset).toBe(0);

        act(() => {
            result.current.setWeekOffset(-1);
        });

        expect(result.current.weekOffset).toBe(-1);
    });
});
