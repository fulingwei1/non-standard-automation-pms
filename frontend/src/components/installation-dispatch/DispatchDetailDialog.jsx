

import { formatDate } from "../../lib/utils";
import { cn } from "../../lib/utils";
import {
  DISPATCH_STATUS,
  DISPATCH_STATUS_LABELS,
  DISPATCH_PRIORITY,
  DISPATCH_PRIORITY_LABELS,
  INSTALLATION_TYPE,
  INSTALLATION_TYPE_LABELS,
} from "./index";

const getStatusBadge = (status) => {
  const config = {
    [DISPATCH_STATUS.PENDING]: {
      label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.PENDING],
      color: "bg-slate-500 text-white",
    },
    [DISPATCH_STATUS.ASSIGNED]: {
      label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.ASSIGNED],
      color: "bg-blue-500 text-white",
    },
    [DISPATCH_STATUS.IN_PROGRESS]: {
      label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.IN_PROGRESS],
      color: "bg-amber-500 text-white",
    },
    [DISPATCH_STATUS.COMPLETED]: {
      label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.COMPLETED],
      color: "bg-emerald-500 text-white",
    },
    [DISPATCH_STATUS.CANCELLED]: {
      label: DISPATCH_STATUS_LABELS[DISPATCH_STATUS.CANCELLED],
      color: "bg-red-500 text-white",
    },
  }[status];

  if (!config) {return <Badge variant="secondary">{status}</Badge>;}

  return (
    <Badge variant="secondary" className={cn("border-0", config.color)}>
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

  if (!config) {return <Badge variant="secondary">{priority}</Badge>;}

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
    [INSTALLATION_TYPE.NEW]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.NEW], icon: "🔧" },
    [INSTALLATION_TYPE.MAINTENANCE]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.MAINTENANCE], icon: "🔨" },
    [INSTALLATION_TYPE.REPAIR]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.REPAIR], icon: "🛠️" },
    [INSTALLATION_TYPE.UPGRADE]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.UPGRADE], icon: "⚙️" },
    [INSTALLATION_TYPE.INSPECTION]: { label: INSTALLATION_TYPE_LABELS[INSTALLATION_TYPE.INSPECTION], icon: "👥" },
  }[type];

  if (!config) {return type;}
  return `${config.icon} ${config.label}`;
};

export default function DispatchDetailDialog({
  open,
  onOpenChange,
  order,
}) {
  if (!order) {return null;}

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>派工单详情</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">派工单号</label>
              <p className="mt-1 text-sm">{order.order_number}</p>
            </div>
            <div>
              <label className="text-sm font-medium">状态</label>
              <div className="mt-1">{getStatusBadge(order.status)}</div>
            </div>
            <div>
              <label className="text-sm font-medium">任务标题</label>
              <p className="mt-1 text-sm">{order.task_title}</p>
            </div>
            <div>
              <label className="text-sm font-medium">任务类型</label>
              <p className="mt-1 text-sm">{getTaskTypeDisplay(order.task_type)}</p>
            </div>
            <div>
              <label className="text-sm font-medium">项目</label>
              <p className="mt-1 text-sm">{order.project?.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium">设备</label>
              <p className="mt-1 text-sm">{order.machine?.name}</p>
            </div>
            <div>
              <label className="text-sm font-medium">优先级</label>
              <div className="mt-1">{getPriorityBadge(order.priority)}</div>
            </div>
            <div>
              <label className="text-sm font-medium">负责人</label>
              <p className="mt-1 text-sm">
                {order.assigned_to?.name || "未分配"}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">计划日期</label>
              <p className="mt-1 text-sm">{formatDate(order.scheduled_date)}</p>
            </div>
            <div>
              <label className="text-sm font-medium">预计工时</label>
              <p className="mt-1 text-sm">{order.estimated_hours} 小时</p>
            </div>
            <div>
              <label className="text-sm font-medium">地点</label>
              <p className="mt-1 text-sm">{order.location}</p>
            </div>
            <div>
              <label className="text-sm font-medium">客户电话</label>
              <p className="mt-1 text-sm">{order.customer_phone}</p>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium">任务描述</label>
            <p className="mt-1 text-sm whitespace-pre-wrap">
              {order.task_description}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium">客户地址</label>
            <p className="mt-1 text-sm">{order.customer_address}</p>
          </div>
          {order.remark && (
            <div>
              <label className="text-sm font-medium">备注</label>
              <p className="mt-1 text-sm whitespace-pre-wrap">{order.remark}</p>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
