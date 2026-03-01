import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  TrendingUp,
  Users,
  Briefcase,
  Calendar,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  BarChart3,
  PieChart,
  Activity } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui/tabs";
import { timesheetApi } from "../services/api";
import { cn as _cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  TimesheetTrendChart,
  DepartmentComparisonChart,
  ProjectDistributionChart } from
"../components/timesheet/TimesheetCharts";

export default function TimesheetDashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [monthSummary, setMonthSummary] = useState(null);
  const [departmentStats, setDepartmentStats] = useState([]);
  const [projectStats, setProjectStats] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());

  useEffect(() => {
    loadDashboardData();
  }, [selectedYear, selectedMonth]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // 加载统计数据
      const [statsRes, summaryRes, anomaliesRes] = await Promise.all([
      timesheetApi.getStatistics({
        year: selectedYear,
        month: selectedMonth
      }),
      timesheetApi.getMonthSummary({
        year: selectedYear,
        month: selectedMonth
      }),
      timesheetApi.detectAnomalies({
        start_date: `${selectedYear}-${String(selectedMonth).padStart(2, "0")}-01`,
        end_date: `${selectedYear}-${String(selectedMonth).padStart(2, "0")}-${new Date(selectedYear, selectedMonth, 0).getDate()}`
      })]
      );

      setStats(statsRes.data?.data || statsRes.data);
      setMonthSummary(summaryRes.data?.data || summaryRes.data);
      setAnomalies(anomaliesRes.data?.data || anomaliesRes.data?.items || anomaliesRes.data || []);

      // 加载部门统计
      if (summaryRes.data?.data?.departments) {
        setDepartmentStats(summaryRes.data.data.departments);
      }

      // 加载项目统计
      if (summaryRes.data?.data?.projects) {
        setProjectStats(summaryRes.data.data.projects.slice(0, 10));
      }
    } catch (error) {
      console.error("加载仪表板数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = async (type) => {
    try {
      const params = {
        year: selectedYear,
        month: selectedMonth,
        format: "excel"
      };

      let response;
      switch (type) {
        case "hr":
          response = await timesheetApi.getHrReport(params);
          break;
        case "finance":
          response = await timesheetApi.getFinanceReport(params);
          break;
        case "rd":
          response = await timesheetApi.getRdReport(params);
          break;
        default:
          return;
      }

      // 下载文件
      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${type}_report_${selectedYear}${String(selectedMonth).padStart(2, "0")}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("导出报表失败:", error);
      alert("导出报表失败，请稍后重试");
    }
  };

  const handleSync = async () => {
    try {
      await timesheetApi.sync({
        year: selectedYear,
        month: selectedMonth,
        sync_target: "all"
      });
      alert("数据同步成功！");
      loadDashboardData();
    } catch (error) {
      console.error("数据同步失败:", error);
      alert("数据同步失败，请稍后重试");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">加载中...</p>
        </div>
      </div>);

  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="工时统计仪表板"
        description="实时查看工时汇总、统计分析、异常检测" />


      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 操作栏 */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeIn}
          className="flex items-center justify-between bg-slate-800/50 rounded-lg p-4">

          <div className="flex items-center gap-4">
            <select
              value={selectedYear || "unknown"}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="bg-slate-700 text-white px-3 py-2 rounded border border-slate-600">

              {[2024, 2025, 2026].map((year) =>
              <option key={year} value={year || "unknown"}>
                  {year}年
              </option>
              )}
            </select>
            <select
              value={selectedMonth || "unknown"}
              onChange={(e) => setSelectedMonth(Number(e.target.value))}
              className="bg-slate-700 text-white px-3 py-2 rounded border border-slate-600">

              {Array.from({ length: 12 }, (_, i) => i + 1).map((month) =>
              <option key={month} value={month || "unknown"}>
                  {month}月
              </option>
              )}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Button
              onClick={handleSync}
              variant="outline"
              className="bg-slate-700 hover:bg-slate-600 text-white border-slate-600">

              <RefreshCw className="w-4 h-4 mr-2" />
              同步数据
            </Button>
            <Button
              onClick={() => handleExportReport("hr")}
              variant="outline"
              className="bg-slate-700 hover:bg-slate-600 text-white border-slate-600">

              <Download className="w-4 h-4 mr-2" />
              导出HR报表
            </Button>
            <Button
              onClick={() => handleExportReport("finance")}
              variant="outline"
              className="bg-slate-700 hover:bg-slate-600 text-white border-slate-600">

              <Download className="w-4 h-4 mr-2" />
              导出财务报表
            </Button>
          </div>
        </motion.div>

        {/* 统计卡片 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">
                总工时
              </CardTitle>
              <Clock className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {stats?.total_hours?.toFixed(1) || 0}
              </div>
              <p className="text-xs text-slate-400 mt-1">小时</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">
                参与人数
              </CardTitle>
              <Users className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {stats?.total_users || 0}
              </div>
              <p className="text-xs text-slate-400 mt-1">人</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">
                项目数
              </CardTitle>
              <Briefcase className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {stats?.total_projects || 0}
              </div>
              <p className="text-xs text-slate-400 mt-1">个</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-300">
                异常记录
              </CardTitle>
              <AlertCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">
                {anomalies.length || 0}
              </div>
              <p className="text-xs text-slate-400 mt-1">条</p>
            </CardContent>
          </Card>
        </motion.div>

        {/* 详细统计 */}
        <Tabs defaultValue="summary" className="space-y-4">
          <TabsList className="bg-slate-800/50">
            <TabsTrigger value="summary">汇总统计</TabsTrigger>
            <TabsTrigger value="departments">部门统计</TabsTrigger>
            <TabsTrigger value="projects">项目统计</TabsTrigger>
            <TabsTrigger value="anomalies">异常检测</TabsTrigger>
          </TabsList>

          <TabsContent value="summary" className="space-y-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">月度汇总</CardTitle>
                <CardDescription className="text-slate-400">
                  {selectedYear}年{selectedMonth}月工时汇总
                </CardDescription>
              </CardHeader>
              <CardContent>
                {monthSummary &&
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-slate-400">正常工时</p>
                      <p className="text-xl font-bold text-white">
                        {monthSummary.normal_hours?.toFixed(1) || 0}h
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400">加班工时</p>
                      <p className="text-xl font-bold text-orange-500">
                        {monthSummary.overtime_hours?.toFixed(1) || 0}h
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400">周末工时</p>
                      <p className="text-xl font-bold text-yellow-500">
                        {monthSummary.weekend_hours?.toFixed(1) || 0}h
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400">节假日工时</p>
                      <p className="text-xl font-bold text-red-500">
                        {monthSummary.holiday_hours?.toFixed(1) || 0}h
                      </p>
                    </div>
                </div>
                }
              </CardContent>
            </Card>

            {/* 数据可视化图表 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {monthSummary?.daily_breakdown &&
              <TimesheetTrendChart
                data={Object.entries(monthSummary.daily_breakdown).map(
                  ([date, hours]) => ({
                    label: date.split("-").slice(1).join("/"),
                    value: parseFloat(hours || 0)
                  })
                )}
                title="每日工时趋势" />

              }
              {departmentStats.length > 0 &&
              <DepartmentComparisonChart
                data={departmentStats}
                title="部门工时对比" />

              }
            </div>
            {projectStats.length > 0 &&
            <ProjectDistributionChart
              data={projectStats}
              title="项目工时分布" />

            }
          </TabsContent>

          <TabsContent value="departments" className="space-y-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">部门工时统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {(departmentStats || []).map((dept, index) =>
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-slate-700/50 rounded">

                      <span className="text-white">{dept.department_name}</span>
                      <div className="flex items-center gap-4">
                        <span className="text-slate-400">
                          {dept.total_hours?.toFixed(1) || 0}h
                        </span>
                        <span className="text-slate-400">
                          {dept.user_count || 0}人
                        </span>
                      </div>
                  </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="projects" className="space-y-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">项目工时统计</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {(projectStats || []).map((project, index) =>
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-slate-700/50 rounded">

                      <div>
                        <span className="text-white">
                          {project.project_name}
                        </span>
                        <p className="text-xs text-slate-400">
                          {project.project_code}
                        </p>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-slate-400">
                          {project.total_hours?.toFixed(1) || 0}h
                        </span>
                        <span className="text-slate-400">
                          {project.user_count || 0}人
                        </span>
                      </div>
                  </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="anomalies" className="space-y-4">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">异常检测</CardTitle>
                <CardDescription className="text-slate-400">
                  检测到的异常工时记录
                </CardDescription>
              </CardHeader>
              <CardContent>
                {anomalies.length === 0 ?
                <div className="text-center py-8">
                    <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-2" />
                    <p className="text-slate-400">未发现异常记录</p>
                </div> :

                <div className="space-y-2">
                    {(anomalies || []).map((anomaly, index) =>
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-red-900/20 border border-red-500/30 rounded">

                        <div>
                          <p className="text-white font-medium">
                            {anomaly.user_name}
                          </p>
                          <p className="text-sm text-slate-400">
                            {anomaly.anomaly_type}: {anomaly.description}
                          </p>
                        </div>
                        <Badge variant="destructive">{anomaly.severity}</Badge>
                  </div>
                  )}
                </div>
                }
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>);

}