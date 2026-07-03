
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
import { CheckSquare, Square, Eye, Users, Clock, CheckCircle2, PlayCircle } from "lucide-react";
import { cn, formatDate } from "../../lib/utils";
import {
  DISPATCH_STATUS,
  DISPATCH_PRIORITY,
  INSTALLATION_TYPE,
  getDispatchPriorityLabel,
  getDispatchStatusLabel,
  getInstallationTypeLabel,
  normalizeDispatchOrder,
} from "@/lib/constants/installationDispatch";

export default function DispatchList({
  orders,
  loading,
  selectedOrders,
  onSelectOrder,
  onSelectAll,
  onViewDetail,
  onAssign,
  onStart,
  onUpdateProgress,
  onComplete,
}) {
  const getStatusBadge = (status) => {
    const config = {
      [DISPATCH_STATUS.PENDING]: {
        label: getDispatchStatusLabel(DISPATCH_STATUS.PENDING),
        className: "bg-slate-500 text-white"
      },
      [DISPATCH_STATUS.ASSIGNED]: {
        label: getDispatchStatusLabel(DISPATCH_STATUS.ASSIGNED),
        className: "bg-blue-500 text-white"
      },
      [DISPATCH_STATUS.IN_PROGRESS]: {
        label: getDispatchStatusLabel(DISPATCH_STATUS.IN_PROGRESS),
        className: "bg-amber-500 text-white"
      },
      [DISPATCH_STATUS.COMPLETED]: {
        label: getDispatchStatusLabel(DISPATCH_STATUS.COMPLETED),
        className: "bg-emerald-500 text-white"
      },
      [DISPATCH_STATUS.CANCELLED]: {
        label: getDispatchStatusLabel(DISPATCH_STATUS.CANCELLED),
        className: "bg-red-500 text-white"
      },
      [DISPATCH_STATUS.DELAYED]: {
        label: getDispatchStatusLabel(DISPATCH_STATUS.DELAYED),
        className: "bg-orange-500 text-white"
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
        label: getDispatchPriorityLabel(DISPATCH_PRIORITY.LOW),
        bg: "bg-slate-500/20",
        text: "text-slate-400",
      },
      [DISPATCH_PRIORITY.NORMAL]: {
        label: getDispatchPriorityLabel(DISPATCH_PRIORITY.NORMAL),
        bg: "bg-gray-500/20",
        text: "text-gray-500",
      },
      [DISPATCH_PRIORITY.MEDIUM]: {
        label: getDispatchPriorityLabel(DISPATCH_PRIORITY.MEDIUM),
        bg: "bg-blue-500/20",
        text: "text-blue-400",
      },
      [DISPATCH_PRIORITY.HIGH]: {
        label: getDispatchPriorityLabel(DISPATCH_PRIORITY.HIGH),
        bg: "bg-amber-500/20",
        text: "text-amber-400",
      },
      [DISPATCH_PRIORITY.URGENT]: {
        label: getDispatchPriorityLabel(DISPATCH_PRIORITY.URGENT),
        bg: "bg-red-500/20",
        text: "text-red-500",
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
      [INSTALLATION_TYPE.INSTALLATION]: {
        label: getInstallationTypeLabel(INSTALLATION_TYPE.INSTALLATION),
      },
      [INSTALLATION_TYPE.DEBUGGING]: {
        label: getInstallationTypeLabel(INSTALLATION_TYPE.DEBUGGING),
      },
      [INSTALLATION_TYPE.TRAINING]: {
        label: getInstallationTypeLabel(INSTALLATION_TYPE.TRAINING),
      },
      [INSTALLATION_TYPE.MAINTENANCE]: {
        label: getInstallationTypeLabel(INSTALLATION_TYPE.MAINTENANCE),
      },
      [INSTALLATION_TYPE.REPAIR]: {
        label: getInstallationTypeLabel(INSTALLATION_TYPE.REPAIR),
      },
      [INSTALLATION_TYPE.OTHER]: {
        label: getInstallationTypeLabel(INSTALLATION_TYPE.OTHER),
      },
    }[type];

    if (!config) return getInstallationTypeLabel(type);
    return config.label;
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
          ) : orders?.length === 0 ? (
            <TableRow>
              <TableCell colSpan={10} className="text-center py-8">
                暂无派工单
              </TableCell>
            </TableRow>
          ) : (
            (orders || []).map((order) => {
              const displayOrder = normalizeDispatchOrder(order);

              return (
              <TableRow key={displayOrder.id}>
                <TableCell>
                  <Square
                    className={cn(
                      "h-4 w-4 cursor-pointer",
                      selectedOrders.has(displayOrder.id) && "text-blue-500"
                    )}
                    onClick={() => onSelectOrder(displayOrder.id)}
                  />
                </TableCell>
                <TableCell className="font-medium">
                  {displayOrder.order_no}
                </TableCell>
                <TableCell>{displayOrder.task_title}</TableCell>
                <TableCell>{displayOrder.project_name}</TableCell>
                <TableCell>{getTaskTypeDisplay(displayOrder.task_type)}</TableCell>
                <TableCell>{getPriorityBadge(displayOrder.priority)}</TableCell>
                <TableCell>{getStatusBadge(displayOrder.status)}</TableCell>
                <TableCell>{displayOrder.assigned_to_name || "未分配"}</TableCell>
                <TableCell>{formatDate(displayOrder.scheduled_date)}</TableCell>
                <TableCell>
                  <div className="flex space-x-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label="查看派工单"
                      title="查看派工单"
                      onClick={() => onViewDetail(displayOrder)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    {displayOrder.status === DISPATCH_STATUS.PENDING && (
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label="指派派工单"
                        title="指派派工单"
                        onClick={() => onAssign(displayOrder)}
                      >
                        <Users className="h-4 w-4" />
                      </Button>
                    )}
                    {displayOrder.status === DISPATCH_STATUS.ASSIGNED && (
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label="开始执行"
                        title="开始执行"
                        onClick={() => onStart(displayOrder)}
                      >
                        <PlayCircle className="h-4 w-4" />
                      </Button>
                    )}
                    {displayOrder.status === DISPATCH_STATUS.IN_PROGRESS && (
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label="更新进度"
                        title="更新进度"
                        onClick={() => onUpdateProgress(displayOrder)}
                      >
                        <Clock className="h-4 w-4" />
                      </Button>
                    )}
                    {displayOrder.status === DISPATCH_STATUS.IN_PROGRESS && (
                      <Button
                        variant="ghost"
                        size="sm"
                        aria-label="完成派工单"
                        title="完成派工单"
                        onClick={() => onComplete(displayOrder)}
                      >
                        <CheckCircle2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>
  );
}
