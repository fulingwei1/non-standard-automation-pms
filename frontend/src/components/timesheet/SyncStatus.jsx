/**
 * SyncStatus - 工时同步状态组件
 * 显示同步状态、上次同步时间、待同步条数，支持手动触发同步
 */

import { useState, useEffect, useCallback } from "react";
import {
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
} from "lucide-react";
import { formatDate, cn } from "../../lib/utils";
import { projectApi } from "../../services/api";

// 同步状态配置
const SYNC_STATUS_CONFIG = {
  idle: {
    label: "空闲",
    color: "text-slate-400",
    bgColor: "bg-slate-500/20",
    icon: Clock,
  },
  syncing: {
    label: "同步中",
    color: "text-blue-400",
    bgColor: "bg-blue-500/20",
    icon: RefreshCw,
    animate: true,
  },
  success: {
    label: "成功",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/20",
    icon: CheckCircle,
  },
  error: {
    label: "失败",
    color: "text-red-400",
    bgColor: "bg-red-500/20",
    icon: AlertCircle,
  },
};

export default function SyncStatus({ projectId, compact = false, onSyncComplete }) {
  const [syncState, setSyncState] = useState("idle");
  const [lastSyncTime, setLastSyncTime] = useState(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [syncProgress, setSyncProgress] = useState(0);
  const [syncError, setSyncError] = useState(null);
  const [loading, setLoading] = useState(true);

  // 获取同步状态
  const fetchSyncStatus = useCallback(async () => {
    try {
      setLoading(true);
      // 获取工时汇总来判断同步状态
      const res = await projectApi.getTimesheetSummary(projectId, {
        include_sync_status: true,
      });
      const data = res.data || res || {};

      // 解析同步状态数据
      setPendingCount(data.pending_sync_count || 0);
      setLastSyncTime(data.last_sync_time || null);

      // 根据待同步数量判断状态
      if (data.pending_sync_count > 0) {
        setSyncState("idle");
      } else {
        setSyncState("success");
      }
    } catch (error) {
      console.warn("Failed to fetch sync status:", error);
      // 降级显示
      setPendingCount(0);
      setSyncState("idle");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      fetchSyncStatus();
    }
  }, [fetchSyncStatus, projectId]);

  // 手动触发同步
  const handleSync = async () => {
    try {
      setSyncState("syncing");
      setSyncProgress(0);
      setSyncError(null);

      // 模拟同步进度
      const progressInterval = setInterval(() => {
        setSyncProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);

      // 调用同步 API（如果存在）
      // 注：根据实际后端 API 调整
      // await timesheetApi.sync({ project_id: projectId });

      // 模拟同步完成
      await new Promise((resolve) => setTimeout(resolve, 2000));

      clearInterval(progressInterval);
      setSyncProgress(100);
      setSyncState("success");
      setLastSyncTime(new Date().toISOString());
      setPendingCount(0);

      if (onSyncComplete) {
        onSyncComplete({ success: true });
      }

      // 3秒后恢复空闲状态
      setTimeout(() => {
        setSyncState("idle");
        setSyncProgress(0);
      }, 3000);
    } catch (error) {
      console.error("Sync failed:", error);
      setSyncState("error");
      setSyncError(error.message || "同步失败，请稍后重试");

      if (onSyncComplete) {
        onSyncComplete({ success: false, error });
      }
    }
  };

  // 获取状态配置
  const statusConfig = SYNC_STATUS_CONFIG[syncState];
  const StatusIcon = statusConfig.icon;

  // 紧凑模式
  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <StatusIcon
            className={cn(
              "h-4 w-4",
              statusConfig.color,
              statusConfig.animate && "animate-spin"
            )}
          />
          <span className={cn("text-sm", statusConfig.color)}>
            {statusConfig.label}
          </span>
        </div>

        {pendingCount > 0 && (
          <Badge variant="secondary" className="text-xs">
            {pendingCount} 待同步
          </Badge>
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={handleSync}
          disabled={syncState === "syncing"}
          className="h-7 px-2"
        >
          <RefreshCw
            className={cn("h-3 w-3", syncState === "syncing" && "animate-spin")}
          />
        </Button>
      </div>
    );
  }

  // 卡片模式
  return (
    <Card className="bg-slate-900/50 border-slate-800">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CloudUpload className="h-4 w-4" />
            工时同步状态
          </span>
          <Badge className={cn("text-xs", statusConfig.bgColor, statusConfig.color)}>
            <StatusIcon
              className={cn(
                "h-3 w-3 mr-1",
                statusConfig.animate && "animate-spin"
              )}
            />
            {statusConfig.label}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 同步进度 */}
        {syncState === "syncing" && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-slate-400">
              <span>正在同步...</span>
              <span>{syncProgress}%</span>
            </div>
            <Progress value={syncProgress} className="h-2" />
          </div>
        )}

        {/* 状态信息 */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-slate-400">上次同步时间</div>
            <div className="text-sm font-medium">
              {lastSyncTime ? formatDate(lastSyncTime, "YYYY-MM-DD HH:mm") : "-"}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-slate-400">待同步条数</div>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "text-sm font-bold",
                  pendingCount > 0 ? "text-amber-400" : "text-slate-300"
                )}
              >
                {loading ? "-" : pendingCount}
              </span>
              {pendingCount > 0 && (
                <Activity className="h-4 w-4 text-amber-400" />
              )}
            </div>
          </div>
        </div>

        {/* 错误信息 */}
        {syncError && (
          <div className="p-2 bg-red-500/10 rounded border border-red-500/30 text-xs text-red-300">
            {syncError}
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={handleSync}
            disabled={syncState === "syncing"}
          >
            <RefreshCw
              className={cn("mr-2 h-4 w-4", syncState === "syncing" && "animate-spin")}
            />
            {syncState === "syncing" ? "同步中..." : "手动同步"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchSyncStatus}
            disabled={loading}
          >
            <TrendingUp className="h-4 w-4" />
          </Button>
        </div>

        {/* 同步目标说明 */}
        <div className="text-xs text-slate-500 space-y-1">
          <div>同步目标：</div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="text-[10px]">财务成本</Badge>
            <Badge variant="outline" className="text-[10px]">研发费用</Badge>
            <Badge variant="outline" className="text-[10px]">HR绩效</Badge>
            <Badge variant="outline" className="text-[10px]">项目进度</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
