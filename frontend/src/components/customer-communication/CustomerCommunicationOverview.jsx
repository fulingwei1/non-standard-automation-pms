import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Phone,
  Mail,
  MessageSquare,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Star,
  Calendar,
  BarChart3,
  Filter } from
'lucide-react';
import {
  COMMUNICATION_STATUS,
  COMMUNICATION_STATUS_LABELS,
  COMMUNICATION_STATUS_COLORS,
  COMMUNICATION_TYPE,
  COMMUNICATION_TYPE_LABELS,
  COMMUNICATION_PRIORITY,
  COMMUNICATION_PRIORITY_LABELS,
  COMMUNICATION_TOPIC,
  COMMUNICATION_TOPIC_LABELS,
  CUSTOMER_SATISFACTION,
  CUSTOMER_SATISFACTION_LABELS,
  calculateAverageSatisfaction,
  calculateResponseRate,
  getCommunicationStatusStats,
  getCommunicationTypeStats,
  getTopicDistributionStats,
  getCommunicationTypeIcon } from
'@/lib/constants/customer';

const CustomerCommunicationOverview = ({
  communications = [],
  customers = [],
  onQuickAction
}) => {
  const [stats, setStats] = useState({
    totalCommunications: 0,
    pendingCommunications: 0,
    inProgressCommunications: 0,
    completedCommunications: 0,
    followUpCommunications: 0,
    averageSatisfaction: 0,
    responseRate: 0
  });

  const [typeStats, setTypeStats] = useState({});
  const [topicStats, setTopicStats] = useState({});

  useEffect(() => {
    if (communications.length > 0) {
      const statusStats = getCommunicationStatusStats(communications);
      const typeStatsData = getCommunicationTypeStats(communications);
      const topicStatsData = getTopicDistributionStats(communications);

      setStats({
        totalCommunications: statusStats.total,
        pendingCommunications: statusStats.pending,
        inProgressCommunications: statusStats.inProgress,
        completedCommunications: statusStats.completed,
        followUpCommunications: statusStats.followUp,
        averageSatisfaction: parseFloat(calculateAverageSatisfaction(communications)),
        responseRate: parseFloat(calculateResponseRate(communications))
      });

      setTypeStats(typeStatsData);
      setTopicStats(topicStatsData);
    }
  }, [communications]);

  const todayCommunications = (communications || []).filter((comm) =>
  new Date(comm.communication_date).toDateString() === new Date().toDateString()
  ).length;

  const highPriorityCommunications = (communications || []).filter((comm) =>
  comm.priority === COMMUNICATION_PRIORITY.HIGH &&
  comm.status !== COMMUNICATION_STATUS.COMPLETED
  ).length;

  const overdueCommunications = (communications || []).filter((comm) => {
    if (comm.status === COMMUNICATION_STATUS.COMPLETED) {return false;}
    const communicationDate = new Date(comm.communication_date);
    const now = new Date();
    const daysDiff = Math.floor((now - communicationDate) / (1000 * 60 * 60 * 24));
    return daysDiff > 7; // 超过7天未处理
  }).length;

  const getTopCommunicationTypes = () => {
    return Object.entries(typeStats).
    filter(([_type, count]) => count > 0).
    sort(([, a], [, b]) => b - a).
    slice(0, 3).
    map(([type, count]) => ({
      type,
      label: COMMUNICATION_TYPE_LABELS[type],
      icon: getCommunicationTypeIcon(type),
      count,
      percentage: (count / communications.length * 100).toFixed(1)
    }));
  };

  const getTopTopics = () => {
    return Object.entries(topicStats).
    filter(([_topic, count]) => count > 0).
    sort(([, a], [, b]) => b - a).
    slice(0, 3).
    map(([topic, count]) => ({
      topic,
      label: COMMUNICATION_TOPIC_LABELS[topic],
      count,
      percentage: (count / communications.length * 100).toFixed(1)
    }));
  };

  const getSatisfactionLevel = () => {
    if (stats.averageSatisfaction >= 4.5) {return { level: '非常满意', color: 'text-green-600' };}
    if (stats.averageSatisfaction >= 3.5) {return { level: '满意', color: 'text-green-500' };}
    if (stats.averageSatisfaction >= 2.5) {return { level: '一般', color: 'text-yellow-500' };}
    if (stats.averageSatisfaction >= 1.5) {return { level: '不满意', color: 'text-orange-500' };}
    return { level: '非常不满意', color: 'text-red-500' };
  };

  const topTypes = getTopCommunicationTypes();
  const topTopics = getTopTopics();
  const satisfactionInfo = getSatisfactionLevel();

  return (
    <div className="space-y-6">
      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总沟通记录</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalCommunications}</div>
            <p className="text-xs text-muted-foreground">
              今日新增: {todayCommunications}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">待处理</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pendingCommunications}</div>
            <p className="text-xs text-muted-foreground">
              进行中: {stats.inProgressCommunications}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">已完成</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.completedCommunications}</div>
            <p className="text-xs text-muted-foreground">
              响应率: {stats.responseRate}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">客户满意度</CardTitle>
            <Star className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${satisfactionInfo.color}`}>
              {stats.averageSatisfaction.toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">
              {satisfactionInfo.level}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 状态分布和类型分析 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>沟通状态分布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(COMMUNICATION_STATUS).map(([key, value]) => {
                const count = stats[`${key.toLowerCase()}Communications`] || 0;
                const percentage = stats.totalCommunications > 0 ? (count / stats.totalCommunications * 100).toFixed(1) : 0;

                return (
                  <div key={value} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: COMMUNICATION_STATUS_COLORS[value] }} />

                      <span className="text-sm">{COMMUNICATION_STATUS_LABELS[value]}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary">{count}</Badge>
                      <span className="text-xs text-muted-foreground">{percentage}%</span>
                    </div>
                  </div>);

              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>紧急提醒</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium">高优先级</span>
                </div>
                <Badge variant="destructive">{highPriorityCommunications}</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">超期未处理</span>
                </div>
                <Badge variant="secondary">{overdueCommunications}</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Calendar className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium">今日待跟进</span>
                </div>
                <Badge variant="outline">{stats.followUpCommunications}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 沟通方式和主题分析 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>主要沟通方式</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(topTypes || []).map((typeData, _index) =>
              <div key={typeData.type} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{typeData.icon}</span>
                    <span className="text-sm font-medium">{typeData.label}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary">{typeData.count}</Badge>
                    <span className="text-xs text-muted-foreground">{typeData.percentage}%</span>
                  </div>
              </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>热门沟通主题</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(topTopics || []).map((topicData, _index) =>
              <div key={topicData.topic} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: COMMUNICATION_TOPIC[topicData.topic] ? '#3B82F6' : '#6B7280' }} />

                    <span className="text-sm font-medium">{topicData.label}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="secondary">{topicData.count}</Badge>
                    <span className="text-xs text-muted-foreground">{topicData.percentage}%</span>
                  </div>
              </div>
              )}
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
              onClick={() => onQuickAction?.('createCommunication')}>

              <MessageSquare className="h-6 w-6" />
              <span className="text-sm">新建沟通记录</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('viewPending')}>

              <Clock className="h-6 w-6" />
              <span className="text-sm">待处理列表</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('viewOverdue')}>

              <AlertCircle className="h-6 w-6" />
              <span className="text-sm">超期提醒</span>
            </Button>
            
            <Button
              variant="outline"
              className="h-auto p-4 flex flex-col items-center space-y-2"
              onClick={() => onQuickAction?.('viewAnalytics')}>

              <BarChart3 className="h-6 w-6" />
              <span className="text-sm">统计分析</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 统计指标 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">平均响应时间</CardTitle>
            <TrendingUp className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {stats.responseRate > 80 ? '优秀' : stats.responseRate > 60 ? '良好' : '需改进'}
            </div>
            <p className="text-xs text-muted-foreground">
              响应率: {stats.responseRate}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">需要跟进</CardTitle>
            <Users className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats.followUpCommunications}</div>
            <p className="text-xs text-muted-foreground">
              占比: {stats.totalCommunications > 0 ? (stats.followUpCommunications / stats.totalCommunications * 100).toFixed(1) : 0}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">客户总数</CardTitle>
            <Users className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{customers.length}</div>
            <p className="text-xs text-muted-foreground">
              平均沟通: {customers.length > 0 ? (stats.totalCommunications / customers.length).toFixed(1) : 0}次
            </p>
          </CardContent>
        </Card>
      </div>
    </div>);

};

export default CustomerCommunicationOverview;