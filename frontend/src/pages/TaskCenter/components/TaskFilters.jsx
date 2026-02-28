import { Filter, Search } from 'lucide-react';
import { Input } from '../../../components/ui/input';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { cn } from '../../../lib/utils';
import { statusConfigs } from '../constants';

/**
 * 任务过滤器组件
 * 提供搜索和状态筛选功能
 */
export function TaskFilters({
    searchQuery,
    onSearchChange,
    statusFilter,
    onStatusFilterChange
}) {
    const filterOptions = [
        { value: 'all', label: '全部', count: null },
        { value: 'pending', label: '待开始', icon: statusConfigs.pending.icon },
        { value: 'in_progress', label: '进行中', icon: statusConfigs.in_progress.icon },
        { value: 'blocked', label: '阻塞', icon: statusConfigs.blocked.icon },
        { value: 'completed', label: '已完成', icon: statusConfigs.completed.icon }
    ];

    return (
        <div className="space-y-4">
            {/* 搜索框 */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                    placeholder="搜索任务..."
                    value={searchQuery}
                    onChange={(e) => onSearchChange(e.target.value)}
                    className="pl-10 bg-surface-1 border-border"
                />
            </div>

            {/* 状态过滤器 */}
            <div className="flex items-center gap-2 flex-wrap">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                    <Filter className="w-4 h-4" />
                    <span>状态筛选:</span>
                </div>
                {(filterOptions || []).map(option => {
                    const Icon = option.icon;
                    const isActive = statusFilter === option.value;

                    return (
                        <Button
                            key={option.value}
                            variant={isActive ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => onStatusFilterChange(option.value)}
                            className={cn(
                                'gap-2',
                                !isActive && 'bg-surface-1 hover:bg-surface-2'
                            )}
                        >
                            {Icon && <Icon className="w-3.5 h-3.5" />}
                            {option.label}
                            {option.count !== null && (
                                <Badge variant="secondary" className="ml-1 text-xs">
                                    {option.count}
                                </Badge>
                            )}
                        </Button>
                    );
                })}
            </div>
        </div>
    );
}
