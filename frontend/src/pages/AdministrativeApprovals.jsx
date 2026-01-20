/**
 * Administrative Approvals - Administrative approval center
 * Features: Approval list, approval workflow, approval history
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Filter,
  ClipboardCheck,
  Package,
  Car,
  Building2,
  Calendar,
  User,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  Download,
  Loader2 } from
"lucide-react";
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
  TabsTrigger } from
"../components/ui";
import { cn, formatCurrency } from "../lib/utils";
import { staggerContainer } from "../lib/animations";
import {
  SimpleBarChart,
  MonthlyTrendChart,
  SimplePieChart,
  TrendComparisonCard } from
"../components/administrative/StatisticsCharts";
import { adminApi } from "../services/api";

export default function AdministrativeApprovals() {
  const [_loading, setLoading] = useState(true);
  const [approvals, setApprovals] = useState([]);
  const [approvedList, setApprovedList] = useState([]);
  const [rejectedList, setRejectedList] = useState([]);
  const [searchText, setSearchText] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await adminApi.approvals.list({ status: "pending" });
        if (res.data?.items) {
          setApprovals(res.data.items);
        }
      } catch (_err) {
        console.error("Failed to fetch pending approvals");
      }

      try {
        const approvedRes = await adminApi.approvals.list({
          status: "approved"
        });
        if (approvedRes.data?.items) {
          setApprovedList(approvedRes.data.items);
        }
      } catch (_err) {
        console.error("Failed to fetch approved list");
      }

      try {
        const rejectedRes = await adminApi.approvals.list({
          status: "rejected"
        });
        if (rejectedRes.data?.items) {
          setRejectedList(rejectedRes.data.items);
        }
      } catch (_err) {
        console.error("Failed to fetch rejected list");
      }

      setLoading(false);
    };
    fetchData();
  }, []);

  const filteredApprovals = useMemo(() => {
    return approvals.filter((approval) => {
      const matchSearch =
      approval.title.toLowerCase().includes(searchText.toLowerCase()) ||
      approval.applicant.toLowerCase().includes(searchText.toLowerCase());
      const matchType = typeFilter === "all" || approval.type === typeFilter;
      const matchPriority =
      priorityFilter === "all" || approval.priority === priorityFilter;
      return matchSearch && matchType && matchPriority;
    });
  }, [approvals, searchText, typeFilter, priorityFilter]);

  const stats = useMemo(() => {
    const total = approvals.length;
    const urgent = approvals.filter((a) => a.priority === "high").length;
    const officeSupplies = approvals.filter(
      (a) => a.type === "office_supplies"
    ).length;
    const vehicle = approvals.filter((a) => a.type === "vehicle").length;
    return { total, urgent, officeSupplies, vehicle };
  }, [approvals]);

  const handleApprove = async (id) => {
    try {
      await adminApi.approvals.approve(id, { comment: "同意" });
      setApprovals((prev) => prev.filter((a) => a.id !== id));
    } catch (_err) {
      console.error("Failed to approve request");
    }
  };

  const handleReject = async (id) => {
    try {
      await adminApi.approvals.reject(id, { reason: "不符合要求" });
      setApprovals((prev) => prev.filter((a) => a.id !== id));
    } catch (_err) {
      console.error("Failed to reject request");
    }
  };

  const getTypeIcon = (type) => {
    const icons = {
      office_supplies: Package,
      vehicle: Car,
      asset: Building2,
      meeting: Calendar,
      leave: User
    };
    return icons[type] || ClipboardCheck;
  };

  const getTypeLabel = (type) => {
    const labels = {
      office_supplies: "办公用品",
      vehicle: "车辆",
      asset: "资产",
      meeting: "会议",
      leave: "请假"
    };
    return labels[type] || "其他";
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="行政审批中心"
        description="行政类审批事项管理、审批流程、审批历史"
        actions={
        <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            导出
        </Button>
        } />


      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">待审批</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {stats.total}
                </p>
              </div>
              <ClipboardCheck className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">紧急事项</p>
                <p className="text-2xl font-bold text-red-400 mt-1">
                  {stats.urgent}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">办公用品</p>
                <p className="text-2xl font-bold text-blue-400 mt-1">
                  {stats.officeSupplies}
                </p>
              </div>
              <Package className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">车辆申请</p>
                <p className="text-2xl font-bold text-cyan-400 mt-1">
                  {stats.vehicle}
                </p>
              </div>
              <Car className="h-8 w-8 text-cyan-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="pending" className="space-y-4">
        <TabsList>
          <TabsTrigger value="pending">待审批</TabsTrigger>
          <TabsTrigger value="approved">已批准</TabsTrigger>
          <TabsTrigger value="rejected">已拒绝</TabsTrigger>
          <TabsTrigger value="history">审批历史</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          {/* Statistics Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>审批类型分布</CardTitle>
              </CardHeader>
              <CardContent>
                <SimplePieChart
                  data={[
                  {
                    label: "办公用品",
                    value: stats.officeSupplies,
                    color: "#3b82f6"
                  },
                  { label: "车辆", value: stats.vehicle, color: "#06b6d4" },
                  {
                    label: "资产",
                    value: approvals.filter((a) => a.type === "asset").length,
                    color: "#a855f7"
                  },
                  {
                    label: "会议",
                    value: approvals.filter((a) => a.type === "meeting").
                    length,
                    color: "#10b981"
                  },
                  {
                    label: "请假",
                    value: approvals.filter((a) => a.type === "leave").length,
                    color: "#f472b6"
                  }]
                  }
                  size={180} />

              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>月度审批趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <MonthlyTrendChart
                  data={[
                  { month: "2024-10", amount: 18 },
                  { month: "2024-11", amount: 22 },
                  { month: "2024-12", amount: 20 },
                  { month: "2025-01", amount: stats.total }]
                  }
                  valueKey="amount"
                  labelKey="month"
                  height={150} />

              </CardContent>
            </Card>
          </div>

          {/* Trend Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <TrendComparisonCard
              title="待审批总数"
              current={stats.total}
              previous={20} />

            <TrendComparisonCard
              title="紧急事项"
              current={stats.urgent}
              previous={5} />

            <TrendComparisonCard
              title="办公用品审批"
              current={stats.officeSupplies}
              previous={8} />

          </div>

          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="flex gap-4">
                <Input
                  placeholder="搜索申请标题、申请人..."
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  className="flex-1" />

                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white">

                  <option value="all">全部类型</option>
                  <option value="office_supplies">办公用品</option>
                  <option value="vehicle">车辆</option>
                  <option value="asset">资产</option>
                  <option value="meeting">会议</option>
                  <option value="leave">请假</option>
                </select>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white">

                  <option value="all">全部优先级</option>
                  <option value="high">紧急</option>
                  <option value="medium">普通</option>
                  <option value="low">低</option>
                </select>
              </div>
            </CardContent>
          </Card>

          {/* Approvals List */}
          <div className="space-y-4">
            {filteredApprovals.map((approval) => {
              const TypeIcon = getTypeIcon(approval.type);
              return (
                <Card key={approval.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <TypeIcon className="h-5 w-5 text-slate-400" />
                          <h3 className="text-lg font-semibold text-white">
                            {approval.title}
                          </h3>
                          <Badge
                            variant="outline"
                            className={cn(
                              approval.type === "office_supplies" &&
                              "bg-blue-500/20 text-blue-400 border-blue-500/30",
                              approval.type === "vehicle" &&
                              "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                              approval.type === "asset" &&
                              "bg-purple-500/20 text-purple-400 border-purple-500/30",
                              approval.type === "meeting" &&
                              "bg-green-500/20 text-green-400 border-green-500/30",
                              approval.type === "leave" &&
                              "bg-pink-500/20 text-pink-400 border-pink-500/30"
                            )}>

                            {getTypeLabel(approval.type)}
                          </Badge>
                          {approval.priority === "high" &&
                          <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                          </Badge>
                          }
                        </div>
                        <div className="text-sm text-slate-400 mb-2">
                          {approval.department} · {approval.applicant}
                        </div>
                        <div className="text-sm text-slate-500 mb-3">
                          {approval.items &&
                          `物品: ${approval.items.join("、")}`}
                          {approval.purpose &&
                          `用途: ${approval.purpose} · 目的地: ${approval.destination || "待定"}`}
                          {approval.item && `资产: ${approval.item}`}
                          {approval.room &&
                          `会议室: ${approval.room} · 时间: ${approval.date} ${approval.time}`}
                          {approval.leaveType &&
                          `类型: ${approval.leaveType} · 天数: ${approval.days} 天 · 日期: ${approval.date}`}
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-500">
                            提交时间: {approval.submitTime}
                          </span>
                          {approval.amount &&
                          <span className="font-medium text-amber-400">
                              {formatCurrency(approval.amount)}
                          </span>
                          }
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleApprove(approval.id)}>

                          批准
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleReject(approval.id)}>

                          拒绝
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>);

            })}
          </div>
        </TabsContent>

        <TabsContent value="approved" className="space-y-4">
          {approvedList.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <CheckCircle2 className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">暂无已批准记录</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {approvedList.map((approval) => {
                const TypeIcon = getTypeIcon(approval.type);
                return (
                  <Card key={approval.id}>
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <TypeIcon className="h-5 w-5 text-slate-400" />
                            <h3 className="text-lg font-semibold text-white">
                              {approval.title}
                            </h3>
                            <Badge
                              variant="outline"
                              className={cn(
                                approval.type === "office_supplies" &&
                                "bg-blue-500/20 text-blue-400 border-blue-500/30",
                                approval.type === "vehicle" &&
                                "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                                approval.type === "asset" &&
                                "bg-purple-500/20 text-purple-400 border-purple-500/30",
                                approval.type === "meeting" &&
                                "bg-green-500/20 text-green-400 border-green-500/30",
                                approval.type === "leave" &&
                                "bg-pink-500/20 text-pink-400 border-pink-500/30"
                              )}>
                              {getTypeLabel(approval.type)}
                            </Badge>
                            <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              已批准
                            </Badge>
                          </div>
                          <div className="text-sm text-slate-400 mb-2">
                            {approval.department} · {approval.applicant}
                          </div>
                          <div className="text-sm text-slate-500 mb-3">
                            {approval.items && `物品: ${approval.items.join("、")}`}
                            {approval.purpose && `用途: ${approval.purpose}`}
                            {approval.item && `资产: ${approval.item}`}
                          </div>
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            <span>提交: {approval.submitTime}</span>
                            {approval.approvedTime && (
                              <span className="text-green-400">
                                批准: {approval.approvedTime}
                              </span>
                            )}
                            {approval.approver && (
                              <span>审批人: {approval.approver}</span>
                            )}
                            {approval.amount && (
                              <span className="font-medium text-amber-400">
                                {formatCurrency(approval.amount)}
                              </span>
                            )}
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="rejected" className="space-y-4">
          {rejectedList.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <XCircle className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">暂无已拒绝记录</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {rejectedList.map((approval) => {
                const TypeIcon = getTypeIcon(approval.type);
                return (
                  <Card key={approval.id}>
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <TypeIcon className="h-5 w-5 text-slate-400" />
                            <h3 className="text-lg font-semibold text-white">
                              {approval.title}
                            </h3>
                            <Badge
                              variant="outline"
                              className={cn(
                                approval.type === "office_supplies" &&
                                "bg-blue-500/20 text-blue-400 border-blue-500/30",
                                approval.type === "vehicle" &&
                                "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                                approval.type === "asset" &&
                                "bg-purple-500/20 text-purple-400 border-purple-500/30",
                                approval.type === "meeting" &&
                                "bg-green-500/20 text-green-400 border-green-500/30",
                                approval.type === "leave" &&
                                "bg-pink-500/20 text-pink-400 border-pink-500/30"
                              )}>
                              {getTypeLabel(approval.type)}
                            </Badge>
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                              <XCircle className="w-3 h-3 mr-1" />
                              已拒绝
                            </Badge>
                          </div>
                          <div className="text-sm text-slate-400 mb-2">
                            {approval.department} · {approval.applicant}
                          </div>
                          <div className="text-sm text-slate-500 mb-3">
                            {approval.items && `物品: ${approval.items.join("、")}`}
                            {approval.purpose && `用途: ${approval.purpose}`}
                            {approval.item && `资产: ${approval.item}`}
                          </div>
                          {approval.rejectReason && (
                            <div className="text-sm text-red-400/80 mb-3 p-2 bg-red-500/10 rounded">
                              拒绝原因: {approval.rejectReason}
                            </div>
                          )}
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            <span>提交: {approval.submitTime}</span>
                            {approval.rejectedTime && (
                              <span className="text-red-400">
                                拒绝: {approval.rejectedTime}
                              </span>
                            )}
                            {approval.approver && (
                              <span>审批人: {approval.approver}</span>
                            )}
                            {approval.amount && (
                              <span className="font-medium text-amber-400">
                                {formatCurrency(approval.amount)}
                              </span>
                            )}
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          {approvedList.length === 0 && rejectedList.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Clock className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">暂无审批历史记录</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {/* Combine and sort by time - approved items marked with status */}
              {[
                ...approvedList.map(item => ({ ...item, status: 'approved' })),
                ...rejectedList.map(item => ({ ...item, status: 'rejected' }))
              ]
                .sort((a, b) => {
                  const timeA = a.approvedTime || a.rejectedTime || a.submitTime || '';
                  const timeB = b.approvedTime || b.rejectedTime || b.submitTime || '';
                  return timeB.localeCompare(timeA);
                })
                .map((approval) => {
                  const TypeIcon = getTypeIcon(approval.type);
                  const isApproved = approval.status === 'approved';
                  return (
                    <Card key={`${approval.status}-${approval.id}`}>
                      <CardContent className="p-6">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <TypeIcon className="h-5 w-5 text-slate-400" />
                              <h3 className="text-lg font-semibold text-white">
                                {approval.title}
                              </h3>
                              <Badge
                                variant="outline"
                                className={cn(
                                  approval.type === "office_supplies" &&
                                  "bg-blue-500/20 text-blue-400 border-blue-500/30",
                                  approval.type === "vehicle" &&
                                  "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                                  approval.type === "asset" &&
                                  "bg-purple-500/20 text-purple-400 border-purple-500/30",
                                  approval.type === "meeting" &&
                                  "bg-green-500/20 text-green-400 border-green-500/30",
                                  approval.type === "leave" &&
                                  "bg-pink-500/20 text-pink-400 border-pink-500/30"
                                )}>
                                {getTypeLabel(approval.type)}
                              </Badge>
                              {isApproved ? (
                                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                                  <CheckCircle2 className="w-3 h-3 mr-1" />
                                  已批准
                                </Badge>
                              ) : (
                                <Badge className="bg-red-500/20 text-red-400 border-red-500/30">
                                  <XCircle className="w-3 h-3 mr-1" />
                                  已拒绝
                                </Badge>
                              )}
                            </div>
                            <div className="text-sm text-slate-400 mb-2">
                              {approval.department} · {approval.applicant}
                            </div>
                            <div className="text-sm text-slate-500 mb-3">
                              {approval.items && `物品: ${approval.items.join("、")}`}
                              {approval.purpose && `用途: ${approval.purpose}`}
                              {approval.item && `资产: ${approval.item}`}
                            </div>
                            {!isApproved && approval.rejectReason && (
                              <div className="text-sm text-red-400/80 mb-3 p-2 bg-red-500/10 rounded">
                                拒绝原因: {approval.rejectReason}
                              </div>
                            )}
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                              <span>提交: {approval.submitTime}</span>
                              {isApproved && approval.approvedTime && (
                                <span className="text-green-400">
                                  批准: {approval.approvedTime}
                                </span>
                              )}
                              {!isApproved && approval.rejectedTime && (
                                <span className="text-red-400">
                                  拒绝: {approval.rejectedTime}
                                </span>
                              )}
                              {approval.approver && (
                                <span>审批人: {approval.approver}</span>
                              )}
                              {approval.amount && (
                                <span className="font-medium text-amber-400">
                                  {formatCurrency(approval.amount)}
                                </span>
                              )}
                            </div>
                          </div>
                          <Button variant="outline" size="sm">
                            <Eye className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </motion.div>);

}