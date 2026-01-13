/**
 * Leave Management - Employee leave application and approval
 * Features: Leave application, approval workflow, leave balance, leave statistics
 */

import { useState, useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  Plus,
  Calendar,
  Clock,
  User,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  BarChart3,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import { cn, formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  SimpleBarChart,
  MonthlyTrendChart,
  SimplePieChart,
  TrendComparisonCard,
} from "../components/administrative/StatisticsCharts";
import { adminApi } from "../services/api";

// Mock data - 已移除，使用真实API

export default function LeaveManagement() {
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [leaveApplications, setLeaveApplications] = useState([]);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await adminApi.leave.list();
        if (res.data?.items) {
          setLeaveApplications(res.data.items);
        } else if (Array.isArray(res.data)) {
          setLeaveApplications(res.data);
        }
      } catch (err) {
        console.log("Leave API unavailable, using mock data");
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const filteredApplications = useMemo(() => {
    return leaveApplications.filter((app) => {
      const matchSearch =
        app.employee.toLowerCase().includes(searchText.toLowerCase()) ||
        app.department.toLowerCase().includes(searchText.toLowerCase());
      const matchStatus = statusFilter === "all" || app.status === statusFilter;
      const matchType = typeFilter === "all" || app.type === typeFilter;
      return matchSearch && matchStatus && matchType;
    });
  }, [leaveApplications, searchText, statusFilter, typeFilter]);

  const stats = useMemo(() => {
    const pending = leaveApplications.filter(
      (a) => a.status === "pending",
    ).length;
    const approved = leaveApplications.filter(
      (a) => a.status === "approved",
    ).length;
    const rejected = leaveApplications.filter(
      (a) => a.status === "rejected",
    ).length;
    const totalDays = leaveApplications
      .filter((a) => a.status === "approved")
      .reduce((sum, a) => sum + a.days, 0);
    return { pending, approved, rejected, totalDays };
  }, [leaveApplications]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="请假管理"
        description="员工请假申请、审批流程、假期余额管理"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出
            </Button>
            <Button variant="outline">
              <BarChart3 className="w-4 h-4 mr-2" />
              统计分析
            </Button>
          </div>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">待审批</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {stats.pending}
                </p>
              </div>
              <Clock className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已批准</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">
                  {stats.approved}
                </p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已拒绝</p>
                <p className="text-2xl font-bold text-red-400 mt-1">
                  {stats.rejected}
                </p>
              </div>
              <XCircle className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已批准天数</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {stats.totalDays}
                </p>
              </div>
              <Calendar className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="applications" className="space-y-4">
        <TabsList>
          <TabsTrigger value="applications">请假申请</TabsTrigger>
          <TabsTrigger value="balance">假期余额</TabsTrigger>
          <TabsTrigger value="statistics">统计分析</TabsTrigger>
        </TabsList>

        <TabsContent value="applications" className="space-y-4">
          {/* Statistics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>请假类型分布</CardTitle>
              </CardHeader>
              <CardContent>
                <SimplePieChart
                  data={[
                    {
                      label: "年假",
                      value: leaveApplications.filter((a) => a.type === "年假")
                        .length,
                      color: "#3b82f6",
                    },
                    {
                      label: "病假",
                      value: leaveApplications.filter((a) => a.type === "病假")
                        .length,
                      color: "#10b981",
                    },
                    {
                      label: "事假",
                      value: leaveApplications.filter((a) => a.type === "事假")
                        .length,
                      color: "#f59e0b",
                    },
                  ]}
                  size={180}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>月度请假趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <MonthlyTrendChart
                  data={[
                    { month: "2024-10", amount: 12 },
                    { month: "2024-11", amount: 15 },
                    { month: "2024-12", amount: 18 },
                    { month: "2025-01", amount: leaveApplications.length },
                  ]}
                  valueKey="amount"
                  labelKey="month"
                  height={150}
                />
              </CardContent>
            </Card>
          </div>

          {/* Trend Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <TrendComparisonCard
              title="待审批"
              current={stats.pending}
              previous={5}
            />
            <TrendComparisonCard
              title="已批准"
              current={stats.approved}
              previous={10}
            />
            <TrendComparisonCard
              title="已批准天数"
              current={stats.totalDays}
              previous={25}
            />
          </div>

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex gap-4">
                <Input
                  placeholder="搜索员工姓名、部门..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="flex-1"
                />
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white"
                >
                  <option value="all">全部类型</option>
                  <option value="年假">年假</option>
                  <option value="病假">病假</option>
                  <option value="事假">事假</option>
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white"
                >
                  <option value="all">全部状态</option>
                  <option value="pending">待审批</option>
                  <option value="approved">已批准</option>
                  <option value="rejected">已拒绝</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Applications List */}
          <div className="space-y-4">
            {filteredApplications.map((app) => (
              <Card key={app.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">
                          {app.employee}
                        </h3>
                        <Badge variant="outline">{app.department}</Badge>
                        <Badge variant="outline">{app.type}</Badge>
                        <Badge
                          variant="outline"
                          className={cn(
                            app.status === "pending" &&
                              "bg-amber-500/20 text-amber-400 border-amber-500/30",
                            app.status === "approved" &&
                              "bg-green-500/20 text-green-400 border-green-500/30",
                            app.status === "rejected" &&
                              "bg-red-500/20 text-red-400 border-red-500/30",
                          )}
                        >
                          {app.status === "pending"
                            ? "待审批"
                            : app.status === "approved"
                              ? "已批准"
                              : "已拒绝"}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                        <div>
                          <p className="text-slate-400">请假天数</p>
                          <p className="text-white font-medium">
                            {app.days} 天
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">开始日期</p>
                          <p className="text-white font-medium">
                            {app.startDate}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">结束日期</p>
                          <p className="text-white font-medium">
                            {app.endDate}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400">审批人</p>
                          <p className="text-white font-medium">
                            {app.approver}
                          </p>
                        </div>
                      </div>
                      <div className="text-sm text-slate-400 mb-2">
                        原因: {app.reason}
                      </div>
                      {app.rejectReason && (
                        <div className="text-sm text-red-400 mb-2">
                          拒绝原因: {app.rejectReason}
                        </div>
                      )}
                      <div className="text-xs text-slate-500">
                        提交时间: {app.submitTime}
                        {app.approveTime && ` · 审批时间: ${app.approveTime}`}
                      </div>
                    </div>
                    {app.status === "pending" && (
                      <div className="flex gap-2 ml-4">
                        <Button size="sm">批准</Button>
                        <Button size="sm" variant="outline">
                          拒绝
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="balance">
          <Card>
            <CardHeader>
              <CardTitle>假期余额</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-400">TODO: 员工假期余额列表</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="statistics">
          <Card>
            <CardHeader>
              <CardTitle>统计分析</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-400">TODO: 请假统计分析图表</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
