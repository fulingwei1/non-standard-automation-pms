import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useProjectTaskList } from '../useProjectTaskList';
import { progressApi, projectApi } from '../../../../services/api';

// Mock the API module
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

describe('useProjectTaskList Hook', () => {
    const projectId = '123';
    const mockProject = { id: projectId, project_name: 'Test Project' };
    const mockSummary = { total_tasks: 10, completed_tasks: 5 };
    const mockTasks = [
        { id: 1, task_name: 'Task 1', description: 'desc 1', status: 'PENDING' },
        { id: 2, task_name: 'Task 2', description: 'desc 2', status: 'COMPLETED' },
    ];

    beforeEach(() => {
        vi.clearAllMocks();

        // Setup default successful responses
        projectApi.get.mockResolvedValue({ data: mockProject });
        progressApi.reports.getSummary.mockResolvedValue({ data: mockSummary });
        progressApi.tasks.list.mockResolvedValue({ data: { items: mockTasks } });
    });

    it('should load initial data correctly', async () => {
        const { result } = renderHook(() => useProjectTaskList(projectId));

        // Initially loading
        expect(result.current.loading).toBe(true);

        // Wait for data to load
        await waitFor(() => expect(result.current.loading).toBe(false));

        // Check data
        expect(result.current.project).toEqual(mockProject);
        expect(result.current.summary).toEqual(mockSummary);
        expect(result.current.tasks).toHaveLength(2);

        // Verify API calls
        expect(projectApi.get).toHaveBeenCalledWith(projectId);
        expect(progressApi.reports.getSummary).toHaveBeenCalledWith(projectId);
        expect(progressApi.tasks.list).toHaveBeenCalledWith({ project_id: projectId });
    });

    it('should filter tasks by keyword', async () => {
        const { result } = renderHook(() => useProjectTaskList(projectId));
        await waitFor(() => expect(result.current.loading).toBe(false));

        act(() => {
            result.current.setFilters(prev => ({ ...prev, keyword: 'Task 1' }));
        });

        // Filtering happens on client side in the hook for now (based on filteredTasks useMemo)
        expect(result.current.tasks).toHaveLength(1);
        expect(result.current.tasks[0].task_name).toBe('Task 1');
    });

    it('should create a task successfully', async () => {
        const { result } = renderHook(() => useProjectTaskList(projectId));
        await waitFor(() => expect(result.current.loading).toBe(false));

        progressApi.tasks.create.mockResolvedValue({ data: { id: 3 } });

        const newTaskData = {
            task_name: 'New Task',
            stage: 'S1'
        };

        act(() => {
            result.current.setNewTask(newTaskData);
        });

        let createResult;
        await act(async () => {
            createResult = await result.current.createTask();
        });

        expect(createResult.success).toBe(true);
        expect(progressApi.tasks.create).toHaveBeenCalledWith(projectId, expect.objectContaining(newTaskData));

        // Should verify it reloads data
        expect(progressApi.tasks.list).toHaveBeenCalledTimes(2); // Initial load + reload
    });

    it('should view task details', async () => {
        const { result } = renderHook(() => useProjectTaskList(projectId));
        await waitFor(() => expect(result.current.loading).toBe(false));

        const mockDetail = { ...mockTasks[0], detailed_info: 'info' };
        progressApi.tasks.get.mockResolvedValue({ data: mockDetail });

        await act(async () => {
            await result.current.viewTask(1);
        });

        expect(result.current.selectedTask).toEqual(mockDetail);
        expect(result.current.dialogs.detail).toBe(true);
    });
});
