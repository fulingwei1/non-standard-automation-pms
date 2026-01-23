import { useState, useMemo, useCallback } from 'react';

/**
 * 任务过滤器 Hook
 * 管理任务列表的所有过滤状态
 */
export function useTaskFilters() {
    const [viewMode, setViewMode] = useState('list'); // list | kanban
    const [statusFilter, setStatusFilter] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedProject, setSelectedProject] = useState(null);

    // 计算过滤参数
    const filterParams = useMemo(() => {
        return {
            statusFilter,
            searchQuery,
            selectedProject: selectedProject?.id || selectedProject
        };
    }, [statusFilter, searchQuery, selectedProject]);

    // 重置所有过滤器
    const resetFilters = useCallback(() => {
        setStatusFilter('all');
        setSearchQuery('');
        setSelectedProject(null);
    }, []);

    // 应用客户端过滤（用于已加载的数据）
    const applyClientFilters = useCallback((tasks) => {
        return tasks.filter(task => {
            // 状态过滤
            if (statusFilter !== 'all' && task.status !== statusFilter) {
                return false;
            }
            // 搜索过滤
            if (searchQuery && !(task.title || "").toLowerCase().includes(searchQuery.toLowerCase())) {
                return false;
            }
            return true;
        });
    }, [statusFilter, searchQuery]);

    return {
        // 状态
        viewMode,
        statusFilter,
        searchQuery,
        selectedProject,
        filterParams,

        // 操作
        setViewMode,
        setStatusFilter,
        setSearchQuery,
        setSelectedProject,
        resetFilters,
        applyClientFilters
    };
}
