/**
 * WorkCenter - 工作中心页面
 * 每个员工的统一工作入口，整合日常所需的核心功能
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Clock,
  ClipboardList,
  Bell,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Users,
  FileText,
  Settings,
  Plus,
  ChevronRight,
  Target,
  Timer,
  Award,
  BookOpen,
  BarChart3,
  Zap } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { cn, formatDate } from "../lib/utils";
import { workLogApi, taskCenterApi } from "../services/api";

export default function WorkCenter() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [userInfo, _setUserInfo] = useState(null);

  // 快速统计数据
  const [stats, setStats] = useState({
    todayTasks: 0,
    pendingTasks: 0,
    completedTasks: 0,
    unreadNotifications: 0,
    recentWorkLogs: 0,
    thisMonthWorkLogs: 0,
    pendingApprovals: 0,
    upcomingDeadlines: 0
  });

  // 快速操作数据
  const [quickActions, _setQuickActions] = useState([
  {
    title: "查看任务",
    description: "管理我的待办任务",
    icon: Target,
    color: "bg-green-500",
    action: () => navigate("/tasks")
  },
  {
    title: "工时填报",
    description: "填写项目工时",
    icon: Timer,
    color: "bg-orange-500",
    action: () => navigate("/timesheet")
  }]
  );

  // 今日概览数据
  const [todayOverview, _setTodayOverview] = useState({
    currentStatus: "working", // working, break, offline
    workStartTime: "09:00",
    todayProgress: 65,
    todayHours: 6.5,
    targetHours: 8
  });

  // 最近活动
  const [recentActivities, _setRecentActivities] = useState([
  {
    id: 1,
    type: "task_completed",
    title: "完成机械结构设计",
    time: "2小时前",
    project: "BMS老化测试设备"
  },
  {
    id: 2,
    type: "work_log",
    title: "提交了工作日志",
    time: "3小时前",
    content: "完成了设备框架的3D建模..."
  },
  {
    id: 3,
    type: "notification",
    title: "收到新的任务分配",
    time: "5小时前",
    content: "BOM整理发布任务已分配给您"
  }]
  );

  useEffect(() => {
    fetchWorkCenterData();
  }, []);

  const fetchWorkCenterData = async () => {
    try {
      setLoading(true);

      // 并行获取各种数据
      const [workLogsRes, tasksRes] = await Promise.allSettled([
      workLogApi.list({ page: 1, page_size: 5 }),
      taskCenterApi.getMyTasks()]
      );

      // 处理工作日志数据
      if (workLogsRes.status === "fulfilled") {
        const workLogData =
        workLogsRes.value.data?.data || workLogsRes.value.data || {};
        const workLogs = workLogData.items || [];

        // 计算工作日志统计
        const today = new Date().toISOString().split("T")[0];
        const todayLogs = workLogs.filter(
          (log) => log.work_date === today
        ).length;
        const thisMonthLogs = workLogs.filter((log) => {
          const logDate = new Date(log.work_date);
          const now = new Date();
          return (
            logDate.getMonth() === now.getMonth() &&
            logDate.getFullYear() === now.getFullYear());

        }).length;

        setStats((prev) => ({
          ...prev,
          recentWorkLogs: todayLogs,
          thisMonthWorkLogs: thisMonthLogs
        }));
      }

      // 处理任务数据
      if (tasksRes.status === "fulfilled") {
        const taskData = tasksRes.value.data?.data || tasksRes.value.data || {};
        const tasks = taskData.items || taskData || [];

        const pendingTasks = tasks.filter(
          (task) => task.status === "pending" || task.status === "in_progress"
        ).length;
        const completedTasks = tasks.filter(
          (task) => task.status === "completed"
        ).length;
        const todayTasks = tasks.filter((task) => {
          const taskDate = new Date(task.due_date);
          const today = new Date();
          return taskDate.toDateString() === today.toDateString();
        }).length;

        setStats((prev) => ({
          ...prev,
          todayTasks,
          pendingTasks,
          completedTasks
        }));
      }
    } catch (error) {
      console.error("Failed to fetch work center data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "working":
        return "bg-green-500";
      case "break":
        return "bg-yellow-500";
      case "offline":
        return "bg-gray-500";
      default:
        return "bg-gray-500";
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case "task_completed":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case "work_log":
        return <ClipboardList className="w-4 h-4 text-blue-500" />;
      case "notification":
        return <Bell className="w-4 h-4 text-purple-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-gray-500">加载工作中心数据...</p>
        </div>
      </div>);

  }

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="工作中心"
        description="您的个人工作台，快速访问日常工作功能" />


      {/* 欢迎区域和状态 */}
      <Card className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">
                欢迎回来，{userInfo?.name || "员工"}！
              </h2>
              <p className="text-blue-100">
                今天是 {formatDate(new Date())}，让我们开始高效的一天
              </p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className={cn(
                    "w-3 h-3 rounded-full",
                    getStatusColor(todayOverview.currentStatus)
                  )} />
                <span className="text-sm">
                  {todayOverview.currentStatus === "working" ?
                  "工作中" :
                  todayOverview.currentStatus === "break" ?
                  "休息中" :
                  "离线"}
                </span>
              </div>
              <p className="text-sm text-blue-100">
                今日已工作 {todayOverview.todayHours}h /{" "}
                {todayOverview.targetHours}h
              </p>
            </div>
          </div>

          {/* 今日进度 */}
          <div className="mt-4">
            <div className="flex justify-between text-sm mb-1">
              <span>今日进度</span>
              <span>{todayOverview.todayProgress}%</span>
            </div>
            <Progress value={todayOverview.todayProgress} className="h-2" />
          </div>
        </CardContent>
      </Card>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">今日任务</p>
                <p className="text-2xl font-bold">{stats.todayTasks}</p>
              </div>
              <Target className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">待办任务</p>
                <p className="text-2xl font-bold">{stats.pendingTasks}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">未读通知</p>
                <p className="text-2xl font-bold">
                  {stats.unreadNotifications}
                </p>
              </div>
              <Bell className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">本月日志</p>
                <p className="text-2xl font-bold">{stats.thisMonthWorkLogs}</p>
              </div>
              <FileText className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 快速操作 */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                快速操作
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {quickActions.map((action, index) =>
                <button
                  key={index}
                  onClick={action.action}
                  className="flex items-center gap-4 p-4 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-left">

                    <div
                    className={cn(
                      "w-12 h-12 rounded-lg flex items-center justify-center",
                      action.color
                    )}>

                      <action.icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-medium">{action.title}</h3>
                      <p className="text-sm text-gray-600">
                        {action.description}
                      </p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-400 ml-auto" />
                </button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 最近活动 */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                最近活动
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivities.map((activity) =>
                <div key={activity.id} className="flex items-start gap-3">
                    {getActivityIcon(activity.type)}
                    <div className="flex-1">
                      <p className="font-medium">{activity.title}</p>
                      {activity.content &&
                    <p className="text-sm text-gray-600">
                          {activity.content}
                    </p>
                    }
                      {activity.project &&
                    <p className="text-sm text-blue-600">
                          {activity.project}
                    </p>
                    }
                      <p className="text-xs text-gray-500">{activity.time}</p>
                    </div>
                </div>
                )}
              </div>

              <Button
                variant="outline"
                className="w-full mt-4"
                onClick={() => navigate("/tasks")}>

                查看所有活动
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* 侧边栏信息 */}
        <div className="space-y-6">
          {/* 今日待办 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">今日待办</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">BMS老化设备设计</p>
                    <p className="text-xs text-red-600">即将到期</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                  <Clock className="w-4 h-4 text-yellow-500" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">提交工作日志</p>
                    <p className="text-xs text-yellow-600">待完成</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
                  <Calendar className="w-4 h-4 text-blue-500" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">项目评审会议</p>
                    <p className="text-xs text-blue-600">下午 2:00</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 快速链接 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">快速链接</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <button
                  onClick={() => navigate("/notifications")}
                  className="w-full flex items-center gap-3 p-2 rounded hover:bg-gray-50 text-left">

                  <Bell className="w-4 h-4 text-gray-500" />
                  <span className="text-sm">通知中心</span>
                  {stats.unreadNotifications > 0 &&
                  <Badge className="ml-auto" variant="destructive">
                      {stats.unreadNotifications}
                  </Badge>
                  }
                </button>

                <button
                  onClick={() => navigate("/settings")}
                  className="w-full flex items-center gap-3 p-2 rounded hover:bg-gray-50 text-left">

                  <Settings className="w-4 h-4 text-gray-500" />
                  <span className="text-sm">个人设置</span>
                </button>

                <button
                  onClick={() => navigate("/knowledge-base")}
                  className="w-full flex items-center gap-3 p-2 rounded hover:bg-gray-50 text-left">

                  <BookOpen className="w-4 h-4 text-gray-500" />
                  <span className="text-sm">知识库</span>
                </button>

                <button
                  onClick={() => navigate("/projects")}
                  className="w-full flex items-center gap-3 p-2 rounded hover:bg-gray-50 text-left">

                  <Award className="w-4 h-4 text-gray-500" />
                  <span className="text-sm">项目列表</span>
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>);

}
