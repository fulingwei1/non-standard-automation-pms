import { cn } from "../../lib/utils";

/**
 * 工时记录同步状态徽章组件
 * 显示同步到财务/研发/HR/项目的状态
 */
export function SyncStatusBadge({ syncStatus, size: _size = "sm" }) {
  if (!syncStatus) {
    return (
      <Badge variant="outline" className="text-xs">
        <Clock className="w-3 h-3 mr-1" />
        未同步
      </Badge>);

  }

  const statusMap = {
    finance: { label: "财务", key: "finance" },
    rd: { label: "研发", key: "rd" },
    hr: { label: "HR", key: "hr" },
    project: { label: "项目", key: "project" }
  };

  const allSynced = Object.values(statusMap).every(
    ({ key }) => syncStatus[key]?.status === "synced"
  );
  const hasError = Object.values(statusMap).some(
    ({ key }) => syncStatus[key]?.status === "error"
  );
  const hasPending = Object.values(statusMap).some(
    ({ key }) => syncStatus[key]?.status === "pending"
  );

  if (allSynced) {
    return (
      <Badge variant="default" className="bg-green-600 text-white text-xs">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        已同步
      </Badge>);

  }

  if (hasError) {
    return (
      <Badge variant="destructive" className="text-xs">
        <XCircle className="w-3 h-3 mr-1" />
        同步失败
      </Badge>);

  }

  if (hasPending) {
    return (
      <Badge
        variant="outline"
        className="text-xs border-yellow-500 text-yellow-500">

        <Clock className="w-3 h-3 mr-1 animate-spin" />
        同步中
      </Badge>);

  }

  return (
    <Badge variant="outline" className="text-xs">
      <AlertCircle className="w-3 h-3 mr-1" />
      部分同步
    </Badge>);

}

/**
 * 详细同步状态显示组件
 */
export function SyncStatusDetail({ syncStatus, className }) {
  if (!syncStatus) {
    return (
      <div className={cn("text-xs text-slate-400", className)}>未同步</div>);

  }

  const statusMap = {
    finance: { label: "财务", icon: "💰" },
    rd: { label: "研发", icon: "🔬" },
    hr: { label: "HR", icon: "👥" },
    project: { label: "项目", icon: "📊" }
  };

  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {Object.entries(statusMap).map(([key, { label, icon: _icon }]) => {
        const status = syncStatus[key]?.status;
        const getStatusColor = () => {
          switch (status) {
            case "synced":
              return "text-green-500";
            case "error":
              return "text-red-500";
            case "pending":
              return "text-yellow-500";
            default:
              return "text-slate-400";
          }
        };

        const getStatusIcon = () => {
          switch (status) {
            case "synced":
              return <CheckCircle2 className="w-3 h-3" />;
            case "error":
              return <XCircle className="w-3 h-3" />;
            case "pending":
              return <Clock className="w-3 h-3 animate-spin" />;
            default:
              return <AlertCircle className="w-3 h-3" />;
          }
        };

        return (
          <div
            key={key}
            className={cn("flex items-center gap-1 text-xs", getStatusColor())}
            title={`${label}: ${status || "未同步"}`}>

            {getStatusIcon()}
            <span>{label}</span>
          </div>);

      })}
    </div>);

}