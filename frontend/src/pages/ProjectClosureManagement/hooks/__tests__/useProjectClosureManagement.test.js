import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useProjectClosureManagement } from '../useProjectClosureManagement';
import { pmoApi, projectApi } from '../../../../services/api';
import { useParams, useNavigate } from 'react-router-dom';

vi.mock('react-router-dom', () => ({
    useParams: vi.fn(),
    useNavigate: vi.fn()
}));

vi.mock('../../../../services/api', () => ({
    projectApi: {
        get: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
        list: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } })
    },
    pmoApi: {
        closures: {
            get: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
            create: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
            review: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }),
            updateLessons: vi.fn().mockResolvedValue({ data: { items: [], total: 0 } }) }
    }
}));

describe('useProjectClosureManagement Hook', () => {
    const mockNavigate = vi.fn().mockResolvedValue({ data: { items: [], total: 0 } });
    const mockProject = { id: 1, project_name: 'Test Project' };
    const mockClosure = { id: 101, status: 'DRAFT' };

    beforeEach(() => {
        vi.clearAllMocks();
        useParams.mockReturnValue({ projectId: '1' });
        useNavigate.mockReturnValue(mockNavigate);
        projectApi.get.mockResolvedValue({ data: mockProject });
        pmoApi.closures.get.mockResolvedValue({ data: mockClosure });
    });

    it('should load project and closure data', async () => {
        const { result } = renderHook(() => useProjectClosureManagement());

        expect(result.current.loading).toBe(true);
        await waitFor(() => expect(result.current.loading).toBe(false));

        expect(projectApi.get).toHaveBeenCalledWith(1);
        expect(pmoApi.closures.get).toHaveBeenCalledWith(1);
        expect(result.current.project).toEqual(mockProject);
        expect(result.current.closure).toEqual(mockClosure);
    });

    it('should handle search projects', async () => {
        useParams.mockReturnValue({});
        projectApi.list.mockResolvedValue({ data: { items: [mockProject] } });

        const { result } = renderHook(() => useProjectClosureManagement());

        await waitFor(() => {
            expect(result.current.showProjectSelect).toBe(true);
            expect(projectApi.list).toHaveBeenCalled();
        });

        await waitFor(() => {
            expect(result.current.projectList).toHaveLength(1);
        });
    });
});
