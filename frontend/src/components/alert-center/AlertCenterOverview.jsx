/**
 * Alert Center Overview Component - 预警中心概览组件
 * 显示预警的关键指标和快速操作入口
 */
import React, { useMemo } from "react";
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Bell,
  Activity,
  BarChart3,
  Eye,
  Settings,
  RefreshCw } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Progress } from "../ui/progress";
import {
  ALERT_LEVELS,
  ALERT_STATUS,
  ALERT_TYPES,
  getAlertLevelConfig,
  getAlertStatusConfig,
  getAlertTypeConfig,
  getAlertSummary as _getAlertSummary,
  isBusinessHour,
  formatAlertTime,
  requiresEscalation } from
"@/lib/constants/alertCenter";

const AlertCenterOverview = ({
  alerts,
  stats,
  onQuickAction
}) => {
  // 计算高级统计数据
  const advancedStats = useMemo(() => {
    if (!alerts || alerts.length === 0) {
      return {
        levelDistribution: {},
        statusDistribution: {},
        typeDistribution: {},
        slaCompliance: { response: 0, resolution: 0 },
        businessHourStats: { business: 0, afterHours: 0 },
        recentTrends: { today: 0, yesterday: 0, week: 0 },
        priorityAlerts: []
      };
    }

    // 预警级别分布
    const levelDistribution = alerts.reduce((acc, alert) => {
      const level = alert.alert_level || 'INFO';
      const levelConfig = getAlertLevelConfig(level);
      acc[levelConfig.label] = (acc[levelConfig.label] || 0) + 1;
      return acc;
    }, {});

    // 状态分布
    const statusDistribution = alerts.reduce((acc, alert) => {
      const status = alert.status || 'PENDING';
      const statusConfig = getAlertStatusConfig(status);
      acc[statusConfig.label] = (acc[statusConfig.label] || 0) + 1;
      return acc;
    }, {});

    // 类型分布
    const typeDistribution = alerts.reduce((acc, alert) => {
      const type = alert.alert_type || 'SYSTEM';
      const typeConfig = getAlertTypeConfig(type);
      acc[typeConfig.label] = (acc[typeConfig.label] || 0) + 1;
      return acc;
    }, {});

    // SLA合规性检查
    const responseSLA = alerts.reduce((acc, alert) => {
      if (alert.first_action_time) {
        const responseTime = (new Date(alert.first_action_time) - new Date(alert.created_time)) / (1000 * 60);
        const levelConfig = getAlertLevelConfig(alert.alert_level);
        const targetTime = levelConfig.level === 5 ? 5 : levelConfig.level === 4 ? 30 : 120;

        if (responseTime <= targetTime) {
          acc.compliant += 1;
        } else {
          acc.total += 1;
        }
      }
      return acc;
    }, { compliant: 0, total: 0 });

    const resolutionSLA = alerts.filter((a) => a.resolved_time).reduce((acc, alert) => {
      const resolutionTime = (new Date(alert.resolved_time) - new Date(alert.created_time)) / (1000 * 60 * 60);
      const levelConfig = getAlertLevelConfig(alert.alert_level);
      const targetTime = levelConfig.level === 5 ? 1 : levelConfig.level === 4 ? 4 : 24;

      if (resolutionTime <= targetTime) {
        acc.compliant += 1;
      } else {
        acc.total += 1;
      }
      return acc;
    }, { compliant: 0, total: 0 });

    // 工作时间统计
    const businessHourStats = alerts.reduce((acc, alert) => {
      if (isBusinessHour(alert.created_time)) {
        acc.business += 1;
      } else {
        acc.afterHours += 1;
      }
      return acc;
    }, { business: 0, afterHours: 0 });

    // 趋势统计
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekStart = new Date(today);
    weekStart.setDate(weekStart.getDate() - 7);

    const recentTrends = {
      today: alerts.filter((a) => new Date(a.created_time) >= today).length,
      yesterday: alerts.filter((a) => {
        const alertDate = new Date(a.created_time);
        return alertDate >= yesterday && alertDate < today;
      }).length,
      week: alerts.filter((a) => new Date(a.created_time) >= weekStart).length
    };

    // 需要紧急处理的预警
    const priorityAlerts = alerts.
    filter((alert) => {
      const levelConfig = getAlertLevelConfig(alert.alert_level);
      return levelConfig.level >= 4 && alert.status === 'PENDING';
    }).
    slice(0, 5).
    map((alert) => ({
      ...alert,
      needsEscalation: requiresEscalation(alert),
      timeDisplay: formatAlertTime(alert.created_time)
    }));

    return {
      levelDistribution,
      statusDistribution,
      typeDistribution,
      slaCompliance: {
        response: responseSLA.total > 0 ? Math.round(responseSLA.compliant / (responseSLA.compliant + responseSLA.total) * 100) : 100,
        resolution: resolutionSLA.total > 0 ? Math.round(resolutionSLA.compliant / (resolutionSLA.compliant + resolutionSLA.total) * 100) : 100
      },
      businessHourStats,
      recentTrends,
      priorityAlerts
    };
  }, [alerts]);

  return (
    <div className="space-y-6">
      {/* 核心指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">总预警数</div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats?.total || 0}
                </div>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">待处理</div>
                <div className="text-2xl font-bold text-amber-600">
                  {stats?.pending || 0}
                </div>
              </div>
              <Clock className="h-8 w-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">已解决</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {stats?.resolved || 0}
                </div>
              </div>
              <CheckCircle2 className="h-8 w-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">响应SLA</div>
                <div className="text-2xl font-bold text-blue-600">
                  {advancedStats.slaCompliance.response}%
                </div>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-600 mb-1">今日新增</div>
                <div className="text-2xl font-bold text-purple-600">
                  {advancedStats.recentTrends.today}
                </div>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 预警分析概览 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 预警级别分布 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertCircle className="h-4 w-4" />
              预警级别分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(advancedStats.levelDistribution).map(([level, count]) => {
                const levelConfig = getAlertLevelConfig(Object.keys(ALERT_LEVELS).find((key) =>
                ALERT_LEVELS[key].label === level
                ) || 'INFO');
                const total = alerts?.length || 1;
                const percentage = Math.round(count / total * 100);

                return (
                  <div key={level} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${levelConfig.color}`} />
                      <span className="text-sm text-gray-700">{level}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className={`${levelConfig.color} h-2 rounded-full`}
                          style={{ width: `${percentage}%` }} />

                      </div>
                      <span className="text-xs text-gray-500 w-8">{count}</span>
                    </div>
                  </div>);

              })}
              {Object.keys(advancedStats.levelDistribution).length === 0 &&
              <div className="text-center text-gray-500 py-4">
                  暂无预警数据
              </div>
              }
            </div>
          </CardContent>
        </Card>

        {/* SLA合规性 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Activity className="h-4 w-4" />
              SLA合规性
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">响应时间SLA</span>
                  <span className="text-sm font-bold">{advancedStats.slaCompliance.response}%</span>
                </div>
                <Progress
                  value={advancedStats.slaCompliance.response}
                  className="h-2"
                  color={advancedStats.slaCompliance.response >= 95 ? "emerald" :
                  advancedStats.slaCompliance.response >= 80 ? "amber" : "red"} />

              </div>
              
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">解决时间SLA</span>
                  <span className="text-sm font-bold">{advancedStats.slaCompliance.resolution}%</span>
                </div>
                <Progress
                  value={advancedStats.slaCompliance.resolution}
                  className="h-2"
                  color={advancedStats.slaCompliance.resolution >= 90 ? "emerald" :
                  advancedStats.slaCompliance.resolution >= 75 ? "amber" : "red"} />

              </div>
            </div>
          </CardContent>
        </Card>

        {/* 紧急预警 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="h-4 w-4" />
              紧急预警
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {advancedStats.priorityAlerts.map((alert, index) => {
                const levelConfig = getAlertLevelConfig(alert.alert_level);

                return (
                  <div key={index} className="flex items-center justify-between p-2 bg-slate-500/10 border border-slate-500/20 rounded">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium truncate text-slate-200">
                        {alert.title || alert.alert_type}
                      </div>
                      <div className="text-xs text-slate-500">
                        {alert.timeDisplay}
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Badge className={levelConfig.color} variant="secondary">
                        {levelConfig.label}
                      </Badge>
                      {alert.needsEscalation &&
                      <Badge className="bg-red-500" variant="secondary">
                          需升级
                      </Badge>
                      }
                    </div>
                  </div>);

              })}
              {advancedStats.priorityAlerts.length === 0 &&
              <div className="text-center text-slate-500 py-4">
                  暂无紧急预警
              </div>
              }
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 工作时间统计 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Clock className="h-4 w-4" />
              工作时间分布
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">工作时间</span>
                <span className="text-lg font-semibold">
                  {advancedStats.businessHourStats.business}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">非工作时间</span>
                <span className="text-lg font-semibold text-amber-600">
                  {advancedStats.businessHourStats.afterHours}
                </span>
              </div>
              <div className="pt-2 border-t">
                <div className="text-sm text-gray-600">
                  工作时间占比
                </div>
                <div className="text-lg font-semibold">
                  {alerts?.length > 0 ?
                  Math.round(advancedStats.businessHourStats.business / alerts.length * 100) :
                  0}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 趋势分析 */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="h-4 w-4" />
              预警趋势
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">今日预警</span>
                <span className="text-lg font-semibold">
                  {advancedStats.recentTrends.today}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">昨日预警</span>
                <span className="text-lg font-semibold">
                  {advancedStats.recentTrends.yesterday}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">本周预警</span>
                <span className="text-lg font-semibold">
                  {advancedStats.recentTrends.week}
                </span>
              </div>
              <div className="pt-2 border-t">
                <div className="text-sm text-gray-600">
                  日变化率
                </div>
                <div className={`text-lg font-semibold ${
                advancedStats.recentTrends.today > advancedStats.recentTrends.yesterday ?
                'text-red-600' : 'text-emerald-600'}`
                }>
                  {advancedStats.recentTrends.yesterday > 0 ?
                  Math.round((advancedStats.recentTrends.today - advancedStats.recentTrends.yesterday) / advancedStats.recentTrends.yesterday * 100) :
                  0}%
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 快速操作 */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => onQuickAction && onQuickAction('createAlert')}>

              <AlertTriangle className="h-4 w-4 mr-2" />
              创建预警
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onQuickAction && onQuickAction('manageRules')}>

              <Settings className="h-4 w-4 mr-2" />
              规则管理
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onQuickAction && onQuickAction('notificationSettings')}>

              <Bell className="h-4 w-4 mr-2" />
              通知设置
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => onQuickAction && onQuickAction('exportReport')}>

              <Eye className="h-4 w-4 mr-2" />
              导出报表
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* SLA提醒 */}
      {(advancedStats.slaCompliance.response < 90 || advancedStats.slaCompliance.resolution < 85) &&
      <Card className="border-red-500/30 bg-red-500/10">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="space-y-1">
                {advancedStats.slaCompliance.response < 90 &&
              <p className="text-sm text-red-300">
                    响应时间SLA达标率偏低 ({advancedStats.slaCompliance.response}%)，建议加强响应时效管理
              </p>
              }
                {advancedStats.slaCompliance.resolution < 85 &&
              <p className="text-sm text-red-300">
                    解决时间SLA达标率偏低 ({advancedStats.slaCompliance.resolution}%)，请关注解决效率提升
              </p>
              }
              </div>
            </div>
          </CardContent>
      </Card>
      }
    </div>);

};

export default AlertCenterOverview;