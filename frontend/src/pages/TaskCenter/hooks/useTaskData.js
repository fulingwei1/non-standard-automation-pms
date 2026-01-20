import { useState, useCallback, useEffect } from 'react';
import { taskCenterApi, progressApi } from '../../../services/api';
import { statusMapToBackend, statusMapToFrontend } from '../constants';

/**
 * 任务数据管理 Hook
 * 负责任务的加载、更新和状态管理
 */
export function useTaskData(filters = {}) {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 加载任务列表
    const loadTasks = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const params = {
                page: 1,
                page_size: 100,
                ...filters
            };

            // 状态过滤
            if (filters.statusFilter && filters.statusFilter !== 'all') {
                params.status = statusMapToBackend[filters.statusFilter] || filters.statusFilter;
            }

            // 搜索关键词
            if (filters.searchQuery) {
                params.keyword = filters.searchQuery;
            }

            // 项目过滤
            if (filters.selectedProject) {
                params.project_id = filters.selectedProject;
            }

            // 获取任务数据
            const response = await taskCenterApi.getMyTasks(params);
            const data = response.data || response;
            const tasksData = data.items || data || [];

            // 转换为前端格式
            const transformedTasks = tasksData.map(transformTask);
            setTasks(transformedTasks);
        } catch (err) {
            console.error('Failed to load tasks:', err);
            setError(err.response?.data?.detail || err.message || '加载任务失败');
            setTasks([]);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    // 转换任务数据格式
    const transformTask = (task) => {
        return {
            id: task.id?.toString() || task.task_code,
            title: task.title || '',
            projectId: task.project_id?.toString(),
            projectName: task.project_name || '',
            status: statusMapToFrontend[task.status] || task.status?.toLowerCase() || 'pending',
            priority: task.priority?.toLowerCase() || 'medium',
            progress: task.progress || 0,
            assignee: task.assignee_name || '',
            dueDate: task.deadline || task.plan_end_date || '',
            estimatedHours: task.estimated_hours || 0,
            actualHours: task.actual_hours || 0,
            tags: task.tags || [],
            subTasks: [],
            blockedBy: null,
            blockReason: task.block_reason || '',
            sourceType: task.source_type,
            sourceName: task.source_name,
            // 装配任务特有字段
            machine: task.machine || '',
            location: task.location || '',
            parts: task.parts || [],
            instructions: task.instructions || [],
            tools: task.tools || [],
            notes: task.notes || ''
        };
    };

    // 更新任务状态
    const updateTaskStatus = useCallback(async (taskId, newStatus) => {
        try {
            const taskIdNum = parseInt(taskId);
            const backendStatus = statusMapToBackend[newStatus];

            if (newStatus === 'completed') {
                await taskCenterApi.completeTask(taskIdNum);
            } else {
                await taskCenterApi.updateTask(taskIdNum, {
                    status: backendStatus,
                    progress: newStatus === 'completed' ? 100 : undefined
                });
            }

            // 刷新任务列表
            await loadTasks();
        } catch (err) {
            console.error('Failed to update task status:', err);
            throw new Error(err.response?.data?.detail || err.message || '更新任务状态失败');
        }
    }, [loadTasks]);

    // 更新任务步骤
    const updateTaskStep = useCallback(async (taskId, stepNumber) => {
        try {
            const task = tasks.find(t => t.id === taskId);
            if (!task) return;

            const newInstructions = task.instructions.map(step =>
                step.step === stepNumber ? { ...step, done: !step.done } : step
            );

            const stepsCompleted = newInstructions.filter(s => s.done).length;
            const progress = task.instructions.length > 0
                ? Math.round((stepsCompleted / task.instructions.length) * 100)
                : task.progress;

            // 更新任务进度
            const taskIdNum = parseInt(taskId.replace('T', ''));
            await progressApi.tasks.updateProgress(taskIdNum, {
                progress_percent: progress,
                update_note: `更新步骤 ${stepNumber} 的状态`
            });

            // 更新本地状态
            setTasks(prev =>
                prev.map(t => {
                    if (t.id !== taskId) return t;
                    return { ...t, instructions: newInstructions, progress };
                })
            );
        } catch (err) {
            console.error('Failed to update task step:', err);
            throw new Error(err.response?.data?.detail || err.message || '更新任务步骤失败');
        }
    }, [tasks]);

    // 初始加载
    useEffect(() => {
        loadTasks();
    }, [loadTasks]);

    return {
        tasks,
        loading,
        error,
        loadTasks,
        updateTaskStatus,
        updateTaskStep
    };
}
