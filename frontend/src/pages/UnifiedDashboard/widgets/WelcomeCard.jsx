/**
 * WelcomeCard - 欢迎卡片组件
 * 显示用户欢迎信息、今日工作状态和进度
 * 整合自原 WorkCenter 页面
 */
import { useState, useEffect } from 'react';
import { Clock, CheckCircle2 } from 'lucide-react';
import { Card, CardContent } from '../../../components/ui/card';
import { Progress } from '../../../components/ui/progress';
import { cn, formatDate } from '../../../lib/utils';
import { useAuth } from '../../../context/AuthContext';

export default function WelcomeCard() {
  const { user } = useAuth();

  // 今日概览数据
  const [todayOverview, setTodayOverview] = useState({
    currentStatus: 'working', // working, break, offline
    todayProgress: 0,
    todayHours: 0,
    targetHours: 8,
    completedTasks: 0,
    totalTasks: 0,
  });

  useEffect(() => {
    // 模拟获取今日数据（后续可接入真实 API）
    const now = new Date();
    const workStartHour = 9;
    const currentHour = now.getHours();
    const workedHours = Math.max(0, Math.min(currentHour - workStartHour, 8));
    const progress = Math.round((workedHours / 8) * 100);

    setTodayOverview({
      currentStatus: currentHour >= 9 && currentHour < 18 ? 'working' : 'offline',
      todayProgress: progress,
      todayHours: workedHours,
      targetHours: 8,
      completedTasks: 3,
      totalTasks: 5,
    });
  }, []);

  const getStatusInfo = (status) => {
    switch (status) {
      case 'working':
        return { color: 'bg-green-500', text: '工作中' };
      case 'break':
        return { color: 'bg-yellow-500', text: '休息中' };
      case 'offline':
        return { color: 'bg-gray-400', text: '离线' };
      default:
        return { color: 'bg-gray-400', text: '离线' };
    }
  };

  const statusInfo = getStatusInfo(todayOverview.currentStatus);

  return (
    <Card className="bg-gradient-to-r from-violet-900/90 to-indigo-900/90 text-white border-0 shadow-lg">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">
              欢迎回来，{user?.name || user?.username || '用户'}！
            </h2>
            <p className="text-blue-100">
              今天是 {formatDate(new Date())}，祝您工作顺利
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 mb-2">
              <div className={cn('w-3 h-3 rounded-full animate-pulse', statusInfo.color)} />
              <span className="text-sm font-medium">{statusInfo.text}</span>
            </div>
            <div className="flex items-center gap-4 text-sm text-blue-100">
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>{todayOverview.todayHours}h / {todayOverview.targetHours}h</span>
              </div>
              <div className="flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4" />
                <span>{todayOverview.completedTasks}/{todayOverview.totalTasks} 任务</span>
              </div>
            </div>
          </div>
        </div>

        {/* 今日进度 */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <span>今日进度</span>
            <span>{todayOverview.todayProgress}%</span>
          </div>
          <Progress
            value={todayOverview.todayProgress}
            className="h-2 bg-white/20"
          />
        </div>
      </CardContent>
    </Card>
  );
}
