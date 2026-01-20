import { useState, useCallback, useEffect, useMemo } from 'react';
import { progressApi, projectApi } from '../../../services/api';

export function useProjectTaskList(projectId) {
    const [loading, setLoading] = useState(true);
    const [project, setProject] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [summary, setSummary] = useState(null);

    // Filters
    const [filters, setFilters] = useState({
        keyword: "",
        status: "",
        stage: "",
        assignee: ""
    });

    // Dialogs
    const [dialogs, setDialogs] = useState({
        create: false,
        detail: false
    });

    const [selectedTask, setSelectedTask] = useState(null);

    // Form
    const [newTask, setNewTask] = useState({
        task_name: "",
        stage: "",
        planned_start_date: "",
        planned_end_date: "",
        weight: 0,
        description: ""
    });

    // Fetch Data
    const loadData = useCallback(async () => {
        if (!projectId) return;

        try {
            setLoading(true);

            // 并行获取基础数据
            const [projectRes, summaryRes] = await Promise.all([
                projectApi.get(projectId),
                progressApi.reports.getSummary(projectId)
            ]);

            setProject(projectRes.data || projectRes);
            setSummary(summaryRes.data || summaryRes);

            // 获取任务列表
            const params = { project_id: projectId };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.stage && filters.stage !== 'all') params.stage = filters.stage;
            if (filters.assignee) params.assignee_id = filters.assignee;
            if (filters.keyword) params.search = filters.keyword;

            const tasksRes = await progressApi.tasks.list(params);
            setTasks(tasksRes.data?.items || tasksRes.data || []);

        } catch (error) {
            console.error("Failed to load project data:", error);
        } finally {
            setLoading(false);
        }
    }, [projectId, filters]);

    // Create Task
    const createTask = useCallback(async () => {
        try {
            await progressApi.tasks.create(projectId, newTask);
            setDialogs(prev => ({ ...prev, create: false }));
            // Reset form
            setNewTask({
                task_name: "",
                stage: "",
                planned_start_date: "",
                planned_end_date: "",
                weight: 0,
                description: ""
            });
            // Reload data
            loadData();
            return { success: true };
        } catch (error) {
            return { success: false, error: error.response?.data?.detail || error.message };
        }
    }, [projectId, newTask, loadData]);

    // View Task Detail
    const viewTask = useCallback(async (taskId) => {
        try {
            const res = await progressApi.tasks.get(taskId);
            setSelectedTask(res.data || res);
            setDialogs(prev => ({ ...prev, detail: true }));
        } catch (error) {
            console.error("Failed to fetch task detail:", error);
        }
    }, []);

    // Filtered Tasks (Client-side search mostly for keyword if not handled by API)
    const filteredTasks = useMemo(() => {
        return tasks.filter((task) => {
            if (!filters.keyword) return true;
            const keyword = filters.keyword.toLowerCase();
            return (
                task.task_name?.toLowerCase().includes(keyword) ||
                task.description?.toLowerCase().includes(keyword)
            );
        });
    }, [tasks, filters.keyword]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    return {
        loading,
        project,
        tasks: filteredTasks,
        summary,
        filters,
        setFilters,
        dialogs,
        setDialogs,
        selectedTask,
        newTask,
        setNewTask,
        loadData,
        createTask,
        viewTask
    };
}
