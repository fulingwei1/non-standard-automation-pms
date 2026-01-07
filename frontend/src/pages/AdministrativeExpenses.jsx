/**
 * Administrative Expenses - Administrative expenses statistics and analysis
 * Features: Expense statistics, budget analysis, expense trends, category breakdown
 */

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Calendar,
  Download,
  Filter,
  Package,
  Car,
  Building2,
  Coffee,
  Printer,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Progress,
} from '../components/ui'
import { cn, formatCurrency } from '../lib/utils'
import { staggerContainer } from '../lib/animations'
import {
  SimpleBarChart,
  SimplePieChart,
  MonthlyTrendChart,
  TrendComparisonCard,
  CategoryBreakdownCard,
} from '../components/administrative/StatisticsCharts'

// Mock data
const mockExpenseStats = {
  monthlyBudget: 500000,
  monthlySpent: 385000,
  budgetUtilization: 77,
  remainingBudget: 115000,
  lastMonthSpent: 420000,
  trend: -8.3,
}

const mockCategoryExpenses = [
  { category: '办公用品', amount: 45000, percentage: 11.7, icon: Package, color: 'text-blue-400' },
  { category: '车辆费用', amount: 28000, percentage: 7.3, icon: Car, color: 'text-cyan-400' },
  { category: '固定资产', amount: 120000, percentage: 31.2, icon: Building2, color: 'text-purple-400' },
  { category: '会议费用', amount: 15000, percentage: 3.9, icon: Coffee, color: 'text-green-400' },
  { category: '设备维护', amount: 35000, percentage: 9.1, icon: Printer, color: 'text-amber-400' },
  { category: '其他费用', amount: 152000, percentage: 39.5, icon: DollarSign, color: 'text-slate-400' },
]

const mockMonthlyTrend = [
  { month: '2024-07', amount: 380000 },
  { month: '2024-08', amount: 395000 },
  { month: '2024-09', amount: 410000 },
  { month: '2024-10', amount: 425000 },
  { month: '2024-11', amount: 420000 },
  { month: '2024-12', amount: 385000 },
]

export default function AdministrativeExpenses() {
  const [periodFilter, setPeriodFilter] = useState('month')

  const totalExpenses = useMemo(() => {
    return mockCategoryExpenses.reduce((sum, item) => sum + item.amount, 0)
  }, [])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="行政费用统计"
        description="行政费用统计分析、预算执行、费用趋势"
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Download className="w-4 h-4 mr-2" />
              导出报表
            </Button>
            <select
              value={periodFilter}
              onChange={(e) => setPeriodFilter(e.target.value)}
              className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white"
            >
              <option value="month">本月</option>
              <option value="quarter">本季度</option>
              <option value="year">本年</option>
            </select>
          </div>
        }
      />

      {/* Key Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">月度预算</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(mockExpenseStats.monthlyBudget)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">已使用</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {formatCurrency(mockExpenseStats.monthlySpent)}
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">剩余预算</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">
                  {formatCurrency(mockExpenseStats.remainingBudget)}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">使用率</p>
                <p className="text-2xl font-bold text-cyan-400 mt-1">
                  {mockExpenseStats.budgetUtilization}%
                </p>
                <div className="flex items-center gap-1 mt-1">
                  {mockExpenseStats.trend < 0 ? (
                    <>
                      <TrendingDown className="w-3 h-3 text-emerald-400" />
                      <span className="text-xs text-emerald-400">{Math.abs(mockExpenseStats.trend)}%</span>
                    </>
                  ) : (
                    <>
                      <TrendingUp className="w-3 h-3 text-red-400" />
                      <span className="text-xs text-red-400">+{mockExpenseStats.trend}%</span>
                    </>
                  )}
                  <span className="text-xs text-slate-500 ml-1">vs 上月</span>
                </div>
              </div>
              <PieChart className="h-8 w-8 text-cyan-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Budget Progress */}
      <Card>
        <CardHeader>
          <CardTitle>预算执行情况</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">月度预算</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {formatCurrency(mockExpenseStats.monthlyBudget)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-400">已使用</p>
                <p className="text-3xl font-bold text-amber-400 mt-1">
                  {formatCurrency(mockExpenseStats.monthlySpent)}
                </p>
              </div>
            </div>
            <Progress
              value={mockExpenseStats.budgetUtilization}
              className="h-4 bg-slate-700/50"
            />
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">
                使用率: {mockExpenseStats.budgetUtilization}%
              </span>
              <span className="text-slate-400">
                剩余: {formatCurrency(mockExpenseStats.remainingBudget)}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs defaultValue="categories" className="space-y-4">
        <TabsList>
          <TabsTrigger value="categories">费用分类</TabsTrigger>
          <TabsTrigger value="trend">趋势分析</TabsTrigger>
          <TabsTrigger value="details">明细列表</TabsTrigger>
        </TabsList>

        <TabsContent value="categories" className="space-y-4">
          {/* Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle>费用分类占比</CardTitle>
            </CardHeader>
            <CardContent>
              <SimplePieChart
                data={mockCategoryExpenses.map((item, index) => ({
                  label: item.category,
                  value: item.amount,
                  color: index === 0 ? '#3b82f6' : 
                         index === 1 ? '#06b6d4' : 
                         index === 2 ? '#a855f7' : 
                         index === 3 ? '#10b981' : 
                         index === 4 ? '#f59e0b' : '#64748b',
                }))}
                size={200}
              />
            </CardContent>
          </Card>

          {/* Category Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>费用分类明细</CardTitle>
            </CardHeader>
            <CardContent>
              <CategoryBreakdownCard
                title="本月费用分类"
                data={mockCategoryExpenses.map((item, index) => ({
                  label: item.category,
                  value: item.amount,
                  color: index === 0 ? '#3b82f6' : 
                         index === 1 ? '#06b6d4' : 
                         index === 2 ? '#a855f7' : 
                         index === 3 ? '#10b981' : 
                         index === 4 ? '#f59e0b' : '#64748b',
                }))}
                total={totalExpenses}
                formatValue={formatCurrency}
              />
            </CardContent>
          </Card>

          {/* Category Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mockCategoryExpenses.map((item, index) => {
              const Icon = item.icon
              return (
                <Card key={index}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <Icon className={cn('h-6 w-6', item.color)} />
                        <div>
                          <h3 className="text-lg font-semibold text-white">{item.category}</h3>
                          <p className="text-sm text-slate-400">占比: {item.percentage}%</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-white">
                          {formatCurrency(item.amount)}
                        </p>
                      </div>
                    </div>
                    <Progress
                      value={item.percentage}
                      className="h-2 bg-slate-700/50"
                    />
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>

        <TabsContent value="trend" className="space-y-4">
          {/* Monthly Trend Chart */}
          <Card>
            <CardHeader>
              <CardTitle>月度费用趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <MonthlyTrendChart
                data={mockMonthlyTrend}
                valueKey="amount"
                labelKey="month"
                height={200}
              />
            </CardContent>
          </Card>

          {/* Trend Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <TrendComparisonCard
              title="本月费用"
              current={mockExpenseStats.monthlySpent}
              previous={mockExpenseStats.lastMonthSpent}
              formatValue={formatCurrency}
            />
            <TrendComparisonCard
              title="预算使用率"
              current={mockExpenseStats.budgetUtilization}
              previous={85}
              unit="%"
            />
            <TrendComparisonCard
              title="剩余预算"
              current={mockExpenseStats.remainingBudget}
              previous={80000}
              formatValue={formatCurrency}
            />
          </div>

          {/* Category Trend */}
          <Card>
            <CardHeader>
              <CardTitle>分类费用趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockCategoryExpenses.slice(0, 3).map((item, index) => {
                  const trendData = mockMonthlyTrend.map(month => ({
                    label: month.month,
                    value: Math.floor(month.amount * (item.percentage / 100)),
                  }))
                  return (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <item.icon className={cn('h-4 w-4', item.color)} />
                          <span className="text-sm font-medium text-white">{item.category}</span>
                        </div>
                        <span className="text-sm text-slate-400">
                          {formatCurrency(item.amount)}
                        </span>
                      </div>
                      <SimpleBarChart
                        data={trendData}
                        height={80}
                        color={index === 0 ? 'bg-blue-500' : 
                               index === 1 ? 'bg-cyan-500' : 'bg-purple-500'}
                      />
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="details" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>费用明细列表</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockCategoryExpenses.flatMap((category, catIndex) => {
                  // 模拟每个分类下的明细
                  const detailCount = Math.floor(category.amount / 5000) || 1
                  return Array.from({ length: Math.min(detailCount, 5) }, (_, i) => ({
                    id: `${catIndex}-${i}`,
                    category: category.category,
                    description: `${category.category}相关费用 ${i + 1}`,
                    amount: Math.floor(category.amount / detailCount),
                    date: `2025-01-${String(i + 1).padStart(2, '0')}`,
                    department: ['销售部', '项目部', '技术开发部', '生产部', '行政部'][i % 5],
                  }))
                }).map((detail) => (
                  <div
                    key={detail.id}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline">{detail.category}</Badge>
                          <span className="font-medium text-white">{detail.description}</span>
                        </div>
                        <div className="text-sm text-slate-400">
                          {detail.department} · {detail.date}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-white">
                          {formatCurrency(detail.amount)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}

