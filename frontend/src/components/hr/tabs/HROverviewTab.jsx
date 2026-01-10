/**
 * HROverviewTab Component
 * HR 概览 Tab 组件
 */
import { useEffect } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
} from "../../ui";
import {
  UserPlus,
  Award,
  Users,
  PieChart,
  Zap,
  Building2,
  Calendar,
  UserCheck,
  Heart,
  BarChart3,
  ChevronRight,
} from "lucide-react";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import { useHROverview } from "../hooks/useHROverview";

// 状态标签映射
const getStatusLabel = (status) => {
  const labels = {
    active: "在职",
    pending: "待处理",
    reviewing: "评审中",
    processing: "处理中",
    completed: "已完成",
    recruiting: "招聘中",
    screening: "筛选中",
    interviewing: "面试中",
    offer: "发Offer",
  };
  return labels[status] || status;
};

export default function HROverviewTab({
  mockHRStats,
  mockPendingRecruitments,
  mockPendingReviews,
  mockDepartmentDistribution,
  mockPerformanceDistribution,
  setSelectedTab,
}) {
  const { loadAll } = useHROverview();

  // 组件加载时获取数据
  useEffect(() => {
    loadAll();
  }, [loadAll]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Pending Items */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pending Recruitments */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <UserPlus className="h-5 w-5 text-amber-400" />
                    待处理招聘
                  </CardTitle>
                  <Badge
                    variant="outline"
                    className="bg-amber-500/20 text-amber-400 border-amber-500/30"
                  >
                    {mockPendingRecruitments.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockPendingRecruitments.map((recruitment, index) => (
                  <motion.div
                    key={recruitment.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                    onClick={() => {
                      setSelectedTab("recruitment");
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white">
                            {recruitment.position}
                          </span>
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-xs",
                              recruitment.urgency === "high" &&
                                "bg-red-500/20 text-red-400 border-red-500/30",
                              recruitment.urgency === "medium" &&
                                "bg-amber-500/20 text-amber-400 border-amber-500/30",
                            )}
                          >
                            {recruitment.urgency === "high" ? "紧急" : "普通"}
                          </Badge>
                          <Badge
                            variant="outline"
                            className="text-xs bg-slate-700/40"
                          >
                            {getStatusLabel(recruitment.status)}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-400">
                          {recruitment.department} · {recruitment.createdDate}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-white">
                          ¥{recruitment.budget.toLocaleString()}
                        </div>
                        <div className="text-xs text-slate-400">预算</div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
                      <span>
                        申请人: {recruitment.applicants} | 面试:{" "}
                        {recruitment.interviews}
                      </span>
                      <span>期望入职: {recruitment.expectedStartDate}</span>
                    </div>
                  </motion.div>
                ))}
                <Button
                  variant="outline"
                  className="w-full mt-3"
                  onClick={() => setSelectedTab("recruitment")}
                >
                  查看全部招聘
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Pending Performance Reviews */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Award className="h-5 w-5 text-purple-400" />
                    待绩效评审
                  </CardTitle>
                  <Badge
                    variant="outline"
                    className="bg-purple-500/20 text-purple-400 border-purple-500/30"
                  >
                    {mockPendingReviews.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockPendingReviews.map((review) => (
                  <motion.div
                    key={review.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                    onClick={() => {
                      setSelectedTab("performance");
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white">
                            {review.employeeName}
                          </span>
                          <Badge
                            variant="outline"
                            className="text-xs bg-slate-700/40"
                          >
                            {review.department}
                          </Badge>
                          {review.priority === "high" && (
                            <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                            </Badge>
                          )}
                        </div>
                        <div className="text-xs text-slate-400">
                          {review.period} · 截止: {review.dueDate}
                        </div>
                      </div>
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-xs",
                          review.status === "pending" &&
                            "bg-amber-500/20 text-amber-400 border-amber-500/30",
                          review.status === "reviewing" &&
                            "bg-blue-500/20 text-blue-400 border-blue-500/30",
                        )}
                      >
                        {getStatusLabel(review.status)}
                      </Badge>
                    </div>
                  </motion.div>
                ))}
                <Button
                  variant="outline"
                  className="w-full mt-3"
                  onClick={() => setSelectedTab("performance")}
                >
                  查看全部评审
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Column - Statistics */}
        <div className="space-y-6">
          {/* Employee Overview */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Users className="h-5 w-5 text-blue-400" />
                  员工概览
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">在职率</p>
                    <p className="text-lg font-bold text-white">
                      {(
                        (mockHRStats.activeEmployees /
                          mockHRStats.totalEmployees) *
                        100
                      ).toFixed(1)}
                      %
                    </p>
                  </div>
                  <Progress
                    value={
                      (mockHRStats.activeEmployees /
                        mockHRStats.totalEmployees) *
                      100
                    }
                    className="h-2 bg-slate-700/50"
                  />
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">本月新增</p>
                    <p className="text-lg font-bold text-emerald-400">
                      +{mockHRStats.newEmployeesThisMonth}
                    </p>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">本月离职</p>
                    <p className="text-lg font-bold text-red-400">
                      -{mockHRStats.leavingEmployeesThisMonth}
                    </p>
                  </div>
                </div>
                <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm text-slate-400">平均工龄</p>
                    <p className="text-lg font-bold text-white">
                      {mockHRStats.avgTenure} 年
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Performance Distribution */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <PieChart className="h-5 w-5 text-purple-400" />
                  绩效分布
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockPerformanceDistribution.map((item, index) => (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={cn(
                            "w-3 h-3 rounded-full",
                            item.color === "emerald" && "bg-emerald-500",
                            item.color === "blue" && "bg-blue-500",
                            item.color === "amber" && "bg-amber-500",
                            item.color === "red" && "bg-red-500",
                          )}
                        />
                        <span className="text-sm text-slate-300">
                          {item.level}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-white">
                          {item.count}人
                        </span>
                        <span className="text-xs text-slate-500">
                          {item.percentage}%
                        </span>
                      </div>
                    </div>
                    <Progress
                      value={item.percentage}
                      className="h-1.5 bg-slate-700/50"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Quick Actions */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Zap className="h-5 w-5 text-yellow-400" />
              快捷操作
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              <Button
                variant="outline"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-blue-500/10 hover:border-blue-500/30 transition-colors"
                onClick={() => {
                  setSelectedTab("recruitment");
                }}
              >
                <UserPlus className="w-5 h-5 text-blue-400" />
                <span className="text-xs">新建招聘</span>
              </Button>
              <Button
                variant="outline"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-purple-500/10 hover:border-purple-500/30 transition-colors"
                onClick={() => {
                  setSelectedTab("performance");
                }}
              >
                <Award className="w-5 h-5 text-purple-400" />
                <span className="text-xs">绩效评审</span>
              </Button>
              <Button
                variant="outline"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-emerald-500/10 hover:border-emerald-500/30 transition-colors"
                onClick={() => {
                  setSelectedTab("employees");
                }}
              >
                <UserCheck className="w-5 h-5 text-emerald-400" />
                <span className="text-xs">新增员工</span>
              </Button>
              <Button
                variant="outline"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-cyan-500/10 hover:border-cyan-500/30 transition-colors"
                onClick={() => {
                  setSelectedTab("attendance");
                }}
              >
                <Calendar className="w-5 h-5 text-cyan-400" />
                <span className="text-xs">考勤管理</span>
              </Button>
              <Button
                variant="outline"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-pink-500/10 hover:border-pink-500/30 transition-colors"
                onClick={() => {
                  setSelectedTab("relations");
                }}
              >
                <Heart className="w-5 h-5 text-pink-400" />
                <span className="text-xs">员工关系</span>
              </Button>
              <Button
                variant="outline"
                className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-amber-500/10 hover:border-amber-500/30 transition-colors"
                onClick={() => {
                  setSelectedTab("statistics");
                }}
              >
                <BarChart3 className="w-5 h-5 text-amber-400" />
                <span className="text-xs">统计分析</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Department Distribution */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Building2 className="h-5 w-5 text-blue-400" />
                部门人员分布
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-primary"
              >
                查看全部 <ChevronRight className="w-3 h-3 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {mockDepartmentDistribution.map((dept) => (
                <div
                  key={dept.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-white text-sm">
                          {dept.name}
                        </span>
                        {dept.new > 0 && (
                          <Badge className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                            +{dept.new}
                          </Badge>
                        )}
                        {dept.leaving > 0 && (
                          <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                            -{dept.leaving}
                          </Badge>
                        )}
                      </div>
                      <div className="text-xs text-slate-400">
                        {dept.active}/{dept.total} 人
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">
                        {dept.performance}
                      </div>
                      <div className="text-xs text-slate-400">绩效分</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">平均年龄</span>
                      <span className="text-slate-300">{dept.avgAge} 岁</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">平均工龄</span>
                      <span className="text-slate-300">
                        {dept.avgTenure} 年
                      </span>
                    </div>
                    <Progress
                      value={(dept.active / dept.total) * 100}
                      className="h-1.5 bg-slate-700/50"
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
