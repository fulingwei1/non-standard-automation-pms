/**
 * 工单卡片组件
 * 显示单个工单的详细信息
 */
import { Clock, Wrench, AlertTriangle, Package } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Button } from '../ui/button';
import { cn, formatDate } from '../../lib/utils';
import { WORK_ORDER_STATUS, WORK_ORDER_TYPES, getStatusColor as _getStatusColor, calculateProgress } from '@/lib/constants/workerWorkstation';

/**
 * 工单卡片组件
 * @param {object} props
 * @param {object} props.order - 工单数据
 * @param {function} props.onAction - 操作回调
 */
export default function WorkOrderCard({ order, onAction }) {
  const statusInfo = WORK_ORDER_STATUS[order.status] || WORK_ORDER_STATUS.PENDING;
  const typeInfo = WORK_ORDER_TYPES[order.work_order_type] || WORK_ORDER_TYPES.ASSEMBLY;
  const progress = calculateProgress(order.completed_qty || 0, order.plan_qty || 0);

  const isUrgent = order.priority === 'urgent' || order.priority === 'high';
  const isOverdue = order.plan_end_time && new Date(order.plan_end_time) < new Date();

  const availableActions = [
  { key: 'start', label: '开工', icon: PlayCircle, show: order.status === 'pending' },
  { key: 'progress', label: '进度', icon: TrendingUp, show: order.status === 'in_progress' },
  { key: 'complete', label: '完工', icon: CheckCircle2, show: order.status === 'in_progress' },
  { key: 'detail', label: '详情', icon: FileText, show: true }].
  filter((action) => action.show);

  return (
    <Card
      className={cn(
        'bg-slate-800/50 border transition-all hover:shadow-lg',
        isOverdue ? 'border-red-500/30' : 'border-slate-700/50'
      )}>

      <CardContent className="p-4">
        {/* 头部 */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h4 className="text-white font-medium">{order.work_order_no || order.code}</h4>
              {isUrgent &&
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              }
              {isOverdue &&
              <Badge variant="destructive" className="text-xs">
                  已逾期
              </Badge>
              }
            </div>
            <p className="text-sm text-slate-400">{order.project_name || order.project_code}</p>
          </div>
          <Badge className={cn(statusInfo.color, 'text-white')}>
            {statusInfo.label}
          </Badge>
        </div>

        {/* 工序信息 */}
        <div className="flex items-center gap-4 mb-3 text-sm">
          <div className="flex items-center gap-1 text-slate-400">
            <Wrench className="w-4 h-4" />
            <span>{order.process_name || order.process_code}</span>
          </div>
          <div className="flex items-center gap-1 text-slate-400">
            <Package className="w-4 h-4" />
            <span>{typeInfo.label}</span>
          </div>
        </div>

        {/* 进度条 */}
        <div className="mb-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-slate-400">完成进度</span>
            <span className="text-white font-medium">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
          <div className="flex items-center justify-between text-xs text-slate-500 mt-1">
            <span>已完成: {order.completed_qty || 0}</span>
            <span>计划: {order.plan_qty || 0}</span>
          </div>
        </div>

        {/* 时间信息 */}
        <div className="flex items-center gap-4 mb-3 text-xs text-slate-400">
          {order.plan_start_time &&
          <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>开始: {formatDate(order.plan_start_time)}</span>
          </div>
          }
          {order.plan_end_time &&
          <div className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              <span>结束: {formatDate(order.plan_end_time)}</span>
          </div>
          }
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-2">
          {(availableActions || []).map((action) =>
          <Button
            key={action.key}
            variant={action.key === 'detail' ? 'outline' : 'default'}
            size="sm"
            onClick={() => onAction && onAction({ type: action.key, orderId: order.id })}
            className="flex-1">

              <action.icon className="w-4 h-4 mr-1"  />
              {action.label}
          </Button>
          )}
        </div>
      </CardContent>
    </Card>);

}

// 导入需要的图标
import { PlayCircle, TrendingUp, CheckCircle2, FileText } from 'lucide-react';