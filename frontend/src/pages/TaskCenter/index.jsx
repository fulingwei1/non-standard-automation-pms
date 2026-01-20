import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { PageHeader } from '../../components/layout';
import { ApiIntegrationError } from '../../components/ui';
import { staggerContainer } from '../../lib/animations';
import { getRoleInfo, isEngineerRole } from '../../lib/roleConfig';
import { projectApi } from '../../services/api';

// Hooks
import { useTaskData, useTaskFilters } from './hooks';

// Components
import { AssemblyTaskCard, TaskCard, TaskStats, TaskFilters } from './components';

/**
 * 任务中心主页面（重构版本）
 * 
 * 功能：
 * - 显示和管理用户的所有任务
 * - 支持按状态筛选、搜索
 * - 装配工人有专用视图
 * - 普通用户有标准视图
 */
export default function TaskCenter() {
    // 获取当前用户信息
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
    const role = currentUser?.role || 'admin';
    const userId = currentUser?.id;
    const isWorker = isEngineerRole(role) || role === 'assembler';
    const roleInfo = getRoleInfo(role);

    // 项目数据
    const [projects, setProjects] = useState([]);

    // 使用自定义 Hooks
    const filters = useTaskFilters();
    const taskData = useTaskData(filters.filterParams);

    // 加载项目列表（用于过滤）
    useEffect(() => {
        const loadProjects = async () => {
            try {
                const response = await projectApi.list({ page_size: 100 });
                const data = response.data || response;
                setProjects(data.items || data || []);
            } catch (err) {
                console.error('Failed to load projects:', err);
                setProjects([]);
            }
        };
        loadProjects();
    }, []);

    // 处理错误状态
    const handleStatusChange = async (taskId, newStatus) => {
        try {
            await taskData.updateTaskStatus(taskId, newStatus);
        } catch (err) {
            alert(err.message);
        }
    };

    const handleStepToggle = async (taskId, stepNumber) => {
        try {
            await taskData.updateTaskStep(taskId, stepNumber);
        } catch (err) {
            alert(err.message);
        }
    };

    // 应用客户端过滤（额外的过滤层）
    const filteredTasks = filters.applyClientFilters(taskData.tasks);

    // 装配工人专用视图
    if (role === 'assembler') {
        return (
            <motion.div
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="space-y-6"
            >
                <PageHeader
                    title="我的装配任务"
                    description={`今日待完成 ${taskData.tasks.filter(t => t.status === 'in_progress').length} 项，共 ${taskData.tasks.length} 项任务`}
                />

                {/* 统计卡片 */}
                <TaskStats tasks={taskData.tasks} />

                {/* 搜索和过滤 */}
                <TaskFilters
                    searchQuery={filters.searchQuery}
                    onSearchChange={filters.setSearchQuery}
                    statusFilter={filters.statusFilter}
                    onStatusFilterChange={filters.setStatusFilter}
                />

                {/* 错误提示 */}
                {taskData.error && (
                    <ApiIntegrationError
                        message={taskData.error}
                        onRetry={taskData.loadTasks}
                    />
                )}

                {/* 任务列表 */}
                <div className="space-y-4">
                    {taskData.loading ? (
                        <div className="text-center text-slate-400 py-8">加载中...</div>
                    ) : filteredTasks.length === 0 ? (
                        <div className="text-center text-slate-400 py-8">
                            {taskData.error ? '加载失败' : '暂无任务'}
                        </div>
                    ) : (
                        filteredTasks.map(task => (
                            <AssemblyTaskCard
                                key={task.id}
                                task={task}
                                onStatusChange={handleStatusChange}
                                onStepToggle={handleStepToggle}
                            />
                        ))
                    )}
                </div>
            </motion.div>
        );
    }

    // 标准用户视图
    return (
        <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-6"
        >
            <PageHeader
                title="任务中心"
                description="管理和跟踪您的所有任务"
            />

            {/* 统计卡片 */}
            <TaskStats tasks={taskData.tasks} />

            {/* 搜索和过滤 */}
            <TaskFilters
                searchQuery={filters.searchQuery}
                onSearchChange={filters.setSearchQuery}
                statusFilter={filters.statusFilter}
                onStatusFilterChange={filters.setStatusFilter}
            />

            {/* 错误提示 */}
            {taskData.error && (
                <ApiIntegrationError
                    message={taskData.error}
                    onRetry={taskData.loadTasks}
                />
            )}

            {/* 任务列表 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {taskData.loading ? (
                    <div className="col-span-full text-center text-slate-400 py-8">
                        加载中...
                    </div>
                ) : filteredTasks.length === 0 ? (
                    <div className="col-span-full text-center text-slate-400 py-8">
                        {taskData.error ? '加载失败' : '暂无任务'}
                    </div>
                ) : (
                    filteredTasks.map(task => (
                        <TaskCard
                            key={task.id}
                            task={task}
                            onStatusChange={handleStatusChange}
                        />
                    ))
                )}
            </div>
        </motion.div>
    );
}
