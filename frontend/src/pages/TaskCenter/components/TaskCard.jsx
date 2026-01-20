import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Calendar,
    CheckCircle2,
    ChevronRight,
    Circle,
    Flag,
    Folder,
    MoreHorizontal,
    Timer,
    AlertTriangle,
    ArrowRight
} from 'lucide-react';
import { Badge } from '../../../components/ui/badge';
import { Progress } from '../../../components/ui/progress';
import { Button } from '../../../components/ui/button';
import { cn } from '../../../lib/utils';
import { statusConfigs, priorityConfigs } from '../constants';

/**
 * 普通任务卡片组件
 * 显示任务的基本信息、进度和子任务
 */
export function TaskCard({ task, onStatusChange }) {
    const [expanded, setExpanded] = useState(false);
    const status = statusConfigs[task.status];
    const priority = priorityConfigs[task.priority];
    const StatusIcon = status.icon;

    const isOverdue = task.status !== 'completed' && new Date(task.dueDate) < new Date();
    const daysUntilDue = Math.ceil((new Date(task.dueDate) - new Date()) / (1000 * 60 * 60 * 24));

    const handleStatusClick = () => {
        if (task.status === 'pending') {
            onStatusChange(task.id, 'in_progress');
        } else if (task.status === 'in_progress') {
            onStatusChange(task.id, 'completed');
        }
    };

    return (
        <motion.div
            layout
            whileHover={{ scale: 1.005 }}
            className={cn(
                'rounded-xl border overflow-hidden transition-colors',
                task.status === 'blocked'
                    ? 'bg-red-500/5 border-red-500/30'
                    : isOverdue
                        ? 'bg-amber-500/5 border-amber-500/30'
                        : 'bg-surface-1 border-border'
            )}
        >
            <div className="p-4">
                {/* Header */}
                <div className="flex items-start gap-3">
                    <button
                        onClick={handleStatusClick}
                        className={cn(
                            'mt-0.5 p-1 rounded-lg transition-colors',
                            status.bgColor,
                            task.status !== 'blocked' && 'hover:bg-accent/20'
                        )}
                    >
                        <StatusIcon className={cn('w-5 h-5', status.color)} />
                    </button>

                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <Flag className={cn('w-3.5 h-3.5', priority.flagColor)} />
                            <span className="font-mono text-xs text-slate-500">{task.id}</span>
                        </div>
                        <h3 className="font-medium text-white mb-1">{task.title}</h3>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                            <Folder className="w-3 h-3" />
                            {task.projectId && <span className="text-accent">{task.projectId}</span>}
                            {task.projectName && (
                                <>
                                    <span>·</span>
                                    <span className="truncate">{task.projectName}</span>
                                </>
                            )}
                        </div>
                    </div>

                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <MoreHorizontal className="w-4 h-4" />
                    </Button>
                </div>

                {/* Block Reason */}
                {task.blockReason && (
                    <div className="mt-3 p-2 rounded-lg bg-red-500/10 text-xs text-red-300 flex items-center gap-2">
                        <AlertTriangle className="w-3 h-3" />
                        {task.blockReason}
                    </div>
                )}

                {/* Progress */}
                {task.status === 'in_progress' && task.progress !== undefined && (
                    <div className="mt-3">
                        <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-slate-400">进度</span>
                            <span className="text-white">{task.progress}%</span>
                        </div>
                        <Progress value={task.progress} className="h-1.5" />
                    </div>
                )}

                {/* Meta Info */}
                <div className="flex items-center gap-4 mt-3 text-xs">
                    <span
                        className={cn(
                            'flex items-center gap-1',
                            isOverdue ? 'text-red-400' : 'text-slate-400'
                        )}
                    >
                        <Calendar className="w-3 h-3" />
                        {isOverdue ? (
                            <>已逾期 {Math.abs(daysUntilDue)} 天</>
                        ) : daysUntilDue <= 3 ? (
                            <span className="text-amber-400">剩余 {daysUntilDue} 天</span>
                        ) : (
                            task.dueDate
                        )}
                    </span>
                    <span className="flex items-center gap-1 text-slate-400">
                        <Timer className="w-3 h-3" />
                        {task.actualHours}/{task.estimatedHours}h
                    </span>
                </div>

                {/* Tags */}
                {task.tags && task.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3">
                        {task.tags.map(tag => (
                            <Badge key={tag} variant="secondary" className="text-[10px] px-1.5">
                                {tag}
                            </Badge>
                        ))}
                    </div>
                )}

                {/* Subtasks */}
                {task.subTasks && task.subTasks.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border/50">
                        <button
                            onClick={() => setExpanded(!expanded)}
                            className="w-full flex items-center justify-between text-xs text-slate-400 hover:text-white transition-colors"
                        >
                            <span>
                                子任务 ({task.subTasks.filter(st => st.completed).length}/{task.subTasks.length})
                            </span>
                            <motion.span animate={{ rotate: expanded ? 90 : 0 }}>
                                <ChevronRight className="w-4 h-4" />
                            </motion.span>
                        </button>

                        <AnimatePresence>
                            {expanded && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden"
                                >
                                    <div className="space-y-1 mt-2">
                                        {task.subTasks.map(subTask => (
                                            <div key={subTask.id} className="flex items-center gap-2 text-xs">
                                                <div
                                                    className={cn(
                                                        'w-3.5 h-3.5 rounded-full border flex items-center justify-center',
                                                        subTask.completed
                                                            ? 'bg-emerald-500 border-emerald-500'
                                                            : 'border-slate-500'
                                                    )}
                                                >
                                                    {subTask.completed && <CheckCircle2 className="w-2.5 h-2.5 text-white" />}
                                                </div>
                                                <span
                                                    className={cn(
                                                        subTask.completed ? 'text-slate-500 line-through' : 'text-slate-300'
                                                    )}
                                                >
                                                    {subTask.title}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}

                {/* Blocked By */}
                {task.blockedBy && (
                    <div className="mt-3 p-2 rounded-lg bg-surface-2/50 text-xs flex items-center gap-2 text-slate-400">
                        <ArrowRight className="w-3 h-3" />
                        依赖任务：<span className="text-accent">{task.blockedBy}</span>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
