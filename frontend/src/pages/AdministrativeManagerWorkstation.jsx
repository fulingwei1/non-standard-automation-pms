/**
 * Administrative Manager Workstation - Main dashboard for administrative manager
 * Features: Office supplies management, Meeting management, Vehicle management, 
 * Fixed assets management, Employee attendance, Administrative approvals
 * Core Functions: Administrative affairs, Asset management, Employee services, Approval workflow
 */

import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import {
  TrendingUp,
  TrendingDown,
  Users,
  Calendar,
  Package,
  Car,
  Building2,
  ClipboardCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  FileText,
  ShoppingCart,
  Wrench,
  Coffee,
  Printer,
  Monitor,
  Box,
  Phone,
  Laptop,
  ChevronRight,
  BarChart3,
  PieChart,
  Activity,
  DollarSign,
  Award,
  Bell,
  Settings,
  UserCheck,
  MapPin,
  Fuel,
  CalendarDays,
  Building,
  Truck,
  Receipt,
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
} from '../components/ui'
import { cn, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { SimplePieChart, MonthlyTrendChart, CategoryBreakdownCard } from '../components/administrative/StatisticsCharts'
import { 
  employeeApi, 
  departmentApi, 
  pmoApi,
  ecnApi,
  purchaseApi,
  quoteApi 
} from '../services/api'
import { toast } from '../components/ui/toast'

const formatCurrency = (value) => {
  if (value >= 100000000) {
    return `¥${(value / 100000000).toFixed(2)}亿`
  }
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(value)
}

const StatCard = ({ title, value, subtitle, trend, icon: IconComponent, color, bg, onClick }) => {
  return (
    <motion.div
      variants={fadeIn}
      onClick={onClick}
      className={cn(
        "relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg",
        onClick && "cursor-pointer"
      )}
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
          <IconComponent className={cn('h-6 w-6', color)} />
        </div>
      </div>
      <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
    </motion.div>
  )
}

export default function AdministrativeManagerWorkstation() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalEmployees: 0,
    attendanceRate: 0,
    pendingApprovals: 0,
    urgentApprovals: 0,
    monthlyAdminBudget: 0,
    monthlyAdminSpent: 0,
    budgetUtilization: 0,
    officeSuppliesTotal: 0,
    officeSuppliesLowStock: 0,
    meetingsThisWeek: 0,
    meetingsToday: 0,
    totalVehicles: 0,
    vehiclesInUse: 0,
  })
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [meetings, setMeetings] = useState([])
  const [officeSupplies, setOfficeSupplies] = useState([])
  const [vehicles, setVehicles] = useState([])
  const [attendanceStats, setAttendanceStats] = useState([])
  const [selectedMeeting, setSelectedMeeting] = useState(null)
  const [showMeetingDetail, setShowMeetingDetail] = useState(false)
  const [selectedApproval, setSelectedApproval] = useState(null)
  const [showApprovalDetail, setShowApprovalDetail] = useState(false)

  // Load data from APIs
  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      
      // Load employee statistics
      try {
        const empRes = await employeeApi.getStatistics({})
        const empStats = empRes.data || empRes
        if (empStats) {
          setStats(prev => ({
            ...prev,
            totalEmployees: empStats.total || prev.totalEmployees,
          }))
        }
      } catch (err) {
        console.error('Failed to load employee statistics:', err)
      }

      // Load department statistics
      try {
        const deptRes = await departmentApi.getStatistics({})
        const deptStats = deptRes.data || deptRes
        // Could use this for department-level stats
      } catch (err) {
        console.error('Failed to load department statistics:', err)
      }

      // Load meetings
      try {
        const today = new Date().toISOString().split('T')[0]
        const meetingsRes = await pmoApi.meetings.list({ 
          date_from: today,
          page_size: 50 
        })
        const meetingsData = meetingsRes.data || meetingsRes
        const meetingsList = meetingsData.items || meetingsData || []
        
        // Transform meetings data
        const transformedMeetings = meetingsList.map(meeting => ({
          id: meeting.id,
          title: meeting.meeting_title || meeting.title || '',
          organizer: meeting.organizer_name || '未知',
          department: meeting.department || '未知部门',
          room: meeting.meeting_room || '未指定',
          date: meeting.meeting_date ? meeting.meeting_date.split('T')[0] : '',
          time: meeting.start_time && meeting.end_time 
            ? `${meeting.start_time}-${meeting.end_time}`
            : '',
          attendees: meeting.attendees?.length || 0,
          status: meeting.status === 'SCHEDULED' ? 'scheduled' : 
                  meeting.status === 'ONGOING' ? 'ongoing' : 
                  meeting.status === 'COMPLETED' ? 'completed' : 'scheduled',
        }))
        
        setMeetings(transformedMeetings)
        
        // Update stats
        const todayMeetings = transformedMeetings.filter(m => m.date === today)
        const thisWeekMeetings = transformedMeetings.filter(m => {
          const meetingDate = new Date(m.date)
          const weekStart = new Date()
          weekStart.setDate(weekStart.getDate() - weekStart.getDay())
          return meetingDate >= weekStart
        })
        
        setStats(prev => ({
          ...prev,
          meetingsToday: todayMeetings.length,
          meetingsThisWeek: thisWeekMeetings.length,
        }))
      } catch (err) {
        console.error('Failed to load meetings:', err)
      }

      // Load pending approvals from various modules
      try {
        const allApprovals = []
        
        // ECN approvals
        try {
          const ecnRes = await ecnApi.list({ status: 'SUBMITTED', page_size: 20 })
          const ecnData = ecnRes.data || ecnRes
          const ecns = ecnData.items || ecnData || []
          ecns.forEach(ecn => {
            allApprovals.push({
              id: `ecn-${ecn.id}`,
              type: 'ecn',
              title: `设计变更申请 - ${ecn.ecn_no || 'ECN'}`,
              applicant: ecn.created_by_name || '未知',
              department: ecn.department || '未知部门',
              amount: 0,
              submitTime: formatDate(ecn.created_at) || '',
              priority: ecn.priority === 'URGENT' ? 'urgent' : 
                       ecn.priority === 'HIGH' ? 'high' : 'medium',
              status: 'pending',
            })
          })
        } catch (err) {
          console.error('Failed to load ECN approvals:', err)
        }

        // Purchase request approvals
        try {
          const prRes = await purchaseApi.requests.list({ status: 'SUBMITTED', page_size: 20 })
          const prData = prRes.data || prRes
          const prs = prData.items || prData || []
          prs.forEach(pr => {
            allApprovals.push({
              id: `pr-${pr.id}`,
              type: 'office_supplies',
              title: `采购申请 - ${pr.request_no || pr.id}`,
              applicant: pr.created_by_name || '未知',
              department: pr.department || '未知部门',
              amount: parseFloat(pr.total_amount || 0),
              submitTime: formatDate(pr.created_at) || '',
              priority: pr.urgent ? 'high' : 'medium',
              status: 'pending',
            })
          })
        } catch (err) {
          console.error('Failed to load purchase request approvals:', err)
        }

        setPendingApprovals(allApprovals.slice(0, 5))
        setStats(prev => ({
          ...prev,
          pendingApprovals: allApprovals.length,
          urgentApprovals: allApprovals.filter(a => a.priority === 'urgent' || a.priority === 'high').length,
        }))
      } catch (err) {
        console.error('Failed to load approvals:', err)
      }

    } catch (err) {
        console.error('Failed to load dashboard data:', err)
        setError(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="行政经理工作台"
        description={`月度行政预算: ${formatCurrency(stats.monthlyAdminBudget)} | 已使用: ${formatCurrency(stats.monthlyAdminSpent)} (${stats.budgetUtilization}%)`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              行政报表
            </Button>
            <Button 
              className="flex items-center gap-2"
              onClick={() => window.location.href = '/approval-center'}
            >
              <ClipboardCheck className="w-4 h-4" />
              审批中心
            </Button>
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
          title="待审批事项"
          value={stats.pendingApprovals}
          subtitle={`紧急: ${stats.urgentApprovals} 项`}
          icon={ClipboardCheck}
          color="text-red-400"
          bg="bg-red-500/10"
          onClick={() => window.location.href = '/approval-center'}
        />
        <StatCard
          title="低库存物品"
          value={stats.officeSuppliesLowStock}
          subtitle="需要补货"
          icon={AlertTriangle}
          color="text-amber-400"
          bg="bg-amber-500/10"
        />
        <StatCard
          title="今日会议"
          value={stats.meetingsToday}
          subtitle={`本周: ${stats.meetingsThisWeek} 场`}
          icon={Calendar}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="在用车辆"
          value={stats.vehiclesInUse}
          subtitle={`总计: ${stats.totalVehicles} 辆`}
          icon={Car}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
        <StatCard
          title="员工出勤率"
          value={`${stats.attendanceRate}%`}
          subtitle="本月平均"
          icon={UserCheck}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          title="固定资产"
          value={stats.fixedAssetsTotal}
          subtitle={`总值: ${formatCurrency(stats.fixedAssetsValue)}`}
          icon={Building2}
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Budget Progress */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <DollarSign className="h-5 w-5 text-emerald-400" />
                  月度行政预算执行
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">月度预算</p>
                      <p className="text-3xl font-bold text-white mt-1">
                        {formatCurrency(stats.monthlyAdminBudget)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-slate-400">已使用</p>
                      <p className="text-3xl font-bold text-amber-400 mt-1">
                        {formatCurrency(stats.monthlyAdminSpent)}
                      </p>
                    </div>
                  </div>
                  <Progress
                    value={stats.budgetUtilization}
                    className="h-4 bg-slate-700/50"
                  />
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">
                      使用率: {stats.budgetUtilization}%
                    </span>
                    <span className="text-slate-400">
                      剩余: {formatCurrency(stats.monthlyAdminBudget - stats.monthlyAdminSpent)}
                    </span>
                  </div>
                  <div className="pt-4 border-t border-slate-700/50">
                    <CategoryBreakdownCard
                      title="费用分类"
                      data={[
                        { label: '办公用品', value: stats.officeSuppliesMonthlyCost, color: '#3b82f6' },
                        { label: '车辆费用', value: stats.monthlyFuelCost, color: '#06b6d4' },
                        { label: '其他费用', value: stats.monthlyAdminSpent - stats.officeSuppliesMonthlyCost - stats.monthlyFuelCost, color: '#64748b' },
                      ]}
                      total={stats.monthlyAdminSpent}
                      formatValue={formatCurrency}
                    />
                  </div>
                  
                  <div className="pt-4 border-t border-slate-700/50">
                    <p className="text-sm text-slate-400 mb-3">月度费用趋势</p>
                    <MonthlyTrendChart
                      data={[
                        { month: '2024-10', amount: 420000 },
                        { month: '2024-11', amount: 395000 },
                        { month: '2024-12', amount: 410000 },
                        { month: '2025-01', amount: stats.monthlyAdminSpent },
                      ]}
                      valueKey="amount"
                      labelKey="month"
                      height={120}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Office Supplies Status */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Package className="h-5 w-5 text-blue-400" />
                    办公用品库存预警
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    查看全部 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {officeSupplies.map((item) => (
                    <div
                      key={item.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-white">{item.name}</span>
                            <Badge
                              variant="outline"
                              className={cn(
                                'text-xs',
                                item.status === 'low' && 'bg-red-500/20 text-red-400 border-red-500/30',
                                item.status === 'normal' && 'bg-slate-700/40'
                              )}
                            >
                              {item.status === 'low' ? '库存不足' : '正常'}
                            </Badge>
                          </div>
                          <div className="text-xs text-slate-400">
                            {item.category} · 供应商: {item.supplier}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-white">
                            {item.currentStock} {item.unit}
                          </div>
                          <div className="text-xs text-slate-400">
                            最低库存: {item.minStock} {item.unit}
                          </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">库存率</span>
                          <span className="text-slate-300">
                            {((item.currentStock / item.minStock) * 100).toFixed(0)}%
                          </span>
                        </div>
                        <Progress
                          value={(item.currentStock / item.minStock) * 100}
                          className={cn(
                            "h-1.5 bg-slate-700/50",
                            item.status === 'low' && "bg-red-500/20"
                          )}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Today's Meetings */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Calendar className="h-5 w-5 text-purple-400" />
                    今日会议安排
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    查看全部 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {meetings.map((meeting) => (
                    <div
                      key={meeting.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                      onClick={() => {
                        setSelectedMeeting(meeting)
                        setShowMeetingDetail(true)
                      }}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-white">{meeting.title}</span>
                            <Badge
                              variant="outline"
                              className={cn(
                                'text-xs',
                                meeting.status === 'ongoing' && 'bg-green-500/20 text-green-400 border-green-500/30',
                                meeting.status === 'scheduled' && 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                              )}
                            >
                              {meeting.status === 'ongoing' ? '进行中' : '已安排'}
                            </Badge>
                          </div>
                          <div className="text-xs text-slate-400 mt-1">
                            {meeting.organizer} · {meeting.department}
                          </div>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                            <div className="flex items-center gap-1">
                              <MapPin className="w-3 h-3" />
                              {meeting.room}
                            </div>
                            <div className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {meeting.time}
                            </div>
                            <div className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {meeting.attendees} 人
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Column - Sidebar Content */}
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
                  <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                    {pendingApprovals.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {pendingApprovals.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                    onClick={() => {
                      setSelectedApproval(item)
                      setShowApprovalDetail(true)
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              item.type === 'office_supplies' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              item.type === 'vehicle' && 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
                              item.type === 'asset' && 'bg-purple-500/20 text-purple-400 border-purple-500/30',
                              item.type === 'meeting' && 'bg-green-500/20 text-green-400 border-green-500/30',
                              item.type === 'leave' && 'bg-pink-500/20 text-pink-400 border-pink-500/30'
                            )}
                          >
                            {item.type === 'office_supplies' ? '办公用品' : 
                             item.type === 'vehicle' ? '车辆' :
                             item.type === 'asset' ? '资产' :
                             item.type === 'meeting' ? '会议' : '请假'}
                          </Badge>
                          {item.priority === 'high' && (
                            <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                            </Badge>
                          )}
                        </div>
                        <p className="font-medium text-white text-sm">{item.title}</p>
                        <p className="text-xs text-slate-400 mt-1">
                          {item.department} · {item.applicant}
                        </p>
                        {(item.items || item.purpose || item.item || item.room || item.type) && (
                          <p className="text-xs text-slate-500 mt-1">
                            {item.items?.join('、') || item.purpose || item.item || `${item.room} ${item.date} ${item.time}` || `${item.type} ${item.days}天`}
                          </p>
                        )}
                      </div>
                    </div>
                    {item.amount && (
                      <div className="flex items-center justify-between text-xs mt-2">
                        <span className="text-slate-400">{item.submitTime.split(' ')[1]}</span>
                        <span className="font-medium text-amber-400">
                          {formatCurrency(item.amount)}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
                <Button 
                  variant="outline" 
                  className="w-full mt-3"
                  onClick={() => window.location.href = '/administrative-approvals'}
                >
                  查看全部审批
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Vehicle Status */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Car className="h-5 w-5 text-cyan-400" />
                    车辆使用状态
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    详情 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {vehicles.map((vehicle) => (
                  <div
                    key={vehicle.id}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white">{vehicle.plateNumber}</span>
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              vehicle.status === 'in_use' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              vehicle.status === 'available' && 'bg-green-500/20 text-green-400 border-green-500/30',
                              vehicle.status === 'maintenance' && 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                            )}
                          >
                            {vehicle.status === 'in_use' ? '使用中' : 
                             vehicle.status === 'available' ? '可用' : '保养中'}
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-400">
                          {vehicle.brand}
                        </div>
                        {vehicle.driver && (
                          <div className="text-xs text-slate-500 mt-1">
                            驾驶员: {vehicle.driver}
                          </div>
                        )}
                        {vehicle.purpose && (
                          <div className="text-xs text-slate-500 mt-1">
                            {vehicle.purpose} · {vehicle.destination}
                          </div>
                        )}
                        {vehicle.maintenanceReason && (
                          <div className="text-xs text-slate-500 mt-1">
                            {vehicle.maintenanceReason} · 预计归还: {vehicle.returnDate}
                          </div>
                        )}
                        {vehicle.nextMaintenance && (
                          <div className="text-xs text-slate-500 mt-1">
                            下次保养: {vehicle.nextMaintenance}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Attendance Statistics */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <UserCheck className="h-5 w-5 text-emerald-400" />
                    部门出勤统计
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    详情 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {attendanceStats.map((stat, index) => (
                  <div
                    key={index}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white text-sm">{stat.department}</span>
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                          <span>总人数: {stat.total}</span>
                          <span>出勤: {stat.present}</span>
                          {stat.leave > 0 && <span className="text-amber-400">请假: {stat.leave}</span>}
                          {stat.late > 0 && <span className="text-red-400">迟到: {stat.late}</span>}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-emerald-400">
                          {stat.attendanceRate}%
                        </div>
                        <div className="text-xs text-slate-400">出勤率</div>
                      </div>
                    </div>
                    <Progress
                      value={stat.attendanceRate}
                      className="h-1.5 bg-slate-700/50 mt-2"
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Approval Detail Dialog */}
      <Dialog open={showApprovalDetail} onOpenChange={setShowApprovalDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>审批详情</DialogTitle>
            <DialogDescription>
              {selectedApproval?.department} · {selectedApproval?.applicant}
            </DialogDescription>
          </DialogHeader>
          <DialogBody>
            {selectedApproval && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      selectedApproval.type === 'office_supplies' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                      selectedApproval.type === 'vehicle' && 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
                      selectedApproval.type === 'asset' && 'bg-purple-500/20 text-purple-400 border-purple-500/30',
                      selectedApproval.type === 'meeting' && 'bg-green-500/20 text-green-400 border-green-500/30',
                      selectedApproval.type === 'leave' && 'bg-pink-500/20 text-pink-400 border-pink-500/30'
                    )}
                  >
                    {selectedApproval.type === 'office_supplies' ? '办公用品' : 
                     selectedApproval.type === 'vehicle' ? '车辆' :
                     selectedApproval.type === 'asset' ? '资产' :
                     selectedApproval.type === 'meeting' ? '会议' : '请假'}
                  </Badge>
                  {selectedApproval.priority === 'high' && (
                    <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                      紧急
                    </Badge>
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">{selectedApproval.title}</h3>
                  {selectedApproval.items && (
                    <div className="mb-2">
                      <p className="text-sm text-slate-400 mb-1">物品清单:</p>
                      <div className="flex flex-wrap gap-2">
                        {selectedApproval.items.map((item, idx) => (
                          <Badge key={idx} variant="outline">{item}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {selectedApproval.amount && (
                    <div className="mb-2">
                      <p className="text-sm text-slate-400">申请金额:</p>
                      <p className="text-lg font-bold text-amber-400">{formatCurrency(selectedApproval.amount)}</p>
                    </div>
                  )}
                  {selectedApproval.purpose && (
                    <div className="mb-2">
                      <p className="text-sm text-slate-400">用途:</p>
                      <p className="text-white">{selectedApproval.purpose}</p>
                    </div>
                  )}
                  {selectedApproval.room && (
                    <div className="mb-2">
                      <p className="text-sm text-slate-400">会议室:</p>
                      <p className="text-white">{selectedApproval.room} · {selectedApproval.date} {selectedApproval.time}</p>
                    </div>
                  )}
                  {selectedApproval.days && (
                    <div className="mb-2">
                      <p className="text-sm text-slate-400">请假天数:</p>
                      <p className="text-white">{selectedApproval.days} 天</p>
                    </div>
                  )}
                  <div className="mt-4 pt-4 border-t border-slate-700/50">
                    <p className="text-xs text-slate-500">提交时间: {selectedApproval.submitTime}</p>
                  </div>
                </div>
                <div className="flex gap-2 pt-4">
                  <Button className="flex-1">批准</Button>
                  <Button variant="outline" className="flex-1">拒绝</Button>
                </div>
              </div>
            )}
          </DialogBody>
        </DialogContent>
      </Dialog>

      {/* Meeting Detail Dialog */}
      <Dialog open={showMeetingDetail} onOpenChange={setShowMeetingDetail}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>会议详情</DialogTitle>
            <DialogDescription>
              {selectedMeeting?.organizer} · {selectedMeeting?.department}
            </DialogDescription>
          </DialogHeader>
          <DialogBody>
            {selectedMeeting && (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      selectedMeeting.status === 'ongoing' && 'bg-green-500/20 text-green-400 border-green-500/30',
                      selectedMeeting.status === 'scheduled' && 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                    )}
                  >
                    {selectedMeeting.status === 'ongoing' ? '进行中' : '已安排'}
                  </Badge>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">{selectedMeeting.title}</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-slate-400 mb-1">会议室</p>
                      <p className="text-white">{selectedMeeting.room}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">时间</p>
                      <p className="text-white">{selectedMeeting.time}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">日期</p>
                      <p className="text-white">{selectedMeeting.date}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400 mb-1">参会人数</p>
                      <p className="text-white">{selectedMeeting.attendees} 人</p>
                    </div>
                  </div>
                </div>
                <div className="pt-4 border-t border-slate-700/50">
                  <Button variant="outline" className="w-full">查看完整信息</Button>
                </div>
              </div>
            )}
          </DialogBody>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

