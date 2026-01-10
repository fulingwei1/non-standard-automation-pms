/**
 * HRManagerDashboard - 重构后的主组件示例
 * 
 * 这个文件展示了重构后的主组件结构
 * 实际使用时，应该替换 pages/HRManagerDashboard.jsx
 * 
 * 重构效果：
 * - 主组件从 ~1855 行减少到约 200 行
 * - 每个 Tab 拆分为独立组件
 * - 状态管理提取到自定义 Hooks
 * - 头部组件独立
 */

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Card,
  CardContent,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../ui'
import {
  Users,
  UserPlus,
  Award,
  CheckCircle2,
  Heart,
  Target,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import { staggerContainer, fadeIn } from '../../lib/animations'
import { cn } from '../../lib/utils'
import { useHRDashboard } from './hooks/useHRDashboard'
import HRDashboardHeader from './HRDashboardHeader'
import HROverviewTab from './tabs/HROverviewTab'
import HRTransactionsTab from './tabs/HRTransactionsTab'
import HRContractsTab from './tabs/HRContractsTab'
import HRRecruitmentTab from './tabs/HRRecruitmentTab'
import HRPerformanceTab from './tabs/HRPerformanceTab'
import HRAttendanceTab from './tabs/HRAttendanceTab'
import HREmployeesTab from './tabs/HREmployeesTab'
import HRRelationsTab from './tabs/HRRelationsTab'
import HRStatisticsTab from './tabs/HRStatisticsTab'
import { toast } from '../ui/toast'

// Mock statistics (这些数据应该从 API 获取)
const mockHRStats = {
  totalEmployees: 186,
  activeEmployees: 178,
  newEmployeesThisMonth: 8,
  leavingEmployeesThisMonth: 2,
  departments: 12,
  avgAge: 32.5,
  avgTenure: 3.2,
  pendingRecruitments: 15,
  inProgressRecruitments: 8,
  completedRecruitments: 12,
  recruitmentSuccessRate: 85.5,
  pendingPerformanceReviews: 28,
  completedPerformanceReviews: 150,
  performanceCompletionRate: 84.3,
  avgPerformanceScore: 82.5,
  todayAttendanceRate: 95.6,
  monthlyAttendanceRate: 94.2,
  lateCount: 3,
  absentCount: 2,
  pendingEmployeeIssues: 5,
  resolvedIssues: 18,
  employeeSatisfaction: 88.5,
}

// Mock data (这些数据应该从 API 获取)
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

const mockPerformanceDistribution = [
  { level: '优秀', count: 32, percentage: 18.0, color: 'emerald' },
  { level: '良好', count: 85, percentage: 47.8, color: 'blue' },
  { level: '合格', count: 48, percentage: 27.0, color: 'amber' },
  { level: '待改进', count: 13, percentage: 7.3, color: 'red' },
]

const mockRecruitmentTrends = [
  { month: '8月', positions: 8, hired: 6 },
  { month: '9月', positions: 10, hired: 8 },
  { month: '10月', positions: 12, hired: 10 },
  { month: '11月', positions: 15, hired: 12 },
  { month: '12月', positions: 18, hired: 15 },
  { month: '1月', positions: 15, hired: 8 },
]

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

const mockDepartmentPerformanceComparison = [
  { department: '技术开发部', avgScore: 85.2, rank: 1, trend: 2.3 },
  { department: '质量部', avgScore: 87.2, rank: 2, trend: 1.8 },
  { department: '销售部', avgScore: 88.5, rank: 3, trend: 3.2 },
  { department: '项目部', avgScore: 82.8, rank: 4, trend: 1.5 },
  { department: '采购部', avgScore: 83.5, rank: 5, trend: 0.8 },
  { department: '生产部', avgScore: 80.5, rank: 6, trend: -0.5 },
]

// StatCard 组件（从原文件提取）
const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg }) => {
  const IconComponent = Icon
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn('text-2xl font-bold mb-1', color)}>{value}</p>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
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
  const {
    selectedTab,
    setSelectedTab,
    statisticsPeriod,
    setStatisticsPeriod,
    employees,
    departments,
    loading,
    refreshing,
    error,
    searchKeyword,
    setSearchKeyword,
    filterDepartment,
    setFilterDepartment,
    filterStatus,
    setFilterStatus,
    loadEmployees,
    refresh,
  } = useHRDashboard()


  // 导出报表
  const handleExportReport = () => {
    try {
      const exportData = {
        统计周期:
          statisticsPeriod === 'month'
            ? '本月'
            : statisticsPeriod === 'quarter'
            ? '本季度'
            : '本年',
        员工总数: mockHRStats.totalEmployees,
        在职员工: mockHRStats.activeEmployees,
        本月新增: mockHRStats.newEmployeesThisMonth,
        本月离职: mockHRStats.leavingEmployeesThisMonth,
        部门数量: mockHRStats.departments,
        平均年龄: mockHRStats.avgAge,
        平均工龄: mockHRStats.avgTenure,
        待招聘: mockHRStats.pendingRecruitments,
        招聘中: mockHRStats.inProgressRecruitments,
        已完成招聘: mockHRStats.completedRecruitments,
        招聘成功率: `${mockHRStats.recruitmentSuccessRate}%`,
        待绩效评审: mockHRStats.pendingPerformanceReviews,
        已完成评审: mockHRStats.completedPerformanceReviews,
        绩效完成率: `${mockHRStats.performanceCompletionRate}%`,
        平均绩效分数: mockHRStats.avgPerformanceScore,
      }

      const csvContent = [
        '项目,数值',
        ...Object.entries(exportData).map(
          ([key, value]) => `"${key}","${value}"`
        ),
      ].join('\n')

      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], {
        type: 'text/csv;charset=utf-8;',
      })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute(
        'download',
        `人事管理报表_${statisticsPeriod}_${new Date().toISOString().split('T')[0]}.csv`
      )
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      toast.success('报表导出成功')
    } catch (error) {
      console.error('导出失败:', error)
      toast.error('导出失败: ' + error.message)
    }
  }

  // 导出员工列表
  const handleExportEmployeeList = () => {
    if (employees.length === 0) {
      toast.error('没有员工数据可导出')
      return
    }

    try {
      const csvContent = [
        '员工编码,姓名,部门,职位,状态,入职日期,电话,邮箱',
        ...employees.map((emp) =>
          [
            emp.employee_code || '',
            emp.name || '',
            emp.department || '',
            emp.position || '',
            emp.is_active ? '在职' : '离职',
            emp.hire_date || '',
            emp.phone || '',
            emp.email || '',
          ]
            .map((field) => `"${field}"`)
            .join(',')
        ),
      ].join('\n')

      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], {
        type: 'text/csv;charset=utf-8;',
      })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute(
        'download',
        `员工列表_${new Date().toISOString().split('T')[0]}.csv`
      )
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      toast.success('员工列表导出成功')
    } catch (error) {
      console.error('导出失败:', error)
      toast.error('导出失败: ' + error.message)
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
      <HRDashboardHeader
        mockHRStats={mockHRStats}
        selectedTab={selectedTab}
        setSelectedTab={setSelectedTab}
        statisticsPeriod={statisticsPeriod}
        refreshing={refreshing}
        onRefresh={refresh}
        onExportReport={handleExportReport}
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
          <TabsTrigger value="transactions">人事事务</TabsTrigger>
          <TabsTrigger value="contracts">合同管理</TabsTrigger>
          <TabsTrigger value="recruitment">招聘管理</TabsTrigger>
          <TabsTrigger value="performance">绩效管理</TabsTrigger>
          <TabsTrigger value="attendance">考勤管理</TabsTrigger>
          <TabsTrigger value="employees">员工管理</TabsTrigger>
          <TabsTrigger value="relations">员工关系</TabsTrigger>
          <TabsTrigger value="statistics">统计分析</TabsTrigger>
        </TabsList>

        {/* Overview Tab - 已重构 */}
        <TabsContent value="overview" className="space-y-6">
          <HROverviewTab
            mockHRStats={mockHRStats}
            mockPendingRecruitments={mockPendingRecruitments}
            mockPendingReviews={mockPendingReviews}
            mockDepartmentDistribution={mockDepartmentDistribution}
            mockPerformanceDistribution={mockPerformanceDistribution}
            setSelectedTab={setSelectedTab}
          />
        </TabsContent>

        {/* Transactions Tab - 已重构 */}
        <TabsContent value="transactions" className="space-y-6">
          <HRTransactionsTab />
        </TabsContent>

        {/* Contracts Tab - 已重构 */}
        <TabsContent value="contracts" className="space-y-6">
          <HRContractsTab />
        </TabsContent>

        {/* Recruitment Tab - 已重构 */}
        <TabsContent value="recruitment" className="space-y-6">
          <HRRecruitmentTab
            mockHRStats={mockHRStats}
            mockRecruitmentTrends={mockRecruitmentTrends}
          />
        </TabsContent>

        {/* Performance Tab - 已重构 */}
        <TabsContent value="performance" className="space-y-6">
          <HRPerformanceTab mockHRStats={mockHRStats} />
        </TabsContent>

        {/* Attendance Tab - 已重构 */}
        <TabsContent value="attendance" className="space-y-6">
          <HRAttendanceTab mockHRStats={mockHRStats} />
        </TabsContent>

        {/* Employees Tab - 已重构 */}
        <TabsContent value="employees" className="space-y-6">
          <HREmployeesTab
            employees={employees}
            departments={departments}
            loading={loading}
            error={error}
            searchKeyword={searchKeyword}
            setSearchKeyword={setSearchKeyword}
            filterDepartment={filterDepartment}
            setFilterDepartment={setFilterDepartment}
            filterStatus={filterStatus}
            setFilterStatus={setFilterStatus}
            loadEmployees={loadEmployees}
            handleExportEmployeeList={handleExportEmployeeList}
            setSelectedEmployee={setSelectedEmployee}
            setShowEmployeeDialog={setShowEmployeeDialog}
          />
        </TabsContent>

        {/* Relations Tab - 已重构 */}
        <TabsContent value="relations" className="space-y-6">
          <HRRelationsTab
            mockHRStats={mockHRStats}
            mockEmployeeIssues={mockEmployeeIssues}
          />
        </TabsContent>

        {/* Statistics Tab - 已重构 */}
        <TabsContent value="statistics" className="space-y-6">
          <HRStatisticsTab
            statisticsPeriod={statisticsPeriod}
            setStatisticsPeriod={setStatisticsPeriod}
            mockHRStats={mockHRStats}
            mockEmployeeAgeDistribution={mockEmployeeAgeDistribution}
            mockEmployeeTenureDistribution={mockEmployeeTenureDistribution}
            mockEmployeeEducationDistribution={mockEmployeeEducationDistribution}
            mockMonthlyEmployeeFlow={[]}
            mockDepartmentPerformanceComparison={mockDepartmentPerformanceComparison}
            mockAttendanceTrend={[]}
            mockRecruitmentChannelStats={[]}
            mockPerformanceTrend={[]}
            handleExportReport={handleExportReport}
          />
        </TabsContent>
      </Tabs>

      {/* TODO: 员工详情对话框 - 后续会创建 */}
      {/* {showEmployeeDialog && (
        <EmployeeDialog
          employee={selectedEmployee}
          onClose={() => setShowEmployeeDialog(false)}
        />
      )} */}
    </motion.div>
  )
}
