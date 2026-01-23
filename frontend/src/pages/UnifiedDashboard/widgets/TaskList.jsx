/**
 * 任务列表组件 (Task List)
 *
 * 显示待办任务列表
 * 支持按类型过滤、优先级排序
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
  ChevronRight,
  ListTodo,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import api from '../../../services/api';
import { cn } from '../../../lib/utils';

// 优先级颜色映射
const priorityColors = {
  high: 'bg-red-500/20 text-red-400 border-red-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-green-500/20 text-green-400 border-green-500/30',
  normal: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
};

// 默认任务数据
const defaultTasks = [
  {
    id: 1,
    title: '完成项目方案评审',
    project: 'PJ250101-001',
    priority: 'high',
    dueDate: '今天',
    status: 'pending',
  },
  {
    id: 2,
    title: '提交工时记录',
    project: null,
    priority: 'medium',
    dueDate: '明天',
    status: 'pending',
  },
  {
    id: 3,
    title: '审核采购订单',
    project: 'PJ250101-002',
    priority: 'medium',
    dueDate: '本周五',
    status: 'pending',
  },
  {
    id: 4,
    title: '更新项目进度',
    project: 'PJ250101-003',
    priority: 'low',
    dueDate: '下周一',
    status: 'pending',
  },
];

/**
 * 单个任务项
 */
function TaskItem({ task, index, onClick }) {
  const isOverdue = task.dueDate === '已逾期';
  const isDueToday = task.dueDate === '今天';

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={() => onClick?.(task)}
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors',
        'hover:bg-white/5',
        isOverdue && 'bg-red-500/10'
      )}
    >
      {/* 状态图标 */}
      <div className="mt-0.5">
        {task.status === 'completed' ? (
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        ) : isOverdue ? (
          <AlertCircle className="h-4 w-4 text-red-500" />
        ) : (
          <Circle className="h-4 w-4 text-muted-foreground" />
        )}
      </div>

      {/* 任务内容 */}
      <div className="flex-1 min-w-0">
        <p className={cn(
          'text-sm font-medium truncate',
          task.status === 'completed' && 'line-through text-muted-foreground'
        )}>
          {task.title}
        </p>
        <div className="flex items-center gap-2 mt-1">
          {task.project && (
            <span className="text-xs text-muted-foreground">
              {task.project}
            </span>
          )}
          <Badge
            variant="outline"
            className={cn('text-xs px-1.5 py-0', priorityColors[task.priority])}
          >
            {task.priority === 'high' ? '高' :
             task.priority === 'medium' ? '中' :
             task.priority === 'low' ? '低' : '普通'}
          </Badge>
        </div>
      </div>

      {/* 截止时间 */}
      <div className={cn(
        'flex items-center text-xs whitespace-nowrap',
        isOverdue ? 'text-red-500' : isDueToday ? 'text-orange-500' : 'text-muted-foreground'
      )}>
        <Clock className="h-3 w-3 mr-1" />
        {task.dueDate}
      </div>
    </motion.div>
  );
}

/**
 * 任务列表主组件
 *
 * @param {Object} props
 * @param {string} props.filter - 过滤类型
 * @param {number} props.limit - 显示数量限制
 * @param {Object} props.data - 预加载的数据
 */
export default function TaskList({ filter, limit = 5, data }) {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadTasks = async () => {
      setLoading(true);
      try {
        // 如果有预加载数据，直接使用
        if (data?.tasks) {
          setTasks(data.tasks.slice(0, limit));
          return;
        }

        // 否则尝试从 API 获取
        try {
          const params = filter ? { filter } : {};
          const response = await api.get('/node-tasks/my-tasks', { params });
          if (response.data?.items) {
            setTasks(response.data.items.slice(0, limit));
            return;
          }
        } catch {
          // API 不可用，使用默认数据
        }

        // 使用默认数据
        setTasks(defaultTasks.slice(0, limit));
      } finally {
        setLoading(false);
      }
    };

    loadTasks();
  }, [filter, limit, data]);

  const handleTaskClick = (task) => {
    if (task.project) {
      navigate(`/projects/${task.project}`);
    } else {
      navigate('/progress-tracking/tasks');
    }
  };

  const handleViewAll = () => {
    navigate('/progress-tracking/tasks');
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <ListTodo className="h-4 w-4" />
            待办任务
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={handleViewAll}>
            查看全部
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {[...Array(limit)].map((_, i) => (
              <div key={i} className="h-14 bg-white/5 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <CheckCircle2 className="h-8 w-8 mb-2" />
            <p className="text-sm">暂无待办任务</p>
          </div>
        ) : (
          <div className="space-y-1">
            {tasks.map((task, index) => (
              <TaskItem
                key={task.id}
                task={task}
                index={index}
                onClick={handleTaskClick}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
