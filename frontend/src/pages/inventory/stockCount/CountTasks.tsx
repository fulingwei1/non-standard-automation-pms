/**
 * 库存盘点任务页面
 * 管理盘点任务的创建和执行
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Plus, Eye, ClipboardCheck } from 'lucide-react';
import CreateTaskDialog from './components/CreateTaskDialog';
import InventoryAPI from '@/services/inventory';
import { CountTask, CountTaskStatus } from '@/types/inventory';
import { format } from 'date-fns';

const CountTasks: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<CountTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await InventoryAPI.getCountTasks();
      setTasks(response.items);
    } catch (error) {
      console.error('加载盘点任务失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (taskId: number) => {
    navigate(`/inventory/stockCount/details/${taskId}`);
  };

  const getStatusBadge = (status: CountTaskStatus) => {
    const badges: Record<CountTaskStatus, { label: string; className: string }> = {
      [CountTaskStatus.DRAFT]: { label: '草稿', className: 'bg-gray-100 text-gray-800' },
      [CountTaskStatus.IN_PROGRESS]: {
        label: '进行中',
        className: 'bg-blue-100 text-blue-800',
      },
      [CountTaskStatus.COMPLETED]: {
        label: '已完成',
        className: 'bg-green-100 text-green-800',
      },
      [CountTaskStatus.APPROVED]: {
        label: '已批准',
        className: 'bg-purple-100 text-purple-800',
      },
      [CountTaskStatus.CANCELLED]: {
        label: '已取消',
        className: 'bg-red-100 text-red-800',
      },
    };
    const badge = badges[status];
    return <Badge className={badge.className}>{badge.label}</Badge>;
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      FULL: '全盘',
      SPOT: '抽盘',
      CYCLE: '循环盘',
    };
    return labels[type] || type;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <ClipboardCheck className="h-8 w-8 text-purple-500" />
            库存盘点任务
          </h1>
          <p className="text-gray-500 mt-1">创建和管理库存盘点任务</p>
        </div>
        <Button
          onClick={() => setDialogOpen(true)}
          className="bg-purple-500 hover:bg-purple-600"
        >
          <Plus className="h-4 w-4 mr-2" />
          创建盘点任务
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>任务编号</TableHead>
              <TableHead>任务名称</TableHead>
              <TableHead>类型</TableHead>
              <TableHead>盘点位置</TableHead>
              <TableHead>计划日期</TableHead>
              <TableHead>物料数</TableHead>
              <TableHead>差异数</TableHead>
              <TableHead>创建人</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks.length > 0 ? (
              tasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell className="font-medium">{task.task_no}</TableCell>
                  <TableCell>{task.task_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{getTypeLabel(task.task_type)}</Badge>
                  </TableCell>
                  <TableCell>{task.location || '全部'}</TableCell>
                  <TableCell>
                    {format(new Date(task.scheduled_date), 'yyyy-MM-dd')}
                  </TableCell>
                  <TableCell className="text-center">{task.item_count || 0}</TableCell>
                  <TableCell className="text-center text-orange-600 font-medium">
                    {task.difference_count || 0}
                  </TableCell>
                  <TableCell>{task.created_by}</TableCell>
                  <TableCell>{getStatusBadge(task.status)}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewDetails(task.id)}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      详情
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={10} className="text-center py-12">
                  <ClipboardCheck className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p className="text-gray-500">暂无盘点任务</p>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <CreateTaskDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSuccess={loadTasks}
      />
    </div>
  );
};

export default CountTasks;
