/**
 * Service Statistics Card Component
 * 客户服务统计卡片组件
 */
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Activity,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Users,
  Star,
  Timer,
  Phone,
  MessageSquare,
  Mail,
  Building2,
  Ticket,
  AlertCircle,
  Target
} from "lucide-react";
import {
  servicePriorityConfigs,
  serviceStatusConfigs,
  calculateServiceStats
} from "../../lib/constants/service";

export function ServiceStatsCard({ tickets = [], stats: externalStats = null }) {
  // 计算统计数据
  const stats = externalStats || calculateServiceStats(tickets);

  // 主要统计卡片
  const primaryCards = [
    {
      title: "总服务工单",
      value: stats.total,
      icon: Ticket,
      color: "text-blue-600",
      bgColor: "bg-blue-50 dark:bg-blue-900/20",
      borderColor: "border-blue-200 dark:border-blue-800",
      description: "系统中的所有服务工单"
    },
    {
      title: "处理中",
      value: stats.inProgress + stats.assigned,
      icon: Clock,
      color: "text-amber-600",
      bgColor: "bg-amber-50 dark:bg-amber-900/20",
      borderColor: "border-amber-200 dark:border-amber-800",
      description: "正在处理的工单"
    },
    {
      title: "等待回复",
      value: stats.awaitingResponse,
      icon: MessageSquare,
      color: "text-orange-600",
      bgColor: "bg-orange-50 dark:bg-orange-900/20",
      borderColor: "border-orange-200 dark:border-orange-800",
      description: "等待客户回复的工单"
    },
    {
      title: "已解决",
      value: stats.resolved,
      icon: CheckCircle2,
      color: "text-green-600",
      bgColor: "bg-green-50 dark:bg-green-900/20",
      borderColor: "border-green-200 dark:border-blue-800",
      description: "已成功解决的工单"
    }
  ];

  // 紧急程度卡片
  const priorityCards = [
    {
      title: "严重",
      value: stats.urgent,
      icon: AlertCircle,
      color: "text-red-700",
      bgColor: "bg-red-100 dark:bg-red-900/30",
      borderColor: "border-red-300 dark:border-red-700",
      description: "需要立即处理"
    },
    {
      title: "高优先级",
      value: stats.high,
      icon: AlertTriangle,
      color: "text-orange-600",
      bgColor: "bg-orange-100 dark:bg-orange-900/30",
      borderColor: "border-orange-300 dark:border-orange-700",
      description: "重要工单"
    },
    {
      title: "平均解决时间",
      value: `${stats.avgResolutionTime}h`,
      icon: Timer,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50 dark:bg-indigo-900/20",
      borderColor: "border-indigo-200 dark:border-indigo-800",
      description: "工单平均处理时长"
    },
    {
      title: "已关闭",
      value: stats.closed,
      icon: Building2,
      color: "text-slate-600",
      bgColor: "bg-slate-50 dark:bg-slate-900/20",
      borderColor: "border-slate-200 dark:border-slate-800",
      description: "已关闭的工单"
    }
  ];

  // 满意度指标卡片
  const satisfactionCards = [
    {
      title: "客户满意度",
      value: `${stats.satisfactionRate}%`,
      icon: Star,
      color: "text-yellow-600",
      bgColor: "bg-yellow-50 dark:bg-yellow-900/20",
      borderColor: "border-yellow-200 dark:border-yellow-800",
      description: "客户满意度率",
      showProgress: true,
      progress: stats.satisfactionRate,
      target: 90
    },
    {
      title: "升级率",
      value: `${stats.escalationRate}%`,
      icon: AlertCircle,
      color: "text-red-600",
      bgColor: "bg-red-50 dark:bg-red-900/20",
      borderColor: "border-red-200 dark:border-red-800",
      description: "工单升级比例",
      showProgress: true,
      progress: stats.escalationRate,
      target: 5,
      isInverse: true
    }
  ];

  return (
    <div className="space-y-6">
      {/* 主要统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {(primaryCards || []).map((config, index) => {
          const Icon = config.icon;
          return (
            <Card
              key={index}
              className={`${config.borderColor} border-l-4 hover:shadow-lg transition-all duration-200`}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  {config.title}
                </CardTitle>
                <div className={`${config.bgColor} p-2 rounded-lg`}>
                  <Icon className={`w-4 h-4 ${config.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {config.value.toLocaleString()}
                </div>
                {config.description && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {config.description}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 紧急程度卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {(priorityCards || []).map((config, index) => {
          const Icon = config.icon;
          return (
            <Card
              key={index}
              className={`${config.borderColor} border-l-4 hover:shadow-md transition-all duration-200`}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  {config.title}
                </CardTitle>
                <div className={`${config.bgColor} p-1.5 rounded-md`}>
                  <Icon className={`w-3.5 h-3.5 ${config.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                  {config.value.toLocaleString()}
                </div>
                {config.description && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {config.description}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 满意度和升级率 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(satisfactionCards || []).map((config, index) => {
          const Icon = config.icon;
          return (
            <Card
              key={index}
              className={`${config.borderColor} border-l-4 hover:shadow-md transition-all duration-200`}
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                  {config.title}
                </CardTitle>
                <div className={`${config.bgColor} p-1.5 rounded-md`}>
                  <Icon className={`w-3.5 h-3.5 ${config.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                    {config.value}
                  </div>
                  {config.showProgress && (
                    <div className="flex flex-col items-end">
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        目标 {config.target}{config.isInverse ? '' : '%'}
                      </div>
                      <div className="w-16 h-2 bg-slate-200 dark:bg-slate-700 rounded-full mt-1 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            config.progress >= config.target
                              ? 'bg-green-500'
                              : config.progress >= config.target * 0.8
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                          }`}
                          style={{
                            width: `${Math.min(config.progress, config.target)}%`,
                            transform: config.isInverse ? 'scaleX(-1)' : 'none',
                            transformOrigin: 'right'
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
                {config.description && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {config.description}
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 状态分布概览 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-slate-600" />
            服务状态分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.entries(serviceStatusConfigs).map(([key, config]) => {
              const count = (tickets || []).filter(ticket => ticket.status === key).length;
              if (count === 0) {return null;}

              return (
                <div key={key} className="text-center">
                  <div className={`${config.color} w-3 h-3 rounded-full mx-auto mb-2`} />
                  <div className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {count}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center justify-center gap-1">
                    <span>{config.icon}</span>
                    {config.label}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 优先级分布 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-slate-600" />
            优先级分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.entries(servicePriorityConfigs).map(([key, config]) => {
              const count = (tickets || []).filter(ticket => ticket.priority === key).length;
              if (count === 0) {return null;}

              return (
                <div key={key} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                  <div className={`${config.bg} p-2 rounded`}>
                    <span className="text-lg">{config.icon}</span>
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-slate-100">
                      {count}
                    </div>
                    <div className="text-sm text-slate-500 dark:text-slate-400">
                      {config.label}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}