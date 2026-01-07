/**
 * Budget Management Page - 预算管理页面
 * Features: Project budget overview, budget usage tracking, budget alerts
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  CreditCard,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Search,
  Filter,
  Download,
  Eye,
  DollarSign,
  Calendar,
  Target,
  BarChart3,
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
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { projectApi, costApi } from '../services/api'

// Mock budget data for demo accounts
const mockBudgets = [
  {
    id: 1,
    project_code: 'PJ250108001',
    project_name: 'BMS老化测试设备',
    budget_amount: 1500000,
    used_amount: 1250000,
    remaining_amount: 250000,
    usage_rate: 83.3,
    status: 'WARNING',
    start_date: '2025-01-01',
    end_date: '2025-06-30',
  },
  {
    id: 2,
    project_code: 'PJ250106002',
    project_name: 'EOL功能测试设备',
    budget_amount: 2000000,
    used_amount: 1200000,
    remaining_amount: 800000,
    usage_rate: 60.0,
    status: 'NORMAL',
    start_date: '2025-01-15',
    end_date: '2025-08-31',
  },
  {
    id: 3,
    project_code: 'PJ250103003',
    project_name: 'ICT在线测试设备',
    budget_amount: 1800000,
    used_amount: 1700000,
    remaining_amount: 100000,
    usage_rate: 94.4,
    status: 'CRITICAL',
    start_date: '2024-12-01',
    end_date: '2025-05-31',
  },
]

export default function BudgetManagement() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [budgets, setBudgets] = useState([])
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterUsageRate, setFilterUsageRate] = useState('all')

  const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')

  const loadBudgets = useCallback(async () => {
    try {
      setLoading(true)
      
      if (isDemoAccount) {
        // Use mock data for demo accounts
        setBudgets(mockBudgets)
      } else {
        // Load projects with budget information
        const res = await projectApi.list({ page: 1, page_size: 100 })
        const projects = res.data?.items || res.data || []
        
        // Transform projects to budget format
        const budgetsData = await Promise.all(
          projects.map(async (project) => {
            try {
              const costSummary = await costApi.getProjectSummary(project.id)
              const summary = costSummary.data || {}
              const usedAmount = summary.total_cost || 0
              const budgetAmount = project.budget_amount || 0
              const usageRate = budgetAmount > 0 ? (usedAmount / budgetAmount) * 100 : 0
              
              let status = 'NORMAL'
              if (usageRate >= 90) status = 'CRITICAL'
              else if (usageRate >= 80) status = 'WARNING'
              
              return {
                id: project.id,
                project_code: project.project_code,
                project_name: project.project_name,
                budget_amount: budgetAmount,
                used_amount: usedAmount,
                remaining_amount: budgetAmount - usedAmount,
                usage_rate: usageRate,
                status,
                start_date: project.planned_start_date,
                end_date: project.planned_end_date,
              }
            } catch (err) {
              console.error(`Failed to load budget for project ${project.id}:`, err)
              return null
            }
          })
        )
        
        setBudgets(budgetsData.filter(Boolean))
      }
    } catch (error) {
      console.error('Failed to load budgets:', error)
      if (isDemoAccount) {
        setBudgets(mockBudgets)
      }
    } finally {
      setLoading(false)
    }
  }, [isDemoAccount])

  useEffect(() => {
    loadBudgets()
  }, [loadBudgets])

  const filteredBudgets = useMemo(() => {
    return budgets.filter(budget => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          budget.project_code?.toLowerCase().includes(keyword) ||
          budget.project_name?.toLowerCase().includes(keyword)
        )
      }
      if (filterStatus !== 'all') {
        if (filterStatus === 'critical' && budget.status !== 'CRITICAL') return false
        if (filterStatus === 'warning' && budget.status !== 'WARNING') return false
        if (filterStatus === 'normal' && budget.status !== 'NORMAL') return false
      }
      if (filterUsageRate !== 'all') {
        if (filterUsageRate === 'high' && budget.usage_rate < 80) return false
        if (filterUsageRate === 'medium' && (budget.usage_rate < 50 || budget.usage_rate >= 80)) return false
        if (filterUsageRate === 'low' && budget.usage_rate >= 50) return false
      }
      return true
    })
  }, [budgets, searchKeyword, filterStatus, filterUsageRate])

  const stats = useMemo(() => {
    const total = budgets.reduce((sum, b) => sum + b.budget_amount, 0)
    const used = budgets.reduce((sum, b) => sum + b.used_amount, 0)
    const remaining = budgets.reduce((sum, b) => sum + b.remaining_amount, 0)
    const critical = budgets.filter(b => b.status === 'CRITICAL').length
    const warning = budgets.filter(b => b.status === 'WARNING').length
    
    return {
      total,
      used,
      remaining,
      usageRate: total > 0 ? (used / total) * 100 : 0,
      critical,
      warning,
    }
  }, [budgets])

  const statusConfig = {
    CRITICAL: { label: '严重超支', color: 'bg-red-500 text-white' },
    WARNING: { label: '预算预警', color: 'bg-amber-500 text-white' },
    NORMAL: { label: '正常', color: 'bg-emerald-500 text-white' },
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title="预算管理"
          description="项目预算跟踪、使用情况监控、预算预警"
        />

        {/* Statistics */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-4 gap-4"
        >
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
                  className="pl-10 bg-slate-900/50 border-slate-700"
                />
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
              <Select value={filterUsageRate} onValueChange={setFilterUsageRate}>
                <SelectTrigger className="bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="使用率" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部</SelectItem>
                  <SelectItem value="high">高 (≥80%)</SelectItem>
                  <SelectItem value="medium">中 (50-80%)</SelectItem>
                  <SelectItem value="low">低 ({'<50%'})</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="outline" onClick={() => navigate('/costs')}>
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
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : filteredBudgets.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无预算数据</div>
            ) : (
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
                    <TableHead className="text-right text-slate-400">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredBudgets.map((budget) => (
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
                          <Progress value={budget.usage_rate} className="flex-1 h-2" />
                          <span className={cn(
                            'text-sm font-medium w-16 text-right',
                            budget.usage_rate >= 90 ? 'text-red-400' :
                            budget.usage_rate >= 80 ? 'text-amber-400' :
                            'text-emerald-400'
                          )}>
                            {budget.usage_rate.toFixed(1)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={statusConfig[budget.status]?.color || 'bg-slate-500'}>
                          {statusConfig[budget.status]?.label || budget.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-slate-400 text-sm">
                        {budget.start_date && budget.end_date
                          ? `${formatDate(budget.start_date)} ~ ${formatDate(budget.end_date)}`
                          : '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate(`/projects/${budget.id}`)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

