/**
 * HR Manager Dashboard - Main dashboard for human resources manager
 * Features: HR planning, Recruitment management, Performance management, Employee relations
 * Core Functions: HR strategy, Recruitment approval, Performance review, Employee relationship management
 */

import { useState, useMemo, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Users,
  UserPlus,
  UserCheck,
  Award,
  TrendingUp,
  TrendingDown,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Building2,
  BarChart3,
  PieChart,
  Target,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Briefcase,
  GraduationCap,
  Heart,
  Shield,
  Zap,
  ChevronRight,
  Eye,
  Edit,
  XCircle,
  Filter,
  FileSpreadsheet,
  RefreshCw,
  MoreVertical,
  Printer,
  Share2,
  Settings,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
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
  TabsTrigger,
  Input,
  LoadingCard,
  ErrorMessage,
  EmptyState,
  SkeletonCard,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  Label,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { employeeApi, departmentApi } from '../services/api'
import { toast } from '../components/ui/toast'

// Mock statistics
const mockHRStats = {
  totalEmployees: 186,
  activeEmployees: 178,
  newEmployeesThisMonth: 8,
  leavingEmployeesThisMonth: 2,
  departments: 12,
  avgAge: 32.5,
  avgTenure: 3.2,
  
  // Recruitment
  pendingRecruitments: 15,
  inProgressRecruitments: 8,
  completedRecruitments: 12,
  recruitmentSuccessRate: 85.5,
  
  // Performance
  pendingPerformanceReviews: 28,
  completedPerformanceReviews: 150,
  performanceCompletionRate: 84.3,
  avgPerformanceScore: 82.5,
  
  // Attendance
  todayAttendanceRate: 95.6,
  monthlyAttendanceRate: 94.2,
  lateCount: 3,
  absentCount: 2,
  
  // Employee Relations
  pendingEmployeeIssues: 5,
  resolvedIssues: 18,
  employeeSatisfaction: 88.5,
}

// Mock pending recruitments
const mockPendingRecruitments = [
  {
    id: 1,
    position: '高级机械工程师',
    department: '技术开发部',
    urgency: 'high',
    applicants: 12,
    interviews: 3,
    status: 'interviewing',
    createdDate: '2025-01-03',
    expectedStartDate: '2025-02-01',
    budget: 15000,
  },
  {
    id: 2,
    position: '项目经理',
    department: '项目部',
    urgency: 'high',
    applicants: 8,
    interviews: 2,
    status: 'screening',
    createdDate: '2025-01-04',
    expectedStartDate: '2025-02-15',
    budget: 18000,
  },
  {
    id: 3,
    position: '电气工程师',
    department: '电气部',
    urgency: 'medium',
    applicants: 15,
    interviews: 0,
    status: 'recruiting',
    createdDate: '2025-01-05',
    expectedStartDate: '2025-03-01',
    budget: 12000,
  },
  {
    id: 4,
    position: '销售工程师',
    department: '销售部',
    urgency: 'medium',
    applicants: 20,
    interviews: 5,
    status: 'offer',
    createdDate: '2024-12-28',
    expectedStartDate: '2025-01-20',
    budget: 14000,
  },
]

// Mock pending performance reviews
const mockPendingReviews = [
  {
    id: 1,
    employeeName: '张工',
    department: '机械部',
    period: '2024年Q4',
    status: 'pending',
    dueDate: '2025-01-10',
    priority: 'high',
  },
  {
    id: 2,
    employeeName: '李工',
    department: '电气部',
    period: '2024年Q4',
    status: 'pending',
    dueDate: '2025-01-10',
    priority: 'high',
  },
  {
    id: 3,
    employeeName: '王经理',
    department: '项目部',
    period: '2024年Q4',
    status: 'reviewing',
    dueDate: '2025-01-12',
    priority: 'medium',
  },
  {
    id: 4,
    employeeName: '刘工',
    department: '测试部',
    period: '2024年Q4',
    status: 'pending',
    dueDate: '2025-01-15',
    priority: 'medium',
  },
]

// Mock department distribution
const mockDepartmentDistribution = [
  {
    id: 1,
    name: '技术开发部',
    total: 45,
    active: 43,
    new: 2,
    leaving: 0,
    avgAge: 30.5,
    avgTenure: 2.8,
    performance: 85.2,
  },
  {
    id: 2,
    name: '项目部',
    total: 28,
    active: 27,
    new: 1,
    leaving: 1,
    avgAge: 33.2,
    avgTenure: 3.5,
    performance: 82.8,
  },
  {
    id: 3,
    name: '销售部',
    total: 35,
    active: 34,
    new: 3,
    leaving: 1,
    avgAge: 31.8,
    avgTenure: 2.5,
    performance: 88.5,
  },
  {
    id: 4,
    name: '生产部',
    total: 52,
    active: 50,
    new: 2,
    leaving: 2,
    avgAge: 35.2,
    avgTenure: 4.2,
    performance: 80.5,
  },
  {
    id: 5,
    name: '采购部',
    total: 8,
    active: 8,
    new: 0,
    leaving: 0,
    avgAge: 32.0,
    avgTenure: 3.0,
    performance: 83.5,
  },
  {
    id: 6,
    name: '质量部',
    total: 12,
    active: 12,
    new: 0,
    leaving: 0,
    avgAge: 34.5,
    avgTenure: 3.8,
    performance: 87.2,
  },
]

// Mock employee issues
const mockEmployeeIssues = [
  {
    id: 1,
    type: 'conflict',
    title: '部门内部冲突',
    employee: '张工',
    department: '机械部',
    status: 'pending',
    priority: 'high',
    createdAt: '2025-01-05',
    description: '与同事在工作分配上存在分歧',
  },
  {
    id: 2,
    type: 'leave',
    title: '长期请假申请',
    employee: '李工',
    department: '电气部',
    status: 'reviewing',
    priority: 'medium',
    createdAt: '2025-01-04',
    description: '申请病假30天，需要审批',
  },
  {
    id: 3,
    type: 'complaint',
    title: '工作环境投诉',
    employee: '王工',
    department: '生产部',
    status: 'processing',
    priority: 'medium',
    createdAt: '2025-01-03',
    description: '反映车间噪音问题',
  },
]

// Mock recruitment trends
const mockRecruitmentTrends = [
  { month: '8月', positions: 8, hired: 6 },
  { month: '9月', positions: 10, hired: 8 },
  { month: '10月', positions: 12, hired: 10 },
  { month: '11月', positions: 15, hired: 12 },
  { month: '12月', positions: 18, hired: 15 },
  { month: '1月', positions: 15, hired: 8 },
]

// Mock performance distribution
const mockPerformanceDistribution = [
  { level: '优秀', count: 32, percentage: 18.0, color: 'emerald' },
  { level: '良好', count: 85, percentage: 47.8, color: 'blue' },
  { level: '合格', count: 48, percentage: 27.0, color: 'amber' },
  { level: '待改进', count: 13, percentage: 7.3, color: 'red' },
]

// Mock detailed statistics data
const mockEmployeeAgeDistribution = [
  { range: '20-25岁', count: 18, percentage: 10.1 },
  { range: '26-30岁', count: 52, percentage: 29.2 },
  { range: '31-35岁', count: 68, percentage: 38.2 },
  { range: '36-40岁', count: 28, percentage: 15.7 },
  { range: '41-45岁', count: 8, percentage: 4.5 },
  { range: '46岁以上', count: 4, percentage: 2.2 },
]

const mockEmployeeTenureDistribution = [
  { range: '0-1年', count: 32, percentage: 18.0 },
  { range: '1-3年', count: 68, percentage: 38.2 },
  { range: '3-5年', count: 45, percentage: 25.3 },
  { range: '5-10年', count: 28, percentage: 15.7 },
  { range: '10年以上', count: 5, percentage: 2.8 },
]

const mockEmployeeEducationDistribution = [
  { level: '博士', count: 2, percentage: 1.1 },
  { level: '硕士', count: 18, percentage: 10.1 },
  { level: '本科', count: 95, percentage: 53.4 },
  { level: '专科', count: 52, percentage: 29.2 },
  { level: '高中及以下', count: 11, percentage: 6.2 },
]

const mockMonthlyEmployeeFlow = [
  { month: '7月', new: 5, leaving: 2, net: 3 },
  { month: '8月', new: 6, leaving: 1, net: 5 },
  { month: '9月', new: 8, leaving: 3, net: 5 },
  { month: '10月', new: 7, leaving: 2, net: 5 },
  { month: '11月', new: 9, leaving: 4, net: 5 },
  { month: '12月', new: 10, leaving: 2, net: 8 },
  { month: '1月', new: 8, leaving: 2, net: 6 },
]

const mockDepartmentPerformanceComparison = [
  { department: '技术开发部', avgScore: 85.2, rank: 1, trend: 2.3 },
  { department: '质量部', avgScore: 87.2, rank: 2, trend: 1.8 },
  { department: '销售部', avgScore: 88.5, rank: 3, trend: 3.2 },
  { department: '项目部', avgScore: 82.8, rank: 4, trend: 1.5 },
  { department: '采购部', avgScore: 83.5, rank: 5, trend: 0.8 },
  { department: '生产部', avgScore: 80.5, rank: 6, trend: -0.5 },
]

const mockAttendanceTrend = [
  { month: '7月', rate: 93.5, late: 12, absent: 8 },
  { month: '8月', rate: 94.2, late: 10, absent: 6 },
  { month: '9月', rate: 93.8, late: 11, absent: 7 },
  { month: '10月', rate: 94.5, late: 9, absent: 5 },
  { month: '11月', rate: 94.8, late: 8, absent: 4 },
  { month: '12月', rate: 95.2, late: 6, absent: 3 },
  { month: '1月', rate: 95.6, late: 3, absent: 2 },
]

const mockRecruitmentChannelStats = [
  { channel: '招聘网站', count: 45, percentage: 45.0, successRate: 82.2 },
  { channel: '内部推荐', count: 28, percentage: 28.0, successRate: 92.9 },
  { channel: '校园招聘', count: 15, percentage: 15.0, successRate: 73.3 },
  { channel: '猎头推荐', count: 8, percentage: 8.0, successRate: 87.5 },
  { channel: '其他', count: 4, percentage: 4.0, successRate: 75.0 },
]

const mockPerformanceTrend = [
  { period: '2024Q1', avgScore: 78.5, excellent: 25, good: 70, qualified: 60, needsImprovement: 23 },
  { period: '2024Q2', avgScore: 80.2, excellent: 28, good: 75, qualified: 55, needsImprovement: 20 },
  { period: '2024Q3', avgScore: 81.8, excellent: 30, good: 80, qualified: 50, needsImprovement: 18 },
  { period: '2024Q4', avgScore: 82.5, excellent: 32, good: 85, qualified: 48, needsImprovement: 13 },
]

const getStatusColor = (status) => {
  const colors = {
    active: 'bg-emerald-500',
    pending: 'bg-amber-500',
    reviewing: 'bg-blue-500',
    processing: 'bg-purple-500',
    completed: 'bg-slate-500',
    recruiting: 'bg-blue-500',
    screening: 'bg-amber-500',
    interviewing: 'bg-purple-500',
    offer: 'bg-emerald-500',
  }
  return colors[status] || 'bg-slate-500'
}

const getStatusLabel = (status) => {
  const labels = {
    active: '在职',
    pending: '待处理',
    reviewing: '评审中',
    processing: '处理中',
    completed: '已完成',
    recruiting: '招聘中',
    screening: '筛选中',
    interviewing: '面试中',
    offer: '发Offer',
  }
  return labels[status] || status
}

const getPriorityColor = (priority) => {
  const colors = {
    high: 'bg-red-500',
    medium: 'bg-amber-500',
    low: 'bg-blue-500',
  }
  return colors[priority] || 'bg-slate-500'
}

const getIssueTypeColor = (type) => {
  const colors = {
    conflict: 'bg-red-500',
    leave: 'bg-amber-500',
    complaint: 'bg-blue-500',
    performance: 'bg-purple-500',
  }
  return colors[type] || 'bg-slate-500'
}

const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg }) => {
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn('text-2xl font-bold mb-1', color)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500">{subtitle}</p>
          )}
          {trend !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}%</span>
                </>
              ) : trend < 0 ? (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}%</span>
                </>
              ) : null}
              {trend !== 0 && (
                <span className="text-xs text-slate-500 ml-1">vs 上月</span>
              )}
            </div>
          )}
        </div>
        <div className={cn('rounded-lg p-3 bg-opacity-20', bg)}>
          <Icon className={cn('h-6 w-6', color)} />
        </div>
      </div>
      <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
    </motion.div>
  )
}

export default function HRManagerDashboard() {
  const [selectedTab, setSelectedTab] = useState('overview')
  const [statisticsPeriod, setStatisticsPeriod] = useState('month')
  const [employees, setEmployees] = useState([])
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterDepartment, setFilterDepartment] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [statsLoading, setStatsLoading] = useState(false)
  const [showEmployeeDialog, setShowEmployeeDialog] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  // Load employees
  useEffect(() => {
    if (selectedTab === 'employees') {
      loadEmployees()
      loadDepartments()
    }
  }, [selectedTab, searchKeyword, filterDepartment, filterStatus])

  const loadEmployees = async () => {
    setLoading(true)
    try {
      const params = {
        skip: 0,
        limit: 100,
      }
      const response = await employeeApi.list(params)
      const employeeList = response.data || []
      
      // 前端筛选（临时方案，待后端支持keyword/department/is_active参数）
      let filtered = employeeList
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        filtered = filtered.filter(emp => 
          (emp.name && emp.name.toLowerCase().includes(keyword)) ||
          (emp.employee_code && emp.employee_code.toLowerCase().includes(keyword)) ||
          (emp.phone && emp.phone.includes(keyword))
        )
      }
      if (filterDepartment !== 'all') {
        filtered = filtered.filter(emp => emp.department === filterDepartment)
      }
      if (filterStatus !== 'all') {
        filtered = filtered.filter(emp => 
          filterStatus === 'active' ? emp.is_active : !emp.is_active
        )
      }
      setEmployees(filtered)
      setError(null)
    } catch (error) {
      setError(error.response?.data?.detail || error.message || '加载员工列表失败')
      setEmployees([])
    } finally {
      setLoading(false)
    }
  }

  const loadDepartments = async () => {
    try {
      const response = await departmentApi.list({})
      setDepartments(response.data || [])
    } catch (error) {
      // 部门加载失败不影响主流程，使用空数组
      setDepartments([])
    }
  }

  // Export report function
  const handleExportReport = () => {
    try {
      const exportData = {
        '统计周期': statisticsPeriod === 'month' ? '本月' : statisticsPeriod === 'quarter' ? '本季度' : '本年',
        '员工总数': mockHRStats.totalEmployees,
        '在职员工': mockHRStats.activeEmployees,
        '本月新增': mockHRStats.newEmployeesThisMonth,
        '本月离职': mockHRStats.leavingEmployeesThisMonth,
        '部门数量': mockHRStats.departments,
        '平均年龄': mockHRStats.avgAge,
        '平均工龄': mockHRStats.avgTenure,
        '待招聘': mockHRStats.pendingRecruitments,
        '招聘中': mockHRStats.inProgressRecruitments,
        '已完成招聘': mockHRStats.completedRecruitments,
        '招聘成功率': `${mockHRStats.recruitmentSuccessRate}%`,
        '待绩效评审': mockHRStats.pendingPerformanceReviews,
        '已完成评审': mockHRStats.completedPerformanceReviews,
        '绩效完成率': `${mockHRStats.performanceCompletionRate}%`,
        '平均绩效分数': mockHRStats.avgPerformanceScore,
      }

      const csvContent = [
        '项目,数值',
        ...Object.entries(exportData).map(([key, value]) => `"${key}","${value}"`),
      ].join('\n')
      
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `人事管理报表_${statisticsPeriod}_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      toast.success('报表导出成功')
    } catch (error) {
      toast.error('导出失败: ' + error.message)
    }
  }

  // Export employee list function
  const handleExportEmployeeList = () => {
    if (employees.length === 0) {
      toast.error('没有员工数据可导出')
      return
    }

    try {
      const csvContent = [
        '员工编码,姓名,部门,职位,状态,入职日期,电话,邮箱',
        ...employees.map(emp => [
          emp.employee_code || '',
          emp.name || '',
          emp.department || '',
          emp.position || '',
          emp.is_active ? '在职' : '离职',
          emp.hire_date || '',
          emp.phone || '',
          emp.email || '',
        ].map(field => `"${field}"`).join(',')),
      ].join('\n')
      
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `员工列表_${new Date().toISOString().split('T')[0]}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      toast.success('员工列表导出成功')
    } catch (error) {
      toast.error('导出失败: ' + error.message)
    }
  }

  // Print function
  const handlePrint = () => {
    window.print()
  }

  // Share function (copy link to clipboard)
  const handleShare = async () => {
    try {
      const url = window.location.href
      await navigator.clipboard.writeText(url)
      toast.success('链接已复制到剪贴板')
    } catch (error) {
      toast.error('分享失败: ' + error.message)
    }
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="人事管理"
        description={`在职员工: ${mockHRStats.activeEmployees}人 | 本月新增: ${mockHRStats.newEmployeesThisMonth}人 | 绩效完成率: ${mockHRStats.performanceCompletionRate}%`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm"
              className="flex items-center gap-2"
              onClick={() => {
                setSelectedTab('recruitment')
                // TODO: 打开新建招聘对话框
              }}
            >
              <UserPlus className="w-4 h-4" />
              新建招聘
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="flex items-center gap-2"
              onClick={() => {
                setSelectedTab('performance')
                // TODO: 跳转到绩效管理页面
              }}
            >
              <Award className="w-4 h-4" />
              绩效管理
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              className="flex items-center gap-2"
              disabled={refreshing}
              onClick={async () => {
                setRefreshing(true)
                try {
                  if (selectedTab === 'employees') {
                    await Promise.all([loadEmployees(), loadDepartments()])
                  } else {
                    // TODO: 刷新其他Tab的数据
                    await new Promise(resolve => setTimeout(resolve, 500))
                  }
                } finally {
                  setRefreshing(false)
                }
              }}
            >
              <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
              刷新
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="flex items-center gap-2">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={handleExportReport}>
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  导出报表
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handlePrint}>
                  <Printer className="w-4 h-4 mr-2" />
                  打印
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleShare}>
                  <Share2 className="w-4 h-4 mr-2" />
                  分享
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => {
                  // TODO: Implement settings
                }}>
                  <Settings className="w-4 h-4 mr-2" />
                  设置
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </motion.div>
        }
      />

      {/* Key Statistics - 6 column grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        <StatCard
          title="在职员工"
          value={mockHRStats.activeEmployees}
          subtitle={`总计 ${mockHRStats.totalEmployees} 人`}
          trend={2.3}
          icon={Users}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="待审批招聘"
          value={mockHRStats.pendingRecruitments}
          subtitle="需要处理"
          icon={UserPlus}
          color="text-amber-400"
          bg="bg-amber-500/10"
        />
        <StatCard
          title="待绩效评审"
          value={mockHRStats.pendingPerformanceReviews}
          subtitle="待完成"
          icon={Award}
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
        <StatCard
          title="今日出勤率"
          value={`${mockHRStats.todayAttendanceRate}%`}
          subtitle="考勤统计"
          icon={CheckCircle2}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          title="员工满意度"
          value={`${mockHRStats.employeeSatisfaction}%`}
          subtitle="关系管理"
          icon={Heart}
          color="text-pink-400"
          bg="bg-pink-500/10"
        />
        <StatCard
          title="平均绩效分"
          value={mockHRStats.avgPerformanceScore}
          subtitle="绩效指标"
          icon={Target}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
      </motion.div>

      {/* Main Content Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="bg-surface-50 border-white/10">
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="recruitment">招聘管理</TabsTrigger>
          <TabsTrigger value="performance">绩效管理</TabsTrigger>
          <TabsTrigger value="attendance">考勤管理</TabsTrigger>
          <TabsTrigger value="employees">员工管理</TabsTrigger>
          <TabsTrigger value="relations">员工关系</TabsTrigger>
          <TabsTrigger value="statistics">统计分析</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Pending Items */}
            <div className="lg:col-span-2 space-y-6">
              {/* Pending Recruitments */}
              <motion.div variants={fadeIn}>
                <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <UserPlus className="h-5 w-5 text-amber-400" />
                        待处理招聘
                      </CardTitle>
                      <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                        {mockPendingRecruitments.length}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {mockPendingRecruitments.map((recruitment, index) => (
                      <motion.div
                        key={recruitment.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                        onClick={() => {
                          // TODO: Navigate to recruitment detail page
                        }}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-white">{recruitment.position}</span>
                              <Badge
                                variant="outline"
                                className={cn(
                                  'text-xs',
                                  recruitment.urgency === 'high' && 'bg-red-500/20 text-red-400 border-red-500/30',
                                  recruitment.urgency === 'medium' && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                                )}
                              >
                                {recruitment.urgency === 'high' ? '紧急' : '普通'}
                              </Badge>
                              <Badge variant="outline" className="text-xs bg-slate-700/40">
                                {getStatusLabel(recruitment.status)}
                              </Badge>
                            </div>
                            <div className="text-xs text-slate-400">
                              {recruitment.department} · {recruitment.createdDate}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-bold text-white">
                              ¥{recruitment.budget.toLocaleString()}
                            </div>
                            <div className="text-xs text-slate-400">预算</div>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
                          <span>申请人: {recruitment.applicants} | 面试: {recruitment.interviews}</span>
                          <span>期望入职: {recruitment.expectedStartDate}</span>
                        </div>
                      </motion.div>
                    ))}
                    <Button variant="outline" className="w-full mt-3">
                      查看全部招聘
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Pending Performance Reviews */}
              <motion.div variants={fadeIn}>
                <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2 text-base">
                        <Award className="h-5 w-5 text-purple-400" />
                        待绩效评审
                      </CardTitle>
                      <Badge variant="outline" className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                        {mockPendingReviews.length}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {mockPendingReviews.map((review) => (
                      <motion.div
                        key={review.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                        onClick={() => {
                          // TODO: Navigate to performance review detail page
                        }}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-white">{review.employeeName}</span>
                              <Badge variant="outline" className="text-xs bg-slate-700/40">
                                {review.department}
                              </Badge>
                              {review.priority === 'high' && (
                                <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                                  紧急
                                </Badge>
                              )}
                            </div>
                            <div className="text-xs text-slate-400">
                              {review.period} · 截止: {review.dueDate}
                            </div>
                          </div>
                          <Badge variant="outline" className={cn(
                            'text-xs',
                            review.status === 'pending' && 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                            review.status === 'reviewing' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                          )}>
                            {getStatusLabel(review.status)}
                          </Badge>
                        </div>
                      </motion.div>
                    ))}
                    <Button variant="outline" className="w-full mt-3">
                      查看全部评审
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Right Column - Statistics */}
            <div className="space-y-6">
              {/* Employee Overview */}
              <motion.div variants={fadeIn}>
                <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Users className="h-5 w-5 text-blue-400" />
                      员工概览
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-slate-400">在职率</p>
                        <p className="text-lg font-bold text-white">
                          {((mockHRStats.activeEmployees / mockHRStats.totalEmployees) * 100).toFixed(1)}%
                        </p>
                      </div>
                      <Progress
                        value={(mockHRStats.activeEmployees / mockHRStats.totalEmployees) * 100}
                        className="h-2 bg-slate-700/50"
                      />
                    </div>
                    <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-slate-400">本月新增</p>
                        <p className="text-lg font-bold text-emerald-400">
                          +{mockHRStats.newEmployeesThisMonth}
                        </p>
                      </div>
                    </div>
                    <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-slate-400">本月离职</p>
                        <p className="text-lg font-bold text-red-400">
                          -{mockHRStats.leavingEmployeesThisMonth}
                        </p>
                      </div>
                    </div>
                    <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm text-slate-400">平均工龄</p>
                        <p className="text-lg font-bold text-white">
                          {mockHRStats.avgTenure} 年
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              {/* Performance Distribution */}
              <motion.div variants={fadeIn}>
                <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <PieChart className="h-5 w-5 text-purple-400" />
                      绩效分布
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {mockPerformanceDistribution.map((item, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className={cn(
                              'w-3 h-3 rounded-full',
                              item.color === 'emerald' && 'bg-emerald-500',
                              item.color === 'blue' && 'bg-blue-500',
                              item.color === 'amber' && 'bg-amber-500',
                              item.color === 'red' && 'bg-red-500',
                            )} />
                            <span className="text-sm text-slate-300">{item.level}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-white">{item.count}人</span>
                            <span className="text-xs text-slate-500">{item.percentage}%</span>
                          </div>
                        </div>
                        <Progress value={item.percentage} className="h-1.5 bg-slate-700/50" />
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </motion.div>
            </div>
          </div>

          {/* Quick Actions */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Zap className="h-5 w-5 text-yellow-400" />
                  快捷操作
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  <Button
                    variant="outline"
                    className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-blue-500/10 hover:border-blue-500/30 transition-colors"
                    onClick={() => {
                      setSelectedTab('recruitment')
                    }}
                  >
                    <UserPlus className="w-5 h-5 text-blue-400" />
                    <span className="text-xs">新建招聘</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-purple-500/10 hover:border-purple-500/30 transition-colors"
                    onClick={() => {
                      setSelectedTab('performance')
                    }}
                  >
                    <Award className="w-5 h-5 text-purple-400" />
                    <span className="text-xs">绩效评审</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-emerald-500/10 hover:border-emerald-500/30 transition-colors"
                    onClick={() => {
                      setSelectedTab('employees')
                    }}
                  >
                    <UserCheck className="w-5 h-5 text-emerald-400" />
                    <span className="text-xs">新增员工</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-cyan-500/10 hover:border-cyan-500/30 transition-colors"
                    onClick={() => {
                      setSelectedTab('attendance')
                    }}
                  >
                    <Calendar className="w-5 h-5 text-cyan-400" />
                    <span className="text-xs">考勤管理</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-pink-500/10 hover:border-pink-500/30 transition-colors"
                    onClick={() => {
                      setSelectedTab('relations')
                    }}
                  >
                    <Heart className="w-5 h-5 text-pink-400" />
                    <span className="text-xs">员工关系</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="flex flex-col items-center gap-2 h-auto py-4 hover:bg-amber-500/10 hover:border-amber-500/30 transition-colors"
                    onClick={() => {
                      setSelectedTab('statistics')
                    }}
                  >
                    <BarChart3 className="w-5 h-5 text-amber-400" />
                    <span className="text-xs">统计分析</span>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Department Distribution */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Building2 className="h-5 w-5 text-blue-400" />
                    部门人员分布
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    查看全部 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {mockDepartmentDistribution.map((dept) => (
                    <div
                      key={dept.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-white text-sm">{dept.name}</span>
                            {dept.new > 0 && (
                              <Badge className="text-xs bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                                +{dept.new}
                              </Badge>
                            )}
                            {dept.leaving > 0 && (
                              <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                                -{dept.leaving}
                              </Badge>
                            )}
                          </div>
                          <div className="text-xs text-slate-400">
                            {dept.active}/{dept.total} 人
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-bold text-white">
                            {dept.performance}
                          </div>
                          <div className="text-xs text-slate-400">绩效分</div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">平均年龄</span>
                          <span className="text-slate-300">{dept.avgAge} 岁</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">平均工龄</span>
                          <span className="text-slate-300">{dept.avgTenure} 年</span>
                        </div>
                        <Progress
                          value={(dept.active / dept.total) * 100}
                          className="h-1.5 bg-slate-700/50"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* Recruitment Tab */}
        <TabsContent value="recruitment" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">进行中招聘</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.inProgressRecruitments}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <UserPlus className="w-6 h-6 text-blue-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">已完成招聘</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.completedRecruitments}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <UserCheck className="w-6 h-6 text-emerald-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">招聘成功率</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.recruitmentSuccessRate}%
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Target className="w-6 h-6 text-purple-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">待审批</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.pendingRecruitments}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <FileText className="w-6 h-6 text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <BarChart3 className="h-5 w-5 text-blue-400" />
                  招聘趋势分析
                </CardTitle>
                <Button variant="ghost" size="sm" className="text-xs text-primary">
                  查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockRecruitmentTrends.map((item, index) => {
                  const successRate = item.positions > 0 ? (item.hired / item.positions) * 100 : 0
                  const maxPositions = Math.max(...mockRecruitmentTrends.map(t => t.positions))
                  const positionPercentage = (item.positions / maxPositions) * 100
                  
                  return (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-slate-300">{item.month}</span>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-400">发布</span>
                            <span className="text-sm font-semibold text-white">{item.positions}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-400">录用</span>
                            <span className="text-sm font-semibold text-emerald-400">{item.hired}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-400">成功率</span>
                            <span className={cn(
                              "text-sm font-semibold",
                              successRate >= 80 ? "text-emerald-400" :
                              successRate >= 60 ? "text-amber-400" : "text-red-400"
                            )}>
                              {successRate.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
                            <div 
                              className="h-full bg-blue-500/50 rounded-full transition-all"
                              style={{ width: `${positionPercentage}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-400 w-12 text-right">发布数</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
                            <div 
                              className="h-full bg-emerald-500/50 rounded-full transition-all"
                              style={{ width: `${successRate}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-400 w-12 text-right">成功率</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="mt-4 pt-4 border-t border-slate-700/50">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>最近6个月平均成功率: {(
                    mockRecruitmentTrends.reduce((sum, item) => sum + (item.positions > 0 ? (item.hired / item.positions) * 100 : 0), 0) / mockRecruitmentTrends.length
                  ).toFixed(1)}%</span>
                  <span>总发布: {mockRecruitmentTrends.reduce((sum, item) => sum + item.positions, 0)} | 总录用: {mockRecruitmentTrends.reduce((sum, item) => sum + item.hired, 0)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">待评审</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.pendingPerformanceReviews}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">已完成</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.completedPerformanceReviews}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">完成率</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.performanceCompletionRate}%
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <Target className="w-6 h-6 text-blue-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">平均分</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.avgPerformanceScore}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-purple-500/20 flex items-center justify-center">
                    <Award className="w-6 h-6 text-purple-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Attendance Tab */}
        <TabsContent value="attendance" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-slate-400">今日出勤率</p>
                  <p className="text-lg font-bold text-white">{mockHRStats.todayAttendanceRate}%</p>
                </div>
                <Progress value={mockHRStats.todayAttendanceRate} className="h-2" />
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-slate-400">月度出勤率</p>
                  <p className="text-lg font-bold text-white">{mockHRStats.monthlyAttendanceRate}%</p>
                </div>
                <Progress value={mockHRStats.monthlyAttendanceRate} className="h-2" />
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">迟到人数</p>
                    <p className="text-3xl font-bold text-white">{mockHRStats.lateCount}</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <Clock className="w-6 h-6 text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">缺勤人数</p>
                    <p className="text-3xl font-bold text-white">{mockHRStats.absentCount}</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center">
                    <AlertTriangle className="w-6 h-6 text-red-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Employees Tab */}
        <TabsContent value="employees" className="space-y-6">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Users className="h-5 w-5 text-blue-400" />
                  员工管理
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Button 
                    variant="outline" 
                    size="sm"
                    className="flex items-center gap-2"
                    title="导出员工列表"
                    onClick={handleExportEmployeeList}
                  >
                    <FileText className="w-4 h-4" />
                    导出
                  </Button>
                  <Button 
                    className="flex items-center gap-2"
                    onClick={() => {
                      // TODO: Open add employee dialog
                    }}
                  >
                    <UserPlus className="w-4 h-4" />
                    新增员工
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Search and Filters */}
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="搜索员工姓名、工号、电话..."
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    className="bg-slate-800/40 border-slate-700/50"
                  />
                </div>
                <select
                  value={filterDepartment}
                  onChange={(e) => setFilterDepartment(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/50 text-white text-sm"
                >
                  <option value="all">全部部门</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.dept_name}>
                      {dept.dept_name}
                    </option>
                  ))}
                </select>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-4 py-2 rounded-lg bg-slate-800/40 border border-slate-700/50 text-white text-sm"
                >
                  <option value="all">全部状态</option>
                  <option value="active">在职</option>
                  <option value="inactive">离职</option>
                </select>
              </div>

              {/* Employee List */}
              {loading ? (
                <LoadingCard message="加载员工列表..." />
              ) : error ? (
                <ErrorMessage
                  title="加载失败"
                  message={error}
                  onRetry={loadEmployees}
                />
              ) : employees.length === 0 ? (
                <EmptyState
                  icon={Users}
                  title="暂无员工数据"
                  message={searchKeyword || filterDepartment !== 'all' || filterStatus !== 'all' 
                    ? "没有找到符合条件的员工，请尝试调整筛选条件"
                    : "当前没有员工数据，点击上方按钮添加新员工"}
                  action={() => {
                    setSearchKeyword('')
                    setFilterDepartment('all')
                    setFilterStatus('all')
                  }}
                  actionLabel={searchKeyword || filterDepartment !== 'all' || filterStatus !== 'all' ? "清除筛选" : undefined}
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-800/40 border-b border-slate-700/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">工号</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">姓名</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">部门</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">角色</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">电话</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">状态</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/50">
                      {employees.map((employee, index) => (
                        <motion.tr
                          key={employee.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.05 }}
                          className="hover:bg-slate-800/40"
                        >
                          <td className="px-6 py-4 text-sm font-semibold text-white">
                            {employee.employee_code || '-'}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">{employee.name}</td>
                          <td className="px-6 py-4 text-sm text-slate-300">{employee.department || '-'}</td>
                          <td className="px-6 py-4 text-sm text-slate-300">{employee.role || '-'}</td>
                          <td className="px-6 py-4 text-sm text-slate-300">{employee.phone || '-'}</td>
                          <td className="px-6 py-4">
                            <Badge
                              className={cn(
                                'text-xs',
                                employee.is_active
                                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                                  : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                              )}
                            >
                              {employee.is_active ? '在职' : '离职'}
                            </Badge>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                title="查看详情"
                                className="hover:bg-blue-500/20 hover:text-blue-400"
                                onClick={async () => {
                                  try {
                                    const response = await employeeApi.get(employee.id)
                                    setSelectedEmployee(response.data)
                                    setShowEmployeeDialog(true)
                                  } catch (error) {
                                    // 如果API失败，使用列表中的数据
                                    setSelectedEmployee(employee)
                                    setShowEmployeeDialog(true)
                                  }
                                }}
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                title="编辑员工"
                                className="hover:bg-amber-500/20 hover:text-amber-400"
                                onClick={() => {
                                  // TODO: Open edit employee dialog
                                }}
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Relations Tab */}
        <TabsContent value="relations" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">待处理问题</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.pendingEmployeeIssues}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-amber-500/20 flex items-center justify-center">
                    <AlertTriangle className="w-6 h-6 text-amber-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">已解决问题</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.resolvedIssues}
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">员工满意度</p>
                    <p className="text-3xl font-bold text-white">
                      {mockHRStats.employeeSatisfaction}%
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-pink-500/20 flex items-center justify-center">
                    <Heart className="w-6 h-6 text-pink-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-surface-50 border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-primary" />
                员工关系问题
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockEmployeeIssues.map((issue, index) => (
                  <motion.div
                    key={issue.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 rounded-lg bg-surface-100 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge className={cn('text-xs', getIssueTypeColor(issue.type))}>
                            {issue.type === 'conflict' ? '冲突' :
                             issue.type === 'leave' ? '请假' :
                             issue.type === 'complaint' ? '投诉' : '绩效'}
                          </Badge>
                          <span className="text-sm font-semibold text-white">{issue.title}</span>
                          {issue.priority === 'high' && (
                            <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-300 mb-2">{issue.description}</p>
                        <div className="flex items-center gap-4 text-xs text-slate-400">
                          <span>{issue.employee} · {issue.department}</span>
                          <span>{issue.createdAt}</span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <Badge className={cn(
                          'text-xs',
                          issue.status === 'pending' && 'bg-amber-500/20 text-amber-400',
                          issue.status === 'reviewing' && 'bg-blue-500/20 text-blue-400',
                          issue.status === 'processing' && 'bg-purple-500/20 text-purple-400',
                        )}>
                          {getStatusLabel(issue.status)}
                        </Badge>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Statistics Tab */}
        <TabsContent value="statistics" className="space-y-6">
          {/* Time Range Filter */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-slate-400">统计周期:</span>
                    <div className="flex items-center gap-2">
                      {['month', 'quarter', 'year'].map((period) => (
                        <Button
                          key={period}
                          variant={statisticsPeriod === period ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => {
                            setStatisticsPeriod(period)
                            // TODO: Reload statistics data
                          }}
                        >
                          {period === 'month' ? '月度' : period === 'quarter' ? '季度' : '年度'}
                        </Button>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" className="flex items-center gap-2">
                      <Filter className="w-4 h-4" />
                      筛选
                    </Button>
                    <Button variant="outline" size="sm" className="flex items-center gap-2">
                      <FileSpreadsheet className="w-4 h-4" />
                      导出报表
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Employee Statistics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Age Distribution */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="h-5 w-5 text-blue-400" />
                    员工年龄分布
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {mockEmployeeAgeDistribution.map((item, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-slate-300">{item.range}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-semibold text-white">{item.count}人</span>
                            <span className="text-xs text-slate-400 w-12 text-right">{item.percentage}%</span>
                          </div>
                        </div>
                        <Progress value={item.percentage} className="h-2 bg-slate-700/50" />
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>平均年龄: {mockHRStats.avgAge} 岁</span>
                      <span>最集中: 31-35岁 ({mockEmployeeAgeDistribution[2].percentage}%)</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Tenure Distribution */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Clock className="h-5 w-5 text-purple-400" />
                    员工工龄分布
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {mockEmployeeTenureDistribution.map((item, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-slate-300">{item.range}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-semibold text-white">{item.count}人</span>
                            <span className="text-xs text-slate-400 w-12 text-right">{item.percentage}%</span>
                          </div>
                        </div>
                        <Progress value={item.percentage} className="h-2 bg-slate-700/50" />
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>平均工龄: {mockHRStats.avgTenure} 年</span>
                      <span>最集中: 1-3年 ({mockEmployeeTenureDistribution[1].percentage}%)</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Education Distribution & Monthly Flow */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Education Distribution */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <GraduationCap className="h-5 w-5 text-amber-400" />
                    学历分布
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {mockEmployeeEducationDistribution.map((item, index) => (
                      <div key={index}>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-slate-300">{item.level}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-sm font-semibold text-white">{item.count}人</span>
                            <span className="text-xs text-slate-400 w-12 text-right">{item.percentage}%</span>
                          </div>
                        </div>
                        <Progress value={item.percentage} className="h-2 bg-slate-700/50" />
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <div className="text-xs text-slate-400">
                      <span>本科及以上占比: {(
                        mockEmployeeEducationDistribution[0].percentage +
                        mockEmployeeEducationDistribution[1].percentage +
                        mockEmployeeEducationDistribution[2].percentage
                      ).toFixed(1)}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Monthly Employee Flow */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Activity className="h-5 w-5 text-emerald-400" />
                    月度人员流动
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {mockMonthlyEmployeeFlow.map((item, index) => {
                      const maxFlow = Math.max(...mockMonthlyEmployeeFlow.map(f => Math.max(f.new, f.leaving)))
                      const newPercentage = (item.new / maxFlow) * 100
                      const leavingPercentage = (item.leaving / maxFlow) * 100
                      
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-slate-300">{item.month}</span>
                            <div className="flex items-center gap-4">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-400">新增</span>
                                <span className="text-sm font-semibold text-emerald-400">+{item.new}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-400">离职</span>
                                <span className="text-sm font-semibold text-red-400">-{item.leaving}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-400">净增</span>
                                <span className={cn(
                                  "text-sm font-semibold",
                                  item.net >= 0 ? "text-emerald-400" : "text-red-400"
                                )}>
                                  {item.net >= 0 ? '+' : ''}{item.net}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-slate-700/30 rounded-full h-1.5 overflow-hidden">
                                <div 
                                  className="h-full bg-emerald-500/50 rounded-full transition-all"
                                  style={{ width: `${newPercentage}%` }}
                                />
                              </div>
                              <span className="text-xs text-slate-400 w-8 text-right">新增</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-slate-700/30 rounded-full h-1.5 overflow-hidden">
                                <div 
                                  className="h-full bg-red-500/50 rounded-full transition-all"
                                  style={{ width: `${leavingPercentage}%` }}
                                />
                              </div>
                              <span className="text-xs text-slate-400 w-8 text-right">离职</span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>7个月总净增: +{mockMonthlyEmployeeFlow.reduce((sum, item) => sum + item.net, 0)}人</span>
                      <span>平均月净增: +{(mockMonthlyEmployeeFlow.reduce((sum, item) => sum + item.net, 0) / mockMonthlyEmployeeFlow.length).toFixed(1)}人</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Department Performance Comparison */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <BarChart3 className="h-5 w-5 text-purple-400" />
                    部门绩效对比
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockDepartmentPerformanceComparison.map((dept, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold",
                            index < 3 ? "bg-gradient-to-br from-amber-500 to-orange-500 text-white" : "bg-slate-700/50 text-slate-300"
                          )}>
                            {dept.rank}
                          </div>
                          <span className="text-sm font-medium text-white">{dept.department}</span>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            {dept.trend >= 0 ? (
                              <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <ArrowDownRight className="w-3 h-3 text-red-400" />
                            )}
                            <span className={cn(
                              "text-xs",
                              dept.trend >= 0 ? "text-emerald-400" : "text-red-400"
                            )}>
                              {dept.trend >= 0 ? '+' : ''}{dept.trend}%
                            </span>
                          </div>
                          <span className="text-sm font-bold text-white w-16 text-right">{dept.avgScore}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
                          <div 
                            className={cn(
                              "h-full rounded-full transition-all",
                              dept.avgScore >= 85 ? "bg-emerald-500/50" :
                              dept.avgScore >= 80 ? "bg-blue-500/50" : "bg-amber-500/50"
                            )}
                            style={{ width: `${(dept.avgScore / 100) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-400 w-12 text-right">平均分</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Attendance Trend & Recruitment Channel */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Attendance Trend */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Calendar className="h-5 w-5 text-cyan-400" />
                    考勤趋势分析
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {mockAttendanceTrend.map((item, index) => {
                      const maxRate = Math.max(...mockAttendanceTrend.map(t => t.rate))
                      const ratePercentage = (item.rate / maxRate) * 100
                      
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium text-slate-300">{item.month}</span>
                            <div className="flex items-center gap-4">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-400">出勤率</span>
                                <span className="text-sm font-semibold text-emerald-400">{item.rate}%</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-400">迟到</span>
                                <span className="text-sm font-semibold text-amber-400">{item.late}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-400">缺勤</span>
                                <span className="text-sm font-semibold text-red-400">{item.absent}</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
                              <div 
                                className="h-full bg-emerald-500/50 rounded-full transition-all"
                                style={{ width: `${ratePercentage}%` }}
                              />
                            </div>
                            <span className="text-xs text-slate-400 w-12 text-right">出勤率</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>7个月平均出勤率: {(
                        mockAttendanceTrend.reduce((sum, item) => sum + item.rate, 0) / mockAttendanceTrend.length
                      ).toFixed(1)}%</span>
                      <span>趋势: {mockAttendanceTrend[mockAttendanceTrend.length - 1].rate > mockAttendanceTrend[0].rate ? '↑ 上升' : '↓ 下降'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Recruitment Channel Stats */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Target className="h-5 w-5 text-pink-400" />
                    招聘渠道分析
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {mockRecruitmentChannelStats.map((channel, index) => (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-slate-300">{channel.channel}</span>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-slate-400">人数</span>
                              <span className="text-sm font-semibold text-white">{channel.count}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-slate-400">成功率</span>
                              <span className={cn(
                                "text-sm font-semibold",
                                channel.successRate >= 85 ? "text-emerald-400" :
                                channel.successRate >= 75 ? "text-amber-400" : "text-red-400"
                              )}>
                                {channel.successRate}%
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-slate-700/30 rounded-full h-1.5 overflow-hidden">
                              <div 
                                className="h-full bg-blue-500/50 rounded-full transition-all"
                                style={{ width: `${channel.percentage}%` }}
                              />
                            </div>
                            <span className="text-xs text-slate-400 w-12 text-right">{channel.percentage}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>最佳渠道: 内部推荐 (成功率 {Math.max(...mockRecruitmentChannelStats.map(c => c.successRate))}%)</span>
                      <span>总招聘: {mockRecruitmentChannelStats.reduce((sum, c) => sum + c.count, 0)}人</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* Performance Trend */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <TrendingUp className="h-5 w-5 text-emerald-400" />
                    绩效趋势分析
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockPerformanceTrend.map((period, index) => {
                    const maxScore = Math.max(...mockPerformanceTrend.map(p => p.avgScore))
                    const scorePercentage = (period.avgScore / maxScore) * 100
                    const total = period.excellent + period.good + period.qualified + period.needsImprovement
                    
                    return (
                      <div key={index} className="space-y-3 p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-slate-300">{period.period}</span>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-slate-400">平均分</span>
                              <span className="text-sm font-bold text-white">{period.avgScore}</span>
                            </div>
                            {index > 0 && (
                              <div className="flex items-center gap-1">
                                {period.avgScore > mockPerformanceTrend[index - 1].avgScore ? (
                                  <>
                                    <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                                    <span className="text-xs text-emerald-400">
                                      +{(period.avgScore - mockPerformanceTrend[index - 1].avgScore).toFixed(1)}
                                    </span>
                                  </>
                                ) : (
                                  <>
                                    <ArrowDownRight className="w-3 h-3 text-red-400" />
                                    <span className="text-xs text-red-400">
                                      {(period.avgScore - mockPerformanceTrend[index - 1].avgScore).toFixed(1)}
                                    </span>
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-slate-700/30 rounded-full h-2 overflow-hidden">
                            <div 
                              className="h-full bg-emerald-500/50 rounded-full transition-all"
                              style={{ width: `${scorePercentage}%` }}
                            />
                          </div>
                          <span className="text-xs text-slate-400 w-12 text-right">平均分</span>
                        </div>
                        <div className="grid grid-cols-4 gap-2 mt-3">
                          <div className="text-center p-2 bg-emerald-500/10 rounded">
                            <div className="text-xs text-slate-400 mb-1">优秀</div>
                            <div className="text-sm font-bold text-emerald-400">{period.excellent}</div>
                            <div className="text-xs text-slate-500">{((period.excellent / total) * 100).toFixed(1)}%</div>
                          </div>
                          <div className="text-center p-2 bg-blue-500/10 rounded">
                            <div className="text-xs text-slate-400 mb-1">良好</div>
                            <div className="text-sm font-bold text-blue-400">{period.good}</div>
                            <div className="text-xs text-slate-500">{((period.good / total) * 100).toFixed(1)}%</div>
                          </div>
                          <div className="text-center p-2 bg-amber-500/10 rounded">
                            <div className="text-xs text-slate-400 mb-1">合格</div>
                            <div className="text-sm font-bold text-amber-400">{period.qualified}</div>
                            <div className="text-xs text-slate-500">{((period.qualified / total) * 100).toFixed(1)}%</div>
                          </div>
                          <div className="text-center p-2 bg-red-500/10 rounded">
                            <div className="text-xs text-slate-400 mb-1">待改进</div>
                            <div className="text-sm font-bold text-red-400">{period.needsImprovement}</div>
                            <div className="text-xs text-slate-500">{((period.needsImprovement / total) * 100).toFixed(1)}%</div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div className="mt-4 pt-4 border-t border-slate-700/50">
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>年度平均分提升: +{(mockPerformanceTrend[mockPerformanceTrend.length - 1].avgScore - mockPerformanceTrend[0].avgScore).toFixed(1)}分</span>
                    <span>优秀率提升: +{(
                      ((mockPerformanceTrend[mockPerformanceTrend.length - 1].excellent / (mockPerformanceTrend[mockPerformanceTrend.length - 1].excellent + mockPerformanceTrend[mockPerformanceTrend.length - 1].good + mockPerformanceTrend[mockPerformanceTrend.length - 1].qualified + mockPerformanceTrend[mockPerformanceTrend.length - 1].needsImprovement)) * 100) -
                      ((mockPerformanceTrend[0].excellent / (mockPerformanceTrend[0].excellent + mockPerformanceTrend[0].good + mockPerformanceTrend[0].qualified + mockPerformanceTrend[0].needsImprovement)) * 100)
                    ).toFixed(1)}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>
      </Tabs>

      {/* Employee Detail Dialog */}
      <Dialog open={showEmployeeDialog} onOpenChange={setShowEmployeeDialog}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-400" />
              员工详情
            </DialogTitle>
            <DialogDescription>
              查看员工的详细信息
            </DialogDescription>
          </DialogHeader>
          {selectedEmployee && (
            <DialogBody>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400 text-xs mb-1 block">工号</Label>
                    <p className="font-medium text-white">{selectedEmployee.employee_code || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs mb-1 block">姓名</Label>
                    <p className="font-medium text-white">{selectedEmployee.name || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs mb-1 block">部门</Label>
                    <p className="font-medium text-white">{selectedEmployee.department || selectedEmployee.department_name || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs mb-1 block">角色/岗位</Label>
                    <p className="font-medium text-white">{selectedEmployee.role || selectedEmployee.position || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs mb-1 block">电话</Label>
                    <p className="font-medium text-white">{selectedEmployee.phone || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-slate-400 text-xs mb-1 block">状态</Label>
                    <Badge
                      className={cn(
                        'text-xs',
                        selectedEmployee.is_active
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                          : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                      )}
                    >
                      {selectedEmployee.is_active ? '在职' : '离职'}
                    </Badge>
                  </div>
                  {selectedEmployee.entry_date && (
                    <div>
                      <Label className="text-slate-400 text-xs mb-1 block">入职日期</Label>
                      <p className="font-medium text-white">{formatDate(selectedEmployee.entry_date)}</p>
                    </div>
                  )}
                  {selectedEmployee.wechat_userid && (
                    <div>
                      <Label className="text-slate-400 text-xs mb-1 block">企业微信ID</Label>
                      <p className="font-medium text-white">{selectedEmployee.wechat_userid}</p>
                    </div>
                  )}
                </div>
                {(selectedEmployee.created_at || selectedEmployee.updated_at) && (
                  <div className="pt-4 border-t border-slate-700/50">
                    <div className="grid grid-cols-2 gap-4 text-xs text-slate-400">
                      {selectedEmployee.created_at && (
                        <div>
                          <span className="text-slate-500">创建时间: </span>
                          <span>{formatDate(selectedEmployee.created_at)}</span>
                        </div>
                      )}
                      {selectedEmployee.updated_at && (
                        <div>
                          <span className="text-slate-500">更新时间: </span>
                          <span>{formatDate(selectedEmployee.updated_at)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </DialogBody>
          )}
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}




