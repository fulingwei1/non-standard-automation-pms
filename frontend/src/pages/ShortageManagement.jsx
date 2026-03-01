/**
 * Shortage Management - 缺料管理
 * Features: 缺料上报、到货跟踪、物料替代、物料调拨、统计分析
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Package,
  AlertTriangle,
  Truck,
  RefreshCw,
  ArrowRightLeft,
  BarChart3,
  Plus,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  Clock,
  XCircle,
  TrendingUp,
  TrendingDown } from
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
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { cn } from "../lib/utils";
import { fadeIn as _fadeIn, staggerContainer } from "../lib/animations";
import { shortageApi } from "../services/api";

const statusConfigs = {
  REPORTED: { label: "已上报", color: "bg-blue-500", icon: Clock },
  CONFIRMED: { label: "已确认", color: "bg-amber-500", icon: CheckCircle2 },
  HANDLING: { label: "处理中", color: "bg-purple-500", icon: RefreshCw },
  RESOLVED: { label: "已解决", color: "bg-emerald-500", icon: CheckCircle2 }
};

const urgentLevelConfigs = {
  NORMAL: { label: "普通", color: "text-slate-400" },
  URGENT: { label: "紧急", color: "text-amber-400" },
  CRITICAL: { label: "特急", color: "text-red-400" }
};

export default function ShortageManagement() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboardData, setDashboardData] = useState(null);
  const [reports, setReports] = useState([]);
  const [arrivals, setArrivals] = useState([]);
  const [substitutions, setSubstitutions] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [arrivalFilters, setArrivalFilters] = useState({
    status: "",
    is_delayed: false
  });

  useEffect(() => {
    loadDashboard();
  }, []);

  useEffect(() => {
    if (activeTab === "reports") {
      setPage(1);
      loadReports();
    } else if (activeTab === "arrivals") {
      loadArrivals();
    } else if (activeTab === "substitutions") {
      loadSubstitutions();
    } else if (activeTab === "transfers") {
      loadTransfers();
    }
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === "reports") {
      setPage(1);
      loadReports();
    }
  }, [searchKeyword, statusFilter]);

  useEffect(() => {
    if (activeTab === "reports") {
      loadReports();
    }
  }, [page]);

  useEffect(() => {
    if (activeTab === "arrivals") {
      loadArrivals();
    }
  }, [arrivalFilters]);

  const loadDashboard = async () => {
    try {
      const res = await shortageApi.statistics.dashboard();
      setDashboardData(res.data.data);
    } catch (error) {
      console.error("加载看板数据失败", error);
    }
  };

  const loadReports = async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchKeyword || undefined,
        status: statusFilter || undefined
      };
      const res = await shortageApi.reports.list(params);
      setReports(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (error) {
      console.error("加载缺料上报列表失败", error);
    } finally {
      setLoading(false);
    }
  };

  const loadArrivals = async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 20,
        status: arrivalFilters.status || undefined,
        is_delayed: arrivalFilters.is_delayed || undefined
      };
      const res = await shortageApi.arrivals.list(params);
      setArrivals(res.data.items || []);
    } catch (error) {
      console.error("加载到货跟踪列表失败", error);
    } finally {
      setLoading(false);
    }
  };

  const loadSubstitutions = async () => {
    setLoading(true);
    try {
      const res = await shortageApi.substitutions.list({
        page: 1,
        page_size: 20
      });
      setSubstitutions(res.data.items || []);
    } catch (error) {
      console.error("加载物料替代列表失败", error);
    } finally {
      setLoading(false);
    }
  };

  const loadTransfers = async () => {
    setLoading(true);
    try {
      const res = await shortageApi.transfers.list({ page: 1, page_size: 20 });
      setTransfers(res.data.items || []);
    } catch (error) {
      console.error("加载物料调拨列表失败", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="缺料管理"
        description="缺料上报、到货跟踪、物料替代、物料调拨" />


      <Tabs
        value={activeTab || "unknown"}
        onValueChange={setActiveTab}
        className="space-y-6">

        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="dashboard">看板</TabsTrigger>
          <TabsTrigger value="reports">缺料上报</TabsTrigger>
          <TabsTrigger value="arrivals">到货跟踪</TabsTrigger>
          <TabsTrigger value="substitutions">物料替代</TabsTrigger>
          <TabsTrigger value="transfers">物料调拨</TabsTrigger>
        </TabsList>

        {/* 看板 */}
        <TabsContent value="dashboard" className="space-y-6">
          {dashboardData &&
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    缺料上报总数
                  </CardTitle>
                  <Package className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardData.reports?.total || 0}
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge
                    variant="outline"
                    className="bg-blue-500/20 text-blue-400">

                      已上报: {dashboardData.reports?.reported || 0}
                    </Badge>
                    <Badge
                    variant="outline"
                    className="bg-amber-500/20 text-amber-400">

                      处理中: {dashboardData.reports?.handling || 0}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    紧急缺料
                  </CardTitle>
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-400">
                    {dashboardData.reports?.urgent || 0}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    需要立即处理
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    到货跟踪
                  </CardTitle>
                  <Truck className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {dashboardData.arrivals?.total || 0}
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge
                    variant="outline"
                    className="bg-amber-500/20 text-amber-400">

                      待处理: {dashboardData.arrivals?.pending || 0}
                    </Badge>
                    <Badge
                    variant="outline"
                    className="bg-red-500/20 text-red-400">

                      延迟: {dashboardData.arrivals?.delayed || 0}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">待审批</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {(dashboardData.substitutions?.pending || 0) + (
                  dashboardData.transfers?.pending || 0)}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    替代: {dashboardData.substitutions?.pending || 0} | 调拨:{" "}
                    {dashboardData.transfers?.pending || 0}
                  </p>
                </CardContent>
              </Card>
          </motion.div>
          }

          {/* 最近缺料上报 */}
          {dashboardData?.recent_reports &&
          dashboardData.recent_reports?.length > 0 &&
          <Card>
                <CardHeader>
                  <CardTitle>最近缺料上报</CardTitle>
                  <CardDescription>最近10条缺料上报记录</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {(dashboardData.recent_reports || []).map((report) => {
                  const urgent =
                  urgentLevelConfigs[report.urgent_level] ||
                  urgentLevelConfigs.NORMAL;
                  const status =
                  statusConfigs[report.status] || statusConfigs.REPORTED;
                  return (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-surface-2 transition-colors">

                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">
                                {report.report_no}
                              </span>
                              <Badge
                            variant="outline"
                            className={cn(urgent.color)}>

                                {urgent.label}
                              </Badge>
                              <Badge
                            variant="outline"
                            className={cn(status.color, "text-white")}>

                                {status.label}
                              </Badge>
                            </div>
                            <div className="text-sm text-muted-foreground mt-1">
                              {report.project_name} - {report.material_name}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-medium">
                              缺料: {report.shortage_qty}
                            </div>
                            <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                          navigate(`/shortage/reports/${report.id}`)
                          }>

                              <Eye className="h-4 w-4" />
                            </Button>
                          </div>
                    </div>);

                })}
                  </div>
                </CardContent>
          </Card>
          }
        </TabsContent>

        {/* 缺料上报 */}
        <TabsContent value="reports" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>缺料上报</CardTitle>
                  <CardDescription>车间缺料上报记录</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="搜索上报单号、物料..."
                      className="pl-8 w-64"
                      value={searchKeyword || "unknown"}
                      onChange={(e) => setSearchKeyword(e.target.value)} />

                  </div>
                  <Select value={statusFilter || "unknown"} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="全部状态" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      <SelectItem value="REPORTED">已上报</SelectItem>
                      <SelectItem value="CONFIRMED">已确认</SelectItem>
                      <SelectItem value="HANDLING">处理中</SelectItem>
                      <SelectItem value="RESOLVED">已解决</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button onClick={() => navigate("/shortage/reports/new")}>
                    <Plus className="h-4 w-4 mr-2" />
                    新建上报
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ?
              <div className="text-center py-8 text-muted-foreground">
                  加载中...
              </div> :
              reports.length === 0 ?
              <div className="text-center py-8 text-muted-foreground">
                  暂无缺料上报记录
              </div> :

              <div className="space-y-3">
                  {(reports || []).map((report) => {
                  const urgent =
                  urgentLevelConfigs[report.urgent_level] ||
                  urgentLevelConfigs.NORMAL;
                  const status =
                  statusConfigs[report.status] || statusConfigs.REPORTED;
                  return (
                    <div
                      key={report.id}
                      className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors">

                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-medium">
                              {report.report_no}
                            </span>
                            <Badge
                            variant="outline"
                            className={cn(urgent.color)}>

                              {urgent.label}
                            </Badge>
                            <Badge
                            variant="outline"
                            className={cn(status.color, "text-white")}>

                              {status.label}
                            </Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {report.project_name} - {report.material_name} |
                            缺料: {report.shortage_qty}
                          </div>
                          <div className="text-xs text-muted-foreground mt-1">
                            上报人: {report.reporter_name} |{" "}
                            {new Date(report.report_time).toLocaleString()}
                          </div>
                        </div>
                        <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                        navigate(`/shortage/reports/${report.id}`)
                        }>

                          <Eye className="h-4 w-4 mr-2" />
                          查看
                        </Button>
                    </div>);

                })}
              </div>
              }
              {total > pageSize &&
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <div className="text-sm text-muted-foreground">
                    共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)}{" "}
                    页
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1 || loading}>

                      上一页
                    </Button>
                    <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                    setPage((p) =>
                    Math.min(Math.ceil(total / pageSize), p + 1)
                    )
                    }
                    disabled={page >= Math.ceil(total / pageSize) || loading}>

                      下一页
                    </Button>
                  </div>
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* 到货跟踪 */}
        <TabsContent value="arrivals" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>到货跟踪</CardTitle>
                  <CardDescription>物料到货跟踪记录</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setArrivalFilters((prev) => ({
                        ...prev,
                        is_delayed: !prev.is_delayed
                      }));
                      loadArrivals();
                    }}>

                    <AlertTriangle className="h-4 w-4 mr-2" />
                    {arrivalFilters.is_delayed ? "全部" : "延迟预警"}
                  </Button>
                  <Button onClick={() => navigate("/shortage/arrivals/new")}>
                    <Plus className="h-4 w-4 mr-2" />
                    新建跟踪
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ?
              <div className="text-center py-8 text-muted-foreground">
                  加载中...
              </div> :
              arrivals.length === 0 ?
              <div className="text-center py-8 text-muted-foreground">
                  暂无到货跟踪记录
              </div> :

              <div className="space-y-3">
                  {(arrivals || []).map((arrival) =>
                <div
                  key={arrival.id}
                  className={cn(
                    "flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors",
                    arrival.is_delayed && "bg-red-500/5 border-red-500/20"
                  )}>

                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium">
                            {arrival.arrival_no}
                          </span>
                          {arrival.is_delayed &&
                      <Badge
                        variant="outline"
                        className="bg-red-500/20 text-red-400">

                              延迟 {arrival.delay_days} 天
                      </Badge>
                      }
                          <Badge variant="outline">{arrival.status}</Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {arrival.material_name} | 预期: {arrival.expected_qty}{" "}
                          | 状态: {arrival.status}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          供应商: {arrival.supplier_name} | 预期日期:{" "}
                          {arrival.expected_date}
                        </div>
                      </div>
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                    navigate(`/shortage/arrivals/${arrival.id}`)
                    }>

                        <Eye className="h-4 w-4 mr-2" />
                        查看
                      </Button>
                </div>
                )}
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* 物料替代 */}
        <TabsContent value="substitutions" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>物料替代</CardTitle>
                  <CardDescription>物料替代申请记录</CardDescription>
                </div>
                <Button onClick={() => navigate("/shortage/substitutions/new")}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建申请
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ?
              <div className="text-center py-8 text-muted-foreground">
                  加载中...
              </div> :
              substitutions.length === 0 ?
              <div className="text-center py-8 text-muted-foreground">
                  暂无物料替代申请
              </div> :

              <div className="space-y-3">
                  {(substitutions || []).map((sub) =>
                <div
                  key={sub.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors">

                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium">
                            {sub.substitution_no}
                          </span>
                          <Badge variant="outline">{sub.status}</Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {sub.original_material_name} →{" "}
                          {sub.substitute_material_name}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {sub.project_name} | 原因: {sub.substitution_reason}
                        </div>
                      </div>
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                    navigate(`/shortage/substitutions/${sub.id}`)
                    }>

                        <Eye className="h-4 w-4 mr-2" />
                        查看
                      </Button>
                </div>
                )}
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* 物料调拨 */}
        <TabsContent value="transfers" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>物料调拨</CardTitle>
                  <CardDescription>物料调拨申请记录</CardDescription>
                </div>
                <Button onClick={() => navigate("/shortage/transfers/new")}>
                  <Plus className="h-4 w-4 mr-2" />
                  新建申请
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading ?
              <div className="text-center py-8 text-muted-foreground">
                  加载中...
              </div> :
              transfers.length === 0 ?
              <div className="text-center py-8 text-muted-foreground">
                  暂无物料调拨申请
              </div> :

              <div className="space-y-3">
                  {(transfers || []).map((transfer) =>
                <div
                  key={transfer.id}
                  className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-surface-2 transition-colors">

                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium">
                            {transfer.transfer_no}
                          </span>
                          <Badge variant="outline">{transfer.status}</Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {transfer.from_project_name || "总库存"} →{" "}
                          {transfer.to_project_name}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {transfer.material_name} | 数量:{" "}
                          {transfer.transfer_qty}
                        </div>
                      </div>
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                    navigate(`/shortage/transfers/${transfer.id}`)
                    }>

                        <Eye className="h-4 w-4 mr-2" />
                        查看
                      </Button>
                </div>
                )}
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>);

}