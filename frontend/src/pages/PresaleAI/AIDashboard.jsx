/**
 * AI仪表盘
 * Team 10: 售前AI系统集成与前端UI
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Brain,
  TrendingUp,
  CheckCircle,
  Clock,
  Activity,
  Users,
} from 'lucide-react';
import { presaleAIService } from '@/services/presaleAIService';
import AIStatsChart from '@/components/PresaleAI/AIStatsChart';
import { toast } from 'sonner';

const AIDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    loadStats();
  }, [days]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await presaleAIService.getDashboardStats(days);
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
      toast.error('加载统计数据失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  const statCards = [
    {
      title: '总使用次数',
      value: stats.total_usage.toLocaleString(),
      icon: Brain,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: '成功率',
      value: `${stats.success_rate}%`,
      icon: CheckCircle,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: '平均响应时间',
      value: `${stats.avg_response_time}ms`,
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      title: '活跃用户',
      value: stats.user_stats.active_users.toLocaleString(),
      icon: Users,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">AI仪表盘</h1>
          <p className="text-muted-foreground mt-1">
            售前AI系统整体运行情况
          </p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-4 py-2 rounded-md transition-colors ${
                days === d
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary hover:bg-secondary/80'
              }`}
            >
              {d}天
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {(statCards || []).map((stat, index) => (
          <Card key={index}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
                <div className={`${stat.bgColor} p-3 rounded-full`}>
                  {(() => { const DynIcon = stat.icon; return <DynIcon className={`h-6 w-6 ${stat.color}`}  />; })()}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage Trend */}
        <Card>
          <CardHeader>
            <CardTitle>使用趋势</CardTitle>
            <CardDescription>AI功能使用量变化趋势</CardDescription>
          </CardHeader>
          <CardContent>
            <AIStatsChart
              data={stats.usage_trend}
              type="line"
              dataKey="count"
              xKey="date"
            />
          </CardContent>
        </Card>

        {/* Top Functions */}
        <Card>
          <CardHeader>
            <CardTitle>热门功能</CardTitle>
            <CardDescription>AI功能使用排行</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(stats.top_functions || []).map((func, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <span className="text-sm font-semibold text-primary">
                        {index + 1}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">{getFunctionLabel(func.function)}</p>
                      <p className="text-sm text-muted-foreground">
                        {func.usage_count} 次使用
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-green-600">
                      {func.success_rate.toFixed(1)}%
                    </p>
                    <p className="text-xs text-muted-foreground">成功率</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Feed */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            最近活动
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">最近AI功能使用记录将显示在这里...</p>
        </CardContent>
      </Card>
    </div>
  );
};

// 辅助函数：获取功能标签
const getFunctionLabel = (func) => {
  const labels = {
    requirement: '需求理解',
    solution: '方案生成',
    cost: '成本估算',
    winrate: '赢率预测',
    quotation: '报价生成',
    knowledge: '知识库推荐',
    script: '话术助手',
    emotion: '情绪分析',
    mobile: '移动助手',
  };
  return labels[func] || func;
};

export default AIDashboard;
