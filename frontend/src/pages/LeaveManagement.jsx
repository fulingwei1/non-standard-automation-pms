/**
 * Leave Management - Employee leave application and approval
 * Features: Leave application, approval workflow, leave balance, leave statistics
 */

import { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
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
} from 'lucide-react'
import { PageHeader } from '../components/layout'
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
} from '../components/ui'
import { cn, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { SimpleBarChart, MonthlyTrendChart, SimplePieChart, TrendComparisonCard } from '../components/administrative/StatisticsCharts'
import { adminApi } from '../services/api'

// Mock data
const mockLeaveApplications = [
  {
    id: 1,
    employee: '赵工程师',
    department: '机械部',
    type: '年假',
    days: 3,
    startDate: '2025-01-10',
    endDate: '2025-01-12',
    reason: '个人事务',
    status: 'pending',
    submitTime: '2025-01-06 11:30',
    approver: '行政经理',
  },
  {
    id: 2,
    employee: '钱工程师',
    department: '电气部',
    type: '病假',
    days: 1,
    startDate: '2025-01-08',
    endDate: '2025-01-08',
    reason: '身体不适',
    status: 'approved',
    submitTime: '2025-01-07 09:00',
    approver: '行政经理',
    approveTime: '2025-01-07 10:30',
  },
  {
    id: 3,
    employee: '孙工程师',
    department: '软件部',
    type: '事假',
    days: 2,
    startDate: '2025-01-09',
    endDate: '2025-01-10',
    reason: '家庭事务',
    status: 'rejected',
    submitTime: '2025-01-06 14:20',
    approver: '行政经理',
    rejectReason: '项目紧急，暂不批准',
  },
]

const mockLeaveBalance = [
  {
    employee: '赵工程师',
    department: '机械部',
    annualLeave: 10,
    usedAnnualLeave: 3,
    sickLeave: 5,
    usedSickLeave: 1,
    personalLeave: 3,
    usedPersonalLeave: 0,
  },
]

export default function LeaveManagement() {
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [leaveApplications, setLeaveApplications] = useState(mockLeaveApplications)

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await adminApi.leave.list()
        if (res.data?.items) {
          setLeaveApplications(res.data.items)
        } else if (Array.isArray(res.data)) {
          setLeaveApplications(res.data)
        }
      } catch (err) {
      console.error('操作失败:', err)
    }
      setLoading(false)
    }
    fetchData()
  }, [])

  const filteredApplications = useMemo(() => {
    return leaveApplications.filter(app => {
      const matchSearch = app.employee.toLowerCase().includes(searchText.toLowerCase()) ||
        app.department.toLowerCase().includes(searchText.toLowerCase())
      const matchStatus = statusFilter === 'all' || app.status === statusFilter
      const matchType = typeFilter === 'all' || app.type === typeFilter
      return matchSearch && matchStatus && matchType
    })
  }, [leaveApplications, searchText, statusFilter, typeFilter])

  const stats = useMemo(() => {
    const pending = leaveApplications.filter(a => a.status === 'pending').length
    const approved = leaveApplications.filter(a => a.status === 'approved').length
    const rejected = leaveApplications.filter(a => a.status === 'rejected').length
    const totalDays = leaveApplications
      .filter(a => a.status === 'approved')
      .reduce((sum, a) => sum + a.days, 0)
    return { pending, approved, rejected, totalDays }
  }, [leaveApplications])

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
                <p className="text-2xl font-bold text-amber-400 mt-1">{stats.pending}</p>
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
                <p className="text-2xl font-bold text-emerald-400 mt-1">{stats.approved}</p>
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
                <p className="text-2xl font-bold text-red-400 mt-1">{stats.rejected}</p>
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
                <p className="text-2xl font-bold text-white mt-1">{stats.totalDays}</p>
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
                    { label: '年假', value: leaveApplications.filter(a => a.type === '年假').length, color: '#3b82f6' },
                    { label: '病假', value: leaveApplications.filter(a => a.type === '病假').length, color: '#10b981' },
                    { label: '事假', value: leaveApplications.filter(a => a.type === '事假').length, color: '#f59e0b' },
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
                    { month: '2024-10', amount: 12 },
                    { month: '2024-11', amount: 15 },
                    { month: '2024-12', amount: 18 },
                    { month: '2025-01', amount: leaveApplications.length },
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
                        <h3 className="text-lg font-semibold text-white">{app.employee}</h3>
                        <Badge variant="outline">{app.department}</Badge>
                        <Badge variant="outline">{app.type}</Badge>
                        <Badge
                          variant="outline"
                          className={cn(
                            app.status === 'pending' && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                            app.status === 'approved' && 'bg-green-500/20 text-green-400 border-green-500/30',
                            app.status === 'rejected' && 'bg-red-500/20 text-red-400 border-red-500/30'
                          )}
                        >
                          {app.status === 'pending' ? '待审批' : 
                           app.status === 'approved' ? '已批准' : '已拒绝'}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm mb-3">
                        <div>
                          <p className="text-slate-400">请假天数</p>
                          <p className="text-white font-medium">{app.days} 天</p>
                        </div>
                        <div>
                          <p className="text-slate-400">开始日期</p>
                          <p className="text-white font-medium">{app.startDate}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">结束日期</p>
                          <p className="text-white font-medium">{app.endDate}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">审批人</p>
                          <p className="text-white font-medium">{app.approver}</p>
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
                    {app.status === 'pending' && (
                      <div className="flex gap-2 ml-4">
                        <Button size="sm">批准</Button>
                        <Button size="sm" variant="outline">拒绝</Button>
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
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">员工</th>
                      <th className="text-left py-3 px-4 text-slate-400 font-medium">部门</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">年假(天)</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">病假(天)</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">事假(天)</th>
                      <th className="text-center py-3 px-4 text-slate-400 font-medium">调休(天)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { name: '赵工程师', dept: '机械部', annual: 8, sick: 5, personal: 3, comp: 2 },
                      { name: '钱工程师', dept: '电气部', annual: 10, sick: 5, personal: 3, comp: 1.5 },
                      { name: '孙工程师', dept: '软件部', annual: 5, sick: 5, personal: 3, comp: 0 },
                      { name: '李工程师', dept: '项目部', annual: 12, sick: 5, personal: 3, comp: 3 },
                      { name: '周工程师', dept: '测试部', annual: 7, sick: 5, personal: 2, comp: 0.5 },
                    ].map((emp, idx) => (
                      <tr key={idx} className="border-b border-slate-800 hover:bg-slate-800/30">
                        <td className="py-3 px-4 text-white">{emp.name}</td>
                        <td className="py-3 px-4 text-slate-400">{emp.dept}</td>
                        <td className="py-3 px-4 text-center">
                          <span className={cn('font-medium', emp.annual > 5 ? 'text-green-400' : 'text-amber-400')}>
                            {emp.annual}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center text-slate-300">{emp.sick}</td>
                        <td className="py-3 px-4 text-center text-slate-300">{emp.personal}</td>
                        <td className="py-3 px-4 text-center text-blue-400">{emp.comp}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="statistics">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>请假类型分布</CardTitle>
              </CardHeader>
              <CardContent>
                <SimplePieChart
                  data={[
                    { name: '年假', value: 45, color: '#22c55e' },
                    { name: '病假', value: 20, color: '#f59e0b' },
                    { name: '事假', value: 25, color: '#3b82f6' },
                    { name: '调休', value: 10, color: '#8b5cf6' },
                  ]}
                  height={250}
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
                    { month: '7月', value: 28 },
                    { month: '8月', value: 35 },
                    { month: '9月', value: 22 },
                    { month: '10月', value: 30 },
                    { month: '11月', value: 25 },
                    { month: '12月', value: 32 },
                  ]}
                  height={250}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>部门请假统计</CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleBarChart
                  data={[
                    { name: '销售部', value: 15 },
                    { name: '项目部', value: 12 },
                    { name: '技术部', value: 18 },
                    { name: '生产部', value: 8 },
                    { name: '行政部', value: 5 },
                  ]}
                  height={250}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>关键指标</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <TrendComparisonCard
                  title="本月请假天数"
                  current={32}
                  previous={25}
                  unit="天"
                />
                <TrendComparisonCard
                  title="平均请假时长"
                  current={2.5}
                  previous={2.8}
                  unit="天/次"
                />
                <TrendComparisonCard
                  title="待审批申请"
                  current={5}
                  previous={8}
                  unit="件"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}

