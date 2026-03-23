/**
 * 滞留预警组件 (Dwell Time Alerts)
 *
 * 显示销售漏斗中滞留时间超标的实体，帮助销售经理及时跟进。
 */

import { useEffect, useState } from "react";



import { funnelApi } from "../../../../services/api/funnel";
import { cn } from "../../../../lib/utils";
import {
  AlertTriangle,
  Clock,
  Eye,
} from "lucide-react";

// 实体类型中文映射
const ENTITY_TYPE_MAP = {
  LEAD: "线索",
  OPPORTUNITY: "商机",
  QUOTE: "报价",
  CONTRACT: "合同",
};

// 严重程度配置
const SEVERITY_CONFIG = {
  CRITICAL: {
    label: "紧急",
    color: "bg-red-500",
    textColor: "text-red-600",
    bgColor: "bg-red-50",
    icon: AlertTriangle,
  },
  WARNING: {
    label: "警告",
    color: "bg-yellow-500",
    textColor: "text-yellow-600",
    bgColor: "bg-yellow-50",
    icon: Clock,
  },
  INFO: {
    label: "提醒",
    color: "bg-blue-500",
    textColor: "text-blue-600",
    bgColor: "bg-blue-50",
    icon: Eye,
  },
};

// 默认数据
const defaultAlerts = [];

export default function DwellTimeAlerts({ onAlertClick }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // 加载预警数据
  const loadAlerts = async () => {
    try {
      const [alertsRes, statsRes] = await Promise.all([
        funnelApi.getDwellTimeAlerts({ status: "ACTIVE", limit: 10 }),
        funnelApi.getStatistics(),
      ]);

      const alertItems = alertsRes.formatted?.items || alertsRes.data?.items || [];
      setAlerts(alertItems);
      setStats(statsRes.formatted || statsRes.data || null);
    } catch (_err) {
      setAlerts(defaultAlerts);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAlerts();
    setRefreshing(false);
  };

  // 确认预警
  const handleAcknowledge = async (alertId, e) => {
    e.stopPropagation();
    try {
      await funnelApi.acknowledgeAlert(alertId);
      // 更新本地状态
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: "ACKNOWLEDGED" } : a))
      );
    } catch (_err) {
      // 非关键操作失败时静默降级
    }
  };

  // 解决预警
  const handleResolve = async (alertId, e) => {
    e.stopPropagation();
    try {
      await funnelApi.resolveAlert(alertId, "已处理");
      // 从列表中移除
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch (_err) {
      // 非关键操作失败时静默降级
    }
  };

  // 格式化滞留时间
  const formatDwellTime = (hours) => {
    if (hours < 24) {
      return `${hours}小时`;
    }
    const days = Math.floor(hours / 24);
    const remainingHours = hours % 24;
    return remainingHours > 0 ? `${days}天${remainingHours}小时` : `${days}天`;
  };

  // 获取统计摘要
  const getStatsSummary = () => {
    if (!stats?.by_severity) return null;
    const critical = stats.by_severity.CRITICAL || 0;
    const warning = stats.by_severity.WARNING || 0;
    const info = stats.by_severity.INFO || 0;
    return { critical, warning, info, total: critical + warning + info };
  };

  const statsSummary = getStatsSummary();

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-orange-500" />
            滞留预警
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="h-7 w-7 p-0"
          >
            <RefreshCw
              className={cn("h-4 w-4", refreshing && "animate-spin")}
            />
          </Button>
        </div>
        {/* 统计摘要 */}
        {statsSummary && statsSummary.total > 0 && (
          <div className="flex gap-2 mt-2">
            {statsSummary.critical > 0 && (
              <Badge variant="destructive" className="text-xs">
                紧急 {statsSummary.critical}
              </Badge>
            )}
            {statsSummary.warning > 0 && (
              <Badge variant="warning" className="text-xs bg-yellow-100 text-yellow-800">
                警告 {statsSummary.warning}
              </Badge>
            )}
            {statsSummary.info > 0 && (
              <Badge variant="secondary" className="text-xs">
                提醒 {statsSummary.info}
              </Badge>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-16 bg-muted/50 rounded-lg animate-pulse"
              />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
            <p className="text-sm">暂无滞留预警</p>
            <p className="text-xs mt-1">所有单据流转正常</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {alerts.map((alert) => {
              const severityConfig = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.INFO;
              const SeverityIcon = severityConfig.icon;

              return (
                <div
                  key={alert.id}
                  className={cn(
                    "p-3 rounded-lg border cursor-pointer hover:shadow-sm transition-shadow",
                    severityConfig.bgColor
                  )}
                  onClick={() => onAlertClick?.(alert)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2 flex-1 min-w-0">
                      <SeverityIcon
                        className={cn("h-4 w-4 mt-0.5 shrink-0", severityConfig.textColor)}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">
                            {ENTITY_TYPE_MAP[alert.entity_type] || alert.entity_type}
                          </span>
                          <span className="text-muted-foreground text-xs">
                            #{alert.entity_id}
                          </span>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {alert.stage && <span className="mr-2">{alert.stage}</span>}
                          <span className={cn("font-medium", severityConfig.textColor)}>
                            滞留 {formatDwellTime(alert.dwell_hours)}
                          </span>
                          <span className="ml-1">(阈值 {formatDwellTime(alert.threshold_hours)})</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {alert.status === "ACTIVE" && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs"
                            onClick={(e) => handleAcknowledge(alert.id, e)}
                          >
                            确认
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2 text-xs text-green-600 hover:text-green-700"
                            onClick={(e) => handleResolve(alert.id, e)}
                          >
                            解决
                          </Button>
                        </>
                      )}
                      {alert.status === "ACKNOWLEDGED" && (
                        <Badge variant="outline" className="text-xs">
                          已确认
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
