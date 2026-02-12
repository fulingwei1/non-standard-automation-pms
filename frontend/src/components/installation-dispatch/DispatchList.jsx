
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CheckSquare, Square, Eye, Users, Clock, CheckCircle2 } from "lucide-react";
import { cn, formatDate } from "../../lib/utils";
import {
  DISPATCH_STATUS,
  DISPATCH_STATUS_LABELS,
  DISPATCH_STATUS_COLORS,
  DISPATCH_PRIORITY,
  DISPATCH_PRIORITY_LABELS,
  PRIORITY_COLORS,
  INSTALLATION_TYPE,
  INSTALLATION_TYPE_LABELS,
} from "@/lib/constants/installationDispatch";

export default function DispatchList({
  orders,
  loading,
  selectedOrders,
  onSelectOrder,
  onSelectAll,
  onViewDetail,
  onAssign,
  onUpdateProgress,
  onComplete,
}) {
  const getStatusBadge = (status) => {
    const config = {
      [DISPATCH_STATUS.PENDING]: {
        label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.PENDING],
        color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.PENDING],
        className: "bg-slate-500 text-white"
      },
      [DISPATCH_STATUS.ASSIGNED]: {
        label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.ASSIGNED],
        color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.ASSIGNED],
        className: "bg-blue-500 text-white"
      },
      [DISPATCH_STATUS.IN_PROGRESS]: {
        label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.IN_PROGRESS],
        color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.IN_PROGRESS],
        className: "bg-amber-500 text-white"
      },
      [DISPATCH_STATUS.COMPLETED]: {
        label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.COMPLETED],
        color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.COMPLETED],
        className: "bg-emerald-500 text-white"
      },
      [DISPATCH_STATUS.CANCELLED]: {
        label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.CANCELLED],
        color: DISPATCH_STATUS_COLORS[DISPATCH_STATUS.CANCELLED],
        className: "bg-red-500 text-white"
      },
    }[status];

    if (!config) return <Badge variant="secondary">{status}</Badge>;

    return (
      <Badge
        variant="secondary"
        className={cn("border-0", config.className)}
      >
        {config.label}
      </Badge>
    );
  };

  const getPriorityBadge = (priority) => {
    const config = {
      [DISPATCH_PRIORITY.LOW]: {
        label: DISPATCH_PRIORITY_LABELS[DISPATCH_PRIORITY.LOW],
        bg: "bg-slate-500/20",
        text: "text-slate-400",
      },
      [DISPATCH_PRIORITY.MEDIUM]: {
        label: DISPATCH_PRIORITY_LABELS[DISPATCH_PRIORITY.MEDIUM],
        bg: "bg-blue-500/20",
        text: "text-blue-400",
      },
      [DISPATCH_PRIORITY.HIGH]: {
        label: DISPATCH_PRIORITY_LABELS[DISPATCH_PRIORITY.HIGH],
        bg: "bg-amber-500/20",
        text: "text-amber-400",
      },
    }[priority];

    if (!config) return <Badge variant="secondary">{priority}</Badge>;

    return (
      <Badge
        variant="secondary"
        className={cn("border-0", config.bg, config.text)}
      >
        {config.label}
      </Badge>
    );
  };

  const getTaskTypeDisplay = (type) => {
    const config = {
      [INSTALLATION_TYPE.NEW]: {
        label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.NEW],
        icon: "🔧",
      },
      [INSTALLATION_TYPE.MAINTENANCE]: {
        label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.MAINTENANCE],
        icon: "🔨",
      },
      [INSTALLATION_TYPE.REPAIR]: {
        label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.REPAIR],
        icon: "🛠️",
      },
      [INSTALLATION_TYPE.UPGRADE]: {
        label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.UPGRADE],
        icon: "⚙️",
      },
      [INSTALLATION_TYPE.INSPECTION]: {
        label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.INSPECTION],
        icon: "👥",
      },
    }[type];

    if (!config) return type;
    return `${config.icon} ${config.label}`;
  };

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <CheckSquare
                className="h-4 w-4 cursor-pointer"
                onClick={onSelectAll}
              />
            </TableHead>
            <TableHead>派工单号</TableHead>
            <TableHead>任务标题</TableHead>
            <TableHead>项目</TableHead>
            <TableHead>任务类型</TableHead>
            <TableHead>优先级</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>负责人</TableHead>
            <TableHead>计划日期</TableHead>
            <TableHead>操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading ? (
            <TableRow>
              <TableCell colSpan={10} className="text-center py-8">
                加载中...
              </TableCell>
            </TableRow>
          ) : orders.length === 0 ? (
            <TableRow>
              <TableCell colSpan={10} className="text-center py-8">
                暂无派工单
              </TableCell>
            </TableRow>
          ) : (
            orders.map((order) => (
              <TableRow key={order.id}>
                <TableCell>
                  <Square
                    className={cn(
                      "h-4 w-4 cursor-pointer",
                      selectedOrders.has(order.id) && "text-blue-500"
                    )}
                    onClick={() => onSelectOrder(order.id)}
                  />
                </TableCell>
                <TableCell className="font-medium">
                  {order.order_number}
                </TableCell>
                <TableCell>{order.task_title}</TableCell>
                <TableCell>{order.project?.name}</TableCell>
                <TableCell>{getTaskTypeDisplay(order.task_type)}</TableCell>
                <TableCell>{getPriorityBadge(order.priority)}</TableCell>
                <TableCell>{getStatusBadge(order.status)}</TableCell>
                <TableCell>{order.assigned_to?.name}</TableCell>
                <TableCell>{formatDate(order.scheduled_date)}</TableCell>
                <TableCell>
                  <div className="flex space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewDetail(order)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    {order.status === DISPATCH_STATUS.PENDING && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onAssign(order)}
                      >
                        <Users className="h-4 w-4" />
                      </Button>
                    )}
                    {order.status === DISPATCH_STATUS.IN_PROGRESS && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onUpdateProgress(order)}
                      >
                        <Clock className="h-4 w-4" />
                      </Button>
                    )}
                    {order.status === DISPATCH_STATUS.IN_PROGRESS && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onComplete(order)}
                      >
                        <CheckCircle2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
