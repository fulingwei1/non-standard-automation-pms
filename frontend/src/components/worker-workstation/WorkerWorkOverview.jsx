/**
 * Worker Work Overview Component - 工人工作概览组件
 * 显示工人的关键指标和快速操作入口
 */
import { useMemo } from "react";
import { 
  Wrench, 
  TrendingUp,
  Target,
  Award,
  AlertTriangle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Progress } from "../ui/progress";
import { 
  WORK_ORDER_STATUS, 
  SKILL_LEVELS,
  PERFORMANCE_METRICS,
  calculateProgress,
  formatWorkHours,
  getQualityLevel,
  getNextAvailableActions
} from "@/lib/constants/workerWorkstation";

const WorkerWorkOverview = ({ 
  worker, 
  workOrders, 
  reports, 
  performance,
  onQuickAction 
}) => {
  // 计算关键指标
  const stats = useMemo(() => {
    if (!workOrders || !reports) {return {};}

    const today = new Date();
    const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    
    // 今日工单统计
    const todayWorkOrders = workOrders.filter(order => 
      new Date(order.created_time) >= todayStart
    );
    
    // 今日报工统计
    const todayReports = reports.filter(report => 
      new Date(report.created_time) >= todayStart
    );
    
    // 工单状态统计
    const statusStats = workOrders.reduce((acc, order) => {
      acc[order.status] = (acc[order.status] || 0) + 1;
      return acc;
    }, {});
    
    // 计算总体进度
    const totalPlanned = workOrders.reduce((sum, order) => sum + (order.plan_qty || 0), 0);
    const totalCompleted = workOrders.reduce((sum, order) => sum + (order.completed_qty || 0), 0);
    const overallProgress = calculateProgress(totalCompleted, totalPlanned);
    
    // 质量统计
    const totalQualified = workOrders.reduce((sum, order) => sum + (order.qualified_qty || 0), 0);
    const qualityRate = totalCompleted > 0 ? totalQualified / totalCompleted : 0;
    const qualityLevel = getQualityLevel(totalQualified, totalCompleted);
    
    // 工时统计
    const todayWorkHours = todayReports.reduce((sum, report) => sum + (report.work_hours || 0), 0);
    
    return {
      todayOrders: todayWorkOrders.length,
      todayReports: todayReports.length,
      activeOrders: statusStats[WORK_ORDER_STATUS.IN_PROGRESS.label.split('')[0] + 'ED'] || 0,
      pendingOrders: statusStats[WORK_ORDER_STATUS.ASSIGNED.label.split('')[0] + 'ED'] || 0,
      completedOrders: statusStats[WORK_ORDER_STATUS.COMPLETED.label.split('')[0] + 'ED'] || 0,
      overallProgress,
      qualityRate,
      qualityLevel,
      todayWorkHours,
      statusStats
    };
  }, [workOrders, reports]);

  // 获取可用的快速操作
  const quickActions = useMemo(() => {
    if (!workOrders || workOrders.length === 0) {return [];}
    
    // 找到当前可以操作的工单
    const actionableOrders = workOrders.filter(order => {
      const actions = getNextAvailableActions(order);
      return actions.length > 0;
    });
    
    if (actionableOrders.length === 0) {return [];}
    
    const firstOrder = actionableOrders[0];
    const actions = getNextAvailableActions(firstOrder);
    
    return actions.map(action => ({
      ...action,
      orderId: firstOrder.id,
      orderNumber: firstOrder.order_number
    }));
  }, [workOrders]);

  // 技能等级配置
  const skillLevel = worker?.skill_level ? SKILL_LEVELS[worker.skill_level] : SKILL_LEVELS.INTERMEDIATE;

  return (
    <div className="space-y-6">
      {/* 工人基本信息 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Wrench className="h-5 w-5" />
              工作概览
            </span>
            <Badge className={skillLevel.color}>
              {skillLevel.label}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {stats.todayOrders || 0}
              </div>
              <div className="text-sm text-gray-600">今日工单</div>
            </div>
            <div className="text-center p-3 bg-amber-50 rounded-lg">
              <div className="text-2xl font-bold text-amber-600">
                {stats.activeOrders || 0}
              </div>
              <div className="text-sm text-gray-600">进行中</div>
            </div>
            <div className="text-center p-3 bg-emerald-50 rounded-lg">
              <div className="text-2xl font-bold text-emerald-600">
                {Math.round((stats.qualityRate || 0) * 100)}%
              </div>
              <div className="text-sm text-gray-600">质量合格率</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {formatWorkHours(stats.todayWorkHours)}
              </div>
              <div className="text-sm text-gray-600">今日工时</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 工作进度概览 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 工单状态分布 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              工单状态分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.statusStats || {}).map(([status, count]) => {
                const statusConfig = WORK_ORDER_STATUS[status] || WORK_ORDER_STATUS.PENDING;
                const total = workOrders?.length || 1;
                const percentage = Math.round((count / total) * 100);
                
                return (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${statusConfig.color}`} />
                      <span className="text-sm">{statusConfig.label}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{count}</span>
                      <span className="text-xs text-gray-500">({percentage}%)</span>
                    </div>
                  </div>
                );
              })}
              {(!stats.statusStats || Object.keys(stats.statusStats).length === 0) && (
                <div className="text-center text-gray-500 py-4">
                  暂无工单数据
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 质量表现 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5" />
              质量表现
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* 合格率 */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">总体合格率</span>
                  <Badge className={stats.qualityLevel?.color || "bg-gray-500"}>
                    {stats.qualityLevel?.label || "无数据"}
                  </Badge>
                </div>
                <Progress 
                  value={(stats.qualityRate || 0) * 100} 
                  className="h-2"
                />
              </div>
              
              {/* 总体进度 */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">总体进度</span>
                  <span className="text-sm text-gray-600">
                    {stats.overallProgress}%
                  </span>
                </div>
                <Progress 
                  value={stats.overallProgress} 
                  className="h-2"
                />
              </div>
              
              {/* 今日报工 */}
              <div className="pt-2 border-t">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">今日报工次数</span>
                  <span className="text-sm font-medium">
                    {stats.todayReports || 0} 次
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 快速操作 */}
      {quickActions.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              快速操作
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  size="sm"
                  className={`${action.color} text-white hover:opacity-90`}
                  onClick={() => onQuickAction && onQuickAction(action)}
                >
                  {action.label}
                  {action.orderNumber && (
                    <span className="ml-1 text-xs opacity-75">
                      ({action.orderNumber})
                    </span>
                  )}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 绩效概览 */}
      {performance && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              绩效概览
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(PERFORMANCE_METRICS).slice(0, 4).map(([key, config]) => {
                const value = performance[key];
                const displayValue = typeof value === 'number' 
                  ? Math.round(value * 100) 
                  : 0;
                
                return (
                  <div key={key} className="text-center">
                    <div className="text-lg font-semibold text-gray-900">
                      {displayValue}%
                    </div>
                    <div className="text-xs text-gray-600">{config.label}</div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 注意事项 */}
      {(stats.pendingOrders > 5 || stats.qualityRate < 0.95) && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
              <div className="space-y-1">
                {stats.pendingOrders > 5 && (
                  <p className="text-sm text-amber-800">
                    待处理工单较多 ({stats.pendingOrders} 个)，建议及时处理
                  </p>
                )}
                {stats.qualityRate < 0.95 && (
                  <p className="text-sm text-amber-800">
                    质量合格率偏低 ({Math.round(stats.qualityRate * 100)}%)，请加强质量控制
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WorkerWorkOverview;