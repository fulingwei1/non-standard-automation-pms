import { useState, useEffect } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "../../../components/ui/dialog";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { DAY_NAMES } from "../constants";
import { formatDate, formatFullDate } from "../utils/dateUtils";

export function AddEntryDialog({
    open,
    onOpenChange,
    onAdd,
    weekDates,
    projects,
    loading,
}) {
    const [selectedProjectId, setSelectedProjectId] = useState("");
    const [selectedTaskId, setSelectedTaskId] = useState("");
    const [hours, setHours] = useState({});
    const [tasks, setTasks] = useState([]);
    const [loadingTasks, setLoadingTasks] = useState(false);

    const selectedProject = projects.find((p) => p.id === Number(selectedProjectId));

    // Load tasks when project selected
    useEffect(() => {
        if (selectedProjectId) {
            loadTasks(Number(selectedProjectId));
        } else {
            setTasks([]);
            setSelectedTaskId("");
        }
    }, [selectedProjectId]);

    const loadTasks = async (projectId) => {
        setLoadingTasks(true);
        try {
            const { progressApi } = await import("../../../services/api");
            const response = await progressApi.tasks.list({
                project_id: projectId,
                page_size: 100,
            });
            const items =
                response.data?.items ||
                response.data?.data?.items ||
                response.items ||
                [];
            setTasks(items);
        } catch (error) {
            console.error("加载任务失败:", error);
            setTasks([]);
        } finally {
            setLoadingTasks(false);
        }
    };

    const handleAdd = () => {
        if (selectedProjectId && selectedTaskId) {
            onAdd({
                project_id: Number(selectedProjectId),
                project_name: selectedProject?.project_name,
                task_id: Number(selectedTaskId),
                task_name: tasks.find((t) => t.id === Number(selectedTaskId))?.task_name,
                hours,
            });
            setSelectedProjectId("");
            setSelectedTaskId("");
            setHours({});
            onOpenChange(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>添加工时记录</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                    {/* Project Select */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">项目</label>
                        <select
                            value={selectedProjectId}
                            onChange={(e) => {
                                setSelectedProjectId(e.target.value);
                                setSelectedTaskId("");
                            }}
                            disabled={loading}
                            className="w-full h-10 px-3 rounded-lg bg-slate-700 border border-slate-600 text-white focus:border-blue-500 focus:outline-none disabled:opacity-50"
                        >
                            <option value="">选择项目</option>
                            {projects.map((project) => (
                                <option key={project.id} value={project.id}>
                                    {project.project_code} - {project.project_name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Task Select */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">任务</label>
                        <select
                            value={selectedTaskId}
                            onChange={(e) => setSelectedTaskId(e.target.value)}
                            disabled={!selectedProjectId || loadingTasks}
                            className="w-full h-10 px-3 rounded-lg bg-slate-700 border border-slate-600 text-white focus:border-blue-500 focus:outline-none disabled:opacity-50"
                        >
                            <option value="">
                                {loadingTasks ? "加载中..." : "选择任务（可选）"}
                            </option>
                            {tasks.map((task) => (
                                <option key={task.id} value={task.id}>
                                    {task.task_name || task.title}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Hours Input */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-300">工时</label>
                        <div className="grid grid-cols-7 gap-2">
                            {weekDates.map((date, index) => (
                                <div key={index} className="text-center">
                                    <div className="text-xs text-slate-500 mb-1">
                                        {DAY_NAMES[index]}
                                    </div>
                                    <div className="text-xs text-slate-400 mb-1">
                                        {formatDate(date)}
                                    </div>
                                    <Input
                                        type="number"
                                        min="0"
                                        max="24"
                                        step="0.5"
                                        placeholder="0"
                                        value={hours[formatFullDate(date)] || ""}
                                        onChange={(e) =>
                                            setHours({
                                                ...hours,
                                                [formatFullDate(date)]: parseFloat(e.target.value) || 0,
                                            })
                                        }
                                        className="text-center h-9 bg-slate-700 border-slate-600 text-white"
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => onOpenChange(false)}>
                        取消
                    </Button>
                    <Button onClick={handleAdd} disabled={!selectedProjectId}>
                        添加
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
