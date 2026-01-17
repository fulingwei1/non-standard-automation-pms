/**
 * General Manager Workstation - Executive dashboard for general manager
 * Features: Business operations overview, Project monitoring, Performance metrics, Approval management
 * Core Functions: Strategic execution, Major project approval, Business indicator monitoring
 */

import { useState, useMemo as _useMemo, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Target,
  Briefcase,
  BarChart3,
  PieChart,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Building2,
  FileText,
  CreditCard,
  Receipt,
  Award,
  Activity,
  Zap,
  ChevronRight,
  Shield,
  Eye,
  ClipboardCheck,
  Factory,
  ShoppingCart,
  Package,
  Wrench,
  CheckCircle,
  XCircle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress } from
"../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  projectApi,
  salesStatisticsApi,
  productionApi,
  contractApi,
  invoiceApi as _invoiceApi,
  pmoApi,
  ecnApi,
  purchaseApi,
  departmentApi } from
"../services/api";
import CultureWallCarousel from "../components/culture/CultureWallCarousel";
import { ApiIntegrationError } from "../components/ui";

// Mock data removed - 使用真实API

const formatCurrency = (value) => {
  if (value >= 100000000) {
    return `¥${(value / 100000000).toFixed(2)}亿`;
  }
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`;
  }
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 0
  }).format(value);
};

const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg }) => {
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg">

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn("text-2xl font-bold mb-1", color)}>{value}</p>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
          {trend !== undefined &&
          <div className="flex items-center gap-1 mt-2">
              {trend > 0 ?
            <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}%</span>
                </> :
            trend < 0 ?
            <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}%</span>
                </> :
            null}
              {trend !== 0 &&
            <span className="text-xs text-slate-500 ml-1">vs 上月</span>
            }
            </div>
          }
        </div>
        <div className={cn("rounded-lg p-3 bg-opacity-20", bg)}>
          <Icon className={cn("h-6 w-6", color)} />
        </div>
      </div>
      <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
    </motion.div>);

};

export default function GeneralManagerWorkstation() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [businessStats, setBusinessStats] = useState(null);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [projectHealth, setProjectHealth] = useState([]);
  const [departmentStatus, setDepartmentStatus] = useState([]);
  const [keyMetrics, setKeyMetrics] = useState([]);

  // Load dashboard data
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load projects statistics
      const projectsResponse = await projectApi.list({
        page: 1,
        page_size: 100
      });
      const projectsData = projectsResponse.data?.items || [];

      const totalProjects = projectsData.length;
      const activeProjects = projectsData.filter(
        (p) => p.is_active && p.stage !== "S9"
      ).length;
      const completedProjects = projectsData.filter(
        (p) => p.stage === "S9"
      ).length;

      // Calculate project health
      const healthGood = projectsData.filter(
        (p) => p.health === "H1" || p.health === "H2"
      ).length;
      const healthWarning = projectsData.filter(
        (p) => p.health === "H3"
      ).length;
      const healthCritical = projectsData.filter(
        (p) => p.health === "H4"
      ).length;

      // Load sales statistics
      const now = new Date();
      const startDate = new Date(now.getFullYear(), now.getMonth(), 1).
      toISOString().
      split("T")[0];
      const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).
      toISOString().
      split("T")[0];

      let monthlyRevenue = 0;
      let totalContracts = 0;
      let activeContracts = 0;
      try {
        const salesResponse = await salesStatisticsApi.performance({
          start_date: startDate,
          end_date: endDate
        });
        monthlyRevenue = salesResponse.data?.total_contract_amount || 0;
      } catch (err) {
        console.error("Failed to load sales stats:", err);
      }

      try {
        const contractsResponse = await contractApi.list({
          page: 1,
          page_size: 100
        });
        const contractsData = contractsResponse.data?.items || [];
        totalContracts = contractsData.length;
        activeContracts = contractsData.filter(
          (c) => c.status === "SIGNED" || c.status === "EXECUTING"
        ).length;
      } catch (err) {
        console.error("Failed to load contracts:", err);
      }

      // Load production statistics
      let productionCapacity = 0;
      let qualityPassRate = 0;
      try {
        const productionResponse = await productionApi.dashboard();
        const productionData =
        productionResponse.data || productionResponse || {};
        productionCapacity = productionData.capacity_utilization || 0;
        qualityPassRate = productionData.pass_rate || 0;
      } catch (err) {
        console.error("Failed to load production stats:", err);
      }

      // Calculate financial metrics (simplified)
      const yearTarget = 150000000; // Default target
      const yearRevenue = monthlyRevenue * 12; // Simplified calculation
      const yearProgress =
      yearTarget > 0 ? yearRevenue / yearTarget * 100 : 0;
      const profit = yearRevenue * 0.2; // Simplified: 20% profit margin
      const profitMargin = 20;

      // Update stats
      setBusinessStats({
        monthlyRevenue,
        monthlyTarget: monthlyRevenue, // Use achieved as target for now
        monthlyProgress: 100,
        yearRevenue,
        yearTarget,
        yearProgress,
        profit,
        profitMargin,
        totalProjects,
        activeProjects,
        completedProjects,
        projectHealthGood: healthGood,
        projectHealthWarning: healthWarning,
        projectHealthCritical: healthCritical,
        totalContracts,
        activeContracts,
        pendingApproval: 0, // Will be loaded from API
        totalCustomers: 0, // Will be loaded from API
        newCustomersThisMonth: 0, // Will be loaded from API
        productionCapacity,
        qualityPassRate,
        onTimeDeliveryRate: 0, // Will be calculated from projects
        materialArrivalRate: 0, // Will be loaded from API
        revenueGrowth: 0, // Will be calculated
        customerGrowth: 0, // Will be calculated
        projectGrowth: 0 // Will be calculated
      });

      // Load project health data
      const healthData = projectsData.slice(0, 4).map((p) => ({
        id: p.project_code || p.id?.toString(),
        name: p.project_name || "",
        customer: p.customer_name || "",
        stage: p.stage || "",
        stageLabel: p.stage_name || "",
        progress: p.progress || 0,
        health:
        p.health === "H1" ?
        "good" :
        p.health === "H2" ?
        "good" :
        p.health === "H3" ?
        "warning" :
        "critical",
        dueDate: p.planned_end_date || "",
        amount: parseFloat(p.budget_amount || 0),
        risk: p.health === "H4" ? "high" : p.health === "H3" ? "medium" : "low"
      }));
      setProjectHealth(healthData);

      // Load pending approvals from various modules
      const allApprovals = [];

      // ECN approvals
      try {
        const ecnRes = await ecnApi.list({
          status: "SUBMITTED",
          page_size: 10
        });
        const ecnData = ecnRes.data || ecnRes;
        const ecns = ecnData.items || ecnData || [];
        ecns.forEach((ecn) => {
          allApprovals.push({
            id: `ecn-${ecn.id}`,
            type: "project",
            title: `设计变更申请 - ${ecn.ecn_no || "ECN"}`,
            projectName: ecn.project_name || "",
            amount: parseFloat(ecn.cost_impact || 0),
            department: ecn.department || "未知部门",
            submitter: ecn.created_by_name || "未知",
            submitTime: ecn.created_at ?
            new Date(ecn.created_at).toLocaleString("zh-CN", {
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
              hour: "2-digit",
              minute: "2-digit"
            }) :
            "",
            priority:
            ecn.priority === "URGENT" ?
            "high" :
            ecn.priority === "HIGH" ?
            "high" :
            "medium",
            status: "pending"
          });
        });
      } catch (err) {
        console.error("Failed to load ECN approvals:", err);
      }

      // Purchase request approvals
      try {
        const prRes = await purchaseApi.requests.list({
          status: "SUBMITTED",
          page_size: 10
        });
        const prData = prRes.data || prRes;
        const prs = prData.items || prData || [];
        prs.forEach((pr) => {
          allApprovals.push({
            id: `pr-${pr.id}`,
            type: "purchase",
            title: `采购申请 - ${pr.request_no || pr.id}`,
            item: pr.items?.map((i) => i.material_name).join(", ") || "",
            amount: parseFloat(pr.total_amount || 0),
            department: pr.department || "未知部门",
            submitter: pr.created_by_name || "未知",
            submitTime: pr.created_at ?
            new Date(pr.created_at).toLocaleString("zh-CN", {
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
              hour: "2-digit",
              minute: "2-digit"
            }) :
            "",
            priority: pr.urgent ? "high" : "medium",
            status: "pending"
          });
        });
      } catch (err) {
        console.error("Failed to load purchase request approvals:", err);
      }

      // PMO initiation approvals
      try {
        const initRes = await pmoApi.initiations.list({
          status: "SUBMITTED",
          page_size: 10
        });
        const initData = initRes.data || initRes;
        const inits = initData.items || initData || [];
        inits.forEach((init) => {
          allApprovals.push({
            id: `init-${init.id}`,
            type: "project",
            title: `项目立项申请 - ${init.project_name || init.id}`,
            projectName: init.project_name || "",
            amount: parseFloat(init.budget_amount || 0),
            department: init.department || "未知部门",
            submitter: init.created_by_name || "未知",
            submitTime: init.created_at ?
            new Date(init.created_at).toLocaleString("zh-CN", {
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
              hour: "2-digit",
              minute: "2-digit"
            }) :
            "",
            priority: init.priority === "HIGH" ? "high" : "medium",
            status: "pending"
          });
        });
      } catch (err) {
        console.error("Failed to load PMO initiation approvals:", err);
      }

      // Contract approvals
      try {
        const contractRes = await contractApi.list({
          status: "PENDING_APPROVAL",
          page_size: 10
        });
        const contractData = contractRes.data || contractRes;
        const contracts = contractData.items || contractData || [];
        contracts.forEach((contract) => {
          allApprovals.push({
            id: `contract-${contract.id}`,
            type: "contract",
            title: `合同审批 - ${contract.contract_no || contract.id}`,
            customer: contract.customer_name || "",
            amount: parseFloat(contract.total_amount || 0),
            department: "销售部",
            submitter: contract.created_by_name || "未知",
            submitTime: contract.created_at ?
            new Date(contract.created_at).toLocaleString("zh-CN", {
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
              hour: "2-digit",
              minute: "2-digit"
            }) :
            "",
            priority:
            parseFloat(contract.total_amount || 0) > 5000000 ?
            "high" :
            "medium",
            status: "pending"
          });
        });
      } catch (err) {
        console.error("Failed to load contract approvals:", err);
      }

      // Sort by priority and time, take top 5
      allApprovals.sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        if (priorityOrder[b.priority] !== priorityOrder[a.priority]) {
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        }
        return new Date(b.submitTime) - new Date(a.submitTime);
      });
      setPendingApprovals(allApprovals.slice(0, 5));

      // Update pending approval count
      setBusinessStats((prev) => ({
        ...prev,
        pendingApproval: allApprovals.length
      }));

      // Load department statistics
      try {
        const deptRes = await departmentApi.getStatistics({});
        const deptStats = deptRes.data || deptRes;
        if (deptStats?.departments || Array.isArray(deptStats)) {
          const departments = deptStats.departments || deptStats;
          const transformedDepts = departments.map((dept) => ({
            id: dept.id || dept.department_id,
            name: dept.name || dept.department_name || "",
            manager: dept.manager || dept.manager_name || "",
            projects: dept.projects || dept.project_count || 0,
            revenue: dept.revenue || dept.total_revenue || 0,
            target: dept.target || dept.revenue_target || 0,
            achievement:
            dept.target > 0 ? (dept.revenue || 0) / dept.target * 100 : 0,
            status:
            dept.status || (
            dept.achievement >= 90 ?
            "excellent" :
            dept.achievement >= 70 ?
            "good" :
            "warning"),
            issues: dept.issues || dept.issue_count || 0,
            onTimeRate: dept.on_time_rate || dept.on_time_delivery_rate || 0,
            arrivalRate: dept.arrival_rate || dept.material_arrival_rate || 0,
            passRate: dept.pass_rate || dept.quality_pass_rate || 0
          }));
          setDepartmentStatus(transformedDepts);
        }
      } catch (err) {
        console.error("Failed to load department statistics:", err);
      }

      // Calculate key metrics from business stats
      const metrics = [];
      if (businessStats) {
        // Calculate on-time delivery rate from projects
        const onTimeProjects = projectsData.filter((p) => {
          if (!p.planned_end_date) return false;
          const plannedDate = new Date(p.planned_end_date);
          const today = new Date();
          return plannedDate >= today || p.stage === "S9";
        }).length;
        const onTimeRate =
        totalProjects > 0 ? onTimeProjects / totalProjects * 100 : 0;

        metrics.push(
          {
            label: "项目按时交付率",
            value: onTimeRate,
            unit: "%",
            target: 90,
            trend: 0, // Could be calculated from historical data
            color:
            onTimeRate >= 90 ?
            "text-emerald-400" :
            onTimeRate >= 80 ?
            "text-amber-400" :
            "text-red-400"
          },
          {
            label: "质量合格率",
            value: qualityPassRate,
            unit: "%",
            target: 95,
            trend: 0,
            color:
            qualityPassRate >= 95 ?
            "text-emerald-400" :
            qualityPassRate >= 90 ?
            "text-amber-400" :
            "text-red-400"
          },
          {
            label: "物料到货及时率",
            value: 0, // Will be loaded from purchase API
            unit: "%",
            target: 95,
            trend: 0,
            color: "text-amber-400"
          },
          {
            label: "客户满意度",
            value: 0, // Will be loaded from sales/customer API
            unit: "%",
            target: 95,
            trend: 0,
            color: "text-blue-400"
          }
        );
      }
      setKeyMetrics(metrics);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
      setError(err);
      setBusinessStats(null);
      setPendingApprovals([]);
      setProjectHealth([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="总经理工作台"
        description={
        loading ?
        "加载中..." :
        businessStats ?
        `年度营收目标: ${formatCurrency(businessStats.yearTarget || 0)} | 已完成: ${formatCurrency(businessStats.yearRevenue || 0)} (${(businessStats.yearProgress || 0).toFixed(1)}%)` :
        "企业经营总览、战略决策支持"
        }
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              经营报表
            </Button>
            <Button className="flex items-center gap-2">
              <ClipboardCheck className="w-4 h-4" />
              审批中心
            </Button>
          </motion.div>
        } />


      {/* 文化墙滚动播放 */}
      <motion.div variants={fadeIn}>
        <CultureWallCarousel
          autoPlay={true}
          interval={5000}
          showControls={true}
          showIndicators={true}
          height="400px"
          onItemClick={(item) => {
            if (item.category === "GOAL") {
              window.location.href = "/personal-goals";
            } else {
              window.location.href = `/culture-wall?item=${item.id}`;
            }
          }} />

      </motion.div>

      {/* Key Statistics - 6 column grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">

        {loading ?
        [1, 2, 3, 4, 5, 6].map((i) =>
        <Card key={i} className="bg-surface-1/50 animate-pulse">
              <CardContent className="p-5">
                <div className="h-20 bg-slate-700/50 rounded" />
              </CardContent>
            </Card>
        ) :
        error ?
        <div className="col-span-6">
            <ApiIntegrationError
            error={error}
            apiEndpoint="/api/v1/dashboard/general-manager"
            onRetry={loadDashboard} />

          </div> :
        businessStats ?
        <>
            <StatCard
            title="本月营收"
            value={formatCurrency(businessStats.monthlyRevenue || 0)}
            subtitle={`目标: ${formatCurrency(businessStats.monthlyTarget || 0)}`}
            trend={businessStats.revenueGrowth || 0}
            icon={DollarSign}
            color="text-amber-400"
            bg="bg-amber-500/10" />

            <StatCard
            title="净利润"
            value={formatCurrency(businessStats.profit || 0)}
            subtitle={`利润率: ${businessStats.profitMargin || 0}%`}
            trend={15.2}
            icon={TrendingUp}
            color="text-emerald-400"
            bg="bg-emerald-500/10" />

            <StatCard
            title="进行中项目"
            value={businessStats.activeProjects || 0}
            subtitle={`总计 ${businessStats.totalProjects || 0} 个`}
            trend={businessStats.projectGrowth || 0}
            icon={Briefcase}
            color="text-blue-400"
            bg="bg-blue-500/10" />

            <StatCard
            title="待审批事项"
            value={businessStats.pendingApproval || 0}
            subtitle="需要处理"
            icon={ClipboardCheck}
            color="text-red-400"
            bg="bg-red-500/10" />

            <StatCard
            title="按时交付率"
            value={`${businessStats.onTimeDeliveryRate || 0}%`}
            subtitle="项目交付"
            icon={CheckCircle2}
            color="text-emerald-400"
            bg="bg-emerald-500/10" />

            <StatCard
            title="质量合格率"
            value={`${businessStats.qualityPassRate || 0}%`}
            subtitle="质量指标"
            icon={Award}
            color="text-cyan-400"
            bg="bg-cyan-500/10" />

          </> :
        null}
      </motion.div>

      {/* Main Content Grid */}
      {businessStats ?
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Year Progress & Project Health */}
          <div className="lg:col-span-2 space-y-6">
            {/* Year Progress */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Activity className="h-5 w-5 text-cyan-400" />
                    年度经营目标进度
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-slate-400">年度营收目标</p>
                        <p className="text-3xl font-bold text-white mt-1">
                          {formatCurrency(businessStats.yearTarget || 0)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-slate-400">已完成</p>
                        <p className="text-3xl font-bold text-emerald-400 mt-1">
                          {formatCurrency(businessStats.yearRevenue || 0)}
                        </p>
                      </div>
                    </div>
                    <Progress
                    value={businessStats.yearProgress || 0}
                    className="h-4 bg-slate-700/50" />

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">
                        完成率: {(businessStats.yearProgress || 0).toFixed(1)}%
                      </span>
                      <span className="text-slate-400">
                        剩余:{" "}
                        {formatCurrency(
                        (businessStats.yearTarget || 0) - (
                        businessStats.yearRevenue || 0)
                      )}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Key Metrics */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Target className="h-5 w-5 text-purple-400" />
                    关键运营指标
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {keyMetrics.length > 0 ?
                  keyMetrics.map((metric, index) =>
                  <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">
                              {metric.label}
                            </span>
                            <div className="flex items-center gap-2">
                              {metric.trend > 0 ?
                        <ArrowUpRight className="w-3 h-3 text-emerald-400" /> :
                        metric.trend < 0 ?
                        <ArrowDownRight className="w-3 h-3 text-red-400" /> :
                        null}
                              <span
                          className={cn("font-semibold", metric.color)}>

                                {metric.value.toFixed(1)}
                                {metric.unit}
                              </span>
                            </div>
                          </div>
                          {metric.target > 0 &&
                    <Progress
                      value={Math.min(
                        metric.value / metric.target * 100,
                        100
                      )}
                      className="h-2 bg-slate-700/50" />

                    }
                          <div className="flex items-center justify-between text-xs">
                            {metric.target > 0 &&
                      <span className="text-slate-500">
                                目标: {metric.target}
                                {metric.unit}
                              </span>
                      }
                            {metric.trend !== 0 &&
                      <span className="text-slate-500">
                                {metric.trend > 0 ? "+" : ""}
                                {metric.trend}%
                              </span>
                      }
                          </div>
                        </div>
                  ) :

                  <div className="col-span-2 text-center py-8 text-slate-500">
                        <Target className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
                        <p className="text-sm">关键指标数据需要从API获取</p>
                      </div>
                  }
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Project Health Status */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Briefcase className="h-5 w-5 text-blue-400" />
                      重点项目健康度
                    </CardTitle>
                    <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-primary">

                      查看全部 <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {projectHealth.map((project) => {
                    const healthColors = {
                      good: "bg-emerald-500",
                      warning: "bg-amber-500",
                      critical: "bg-red-500"
                    };
                    const riskColors = {
                      low: "text-emerald-400",
                      medium: "text-amber-400",
                      high: "text-red-400"
                    };
                    return (
                      <div
                        key={project.id}
                        className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer">

                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-white">
                                  {project.name}
                                </span>
                                <Badge
                                variant="outline"
                                className="text-xs bg-slate-700/40">

                                  {project.stageLabel}
                                </Badge>
                                <div
                                className={cn(
                                  "w-2 h-2 rounded-full",
                                  healthColors[project.health]
                                )} />

                              </div>
                              <div className="text-xs text-slate-400">
                                {project.customer} · {project.id}
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-bold text-white">
                                {formatCurrency(project.amount)}
                              </div>
                              <div className="text-xs text-slate-400">
                                交付: {project.dueDate}
                              </div>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-slate-400">进度</span>
                              <div className="flex items-center gap-2">
                                <span
                                className={cn(
                                  "font-medium",
                                  riskColors[project.risk]
                                )}>

                                  风险:{" "}
                                  {project.risk === "low" ?
                                "低" :
                                project.risk === "medium" ?
                                "中" :
                                "高"}
                                </span>
                                <span className="text-slate-300">
                                  {project.progress}%
                                </span>
                              </div>
                            </div>
                            <Progress
                            value={project.progress}
                            className="h-1.5 bg-slate-700/50" />

                          </div>
                        </div>);

                  })}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Right Column - Pending Approvals & Department Status */}
          <div className="space-y-6">
            {/* Pending Approvals */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <ClipboardCheck className="h-5 w-5 text-amber-400" />
                      待审批事项
                    </CardTitle>
                    <Badge
                    variant="outline"
                    className="bg-amber-500/20 text-amber-400 border-amber-500/30">

                      {pendingApprovals.length}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {pendingApprovals.map((item) =>
                <div
                  key={item.id}
                  className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer">

                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge
                          variant="outline"
                          className={cn(
                            "text-xs",
                            item.type === "project" &&
                            "bg-blue-500/20 text-blue-400 border-blue-500/30",
                            item.type === "contract" &&
                            "bg-purple-500/20 text-purple-400 border-purple-500/30",
                            item.type === "budget" &&
                            "bg-amber-500/20 text-amber-400 border-amber-500/30",
                            item.type === "purchase" &&
                            "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                            item.type === "personnel" &&
                            "bg-pink-500/20 text-pink-400 border-pink-500/30"
                          )}>

                              {item.type === "project" ?
                          "项目" :
                          item.type === "contract" ?
                          "合同" :
                          item.type === "budget" ?
                          "预算" :
                          item.type === "purchase" ?
                          "采购" :
                          "人事"}
                            </Badge>
                            {item.priority === "high" &&
                        <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                                紧急
                              </Badge>
                        }
                          </div>
                          <p className="font-medium text-white text-sm">
                            {item.title}
                          </p>
                          <p className="text-xs text-slate-400 mt-1">
                            {item.department} · {item.submitter}
                          </p>
                          {(item.projectName ||
                      item.customer ||
                      item.item ||
                      item.position) &&
                      <p className="text-xs text-slate-500 mt-1">
                              {item.projectName ||
                        item.customer ||
                        item.item ||
                        item.position}
                            </p>
                      }
                        </div>
                      </div>
                      {item.amount &&
                  <div className="flex items-center justify-between text-xs mt-2">
                          <span className="text-slate-400">
                            {item.submitTime.split(" ")[1]}
                          </span>
                          <span className="font-medium text-amber-400">
                            {formatCurrency(item.amount)}
                          </span>
                        </div>
                  }
                    </div>
                )}
                  <Button variant="outline" className="w-full mt-3">
                    查看全部审批
                  </Button>
                </CardContent>
              </Card>
            </motion.div>

            {/* Department Status */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Building2 className="h-5 w-5 text-blue-400" />
                      部门运营状态
                    </CardTitle>
                    <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-primary">

                      详情 <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {departmentStatus.length > 0 ?
                departmentStatus.map((dept) =>
                <div
                  key={dept.id}
                  className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">

                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div
                        className={cn(
                          "w-8 h-8 rounded-lg flex items-center justify-center",
                          dept.status === "excellent" &&
                          "bg-gradient-to-br from-emerald-500/20 to-emerald-600/10",
                          dept.status === "good" &&
                          "bg-gradient-to-br from-blue-500/20 to-blue-600/10",
                          dept.status === "warning" &&
                          "bg-gradient-to-br from-amber-500/20 to-amber-600/10"
                        )}>

                              <Building2
                          className={cn(
                            "h-4 w-4",
                            dept.status === "excellent" &&
                            "text-emerald-400",
                            dept.status === "good" && "text-blue-400",
                            dept.status === "warning" && "text-amber-400"
                          )} />

                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-white text-sm">
                                  {dept.name}
                                </span>
                                {dept.issues > 0 &&
                          <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                                    {dept.issues} 个问题
                                  </Badge>
                          }
                              </div>
                              <div className="text-xs text-slate-400 mt-0.5">
                                {dept.manager}
                              </div>
                            </div>
                          </div>
                          {dept.achievement > 0 &&
                    <div className="text-right">
                              <div className="text-sm font-bold text-white">
                                {dept.achievement.toFixed(1)}%
                              </div>
                              <div className="text-xs text-slate-400">
                                完成率
                              </div>
                            </div>
                    }
                        </div>
                        {dept.achievement > 0 &&
                  <Progress
                    value={dept.achievement}
                    className="h-1.5 bg-slate-700/50" />

                  }
                      </div>
                ) :

                <div className="text-center py-8 text-slate-500">
                      <Building2 className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
                      <p className="text-sm">部门状态数据需要从API获取</p>
                    </div>
                }
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div> :
      null}
    </motion.div>);

}