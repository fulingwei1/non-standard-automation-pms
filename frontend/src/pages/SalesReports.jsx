/**
 * Sales Reports Page - Comprehensive sales analytics and reports for sales directors
 * Features: Sales trends, Performance analysis, Customer analysis, Revenue forecasting
 */

import { useState, useMemo as _useMemo, useEffect } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Target,
  Calendar,
  Download,
  Filter,
  PieChart,
  LineChart,
  Activity,
  Award,
  Building2,
  FileText,
  ChevronRight,
  ArrowUpRight,
  ArrowDownRight } from
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
  ApiIntegrationError } from
"../components/ui";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { salesStatisticsApi } from "../services/api";

// Mock data removed - using real API only

const formatCurrency = (value) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`;
  }
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
    minimumFractionDigits: 0
  }).format(value);
};

export default function SalesReports() {
  const [selectedPeriod, _setSelectedPeriod] = useState("month");
  const [_selectedReport, _setSelectedReport] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [monthlySales, setMonthlySales] = useState(null);
  const [customerAnalysis, setCustomerAnalysis] = useState(null);
  const [productAnalysis, setProductAnalysis] = useState(null);
  const [regionalAnalysis, setRegionalAnalysis] = useState(null);

  // Fetch data from API
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [monthlyRes, customerRes, productRes, regionalRes] =
      await Promise.allSettled([
      salesStatisticsApi.getMonthlyTrend({ period: selectedPeriod }),
      salesStatisticsApi.getByCustomer({ limit: 10 }),
      salesStatisticsApi.getByProduct({ limit: 10 }),
      salesStatisticsApi.getByRegion()]
      );

      // 检查是否有失败的请求
      const failedRequests = [
      monthlyRes,
      customerRes,
      productRes,
      regionalRes].
      filter((res) => res.status === "rejected");

      if (failedRequests.length > 0) {
        // 使用第一个失败的错误
        throw failedRequests[0].reason;
      }

      // 设置成功的数据
      if (monthlyRes.status === "fulfilled" && monthlyRes.value.data) {
        setMonthlySales(monthlyRes.value.data);
      } else {
        setMonthlySales([]);
      }

      if (customerRes.status === "fulfilled" && customerRes.value.data) {
        setCustomerAnalysis(customerRes.value.data);
      } else {
        setCustomerAnalysis([]);
      }

      if (productRes.status === "fulfilled" && productRes.value.data) {
        setProductAnalysis(productRes.value.data);
      } else {
        setProductAnalysis([]);
      }

      if (regionalRes.status === "fulfilled" && regionalRes.value.data) {
        setRegionalAnalysis(regionalRes.value.data);
      } else {
        setRegionalAnalysis([]);
      }
    } catch (err) {
      console.error("销售报表 API 调用失败:", err);
      setError(err);
      // 清空所有数据
      setMonthlySales(null);
      setCustomerAnalysis(null);
      setProductAnalysis(null);
      setRegionalAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedPeriod]);

  // 如果有错误，显示错误组件
  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="销售报表"
          description="销售数据分析、业绩趋势、客户分析、产品分析" />

        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/sales/statistics/*"
          onRetry={fetchData} />

      </div>);

  }

  // 如果正在加载
  if (loading || !monthlySales) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="销售报表"
          description="销售数据分析、业绩趋势、客户分析、产品分析" />

        <div className="text-center py-16 text-slate-400">加载中...</div>
      </div>);

  }

  // 如果数据为空
  if (monthlySales.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="销售报表"
          description="销售数据分析、业绩趋势、客户分析、产品分析" />

        <Card>
          <CardContent className="p-12 text-center text-slate-500">
            暂无数据
          </CardContent>
        </Card>
      </div>);

  }

  const currentMonth = monthlySales[monthlySales.length - 1];
  const avgAchievement =
  monthlySales.reduce((sum, m) => sum + m.achieved / m.target * 100, 0) /
  monthlySales.length;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="销售报表"
        description="销售数据分析、业绩趋势、客户分析、产品分析"
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


      {/* Summary Cards */}
      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

        <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">本月销售额</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {formatCurrency(currentMonth.achieved)}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  {currentMonth.growth > 0 ?
                  <>
                      <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                      <span className="text-xs text-emerald-400">
                        +{currentMonth.growth}%
                      </span>
                    </> :

                  <>
                      <ArrowDownRight className="w-3 h-3 text-red-400" />
                      <span className="text-xs text-red-400">
                        {currentMonth.growth}%
                      </span>
                    </>
                  }
                  <span className="text-xs text-slate-500">vs 上月</span>
                </div>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div className="mt-3">
              <Progress
                value={currentMonth.achieved / currentMonth.target * 100}
                className="h-1.5" />

              <p className="text-xs text-slate-500 mt-1">
                目标完成率{" "}
                {(currentMonth.achieved / currentMonth.target * 100).toFixed(
                  1
                )}
                %
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">平均完成率</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {avgAchievement.toFixed(1)}%
                </p>
                <p className="text-xs text-slate-500 mt-1">近7个月平均</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Target className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">累计销售额</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(
                    monthlySales.reduce((sum, m) => sum + m.achieved, 0)
                  )}
                </p>
                <p className="text-xs text-slate-500 mt-1">近7个月累计</p>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <BarChart3 className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">活跃客户</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {customerAnalysis?.length || 0}
                </p>
                <p className="text-xs text-slate-500 mt-1">TOP客户数</p>
              </div>
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Building2 className="w-5 h-5 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Trend Chart */}
        <motion.div variants={fadeIn}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LineChart className="h-5 w-5 text-blue-400" />
                销售趋势分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {monthlySales.map((item, _index) => {
                  const achievementRate = item.achieved / item.target * 100;
                  return (
                    <div key={item.month} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-300">{item.month}</span>
                        <div className="flex items-center gap-4">
                          <span className="text-slate-400">
                            目标: {formatCurrency(item.target)}
                          </span>
                          <span className="text-white font-medium">
                            完成: {formatCurrency(item.achieved)}
                          </span>
                          {item.growth > 0 ?
                          <span className="text-emerald-400 text-xs">
                              +{item.growth}%
                            </span> :

                          <span className="text-red-400 text-xs">
                              {item.growth}%
                            </span>
                          }
                        </div>
                      </div>
                      <Progress value={achievementRate} className="h-2" />
                    </div>);

                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Customer Analysis */}
        <motion.div variants={fadeIn}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-purple-400" />
                TOP客户分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {customerAnalysis && customerAnalysis.length > 0 ?
                customerAnalysis.map((customer, index) =>
                <div
                  key={customer.name}
                  className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50">

                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div
                        className={cn(
                          "w-6 h-6 rounded flex items-center justify-center text-xs font-bold text-white",
                          index === 0 &&
                          "bg-gradient-to-br from-amber-500 to-orange-500",
                          index === 1 &&
                          "bg-gradient-to-br from-blue-500 to-cyan-500",
                          index === 2 &&
                          "bg-gradient-to-br from-purple-500 to-pink-500",
                          index >= 3 && "bg-slate-600"
                        )}>

                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-white text-sm">
                              {customer.name}
                            </p>
                            <p className="text-xs text-slate-400 mt-0.5">
                              {customer.projects} 个项目
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-white">
                            {formatCurrency(customer.amount)}
                          </p>
                          {customer.growth > 0 ?
                      <p className="text-xs text-emerald-400">
                              +{customer.growth}%
                            </p> :

                      <p className="text-xs text-red-400">
                              {customer.growth}%
                            </p>
                      }
                        </div>
                      </div>
                    </div>
                ) :

                <div className="text-center py-8 text-slate-500 text-sm">
                    暂无客户数据
                  </div>
                }
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Product Analysis */}
        <motion.div variants={fadeIn}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5 text-amber-400" />
                产品线分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {productAnalysis && productAnalysis.length > 0 ?
                productAnalysis.map((product, _index) =>
                <div
                  key={product.name}
                  className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50">

                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-white text-sm">
                          {product.name}
                        </span>
                        <span className="text-white font-bold">
                          {formatCurrency(product.amount)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs mb-2">
                        <span className="text-slate-400">
                          {product.count} 台 · 均价{" "}
                          {formatCurrency(product.avgPrice)}
                        </span>
                        <span className="text-slate-400">
                          占比 {product.ratio}%
                        </span>
                      </div>
                      <Progress value={product.ratio} className="h-1.5" />
                    </div>
                ) :

                <div className="text-center py-8 text-slate-500 text-sm">
                    暂无产品数据
                  </div>
                }
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Regional Analysis */}
        <motion.div variants={fadeIn}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-cyan-400" />
                区域销售分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {regionalAnalysis && regionalAnalysis.length > 0 ?
                regionalAnalysis.map((region, _index) =>
                <div
                  key={region.region}
                  className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50">

                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <p className="font-medium text-white text-sm">
                            {region.region}
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {region.customers} 个客户
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-white">
                            {formatCurrency(region.amount)}
                          </p>
                          <p className="text-xs text-emerald-400">
                            +{region.growth}%
                          </p>
                        </div>
                      </div>
                      <Progress
                    value={
                    region.amount /
                    regionalAnalysis.reduce(
                      (sum, r) => sum + r.amount,
                      0
                    ) *
                    100
                    }
                    className="h-1.5 mt-2" />

                    </div>
                ) :

                <div className="text-center py-8 text-slate-500 text-sm">
                    暂无区域数据
                  </div>
                }
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>);

}