/**
 * Team Performance Component
 * 客户服务团队绩效视图组件
 */
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../ui/select";
import {
  Progress,
  ProgressValueLabel } from
"../ui/progress";
import {
  BarChart3,
  Users,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Star,
  TrendingUp,
  TrendingDown,
  Target,
  Calendar,
  Award,
  User,
  Award as AwardIcon,
  RefreshCw,
  Filter } from
"lucide-react";

export function TeamPerformance({
  teamData = [],
  period = "month",
  onTeamMemberClick,
  className = ""
}) {
  const [sortedTeam, setSortedTeam] = useState(teamData);
  const [sortBy, setSortBy] = useState("ticketsResolved");
  const [sortOrder, setSortOrder] = useState("desc");
  const [selectedPeriod, setSelectedPeriod] = useState(period);

  // 模拟团队成员数据
  const teamMembers = teamData.length > 0 ? teamData : [
  {
    id: 1,
    name: "张明",
    avatar: "https://via.placeholder.com/40",
    role: "高级客服专员",
    department: "技术支持部",
    ticketsAssigned: 45,
    ticketsResolved: 38,
    resolutionRate: 84.4,
    avgResponseTime: 15,
    avgResolutionTime: 4.2,
    satisfactionScore: 4.6,
    escalatedTickets: 2,
    attendanceRate: 98,
    overtimeHours: 12,
    skills: ["技术支持", "产品咨询", "投诉处理"]
  },
  {
    id: 2,
    name: "李华",
    avatar: "https://via.placeholder.com/40",
    role: "客服专员",
    department: "客户服务部",
    ticketsAssigned: 52,
    ticketsResolved: 45,
    resolutionRate: 86.5,
    avgResponseTime: 12,
    avgResolutionTime: 3.8,
    satisfactionScore: 4.7,
    escalatedTickets: 1,
    attendanceRate: 100,
    overtimeHours: 8,
    skills: ["客户关怀", "账单咨询", "培训服务"]
  },
  {
    id: 3,
    name: "王芳",
    avatar: "https://via.placeholder.com/40",
    role: "资深客服专家",
    department: "VIP服务部",
    ticketsAssigned: 35,
    ticketsResolved: 33,
    resolutionRate: 94.3,
    avgResponseTime: 8,
    avgResolutionTime: 2.5,
    satisfactionScore: 4.9,
    escalatedTickets: 0,
    attendanceRate: 99,
    overtimeHours: 5,
    skills: ["VIP客户", "复杂问题", "团队培训"]
  },
  {
    id: 4,
    name: "赵强",
    avatar: "https://via.placeholder.com/40",
    role: "客服专员",
    department: "客户服务部",
    ticketsAssigned: 48,
    ticketsResolved: 40,
    resolutionRate: 83.3,
    avgResponseTime: 18,
    avgResolutionTime: 5.1,
    satisfactionScore: 4.3,
    escalatedTickets: 3,
    attendanceRate: 95,
    overtimeHours: 15,
    skills: ["新客户", "现场服务", "设备维护"]
  }];


  // 处理排序
  const _handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  // 排序团队成员
  useEffect(() => {
    const sorted = [...teamMembers].sort((a, b) => {
      let valueA = a[sortBy];
      let valueB = b[sortBy];

      // 特殊处理字符串比较
      if (typeof valueA === "string") {
        valueA = parseFloat(valueA) || 0;
        valueB = parseFloat(valueB) || 0;
      }

      if (sortOrder === "asc") {
        return valueA - valueB;
      } else {
        return valueB - valueA;
      }
    });

    setSortedTeam(sorted);
  }, [sortBy, sortOrder, teamMembers]);

  // 计算团队整体统计
  const teamStats = {
    totalMembers: teamMembers.length,
    totalTicketsAssigned: teamMembers.reduce((sum, member) => sum + member.ticketsAssigned, 0),
    totalTicketsResolved: teamMembers.reduce((sum, member) => sum + member.ticketsResolved, 0),
    overallResolutionRate: teamMembers.reduce((sum, member) => sum + member.resolutionRate, 0) / teamMembers.length,
    avgResponseTime: teamMembers.reduce((sum, member) => sum + member.avgResponseTime, 0) / teamMembers.length,
    avgSatisfactionScore: teamMembers.reduce((sum, member) => sum + member.satisfactionScore, 0) / teamMembers.length,
    totalEscalated: teamMembers.reduce((sum, member) => sum + member.escalatedTickets, 0)
  };

  // 绩效等级映射
  const getPerformanceLevel = (resolutionRate) => {
    if (resolutionRate >= 90) return { level: "优秀", color: "text-green-600", bgColor: "bg-green-100" };
    if (resolutionRate >= 80) return { level: "良好", color: "text-blue-600", bgColor: "bg-blue-100" };
    if (resolutionRate >= 70) return { level: "合格", color: "text-yellow-600", bgColor: "bg-yellow-100" };
    return { level: "待改进", color: "text-red-600", bgColor: "bg-red-100" };
  };

  // 获取趋势图标
  const _getTrendIcon = (current, previous) => {
    if (current > previous) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (current < previous) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return null;
  };

  return (
    <div className={className}>
      {/* 团队整体统计 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              团队成员
            </CardTitle>
            <Users className="h-4 w-4 text-slate-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {teamStats.totalMembers}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              在职客服人员
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              工单处理率
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-slate-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {teamStats.totalTicketsResolved}/{teamStats.totalTicketsAssigned}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              已处理/总分配
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              平均响应时间
            </CardTitle>
            <Clock className="h-4 w-4 text-slate-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {teamStats.avgResponseTime.toFixed(1)}分钟
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              <Target className="inline w-3 h-3 mr-1" />
              目标 &lt; 30分钟
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
              客户满意度
            </CardTitle>
            <Star className="h-4 w-4 text-slate-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {teamStats.avgSatisfactionScore.toFixed(1)}/5.0
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              团队平均评分
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 团队成员列表 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-slate-600" />
              团队绩效详情
            </CardTitle>
            <div className="flex items-center gap-2">
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">本周</SelectItem>
                  <SelectItem value="month">本月</SelectItem>
                  <SelectItem value="quarter">本季度</SelectItem>
                  <SelectItem value="year">本年</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" size="sm">
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="space-y-4">
            {sortedTeam.map((member, index) => {
              const performanceLevel = getPerformanceLevel(member.resolutionRate);

              return (
                <div
                  key={member.id}
                  className="p-4 border rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer"
                  onClick={() => onTeamMemberClick?.(member)}>

                  <div className="flex items-center justify-between">
                    {/* 左侧成员信息 */}
                    <div className="flex items-center gap-4">
                      <div className="flex-shrink-0">
                        <img
                          src={member.avatar}
                          alt={member.name}
                          className="w-12 h-12 rounded-full object-cover" />

                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                            {member.name}
                          </h3>
                          <Badge variant="outline" className="text-xs">
                            {member.role}
                          </Badge>
                          <Badge className={`${performanceLevel.bg} ${performanceLevel.color} text-xs`}>
                            {performanceLevel.level}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {member.department}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          {member.skills.map((skill, idx) =>
                          <span
                            key={idx}
                            className="text-xs text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded">

                              {skill}
                          </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* 右侧绩效指标 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                          {member.resolutionRate.toFixed(1)}%
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          解决率
                        </div>
                        <Progress
                          value={member.resolutionRate}
                          className="mt-1 h-1.5" />

                      </div>

                      <div className="text-center">
                        <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                          {member.avgResponseTime}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          响应时间(分钟)
                        </div>
                        <div className="flex items-center justify-center gap-1 mt-1">
                          <Clock className="w-3 h-3 text-slate-400" />
                          <span className="text-xs text-slate-500">目标: &lt;30</span>
                        </div>
                      </div>

                      <div className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          <Star className="w-5 h-5 text-yellow-500" />
                          <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                            {member.satisfactionScore.toFixed(1)}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          满意度评分
                        </div>
                      </div>

                      <div className="text-center">
                        <div className="flex items-center justify-center gap-1">
                          {member.escalatedTickets === 0 ?
                          <CheckCircle2 className="w-5 h-5 text-green-500" /> :

                          <AlertTriangle className="w-5 h-5 text-orange-500" />
                          }
                          <span className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                            {member.escalatedTickets}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          升级工单
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 底部指标 */}
                  <div className="flex items-center justify-between mt-4 pt-4 border-t">
                    <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
                      <span>
                        <AwardIcon className="inline w-4 h-4 mr-1" />
                        出勤率: {member.attendanceRate}%
                      </span>
                      <span>
                        <Clock className="inline w-4 h-4 mr-1" />
                        加班: {member.overtimeHours}h
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        排名 #{index + 1}
                      </Badge>
                    </div>
                  </div>
                </div>);

            })}
          </div>
        </CardContent>
      </Card>
    </div>);

}