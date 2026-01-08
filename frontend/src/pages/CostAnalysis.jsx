/**
 * Cost Analysis Page - 成本分析页面
 * Features: Purchase cost analysis, supplier cost comparison, cost trends
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Package,
  Building2,
  Calendar,
  Search,
  Filter,
  Download,
  PieChart,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui'
import { cn, formatCurrency } from '../lib/utils'
import { staggerContainer } from '../lib/animations'
import { purchaseApi, supplierApi, costApi, projectApi } from '../services/api'

// Mock cost analysis data for demo accounts
const mockCostAnalysis = {
  totalPurchaseCost: 2850000,
  monthlyTrend: [
    { month: '2024-10', amount: 1200000, orders: 15 },
    { month: '2024-11', amount: 1350000, orders: 18 },
    { month: '2024-12', amount: 1500000, orders: 20 },
    { month: '2025-01', amount: 1650000, orders: 22 },
  ],
  byCategory: [
    { category: '标准件', amount: 850000, percentage: 29.8 },
    { category: '电气件', amount: 1200000, percentage: 42.1 },
    { category: '机械件', amount: 600000, percentage: 21.1 },
    { category: '其他', amount: 200000, percentage: 7.0 },
  ],
  bySupplier: [
    { supplier: '欧姆龙(上海)代理', amount: 450000, orders: 12, avgPrice: 37500 },
    { supplier: 'THK(深圳)销售', amount: 380000, orders: 8, avgPrice: 47500 },
    { supplier: '三菱电机', amount: 320000, orders: 6, avgPrice: 53333 },
    { supplier: '其他供应商', amount: 1700000, orders: 28, avgPrice: 60714 },
  ],
  costSavings: 125000,
  savingsRate: 4.2,
}

export default function CostAnalysis() {
  const [loading, setLoading] = useState(true)
  const [selectedTab, setSelectedTab] = useState('overview')
  const [timeRange, setTimeRange] = useState('month')
  const [analysisData, setAnalysisData] = useState(mockCostAnalysis)

  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')

  const loadAnalysisData = useCallback(async () => {
    try {
      setLoading(true)
      
      if (isDemoAccount) {
        // Use mock data for demo accounts
        setAnalysisData(mockCostAnalysis)
      } else {
        // Calculate date range
        const now = new Date()
        const startDate = timeRange === 'month' 
          ? new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
          : timeRange === 'quarter'
          ? new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1).toISOString().split('T')[0]
          : new Date(now.getFullYear(), 0, 1).toISOString().split('T')[0]
        const endDate = now.toISOString().split('T')[0]

        // Load purchase orders
        const ordersRes = await purchaseApi.orders.list({
          page: 1,
          page_size: 1000,
          start_date: startDate,
          end_date: endDate,
        })
        const orders = ordersRes.data?.items || ordersRes.data || []

        // Calculate statistics
        const totalCost = orders.reduce((sum, o) => sum + (parseFloat(o.total_amount || 0)), 0)
        
        // Group by category
        const byCategory = {}
        orders.forEach(order => {
          order.items?.forEach(item => {
            const category = item.material_category || item.category || '其他'
            const itemAmount = parseFloat(item.amount || item.unit_price * item.quantity || 0)
            byCategory[category] = (byCategory[category] || 0) + itemAmount
          })
        })

        // Group by supplier
        const bySupplier = {}
        orders.forEach(order => {
          const supplier = order.supplier_name || order.supplier?.name || '未知供应商'
          if (!bySupplier[supplier]) {
            bySupplier[supplier] = { amount: 0, orders: 0 }
          }
          bySupplier[supplier].amount += parseFloat(order.total_amount || 0)
          bySupplier[supplier].orders += 1
        })

        // Calculate monthly trend
        const monthlyTrendMap = {}
        orders.forEach(order => {
          const orderDate = order.order_date || order.created_at
          if (orderDate) {
            const date = new Date(orderDate)
            const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
            if (!monthlyTrendMap[monthKey]) {
              monthlyTrendMap[monthKey] = { amount: 0, orders: 0 }
            }
            monthlyTrendMap[monthKey].amount += parseFloat(order.total_amount || 0)
            monthlyTrendMap[monthKey].orders += 1
          }
        })
        const monthlyTrend = Object.entries(monthlyTrendMap)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([month, data]) => ({
            month,
            amount: data.amount,
            orders: data.orders,
          }))

        // Calculate cost savings (simplified: compare with previous period)
        // For now, we'll use a placeholder calculation
        let costSavings = 0
        let savingsRate = 0
        if (monthlyTrend.length >= 2) {
          const currentMonth = monthlyTrend[monthlyTrend.length - 1]
          const previousMonth = monthlyTrend[monthlyTrend.length - 2]
          const avgOrderCostCurrent = currentMonth.orders > 0 ? currentMonth.amount / currentMonth.orders : 0
          const avgOrderCostPrevious = previousMonth.orders > 0 ? previousMonth.amount / previousMonth.orders : 0
          if (avgOrderCostPrevious > 0) {
            const savingsPerOrder = avgOrderCostPrevious - avgOrderCostCurrent
            costSavings = savingsPerOrder * currentMonth.orders
            savingsRate = (savingsPerOrder / avgOrderCostPrevious) * 100
          }
        }

        setAnalysisData({
          totalPurchaseCost: totalCost,
          monthlyTrend,
          byCategory: Object.entries(byCategory).map(([category, amount]) => ({
            category,
            amount,
            percentage: totalCost > 0 ? (amount / totalCost) * 100 : 0,
          })),
          bySupplier: Object.entries(bySupplier).map(([supplier, data]) => ({
            supplier,
            amount: data.amount,
            orders: data.orders,
            avgPrice: data.orders > 0 ? data.amount / data.orders : 0,
          })),
          costSavings: Math.max(0, costSavings), // Ensure non-negative
          savingsRate: Math.max(0, savingsRate),
        })
      }
    } catch (error) {
      console.error('Failed to load cost analysis:', error)
      if (isDemoAccount) {
        setAnalysisData(mockCostAnalysis)
      }
    } finally {
      setLoading(false)
    }
  }, [isDemoAccount, timeRange])

  useEffect(() => {
    loadAnalysisData()
  }, [loadAnalysisData])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="成本分析"
          description="采购成本分析、供应商成本对比、成本趋势"
        />

        {/* Time Range Selector */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span className="text-slate-400">时间范围：</span>
                <Select value={timeRange} onValueChange={setTimeRange}>
                  <SelectTrigger className="w-32 bg-slate-900/50 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="month">本月</SelectItem>
                    <SelectItem value="quarter">本季度</SelectItem>
                    <SelectItem value="year">本年</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button variant="outline">
                <Download className="w-4 h-4 mr-2" />
                导出报表
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Summary Stats */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-4 gap-4"
        >
          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2">采购总成本</p>
                  <p className="text-2xl font-bold text-white">
                    {formatCurrency(analysisData.totalPurchaseCost)}
                  </p>
                </div>
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <DollarSign className="w-5 h-5 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2">成本节省</p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {formatCurrency(analysisData.costSavings)}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    {analysisData.savingsRate.toFixed(1)}% 节省率
                  </p>
                </div>
                <div className="p-2 bg-emerald-500/20 rounded-lg">
                  <TrendingDown className="w-5 h-5 text-emerald-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2">供应商数量</p>
                  <p className="text-2xl font-bold text-purple-400">
                    {analysisData.bySupplier.length}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    活跃供应商
                  </p>
                </div>
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Building2 className="w-5 h-5 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700/50">
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-2">物料类别</p>
                  <p className="text-2xl font-bold text-amber-400">
                    {analysisData.byCategory.length}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    主要类别
                  </p>
                </div>
                <div className="p-2 bg-amber-500/20 rounded-lg">
                  <Package className="w-5 h-5 text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Analysis Tabs */}
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
          <TabsList className="bg-slate-800/50 border-slate-700/50">
            <TabsTrigger value="overview" className="data-[state=active]:bg-slate-700">概览</TabsTrigger>
            <TabsTrigger value="category" className="data-[state=active]:bg-slate-700">按类别</TabsTrigger>
            <TabsTrigger value="supplier" className="data-[state=active]:bg-slate-700">按供应商</TabsTrigger>
            <TabsTrigger value="trend" className="data-[state=active]:bg-slate-700">趋势分析</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Cost by Category */}
              <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-slate-200">成本分布（按类别）</CardTitle>
                  <CardDescription className="text-slate-400">各物料类别的成本占比</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analysisData.byCategory.map((item, idx) => (
                      <div key={idx} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-300">{item.category}</span>
                          <span className="text-slate-200 font-medium">
                            {formatCurrency(item.amount)} ({item.percentage.toFixed(1)}%)
                          </span>
                        </div>
                        <div className="w-full bg-slate-700/50 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${item.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Top Suppliers */}
              <Card className="bg-slate-800/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-slate-200">主要供应商</CardTitle>
                  <CardDescription className="text-slate-400">采购金额排名</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {analysisData.bySupplier
                      .sort((a, b) => b.amount - a.amount)
                      .slice(0, 5)
                      .map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg">
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
                              idx === 0 ? 'bg-amber-500/20 text-amber-400' :
                              idx === 1 ? 'bg-slate-500/20 text-slate-400' :
                              idx === 2 ? 'bg-orange-500/20 text-orange-400' :
                              'bg-slate-600/20 text-slate-400'
                            )}>
                              {idx + 1}
                            </div>
                            <div>
                              <p className="text-slate-200 font-medium">{item.supplier}</p>
                              <p className="text-xs text-slate-400">{item.orders} 个订单</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-slate-200 font-semibold">{formatCurrency(item.amount)}</p>
                            <p className="text-xs text-slate-400">均价 {formatCurrency(item.avgPrice)}</p>
                          </div>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Category Tab */}
          <TabsContent value="category" className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">成本类别分析</CardTitle>
                <CardDescription className="text-slate-400">详细的类别成本统计</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analysisData.byCategory.map((item, idx) => (
                    <div key={idx} className="p-4 bg-slate-900/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-200 font-medium">{item.category}</span>
                        <span className="text-slate-300">{formatCurrency(item.amount)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-700/50 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${item.percentage}%` }}
                          />
                        </div>
                        <span className="text-sm text-slate-400 w-16 text-right">
                          {item.percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Supplier Tab */}
          <TabsContent value="supplier" className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">供应商成本分析</CardTitle>
                <CardDescription className="text-slate-400">各供应商的采购金额和订单统计</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {analysisData.bySupplier
                    .sort((a, b) => b.amount - a.amount)
                    .map((item, idx) => (
                      <div key={idx} className="p-4 bg-slate-900/50 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <Building2 className="w-5 h-5 text-slate-400" />
                            <div>
                              <p className="text-slate-200 font-medium">{item.supplier}</p>
                              <p className="text-xs text-slate-400">{item.orders} 个订单</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-slate-200 font-semibold text-lg">
                              {formatCurrency(item.amount)}
                            </p>
                            <p className="text-xs text-slate-400">
                              均价 {formatCurrency(item.avgPrice)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-slate-700/50 rounded-full h-1.5">
                            <div
                              className="bg-purple-500 h-1.5 rounded-full"
                              style={{ 
                                width: `${(item.amount / analysisData.totalPurchaseCost) * 100}%` 
                              }}
                            />
                          </div>
                          <span className="text-xs text-slate-400 w-20 text-right">
                            {((item.amount / analysisData.totalPurchaseCost) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Trend Tab */}
          <TabsContent value="trend" className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">成本趋势</CardTitle>
                <CardDescription className="text-slate-400">采购成本月度趋势分析</CardDescription>
              </CardHeader>
              <CardContent>
                {analysisData.monthlyTrend.length > 0 ? (
                  <div className="space-y-4">
                    {analysisData.monthlyTrend.map((item, idx) => (
                      <div key={idx} className="p-4 bg-slate-900/50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-slate-200 font-medium">{item.month}</span>
                          <span className="text-slate-300">{formatCurrency(item.amount)}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <span>{item.orders} 个订单</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400">
                    暂无趋势数据
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

