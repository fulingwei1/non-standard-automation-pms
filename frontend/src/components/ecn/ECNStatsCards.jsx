/**
 * ECN Stats Cards Component
 * ECN统计卡片组件
 */
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { 
  FileText, 
  Clock, 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp,
  Users
} from "lucide-react";
import { statusConfigs } from "@/lib/constants/ecn";

export function ECNStatsCards({ stats = {}, ecns = [] }) {
  // 如果没有传入统计数据，从ecns计算
  const computedStats = stats.total ? stats : {
    total: ecns.length,
    pending: ecns.filter(ecn => 
      ['SUBMITTED', 'EVALUATING', 'PENDING_APPROVAL'].includes(ecn.status)
    ).length,
    inProgress: ecns.filter(ecn => 
      ['EXECUTING', 'PENDING_VERIFY'].includes(ecn.status)
    ).length,
    completed: ecns.filter(ecn => ecn.status === 'COMPLETED').length,
    urgent: ecns.filter(ecn => ecn.priority === 'URGENT').length,
    high: ecns.filter(ecn => ecn.priority === 'HIGH').length,
    // 计算本月新增
    thisMonth: ecns.filter(ecn => {
      const createdDate = new Date(ecn.created_at || ecn.createdAt);
      const now = new Date();
      return createdDate.getMonth() === now.getMonth() && 
             createdDate.getFullYear() === now.getFullYear();
    }).length,
    // 计算本月完成
    thisMonthCompleted: ecns.filter(ecn => {
      const completedDate = new Date(ecn.completed_at || ecn.updatedAt);
      const now = new Date();
      return ecn.status === 'COMPLETED' &&
             completedDate.getMonth() === now.getMonth() && 
             completedDate.getFullYear() === now.getFullYear();
    }).length,
  };

  const finalStats = { ...computedStats, ...stats };

  const cardConfigs = [
    {
      title: "总ECN数",
      value: finalStats.total || 0,
      icon: FileText,
      color: "text-blue-600",
      bgColor: "bg-blue-50 dark:bg-blue-900/20",
      borderColor: "border-blue-200 dark:border-blue-800",
      description: "系统中所有ECN"
    },
    {
      title: "待处理",
      value: finalStats.pending || 0,
      icon: Clock,
      color: "text-amber-600",
      bgColor: "bg-amber-50 dark:bg-amber-900/20",
      borderColor: "border-amber-200 dark:border-amber-800",
      description: "待评估和审批"
    },
    {
      title: "执行中",
      value: finalStats.inProgress || 0,
      icon: AlertTriangle,
      color: "text-purple-600",
      bgColor: "bg-purple-50 dark:bg-purple-900/20",
      borderColor: "border-purple-200 dark:border-purple-800",
      description: "正在执行"
    },
    {
      title: "已完成",
      value: finalStats.completed || 0,
      icon: CheckCircle2,
      color: "text-green-600",
      bgColor: "bg-green-50 dark:bg-green-900/20",
      borderColor: "border-green-200 dark:border-green-800",
      description: "本月完成 " + (finalStats.thisMonthCompleted || 0) + " 个"
    }
  ];

  const urgentCards = [
    {
      title: "紧急ECN",
      value: finalStats.urgent || 0,
      icon: AlertTriangle,
      color: "text-red-600",
      bgColor: "bg-red-50 dark:bg-red-900/20",
      borderColor: "border-red-200 dark:border-red-800"
    },
    {
      title: "高优先级",
      value: finalStats.high || 0,
      icon: TrendingUp,
      color: "text-orange-600",
      bgColor: "bg-orange-50 dark:bg-orange-900/20",
      borderColor: "border-orange-200 dark:border-orange-800"
    },
    {
      title: "本月新增",
      value: finalStats.thisMonth || 0,
      icon: TrendingUp,
      color: "text-indigo-600",
      bgColor: "bg-indigo-50 dark:bg-indigo-900/20",
      borderColor: "border-indigo-200 dark:border-indigo-800"
    },
    {
      title: "参与人数",
      value: finalStats.participants || 0,
      icon: Users,
      color: "text-cyan-600",
      bgColor: "bg-cyan-50 dark:bg-cyan-900/20",
      borderColor: "border-cyan-200 dark:border-cyan-800",
      description: "涉及人员总数"
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

      {/* 状态分布概览 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <FileText className="w-5 h-5 text-slate-600" />
            状态分布概览
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(statusConfigs).map(([key, config]) => {
              const count = ecns.filter(ecn => ecn.status === key).length;
              if (count === 0) {return null;}
              
              return (
                <div key={key} className="text-center">
                  <div className={`${config.color} w-3 h-3 rounded-full mx-auto mb-2`} />
                  <div className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                    {count}
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    {config.label}
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