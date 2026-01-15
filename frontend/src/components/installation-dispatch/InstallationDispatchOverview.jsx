import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  CalendarDays, 
  Users, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  UserCheck,
  Timer,
  TrendingUp
} from 'lucide-react';
import {
  DISPATCH_STATUS,
  DISPATCH_STATUS_LABELS,
  DISPATCH_STATUS_COLORS,
  TECHNICIAN_STATUS,
  TECHNICIAN_STATUS_COLORS,
  calculateCompletionRate,
  calculateDelayRate,
  getDispatchStatusStats,
  getTechnicianStatusStats
} from './installationDispatchConstants';

const InstallationDispatchOverview = ({ 
  dispatches = [], 
  technicians = [], 
  onQuickAction 
}) => {
  const [stats, setStats] = useState({
    totalDispatches: 0,
    pendingDispatches: 0,
    inProgressDispatches: 0,
    completedDispatches: 0,
    delayedDispatches: 0,
    availableTechnicians: 0
  });

  const [completionRate, setCompletionRate] = useState(0);
  const [delayRate, setDelayRate] = useState(0);

  useEffect(() => {
    if (dispatches.length > 0) {
      const dispatchStats = getDispatchStatusStats(dispatches);
      const technicianStats = getTechnicianStatusStats(technicians);
      
      setStats({
        totalDispatches: dispatchStats.total,
        pendingDispatches: dispatchStats.pending,
        inProgressDispatches: dispatchStats.inProgress,
        completedDispatches: dispatchStats.completed,
        delayedDispatches: dispatchStats.delayed,
        availableTechnicians: technicianStats.available
      });

      setCompletionRate(calculateCompletionRate(dispatchStats.completed, dispatchStats.total));
      setDelayRate(calculateDelayRate(dispatchStats.delayed, dispatchStats.total));
    }
  }, [dispatches, technicians]);

  const pendingToday = dispatches.filter(dispatch => 
    dispatch.status === DISPATCH_STATUS.PENDING &&
    new Date(dispatch.scheduledDate).toDateString() === new Date().toDateString()
  ).length;

  const urgentTasks = dispatches.filter(dispatch => 
    dispatch.priority === 'high' && 
    dispatch.status !== DISPATCH_STATUS.COMPLETED
  ).length;

  const overdueTasks = dispatches.filter(dispatch => {
    const scheduledDate = new Date(dispatch.scheduledDate);
    const now = new Date();
    return scheduledDate < now && dispatch.status !== DISPATCH_STATUS.COMPLETED;
  }).length;

  return (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总派工单</CardTitle>
            <CalendarDays className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalDispatches}</div>
            <p className="text-xs text-muted-foreground">
              待派工: {stats.pendingDispatches}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">进行中</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.inProgressDispatches}</div>
            <p className="text-xs text-muted-foreground">
              今日到期: {pendingToday}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">已完成</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.completedDispatches}</div>
            <p className="text-xs text-muted-foreground">
              完成率: {completionRate}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">可用技术人员</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.availableTechnicians}</div>
            <p className="text-xs text-muted-foreground">
              总技术人员: {technicians.length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 状态分布分析 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>派工状态分布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(DISPATCH_STATUS).map(([key, value]) => {
                const count = stats[`${key.toLowerCase()}Dispatches`] || 0;
                const percentage = stats.totalDispatches > 0 ? (count / stats.totalDispatches * 100).toFixed(1) : 0;
                
                return (
                  <div key={value} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: DISPATCH_STATUS_COLORS[value] }}
                      />
                      <span className="text-sm">{DISPATCH_STATUS_LABELS[value]}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary">{count}</Badge>
                      <span className="text-xs text-muted-foreground">{percentage}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>紧急任务提醒</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium">超期任务</span>
                </div>
                <Badge variant="destructive">{overdueTasks}</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Timer className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">高优先级任务</span>
                </div>
                <Badge variant="secondary">{urgentTasks}</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium">今日待派工</span>
                </div>
                <Badge variant="outline">{pendingToday}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 快速操作 */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button 
              variant="outline" 
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('createDispatch')}
            >
              <CalendarDays className="h-6 w-6" />
              <span className="text-sm">新建派工</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('viewPending')}
            >
              <Clock className="h-6 w-6" />
              <span className="text-sm">待派工列表</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('viewOverdue')}
            >
              <AlertTriangle className="h-6 w-6" />
              <span className="text-sm">超期任务</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('technicianSchedule')}
            >
              <Users className="h-6 w-6" />
              <span className="text-sm">人员排班</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 统计指标 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">完成率</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{completionRate}%</div>
            <p className="text-xs text-muted-foreground">
              已完成 {stats.completedDispatches} / {stats.totalDispatches}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">延期率</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{delayRate}%</div>
            <p className="text-xs text-muted-foreground">
              延期 {stats.delayedDispatches} / {stats.totalDispatches}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均任务数</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {technicians.length > 0 ? (stats.totalDispatches / technicians.length).toFixed(1) : 0}
            </div>
            <p className="text-xs text-muted-foreground">
              每人平均任务数
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InstallationDispatchOverview;