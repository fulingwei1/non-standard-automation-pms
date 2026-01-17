/**
 * HRStatisticsTab Component
 * 统计分析 Tab 组件
 */
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Progress } from
"../../ui";
import {
  Users,
  Clock,
  GraduationCap,
  TrendingUp,
  Filter,
  FileSpreadsheet,
  BarChart3,
  PieChart,
  Activity } from
"lucide-react";
import { fadeIn } from "../../../lib/animations";
import { cn } from "../../../lib/utils";

export default function HRStatisticsTab({
  statisticsPeriod,
  setStatisticsPeriod,
  mockHRStats,
  mockEmployeeAgeDistribution,
  mockEmployeeTenureDistribution,
  mockEmployeeEducationDistribution,
  mockMonthlyEmployeeFlow: _mockMonthlyEmployeeFlow,
  mockDepartmentPerformanceComparison,
  mockAttendanceTrend: _mockAttendanceTrend,
  mockRecruitmentChannelStats: _mockRecruitmentChannelStats,
  mockPerformanceTrend: _mockPerformanceTrend,
  handleExportReport
}) {
  return (
    <div className="space-y-6">
      {/* Time Range Filter */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm text-slate-400">统计周期:</span>
                <div className="flex items-center gap-2">
                  {["month", "quarter", "year"].map((period) =>
                  <Button
                    key={period}
                    variant={
                    statisticsPeriod === period ? "default" : "outline"
                    }
                    size="sm"
                    onClick={() => {
                      setStatisticsPeriod(period);
                      // TODO: Reload statistics data
                    }}>

                      {period === "month" ?
                    "月度" :
                    period === "quarter" ?
                    "季度" :
                    "年度"}
                    </Button>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2">

                  <Filter className="w-4 h-4" />
                  筛选
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                  onClick={handleExportReport}>

                  <FileSpreadsheet className="w-4 h-4" />
                  导出报表
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Employee Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Age Distribution */}
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Users className="h-5 w-5 text-blue-400" />
                员工年龄分布
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockEmployeeAgeDistribution.map((item, index) =>
                <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-300">
                        {item.range}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-white">
                          {item.count}人
                        </span>
                        <span className="text-xs text-slate-400 w-12 text-right">
                          {item.percentage}%
                        </span>
                      </div>
                    </div>
                    <Progress
                    value={item.percentage}
                    className="h-2 bg-slate-700/50" />

                  </div>
                )}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-700/50">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>平均年龄: {mockHRStats.avgAge} 岁</span>
                  <span>
                    最集中: 31-35岁 ({mockEmployeeAgeDistribution[2].percentage}
                    %)
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Tenure Distribution */}
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Clock className="h-5 w-5 text-purple-400" />
                员工工龄分布
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockEmployeeTenureDistribution.map((item, index) =>
                <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-300">
                        {item.range}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-white">
                          {item.count}人
                        </span>
                        <span className="text-xs text-slate-400 w-12 text-right">
                          {item.percentage}%
                        </span>
                      </div>
                    </div>
                    <Progress
                    value={item.percentage}
                    className="h-2 bg-slate-700/50" />

                  </div>
                )}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-700/50">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>平均工龄: {mockHRStats.avgTenure} 年</span>
                  <span>
                    最集中: 1-3年 (
                    {mockEmployeeTenureDistribution[1].percentage}%)
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Additional Statistics Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Education Distribution */}
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <GraduationCap className="h-5 w-5 text-cyan-400" />
                学历分布
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockEmployeeEducationDistribution.map((item, index) =>
                <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-300">
                        {item.level}
                      </span>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-white">
                          {item.count}人
                        </span>
                        <span className="text-xs text-slate-400 w-12 text-right">
                          {item.percentage}%
                        </span>
                      </div>
                    </div>
                    <Progress
                    value={item.percentage}
                    className="h-2 bg-slate-700/50" />

                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Department Performance */}
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <BarChart3 className="h-5 w-5 text-emerald-400" />
                部门绩效对比
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockDepartmentPerformanceComparison.map((dept, index) =>
                <div key={index}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white">
                          {dept.department}
                        </span>
                        <span className="text-xs text-slate-400">
                          #{dept.rank}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-semibold text-white">
                          {dept.avgScore}分
                        </span>
                        <span
                        className={cn(
                          "text-xs",
                          dept.trend > 0 ?
                          "text-emerald-400" :
                          "text-red-400"
                        )}>

                          {dept.trend > 0 ? "+" : ""}
                          {dept.trend}%
                        </span>
                      </div>
                    </div>
                    <Progress
                    value={dept.avgScore}
                    className="h-2 bg-slate-700/50" />

                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>);

}