import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { PlayCircle, Circle, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Card, CardContent } from '../../../components/ui/card';
import { cn } from '../../../lib/utils';
import { fadeIn } from '../../../lib/animations';

/**
 * 任务统计卡片组件
 * 显示任务的各种统计数据
 */
export function TaskStats({ tasks }) {
    const stats = useMemo(() => {
        return {
            total: tasks.length,
            pending: tasks.filter(t => t.status === 'pending').length,
            inProgress: tasks.filter(t => t.status === 'in_progress').length,
            blocked: tasks.filter(t => t.status === 'blocked').length,
            completed: tasks.filter(t => t.status === 'completed').length,
            overdue: tasks.filter(
                t => t.status !== 'completed' && new Date(t.dueDate) < new Date()
            ).length
        };
    }, [tasks]);

    const statCards = [
        {
            label: '进行中',
            value: stats.inProgress,
            icon: PlayCircle,
            color: 'text-blue-400',
            bg: 'bg-blue-500/10'
        },
        {
            label: '待开始',
            value: stats.pending,
            icon: Circle,
            color: 'text-slate-400',
            bg: 'bg-slate-500/10'
        },
        {
            label: '已阻塞',
            value: stats.blocked,
            icon: AlertTriangle,
            color: 'text-red-400',
            bg: 'bg-red-500/10'
        },
        {
            label: '已完成',
            value: stats.completed,
            icon: CheckCircle2,
            color: 'text-emerald-400',
            bg: 'bg-emerald-500/10'
        }
    ];

    return (
        <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {statCards.map((stat, index) => {
                const Icon = stat.icon;
                return (
                    <Card key={index} className={cn('bg-surface-1/50', stat.bg)}>
                        <CardContent className="p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-slate-400">{stat.label}</p>
                                    <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                                </div>
                                <Icon className={cn('w-8 h-8', stat.color)} />
                            </div>
                        </CardContent>
                    </Card>
                );
            })}
        </motion.div>
    );
}
