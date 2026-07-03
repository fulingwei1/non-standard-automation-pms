

import { formatDate } from "../../lib/utils";
import { cn } from "../../lib/utils";
import { Badge, Button, Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../ui";
import {
  DISPATCH_STATUS,
  DISPATCH_PRIORITY,
  INSTALLATION_TYPE,
  getDispatchPriorityLabel,
  getDispatchStatusLabel,
  getInstallationTypeLabel,
  normalizeDispatchOrder,
} from "./index";

const getStatusBadge = (status) => {
  const config = {
    [DISPATCH_STATUS.PENDING]: {
      label: getDispatchStatusLabel(DISPATCH_STATUS.PENDING),
      color: "bg-slate-500 text-white",
    },
    [DISPATCH_STATUS.ASSIGNED]: {
      label: getDispatchStatusLabel(DISPATCH_STATUS.ASSIGNED),
      color: "bg-blue-500 text-white",
    },
    [DISPATCH_STATUS.IN_PROGRESS]: {
      label: getDispatchStatusLabel(DISPATCH_STATUS.IN_PROGRESS),
      color: "bg-amber-500 text-white",
    },
    [DISPATCH_STATUS.COMPLETED]: {
      label: getDispatchStatusLabel(DISPATCH_STATUS.COMPLETED),
      color: "bg-emerald-500 text-white",
    },
    [DISPATCH_STATUS.CANCELLED]: {
      label: getDispatchStatusLabel(DISPATCH_STATUS.CANCELLED),
      color: "bg-red-500 text-white",
    },
    [DISPATCH_STATUS.DELAYED]: {
      label: getDispatchStatusLabel(DISPATCH_STATUS.DELAYED),
      color: "bg-orange-500 text-white",
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
    [INSTALLATION_TYPE.INSTALLATION]: { label: getInstallationTypeLabel(INSTALLATION_TYPE.INSTALLATION) },
    [INSTALLATION_TYPE.DEBUGGING]: { label: getInstallationTypeLabel(INSTALLATION_TYPE.DEBUGGING) },
    [INSTALLATION_TYPE.TRAINING]: { label: getInstallationTypeLabel(INSTALLATION_TYPE.TRAINING) },
    [INSTALLATION_TYPE.MAINTENANCE]: { label: getInstallationTypeLabel(INSTALLATION_TYPE.MAINTENANCE) },
    [INSTALLATION_TYPE.REPAIR]: { label: getInstallationTypeLabel(INSTALLATION_TYPE.REPAIR) },
    [INSTALLATION_TYPE.OTHER]: { label: getInstallationTypeLabel(INSTALLATION_TYPE.OTHER) },
  }[type];

  if (!config) {return getInstallationTypeLabel(type);}
  return config.label;
};

export default function DispatchDetailDialog({
  open,
  onOpenChange,
  order,
}) {
  if (!order) {return null;}
  const displayOrder = normalizeDispatchOrder(order);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>派工单详情</DialogTitle>
          <DialogDescription>查看安装调试派工单的项目、负责人和执行信息</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">派工单号</label>
              <p className="mt-1 text-sm">{displayOrder.order_no}</p>
            </div>
            <div>
              <label className="text-sm font-medium">状态</label>
              <div className="mt-1">{getStatusBadge(displayOrder.status)}</div>
            </div>
            <div>
              <label className="text-sm font-medium">任务标题</label>
              <p className="mt-1 text-sm">{displayOrder.task_title}</p>
            </div>
            <div>
              <label className="text-sm font-medium">任务类型</label>
              <p className="mt-1 text-sm">{getTaskTypeDisplay(displayOrder.task_type)}</p>
            </div>
            <div>
              <label className="text-sm font-medium">项目</label>
              <p className="mt-1 text-sm">{displayOrder.project_name}</p>
            </div>
            <div>
              <label className="text-sm font-medium">设备</label>
              <p className="mt-1 text-sm">{displayOrder.machine_name || "未关联设备"}</p>
            </div>
            <div>
              <label className="text-sm font-medium">优先级</label>
              <div className="mt-1">{getPriorityBadge(displayOrder.priority)}</div>
            </div>
            <div>
              <label className="text-sm font-medium">负责人</label>
              <p className="mt-1 text-sm">
                {displayOrder.assigned_to_name || "未分配"}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">计划日期</label>
              <p className="mt-1 text-sm">{formatDate(displayOrder.scheduled_date)}</p>
            </div>
            <div>
              <label className="text-sm font-medium">预计工时</label>
              <p className="mt-1 text-sm">{displayOrder.estimated_hours || 0} 小时</p>
            </div>
            <div>
              <label className="text-sm font-medium">地点</label>
              <p className="mt-1 text-sm">{displayOrder.location}</p>
            </div>
            <div>
              <label className="text-sm font-medium">客户电话</label>
              <p className="mt-1 text-sm">{displayOrder.customer_phone}</p>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium">任务描述</label>
            <p className="mt-1 text-sm whitespace-pre-wrap">
              {displayOrder.task_description}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium">客户地址</label>
            <p className="mt-1 text-sm">{displayOrder.customer_address}</p>
          </div>
          {displayOrder.remark && (
            <div>
              <label className="text-sm font-medium">备注</label>
              <p className="mt-1 text-sm whitespace-pre-wrap">{displayOrder.remark}</p>
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
