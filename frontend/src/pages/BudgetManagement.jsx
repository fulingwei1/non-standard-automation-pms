/**
 * Budget Management Page - 预算管理页面
 * Features: Project budget overview, budget usage tracking, budget alerts
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  CreditCard,
  TrendingUp,
  AlertTriangle,
  Search,
  Download,
  Eye,
  Target } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui";
import { cn, formatCurrency, formatDate } from "../lib/utils";
import { staggerContainer } from "../lib/animations";
import { budgetApi, projectApi } from "../services/api";
import { mergeProjectContextFilters } from "../lib/projectContext";

// Mock data - 已移除，使用真实API
const toFiniteAmount = (value) => {
  const amount = Number(value);
  return Number.isFinite(amount) ? amount : 0;
};

const getProjectUsedAmount = (project) =>
  toFiniteAmount(
    project.actual_cost ??
      project.used_amount ??
      project.total_cost ??
      project.cost_amount ??
      project.cost_summary?.total_cost
  );

const extractItems = (response) =>
  response?.data?.items || response?.items || response?.data || [];

const getBudgetStatus = (status, usageRate) => {
  if (["DRAFT", "SUBMITTED", "APPROVED", "REJECTED"].includes(status)) {
    return status;
  }
  if (usageRate >= 90) return "CRITICAL";
  if (usageRate >= 80) return "WARNING";
  return "NORMAL";
};

export default function BudgetManagement({ embedded = false }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const projectListParams = useMemo(
    () => mergeProjectContextFilters(searchParams, { page: 1, page_size: 8 }),
    [searchParams]
  );
  const [loading, setLoading] = useState(true);
  const [budgets, setBudgets] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterUsageRate, setFilterUsageRate] = useState("all");

  const loadBudgets = useCallback(async () => {
    try {
      setLoading(true);
      const budgetRes = await budgetApi.list(projectListParams);
      const budgetItems = extractItems(budgetRes);
      if (budgetItems.length > 0) {
        const budgetsData = budgetItems.map((budget) => {
          const budgetAmount = toFiniteAmount(budget.total_amount ?? budget.budget_amount);
          const usedAmount = toFiniteAmount(
            budget.used_amount ?? budget.actual_cost ?? budget.project_actual_cost,
          );
          const usageRate = budgetAmount > 0 ? (usedAmount / budgetAmount) * 100 : 0;
          return {
            id: budget.id,
            project_id: budget.project_id,
            project_code: budget.project_code,
            project_name: budget.project_name || budget.budget_name,
            budget_amount: budgetAmount,
            used_amount: usedAmount,
            remaining_amount: budgetAmount - usedAmount,
            usage_rate: usageRate,
            status: getBudgetStatus(budget.status, usageRate),
            start_date: budget.effective_date,
            end_date: budget.expiry_date,
          };
        });
        setBudgets((budgetsData || []).filter(Boolean));
        return;
      }

      // Load projects with budget information
      const res = await projectApi.list(projectListParams);
      const projects = res.data?.items || res.data?.items || res.data || [];

      // Transform projects to budget format. The project list already carries
      // budget/cost fields, so avoid N extra cost-summary calls on page load.
      const budgetsData = (projects || []).map((project) => {
            const usedAmount = getProjectUsedAmount(project);
            const budgetAmount = toFiniteAmount(project.budget_amount);
            const usageRate =
            budgetAmount > 0 ? usedAmount / budgetAmount * 100 : 0;

            return {
              id: project.id,
              project_code: project.project_code,
              project_name: project.project_name,
              budget_amount: budgetAmount,
              used_amount: usedAmount,
              remaining_amount: budgetAmount - usedAmount,
              usage_rate: usageRate,
              status: getBudgetStatus(project.budget_status, usageRate),
              start_date: project.planned_start_date,
              end_date: project.planned_end_date
            };
      });

      setBudgets((budgetsData || []).filter(Boolean));
    } catch (error) {
      console.error("Failed to load budgets:", error);
      setBudgets([]);
    } finally {
      setLoading(false);
    }
  }, [projectListParams]);

  useEffect(() => {
    loadBudgets();
  }, [loadBudgets]);

  const filteredBudgets = useMemo(() => {
    return (budgets || []).filter((budget) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          budget.project_code?.toLowerCase().includes(keyword) ||
          budget.project_name?.toLowerCase().includes(keyword));

      }
      if (filterStatus !== "all") {
        if (filterStatus === "critical" && budget.status !== "CRITICAL")
        {return false;}
        if (filterStatus === "warning" && budget.status !== "WARNING")
        {return false;}
        if (filterStatus === "normal" && budget.status !== "NORMAL")
        {return false;}
      }
      if (filterUsageRate !== "all") {
        if (filterUsageRate === "high" && budget.usage_rate < 80) {return false;}
        if (
        filterUsageRate === "medium" && (
        budget.usage_rate < 50 || budget.usage_rate >= 80))

        {return false;}
        if (filterUsageRate === "low" && budget.usage_rate >= 50) {return false;}
      }
      return true;
    });
  }, [budgets, searchKeyword, filterStatus, filterUsageRate]);

  const stats = useMemo(() => {
    const total = (budgets || []).reduce((sum, b) => sum + toFiniteAmount(b.budget_amount), 0);
    const used = (budgets || []).reduce((sum, b) => sum + toFiniteAmount(b.used_amount), 0);
    const remaining = (budgets || []).reduce((sum, b) => sum + toFiniteAmount(b.remaining_amount), 0);
    const critical = (budgets || []).filter((b) => b.status === "CRITICAL").length;
    const warning = (budgets || []).filter((b) => b.status === "WARNING").length;

    return {
      total,
      used,
      remaining,
      usageRate: total > 0 ? used / total * 100 : 0,
      critical,
      warning
    };
  }, [budgets]);

  const statusConfig = {
    CRITICAL: { label: "严重超支", color: "bg-red-500 text-white" },
    WARNING: { label: "预算预警", color: "bg-amber-500 text-white" },
    NORMAL: { label: "正常", color: "bg-emerald-500 text-white" },
    DRAFT: { label: "草稿", color: "bg-slate-500 text-white" },
    SUBMITTED: { label: "审批中", color: "bg-blue-500 text-white" },
    APPROVED: { label: "已批准", color: "bg-emerald-500 text-white" },
    REJECTED: { label: "已驳回", color: "bg-red-500 text-white" }
  };

  return (
    <div
      className={
        embedded
          ? ""
          : "min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950"
      }
    >
      <div className={embedded ? "space-y-6" : "container mx-auto px-4 py-6 space-y-6"}>
        {!embedded ? (
          <PageHeader
            title="预算管理"
            description="项目预算跟踪、使用情况监控、预算预警"
          />
        ) : null}


        {/* Statistics */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-4 gap-4">

          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2">总预算</p>
                  <p className="text-2xl font-bold text-white">
                    {formatCurrency(stats.total)}
                  </p>
                </div>
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <CreditCard className="w-5 h-5 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2">已使用</p>
                  <p className="text-2xl font-bold text-amber-400">
                    {formatCurrency(stats.used)}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {stats.usageRate.toFixed(1)}% 使用率
                  </p>
                </div>
                <div className="p-2 bg-amber-500/20 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2">剩余预算</p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {formatCurrency(stats.remaining)}
                  </p>
                </div>
                <div className="p-2 bg-emerald-500/20 rounded-lg">
                  <Target className="w-5 h-5 text-emerald-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2">预警项目</p>
                  <p className="text-2xl font-bold text-red-400">
                    {stats.critical + stats.warning}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {stats.critical} 严重 / {stats.warning} 警告
                  </p>
                </div>
                <div className="p-2 bg-red-500/20 rounded-lg">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Filters */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                <Input
                  placeholder="搜索项目编码、名称..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 bg-slate-900/50 border-slate-700" />

              </div>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="预算状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="critical">严重超支</SelectItem>
                  <SelectItem value="warning">预算预警</SelectItem>
                  <SelectItem value="normal">正常</SelectItem>
                </SelectContent>
              </Select>
              <Select
                value={filterUsageRate}
                onValueChange={setFilterUsageRate}>

                <SelectTrigger className="bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="使用率" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="high">高 (≥80%)</SelectItem>
                  <SelectItem value="medium">中 (50-80%)</SelectItem>
                  <SelectItem value="low">低 ({"<50%"})</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" onClick={() => navigate("/costs")}>
                <Download className="w-4 h-4 mr-2" />
                导出报表
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Budget List */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-slate-200">预算列表</CardTitle>
            <CardDescription className="text-slate-400">
              共 {filteredBudgets.length} 个项目
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ?
            <div className="text-center py-8 text-slate-400">加载中...</div> :
            filteredBudgets.length === 0 ?
            <div className="text-center py-8 text-slate-400">
                暂无预算数据
            </div> :

            <Table>
                <TableHeader>
                  <TableRow className="border-slate-700">
                    <TableHead className="text-slate-400">项目编码</TableHead>
                    <TableHead className="text-slate-400">项目名称</TableHead>
                    <TableHead className="text-slate-400">预算金额</TableHead>
                    <TableHead className="text-slate-400">已使用</TableHead>
                    <TableHead className="text-slate-400">剩余</TableHead>
                    <TableHead className="text-slate-400">使用率</TableHead>
                    <TableHead className="text-slate-400">状态</TableHead>
                    <TableHead className="text-slate-400">项目周期</TableHead>
                    <TableHead className="text-right text-slate-400">
                      操作
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(filteredBudgets || []).map((budget) =>
                <TableRow key={budget.id} className="border-slate-700">
                      <TableCell className="font-mono text-sm text-slate-200">
                        {budget.project_code}
                      </TableCell>
                      <TableCell className="font-medium text-slate-200">
                        {budget.project_name}
                      </TableCell>
                      <TableCell className="text-slate-300">
                        {formatCurrency(budget.budget_amount)}
                      </TableCell>
                      <TableCell className="text-amber-400">
                        {formatCurrency(budget.used_amount)}
                      </TableCell>
                      <TableCell className="text-emerald-400">
                        {formatCurrency(budget.remaining_amount)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress
                        value={budget.usage_rate}
                        className="flex-1 h-2" />

                          <span
                        className={cn(
                          "text-sm font-medium w-16 text-right",
                          budget.usage_rate >= 90 ?
                          "text-red-400" :
                          budget.usage_rate >= 80 ?
                          "text-amber-400" :
                          "text-emerald-400"
                        )}>

                            {budget.usage_rate.toFixed(1)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                      className={
                      statusConfig[budget.status]?.color || "bg-slate-500"
                      }>

                          {statusConfig[budget.status]?.label || budget.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {budget.start_date && budget.end_date ?
                    `${formatDate(budget.start_date)} ~ ${formatDate(budget.end_date)}` :
                    "-"}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/projects/${budget.id}`)}>

                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                </TableRow>
                )}
                </TableBody>
            </Table>
            }
          </CardContent>
        </Card>
      </div>
    </div>);

}
