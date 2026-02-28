/**
 * Service Ticket Stats Component
 * 服务工单统计卡片组件
 */
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { 
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Star,
  Timer,
  Activity
} from "lucide-react";
import { 
  statusConfigs, 
  urgencyConfigs,
  calculateTicketStats
} from "@/lib/constants/service";

export function ServiceTicketStats({ tickets = [], stats: externalStats = null }) {
  // 计算统计数据
  const stats = externalStats || calculateTicketStats(tickets);

  const cardConfigs = [
    {
      title: "总工单数",
      value: stats.total,
      icon: Activity,
      color: "text-blue-600",
      bgColor: "bg-blue-50 dark:bg-blue-900/20",
      borderColor: "border-blue-200 dark:border-blue-800",
      description: "系统中所有工单"
    },
    {
      title: "待分配",
      value: stats.pending,
      icon: Clock,
      color: "text-slate-600",
      bgColor: "bg-slate-50 dark:bg-slate-900/20",
      borderColor: "border-slate-200 dark:border-slate-800",
      description: "等待分配的工单"
    },
    {
      title: "处理中",
      value: stats.inProgress,
      icon: Timer,
      color: "text-blue-600",
      bgColor: "bg-blue-50 dark:bg-blue-900/20",
      borderColor: "border-blue-200 dark:border-blue-800",
      description: "正在处理的工单"
    },
    {
      title: "待验证",
      value: stats.pendingVerify,
      icon: CheckCircle2,
      color: "text-amber-600",
      bgColor: "bg-amber-50 dark:bg-amber-900/20",
      borderColor: "border-amber-200 dark:border-amber-800",
      description: "等待客户验证"
    }
  ];

  const urgentCards = [
    {
      title: "已关闭",
      value: stats.closed,
      icon: CheckCircle2,
      color: "text-emerald-600",
      bgColor: "bg-emerald-50 dark:bg-emerald-900/20",
      borderColor: "border-emerald-200 dark:border-emerald-800",
      description: "已成功关闭的工单"
    },
    {
      title: "紧急工单",
      value: stats.urgent,
      icon: AlertTriangle,
      color: "text-red-600",
      bgColor: "bg-red-50 dark:bg-red-900/20",
      borderColor: "border-red-200 dark:border-red-800",
      description: "需要优先处理"
    },
    {
      title: "高优先级",
      value: stats.high,
      icon: TrendingUp,
      color: "text-orange-600",
      bgColor: "bg-orange-50 dark:bg-orange-900/20",
      borderColor: "border-orange-200 dark:border-orange-800",
      description: "重要工单"
    },
    {
      title: "平均解决时间",
      value: `${Math.round(stats.avgResolutionTime)}h`,
      icon: Clock,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50 dark:bg-indigo-900/20",
      borderColor: "border-indigo-200 dark:border-indigo-800",
      description: "工单平均处理时长"
    }
  ];

  const satisfactionCards = [
    {
      title: "客户满意度",
      value: stats.satisfactionScore.toFixed(1),
      icon: Star,
      color: "text-yellow-600",
      bgColor: "bg-yellow-50 dark:bg-yellow-900/20",
      borderColor: "border-yellow-200 dark:border-yellow-800",
      description: "客户评分（满分5.0）",
      showStars: true,
      rating: stats.satisfactionScore
    },
    {
      title: "关闭率",
      value: `${stats.total > 0 ? Math.round((stats.closed / stats.total) * 100) : 0}%`,
      icon: CheckCircle2,
      color: "text-green-600",
      bgColor: "bg-green-50 dark:bg-green-900/20",
      borderColor: "border-green-200 dark:border-green-800",
      description: "工单关闭成功率"
    }
  ];

  return (
    <div className="space-y-6">
      {/* 主要统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cardConfigs.map((config, index) => {
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

      {/* 次要统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {urgentCards.map((config, index) => {
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

      {/* 满意度和关闭率 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {satisfactionCards.map((config, index) => {
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
                <div className="flex items-center gap-3">
                  <div className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                    {config.value}
                  </div>
                  {config.showStars && (
                    <div className="flex items-center gap-1">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <Star
                          key={i}
                          className={`w-4 h-4 ${
                            i <= Math.floor(config.rating)
                              ? "fill-yellow-400 text-yellow-400"
                              : "text-slate-300"
                          }`}
                        />
                      ))}
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
            工单状态分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {Object.entries(statusConfigs).map(([key, config]) => {
              const count = tickets.filter(ticket => ticket.status === key).length;
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

      {/* 紧急程度分布 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-slate-600" />
            紧急程度分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-3 gap-4">
            {Object.entries(urgencyConfigs).map(([key, config]) => {
              const count = tickets.filter(ticket => ticket.urgency === key).length;
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