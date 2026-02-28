/**
 * Financial Reports Page - Financial reports and analysis
 * Features: Financial statements, Profit & loss, Cash flow, Budget analysis, Export reports
 */

import { useState, useMemo as _useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  DollarSign,
  FileText,
  Download,
  Calendar,
  Filter,
  PieChart,
  LineChart,
  Activity,
  Receipt,
  CreditCard,
  Wallet,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  ChevronRight } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui";
import { cn, formatCurrency } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { financialReportApi, reportCenterApi as _reportCenterApi } from "../services/api";
import {
  LineChart as LineChartComponent,
  BarChart as BarChartComponent,
  PieChart as PieChartComponent,
  AreaChart as AreaChartComponent,
  DualAxesChart } from
"../components/charts";

// Mock financial data
// Mock data - 已移除，使用真实API
// Mock data - 已移除，使用真实API
// Mock data - 已移除，使用真实API
// Mock data - 已移除，使用真实API
const reportTypes = [
{ id: "profit-loss", label: "损益表", icon: BarChart3 },
{ id: "cash-flow", label: "现金流量表", icon: Wallet },
{ id: "budget", label: "预算执行", icon: Target },
{ id: "cost", label: "成本分析", icon: Receipt },
{ id: "project", label: "项目盈利", icon: FileText }];


export default function FinancialReports() {
  const [selectedPeriod, setSelectedPeriod] = useState("month"); // month, quarter, year
  const [selectedReport, setSelectedReport] = useState("profit-loss");
  const [dateRange, setDateRange] = useState("2024-07");
  const [_loading, setLoading] = useState(true);
  const [_error, setError] = useState(null);

  // State initialized with empty data
  const [monthlyFinancials, setMonthlyFinancials] = useState([]);
  const [costBreakdown, setCostBreakdown] = useState([]);
  const [projectProfitability, setProjectProfitability] = useState([]);
  const [cashFlowData, setCashFlowData] = useState([]);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [summaryRes, costRes, projectRes, cashFlowRes] =
        await Promise.allSettled([
        financialReportApi.getMonthlyTrend({
          period: selectedPeriod,
          year: dateRange.split("-")[0]
        }),
        financialReportApi.getCostAnalysis({ period: selectedPeriod }),
        financialReportApi.getProjectProfitability({ limit: 10 }),
        financialReportApi.getCashFlow({ period: selectedPeriod })]
        );

        if (summaryRes.status === "fulfilled" && summaryRes.value.data) {
          const data = summaryRes.value.data;
          setMonthlyFinancials(Array.isArray(data) ? data : []);
        }
        if (costRes.status === "fulfilled" && costRes.value.data) {
          setCostBreakdown(costRes.value.data || {});
        }
        if (projectRes.status === "fulfilled" && projectRes.value.data) {
          const data = projectRes.value.data;
          setProjectProfitability(Array.isArray(data) ? data : []);
        }
        if (cashFlowRes.status === "fulfilled" && cashFlowRes.value.data) {
          const data = cashFlowRes.value.data;
          setCashFlowData(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        console.error("Failed to load financial reports:", err);
        setError("加载财务报表失败");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedPeriod, dateRange]);

  const currentData = monthlyFinancials[monthlyFinancials.length - 1] || { cashFlow: 0, revenue: 0, cost: 0, profit: 0 };
  const totalRevenue = monthlyFinancials.reduce((sum, m) => sum + m.revenue, 0);
  const totalCost = monthlyFinancials.reduce((sum, m) => sum + m.cost, 0);
  const totalProfit = monthlyFinancials.reduce((sum, m) => sum + m.profit, 0);
  const avgMargin = totalProfit / totalRevenue * 100;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="财务报表"
        description="财务数据统计、分析和报表导出"
        icon={BarChart3}
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              筛选
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出报表
            </Button>
        </motion.div>
        } />


      {/* Period Selector */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <Button
                  variant={selectedPeriod === "month" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setSelectedPeriod("month")}>

                  月度
                </Button>
                <Button
                  variant={selectedPeriod === "quarter" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setSelectedPeriod("quarter")}>

                  季度
                </Button>
                <Button
                  variant={selectedPeriod === "year" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setSelectedPeriod("year")}>

                  年度
                </Button>
              </div>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary">

                <option value="2024-07">2024年7月</option>
                <option value="2024-08">2024年8月</option>
                <option value="2024-09">2024年9月</option>
                <option value="2024-10">2024年10月</option>
                <option value="2024-11">2024年11月</option>
                <option value="2024-12">2024年12月</option>
                <option value="2025-01">2025年1月</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Summary Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">累计营收</p>
                <p className="text-2xl font-bold text-amber-400">
                  {formatCurrency(totalRevenue)}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+18.5%</span>
                </div>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">累计成本</p>
                <p className="text-2xl font-bold text-red-400">
                  {formatCurrency(totalCost)}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingDown className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">-2.3%</span>
                </div>
              </div>
              <div className="p-2 bg-red-500/20 rounded-lg">
                <Receipt className="w-5 h-5 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">累计利润</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {formatCurrency(totalProfit)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  利润率: {avgMargin.toFixed(1)}%
                </p>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-2">现金流</p>
                <p className="text-2xl font-bold text-cyan-400">
                  {formatCurrency(currentData.cashFlow)}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+8.5%</span>
                </div>
              </div>
              <div className="p-2 bg-cyan-500/20 rounded-lg">
                <Wallet className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Report Tabs */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <Tabs value={selectedReport} onValueChange={setSelectedReport}>
              <TabsList className="grid w-full grid-cols-5">
                {reportTypes.map((type) => {
                  const Icon = type.icon;
                  return (
                    <TabsTrigger
                      key={type.id}
                      value={type.id}
                      className="flex items-center gap-2">

                      <Icon className="w-4 h-4" />
                      {type.label}
                    </TabsTrigger>);

                })}
              </TabsList>

              {/* Profit & Loss Statement */}
              <TabsContent value="profit-loss" className="space-y-6 mt-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* 损益汇总 */}
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      损益表
                    </h3>
                    <div className="space-y-4">
                      <div className="p-4 bg-slate-800/40 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-slate-400">营业收入</span>
                          <span className="text-2xl font-bold text-amber-400">
                            {formatCurrency(currentData.revenue)}
                          </span>
                        </div>
                      </div>
                      <div className="p-4 bg-slate-800/40 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-slate-400">营业成本</span>
                          <span className="text-xl font-bold text-red-400">
                            {formatCurrency(currentData.cost)}
                          </span>
                        </div>
                      </div>
                      <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-slate-400">净利润</span>
                          <span className="text-2xl font-bold text-emerald-400">
                            {formatCurrency(currentData.profit)}
                          </span>
                        </div>
                        <div className="text-sm text-slate-400 mt-2">
                          利润率:{" "}
                          {(
                          currentData.profit / currentData.revenue *
                          100).
                          toFixed(1)}
                          %
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 营收利润趋势图 */}
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      营收与利润趋势
                    </h3>
                    <DualAxesChart
                      data={monthlyFinancials.map((item) => ({
                        month: item.month,
                        revenue: item.revenue,
                        profit: item.profit,
                        margin: (item.profit / item.revenue * 100).toFixed(1)
                      }))}
                      xField="month"
                      yField={["revenue", "margin"]}
                      leftYAxisTitle="营收 (元)"
                      rightYAxisTitle="利润率 (%)"
                      height={280}
                      leftFormatter={(v) => `¥${(v / 10000).toFixed(0)}万`}
                      rightFormatter={(v) => `${v}%`} />

                  </div>
                </div>

                {/* 收入成本对比柱状图 */}
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-3">
                    收入成本对比
                  </h4>
                  <BarChartComponent
                    data={monthlyFinancials.flatMap((item) => [
                    {
                      month: item.month,
                      type: "营业收入",
                      value: item.revenue
                    },
                    { month: item.month, type: "营业成本", value: item.cost },
                    { month: item.month, type: "净利润", value: item.profit }]
                    )}
                    xField="month"
                    yField="value"
                    seriesField="type"
                    isGroup
                    height={300}
                    colors={["#f59e0b", "#ef4444", "#10b981"]}
                    formatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />

                </div>

                {/* Revenue Trend List */}
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-3">
                    月度营收明细
                  </h4>
                  <div className="space-y-3">
                    {monthlyFinancials.map((item, index) => {
                      const maxRevenue = Math.max(
                        ...monthlyFinancials.map((m) => m.revenue)
                      );
                      const percentage = item.revenue / maxRevenue * 100;
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">{item.month}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-white font-medium">
                                {formatCurrency(item.revenue)}
                              </span>
                              {index > 0 &&
                              <span
                                className={cn(
                                  "text-xs",
                                  item.revenue >
                                  monthlyFinancials[index - 1].revenue ?
                                  "text-emerald-400" :
                                  "text-red-400"
                                )}>

                                  {item.revenue >
                                monthlyFinancials[index - 1].revenue ?
                                "↑" :
                                "↓"}
                                  {Math.abs(
                                  (item.revenue -
                                  monthlyFinancials[index - 1].revenue) /
                                  monthlyFinancials[index - 1].revenue *
                                  100
                                ).toFixed(1)}
                                  %
                              </span>
                              }
                            </div>
                          </div>
                          <Progress
                            value={percentage}
                            className="h-2 bg-slate-700/50" />

                        </div>);

                    })}
                  </div>
                </div>
              </TabsContent>

              {/* Cash Flow Statement */}
              <TabsContent value="cash-flow" className="space-y-6 mt-6">
                {/* 现金流趋势图 */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    现金流量趋势
                  </h3>
                  <AreaChartComponent
                    data={cashFlowData.flatMap((item) => [
                    {
                      month: item.month,
                      type: "现金流入",
                      value: item.inflow
                    },
                    {
                      month: item.month,
                      type: "现金流出",
                      value: -item.outflow
                    },
                    { month: item.month, type: "净现金流", value: item.net }]
                    )}
                    xField="month"
                    yField="value"
                    seriesField="type"
                    height={300}
                    colors={["#10b981", "#ef4444", "#3b82f6"]}
                    formatter={(v) => `¥${(Math.abs(v) / 10000).toFixed(0)}万`} />

                </div>

                {/* 现金流明细 */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    现金流量明细
                  </h3>
                  <div className="space-y-4">
                    {cashFlowData.map((item, index) => {
                      const maxFlow = Math.max(
                        ...cashFlowData.map((c) => Math.abs(c.net))
                      );
                      const percentage = Math.abs(item.net) / maxFlow * 100;
                      return (
                        <div
                          key={index}
                          className="p-4 bg-slate-800/40 rounded-lg">

                          <div className="flex items-center justify-between mb-3">
                            <span className="text-slate-400">{item.month}</span>
                            <div className="flex items-center gap-4">
                              <div className="text-right">
                                <div className="text-xs text-slate-500">
                                  流入
                                </div>
                                <div className="text-sm font-medium text-emerald-400">
                                  {formatCurrency(item.inflow)}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-xs text-slate-500">
                                  流出
                                </div>
                                <div className="text-sm font-medium text-red-400">
                                  {formatCurrency(item.outflow)}
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="text-xs text-slate-500">
                                  净流量
                                </div>
                                <div
                                  className={cn(
                                    "text-lg font-bold",
                                    item.net > 0 ?
                                    "text-emerald-400" :
                                    "text-red-400"
                                  )}>

                                  {formatCurrency(item.net)}
                                </div>
                              </div>
                            </div>
                          </div>
                          <Progress
                            value={percentage}
                            className={cn(
                              "h-2",
                              item.net > 0 ?
                              "bg-emerald-500/20" :
                              "bg-red-500/20"
                            )} />

                        </div>);

                    })}
                  </div>
                </div>
              </TabsContent>

              {/* Budget Analysis */}
              <TabsContent value="budget" className="space-y-6 mt-6">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    预算执行分析
                  </h3>
                  <div className="space-y-3">
                    {costBreakdown.map((item, index) => {
                      const used = item.amount / item.budget * 100;
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">
                              {item.category}
                            </span>
                            <div className="flex items-center gap-3">
                              <span className="text-slate-500 text-xs">
                                预算: {formatCurrency(item.budget)}
                              </span>
                              <span className="text-white font-medium">
                                实际: {formatCurrency(item.amount)}
                              </span>
                              {item.variance !== 0 &&
                              <span
                                className={cn(
                                  "text-xs",
                                  item.variance > 0 ?
                                  "text-red-400" :
                                  "text-emerald-400"
                                )}>

                                  {item.variance > 0 ? "+" : ""}
                                  {formatCurrency(item.variance)}
                              </span>
                              }
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Progress
                              value={used}
                              className={cn(
                                "flex-1 h-2",
                                used > 100 ?
                                "bg-red-500/20" :
                                used > 90 ?
                                "bg-amber-500/20" :
                                "bg-slate-700/50"
                              )} />

                            <span className="text-xs text-slate-400 w-16 text-right">
                              {used.toFixed(1)}%
                            </span>
                          </div>
                        </div>);

                    })}
                  </div>
                </div>
              </TabsContent>

              {/* Cost Analysis */}
              <TabsContent value="cost" className="space-y-6 mt-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* 成本构成饼图 */}
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      成本构成占比
                    </h3>
                    <PieChartComponent
                      data={costBreakdown.map((item) => ({
                        category: item.category,
                        value: item.amount
                      }))}
                      angleField="value"
                      colorField="category"
                      height={300}
                      innerRadius={0.6}
                      label={{
                        type: "spider",
                        content: "{name}: {percentage}"
                      }}
                      formatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />

                  </div>

                  {/* 成本明细列表 */}
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      成本构成明细
                    </h3>
                    <div className="space-y-3">
                      {costBreakdown.map((item, index) => {
                        const total = costBreakdown.reduce(
                          (sum, c) => sum + c.amount,
                          0
                        );
                        const percentage = item.amount / total * 100;
                        const colors = [
                        "bg-blue-500",
                        "bg-purple-500",
                        "bg-amber-500",
                        "bg-cyan-500",
                        "bg-emerald-500",
                        "bg-pink-500"];

                        return (
                          <div key={index} className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <div className="flex items-center gap-2">
                                <div
                                  className={cn(
                                    "w-3 h-3 rounded-full",
                                    colors[index % colors.length]
                                  )} />

                                <span className="text-slate-400">
                                  {item.category}
                                </span>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="text-white font-medium">
                                  {formatCurrency(item.amount)}
                                </span>
                                <span className="text-slate-500 text-xs w-12 text-right">
                                  {percentage.toFixed(1)}%
                                </span>
                              </div>
                            </div>
                            <Progress
                              value={percentage}
                              className="h-2 bg-slate-700/50" />

                          </div>);

                      })}
                    </div>
                  </div>
                </div>

                {/* 成本趋势对比 */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    预算与实际对比
                  </h3>
                  <BarChartComponent
                    data={costBreakdown.flatMap((item) => [
                    {
                      category: item.category,
                      type: "预算",
                      value: item.budget
                    },
                    {
                      category: item.category,
                      type: "实际",
                      value: item.amount
                    }]
                    )}
                    xField="category"
                    yField="value"
                    seriesField="type"
                    isGroup
                    height={280}
                    colors={["#64748b", "#3b82f6"]}
                    formatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />

                </div>
              </TabsContent>

              {/* Project Profitability */}
              <TabsContent value="project" className="space-y-6 mt-6">
                {/* 项目利润率对比图 */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    项目利润率对比
                  </h3>
                  <BarChartComponent
                    data={projectProfitability.map((p) => ({
                      project:
                      p.project.length > 8 ?
                      p.project.slice(0, 8) + "..." :
                      p.project,
                      margin: p.margin
                    }))}
                    xField="project"
                    yField="margin"
                    height={250}
                    colors={projectProfitability.map((p) =>
                    p.margin >= 30 ?
                    "#10b981" :
                    p.margin >= 20 ?
                    "#f59e0b" :
                    "#ef4444"
                    )}
                    formatter={(v) => `${v}%`}
                    label={{
                      position: "top",
                      style: { fill: "#94a3b8" },
                      formatter: (datum) => `${datum.margin}%`
                    }} />

                </div>

                {/* 项目收入成本对比 */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    项目收入与成本
                  </h3>
                  <BarChartComponent
                    data={projectProfitability.flatMap((p) => [
                    {
                      project:
                      p.project.length > 8 ?
                      p.project.slice(0, 8) + "..." :
                      p.project,
                      type: "收入",
                      value: p.revenue
                    },
                    {
                      project:
                      p.project.length > 8 ?
                      p.project.slice(0, 8) + "..." :
                      p.project,
                      type: "成本",
                      value: p.cost
                    }]
                    )}
                    xField="project"
                    yField="value"
                    seriesField="type"
                    isGroup
                    height={280}
                    colors={["#f59e0b", "#ef4444"]}
                    formatter={(v) => `¥${(v / 10000).toFixed(0)}万`} />

                </div>

                {/* 项目盈利明细列表 */}
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    项目盈利明细
                  </h3>
                  <div className="space-y-3">
                    {projectProfitability.map((project, index) => {
                      const statusColors = {
                        good: "bg-emerald-500",
                        warning: "bg-amber-500",
                        critical: "bg-red-500"
                      };
                      return (
                        <div
                          key={index}
                          className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">

                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-white">
                                  {project.project}
                                </span>
                                <div
                                  className={cn(
                                    "w-2 h-2 rounded-full",
                                    statusColors[project.status]
                                  )} />

                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-bold text-amber-400">
                                {formatCurrency(project.revenue)}
                              </div>
                              <div className="text-sm text-emerald-400">
                                利润: {formatCurrency(project.profit)}
                              </div>
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-slate-400">成本</span>
                              <span className="text-red-400">
                                {formatCurrency(project.cost)}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-slate-400">利润率</span>
                              <span
                                className={cn(
                                  "font-medium",
                                  project.margin >= 30 ?
                                  "text-emerald-400" :
                                  project.margin >= 20 ?
                                  "text-amber-400" :
                                  "text-red-400"
                                )}>

                                {project.margin.toFixed(1)}%
                              </span>
                            </div>
                            <Progress
                              value={project.margin}
                              className={cn(
                                "h-2",
                                project.margin >= 30 ?
                                "bg-emerald-500/20" :
                                project.margin >= 20 ?
                                "bg-amber-500/20" :
                                "bg-red-500/20"
                              )} />

                          </div>
                        </div>);

                    })}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardHeader>
        </Card>
      </motion.div>
    </motion.div>);

}