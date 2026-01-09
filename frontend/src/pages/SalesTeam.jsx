/**
 * Sales Team Management Page - Team performance and management for sales directors
 * Features: Team member management, Performance tracking, Target assignment, Team analytics
 */

import { useState, useMemo, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Users,
  UserPlus,
  Target,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Award,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BarChart3,
  Mail,
  Phone,
  Calendar,
  Edit,
  MoreHorizontal,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Download,
  Filter,
  RefreshCw,
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
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '../components/ui'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { salesStatisticsApi, salesTeamApi, salesTargetApi, customerApi, orgApi } from '../services/api'

const getDefaultDateRange = () => {
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1)
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  return {
    start: start.toISOString().split('T')[0],
    end: end.toISOString().split('T')[0],
  }
}

// Mock team data (演示环境备用数据)
const mockTeamMembers = [
  {
    id: 1,
    name: '张销售',
    role: '销售工程师',
    department: '销售部',
    region: '华东',
    email: 'zhang@example.com',
    phone: '138****1234',
    monthlyTarget: 300000,
    monthlyAchieved: 285000,
    achievementRate: 95,
    yearTarget: 3600000,
    yearAchieved: 2850000,
    yearProgress: 79.2,
    activeProjects: 5,
    newCustomers: 2,
    status: 'excellent',
    joinDate: '2023-03-15',
    lastActivity: '2小时前',
    personalTargets: {
      monthly: {
        completion_rate: 95,
        actual_value: 285000,
        target_value: 300000,
        period_value: '2024-05',
      },
      yearly: {
        completion_rate: 79.2,
        actual_value: 2850000,
        target_value: 3600000,
        period_value: '2024',
      },
    },
    recentFollowUp: {
      leadName: '比亚迪扩建项目',
      followUpType: 'VISIT',
      createdAt: '2024-05-22T09:00:00Z',
      content: '客户现场沟通方案细节',
    },
    customerDistribution: [
      { label: '汽车', value: 4, percentage: 50 },
      { label: '新能源', value: 3, percentage: 37.5 },
      { label: '电子', value: 1, percentage: 12.5 },
    ],
    customerTotal: 9,
  },
  {
    id: 2,
    name: '李销售',
    role: '销售工程师',
    department: '销售部',
    region: '华南',
    email: 'li@example.com',
    phone: '139****5678',
    monthlyTarget: 300000,
    monthlyAchieved: 245000,
    achievementRate: 81.7,
    yearTarget: 3600000,
    yearAchieved: 2450000,
    yearProgress: 68.1,
    activeProjects: 4,
    newCustomers: 1,
    status: 'good',
    joinDate: '2023-06-20',
    lastActivity: '1天前',
    personalTargets: {
      monthly: {
        completion_rate: 81.7,
        actual_value: 245000,
        target_value: 300000,
        period_value: '2024-05',
      },
      yearly: {
        completion_rate: 68.1,
        actual_value: 2450000,
        target_value: 3600000,
        period_value: '2024',
      },
    },
    recentFollowUp: {
      leadName: '宁德时代产线升级',
      followUpType: 'CALL',
      createdAt: '2024-05-20T13:30:00Z',
      content: '电话确认商务条款',
    },
    customerDistribution: [
      { label: '新能源', value: 3, percentage: 60 },
      { label: '电子', value: 2, percentage: 40 },
    ],
    customerTotal: 5,
  },
  {
    id: 3,
    name: '王销售',
    role: '销售工程师',
    department: '销售部',
    region: '华中',
    email: 'wang@example.com',
    phone: '137****9012',
    monthlyTarget: 300000,
    monthlyAchieved: 198000,
    achievementRate: 66,
    yearTarget: 3600000,
    yearAchieved: 1980000,
    yearProgress: 55,
    activeProjects: 3,
    newCustomers: 0,
    status: 'warning',
    joinDate: '2024-01-10',
    lastActivity: '3天前',
    personalTargets: {
      monthly: {
        completion_rate: 66,
        actual_value: 198000,
        target_value: 300000,
        period_value: '2024-05',
      },
      yearly: {
        completion_rate: 55,
        actual_value: 1980000,
        target_value: 3600000,
        period_value: '2024',
      },
    },
    recentFollowUp: {
      leadName: '立讯精密扩线',
      followUpType: 'EMAIL',
      createdAt: '2024-05-18T08:00:00Z',
      content: '邮件发送技术答疑资料',
    },
    customerDistribution: [
      { label: '3C电子', value: 2, percentage: 66.7 },
      { label: '汽车', value: 1, percentage: 33.3 },
    ],
    customerTotal: 3,
  },
  {
    id: 4,
    name: '刘销售',
    role: '销售经理',
    department: '销售部',
    region: '华南',
    email: 'liu@example.com',
    phone: '136****3456',
    monthlyTarget: 800000,
    monthlyAchieved: 720000,
    achievementRate: 90,
    yearTarget: 9600000,
    yearAchieved: 7200000,
    yearProgress: 75,
    activeProjects: 8,
    newCustomers: 3,
    status: 'excellent',
    joinDate: '2022-05-12',
    lastActivity: '30分钟前',
    personalTargets: {
      monthly: {
        completion_rate: 90,
        actual_value: 720000,
        target_value: 800000,
        period_value: '2024-05',
      },
      yearly: {
        completion_rate: 75,
        actual_value: 7200000,
        target_value: 9600000,
        period_value: '2024',
      },
    },
    recentFollowUp: {
      leadName: '小鹏整车柔性线',
      followUpType: 'MEETING',
      createdAt: '2024-05-23T03:30:00Z',
      content: '项目例会同步风险',
    },
    customerDistribution: [
      { label: '汽车', value: 5, percentage: 55.6 },
      { label: '新能源', value: 3, percentage: 33.3 },
      { label: '物流', value: 1, percentage: 11.1 },
    ],
    customerTotal: 9,
  },
  {
    id: 5,
    name: '陈销售',
    role: '销售工程师',
    department: '销售部',
    region: '华北',
    email: 'chen@example.com',
    phone: '135****7890',
    monthlyTarget: 300000,
    monthlyAchieved: 320000,
    achievementRate: 106.7,
    yearTarget: 3600000,
    yearAchieved: 3200000,
    yearProgress: 88.9,
    activeProjects: 6,
    newCustomers: 2,
    status: 'excellent',
    joinDate: '2023-09-01',
    lastActivity: '1小时前',
    personalTargets: {
      monthly: {
        completion_rate: 106.7,
        actual_value: 320000,
        target_value: 300000,
        period_value: '2024-05',
      },
      yearly: {
        completion_rate: 88.9,
        actual_value: 3200000,
        target_value: 3600000,
        period_value: '2024',
      },
    },
    recentFollowUp: {
      leadName: '海尔家电升级',
      followUpType: 'VISIT',
      createdAt: '2024-05-21T14:00:00Z',
      content: '客户现场演示解决方案',
    },
    customerDistribution: [
      { label: '家电', value: 3, percentage: 50 },
      { label: '物流', value: 2, percentage: 33.3 },
      { label: '食品', value: 1, percentage: 16.7 },
    ],
    customerTotal: 6,
  },
]

const formatCurrency = (value) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(value)
}

const statusConfig = {
  excellent: { label: '优秀', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  good: { label: '良好', color: 'bg-blue-500', textColor: 'text-blue-400' },
  warning: { label: '需关注', color: 'bg-amber-500', textColor: 'text-amber-400' },
  poor: { label: '待改进', color: 'bg-red-500', textColor: 'text-red-400' },
}

const DEFAULT_TEAM_STATS = {
  totalMembers: 0,
  activeMembers: 0,
  totalTarget: 0,
  totalAchieved: 0,
  avgAchievementRate: 0,
  totalProjects: 0,
  totalCustomers: 0,
  newCustomersThisMonth: 0,
}

const followUpTypeLabels = {
  CALL: '电话',
  EMAIL: '邮件',
  VISIT: '拜访',
  MEETING: '会议',
  OTHER: '其他',
}

const formatFollowUpType = (value) => followUpTypeLabels[value] || value || '跟进'

const formatTimeAgo = (value) => {
  if (!value) return ''
  const target = new Date(value)
  if (Number.isNaN(target.getTime())) return value
  const diff = Date.now() - target.getTime()
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.max(1, Math.floor(diff / minute))}分钟前`
  if (diff < day) return `${Math.floor(diff / hour)}小时前`
  if (diff < 30 * day) return `${Math.floor(diff / day)}天前`
  return target.toLocaleDateString('zh-CN')
}

const formatDateTime = (value) => {
  if (!value) return ''
  const target = new Date(value)
  if (Number.isNaN(target.getTime())) return value
  return target.toLocaleString('zh-CN', { hour12: false })
}

const normalizeDistribution = (distribution = []) => {
  if (!Array.isArray(distribution)) return []
  return distribution.map((item, index) => {
    const rawValue = Number(item.value ?? item.count ?? 0)
    const rawPercentage = Number(item.percentage ?? item.rate ?? 0)
    return {
      label: item.label || item.category || `分类${index + 1}`,
      value: Number.isFinite(rawValue) ? rawValue : 0,
      percentage: Number.isFinite(rawPercentage) ? Number(rawPercentage.toFixed(1)) : 0,
    }
  })
}

const getAchievementStatus = (rate) => {
  if (rate >= 100) return 'excellent'
  if (rate >= 80) return 'good'
  if (rate >= 60) return 'warning'
  return 'poor'
}

const aggregateTargets = (targets = []) => {
  if (!targets.length) return null
  const totals = targets.reduce(
    (acc, target) => {
      const targetValue = Number(target.target_value ?? 0)
      const actualValue = Number(target.actual_value ?? 0)
      return {
        target: acc.target + targetValue,
        actual: acc.actual + actualValue,
      }
    },
    { target: 0, actual: 0 }
  )
  return {
    targetValue: totals.target,
    actualValue: totals.actual,
    completionRate: totals.target > 0 ? (totals.actual / totals.target) * 100 : 0,
  }
}

const transformTeamMember = (member = {}) => {
  const personalTargets = member.personal_targets || member.personalTargets || null
  const monthlyTargetInfo = personalTargets?.monthly
  const yearlyTargetInfo = personalTargets?.yearly
  const regionName = member.region || member.department_name || member.department || '未分配'

  const monthlyTarget = Number(
    member.monthly_target ??
    monthlyTargetInfo?.target_value ??
    member.target_amount ??
    member.contract_amount ??
    0
  )
  const monthlyAchieved = Number(
    member.monthly_actual ??
    monthlyTargetInfo?.actual_value ??
    member.collection_amount ??
    member.contract_amount ??
    0
  )
  const monthlyCompletion = Number(
    member.monthly_completion_rate ??
    monthlyTargetInfo?.completion_rate ??
    (monthlyTarget > 0 ? (monthlyAchieved / monthlyTarget) * 100 : 0)
  )
  const yearTarget = Number(
    member.year_target ??
    yearlyTargetInfo?.target_value ??
    monthlyTarget * 12
  )
  const yearAchieved = Number(
    member.year_actual ??
    yearlyTargetInfo?.actual_value ??
    member.contract_amount ??
    member.collection_amount ??
    0
  )
  const yearCompletion = Number(
    member.year_completion_rate ??
    yearlyTargetInfo?.completion_rate ??
    (yearTarget > 0 ? (yearAchieved / yearTarget) * 100 : 0)
  )

  const normalizedMonthlyCompletion = Number.isFinite(monthlyCompletion) ? monthlyCompletion : 0
  const normalizedYearCompletion = Number.isFinite(yearCompletion) ? yearCompletion : 0

  const rawFollowUp = member.recent_follow_up || member.recentFollowUp
  const recentFollowUp = rawFollowUp
    ? {
        leadName: rawFollowUp.lead_name || rawFollowUp.leadName,
        leadCode: rawFollowUp.lead_code || rawFollowUp.leadCode,
        followUpType: rawFollowUp.follow_up_type || rawFollowUp.followUpType,
        content: rawFollowUp.content,
        createdAt: rawFollowUp.created_at || rawFollowUp.createdAt,
      }
    : null

  const customerDistribution = normalizeDistribution(
    member.customer_distribution || member.customerDistribution || []
  )
  const customerTotal =
    member.customer_total ??
    member.customerTotal ??
    customerDistribution.reduce((sum, item) => sum + (item.value || 0), 0)

  return {
    id: member.user_id,
    name: member.user_name || member.username || '未知成员',
    role: member.role || '销售',
    department: member.department_name || '未知部门',
    region: regionName,
    email: member.email || '',
    phone: member.phone || '',
    monthlyTarget,
    monthlyAchieved,
    achievementRate: Number(normalizedMonthlyCompletion.toFixed(1)),
    yearTarget,
    yearAchieved,
    yearProgress: Number(normalizedYearCompletion.toFixed(1)),
    activeProjects: member.contract_count ?? member.opportunity_count ?? 0,
    newCustomers: member.new_customers ?? member.newCustomers ?? 0,
    status: getAchievementStatus(normalizedMonthlyCompletion || normalizedYearCompletion),
    joinDate: member.join_date || '',
    lastActivity: member.last_activity || '',
    leadCount: member.lead_count || 0,
    opportunityCount: member.opportunity_count || 0,
    contractCount: member.contract_count || 0,
    contractAmount: member.contract_amount || 0,
    collectionAmount: member.collection_amount || 0,
    personalTargets,
    recentFollowUp,
    customerDistribution,
    customerTotal,
  }
}

const calculateTeamStats = (members, summary) => {
  const fallbackTarget = members.reduce((sum, m) => sum + (m.monthlyTarget || 0), 0)
  const fallbackAchieved = members.reduce((sum, m) => sum + (m.monthlyAchieved || 0), 0)
  const fallbackProjects = members.reduce((sum, m) => sum + (m.activeProjects || 0), 0)
  const fallbackNewCustomers = members.reduce((sum, m) => sum + (m.newCustomers || 0), 0)
  const fallbackCustomerTotal = members.reduce((sum, m) => sum + (m.customerTotal || 0), 0)

  const targetFromSummary = summary?.team_target_value
  const achievedFromSummary = summary?.team_actual_value
  const completionFromSummary = summary?.team_completion_rate
  const projectsFromSummary = summary?.total_opportunities
  const customersFromSummary =
    summary?.customer_total ??
    summary?.converted_leads ??
    summary?.total_leads ??
    fallbackCustomerTotal
  const newCustomersSummary =
    summary?.customer_new_this_month ??
    summary?.new_customers ??
    fallbackNewCustomers ??
    DEFAULT_TEAM_STATS.newCustomersThisMonth

  const totalMembers = members.length
  const totalTarget = targetFromSummary ?? fallbackTarget
  const totalAchieved = achievedFromSummary ?? fallbackAchieved
  const avgAchievementRate = completionFromSummary ?? (totalTarget > 0 ? (totalAchieved / totalTarget) * 100 : 0)

  return {
    totalMembers,
    activeMembers: members.filter((m) => m.status !== 'poor').length || totalMembers,
    totalTarget,
    totalAchieved,
    avgAchievementRate: Number((avgAchievementRate || 0).toFixed(1)),
    totalProjects: projectsFromSummary ?? fallbackProjects,
    totalCustomers: customersFromSummary ?? DEFAULT_TEAM_STATS.totalCustomers,
    newCustomersThisMonth: newCustomersSummary ?? fallbackNewCustomers ?? DEFAULT_TEAM_STATS.newCustomersThisMonth,
  }
}

const formatAutoRefreshTime = (value) => {
  if (!value) return ''
  return value.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  })
}

export default function SalesTeam() {
  const navigate = useNavigate()
  const defaultRange = useMemo(() => getDefaultDateRange(), [])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedMember, setSelectedMember] = useState(null)
  const [showMemberDialog, setShowMemberDialog] = useState(false)
  const [loading, setLoading] = useState(false)
  const [teamMembers, setTeamMembers] = useState([])
  const [teamStats, setTeamStats] = useState(DEFAULT_TEAM_STATS)
  const [usingMockData, setUsingMockData] = useState(false)
  const [departmentOptions, setDepartmentOptions] = useState([{ label: '全部', value: '' }])
  const [regionOptions, setRegionOptions] = useState([])
  const [lastAutoRefreshAt, setLastAutoRefreshAt] = useState(null)
  const [highlightAutoRefresh, setHighlightAutoRefresh] = useState(false)
  const [filters, setFilters] = useState({
    departmentId: '',
    region: '',
    startDate: defaultRange.start,
    endDate: defaultRange.end,
  })
  const [dateError, setDateError] = useState('')
  const [exporting, setExporting] = useState(false)
  const [rankingType, setRankingType] = useState('contract_amount')
  const [rankingData, setRankingData] = useState([])
  const [showRanking, setShowRanking] = useState(false)
  const [rankingLoading, setRankingLoading] = useState(false)
  const autoRefreshTimerRef = useRef(null)

  useEffect(() => {
    if (filters.startDate && filters.endDate) {
      const start = new Date(filters.startDate)
      const end = new Date(filters.endDate)
      if (start > end) {
        setDateError('开始日期不能晚于结束日期')
        return
      }
    }
    setDateError('')
  }, [filters.startDate, filters.endDate])

  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const res = await orgApi.departments({ page: 1, page_size: 200 })
        const payload = res.data?.data || res.data || res
        const list = payload.items || payload.data || []
        const options = Array.isArray(list)
          ? list.map((dept) => ({
              label: dept.dept_name || dept.name || `部门${dept.id}`,
              value: String(dept.id),
            }))
          : []
        setDepartmentOptions([{ label: '全部', value: '' }, ...options])
      } catch (err) {
        console.error('获取部门列表失败:', err)
      }
    }
    fetchDepartments()
  }, [])

  useEffect(() => {
    return () => {
      if (autoRefreshTimerRef.current) {
        clearTimeout(autoRefreshTimerRef.current)
      }
    }
  }, [])

  const updateRegionOptions = useCallback((members) => {
    const options = Array.from(
      new Set(
        members
          .map((member) => (member.region || '').trim())
          .filter(Boolean)
      )
    ).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'))
    setRegionOptions(options)
  }, [])

  const triggerAutoRefreshToast = useCallback(() => {
    const refreshTime = new Date()
    setLastAutoRefreshAt(refreshTime)
    setHighlightAutoRefresh(true)
    if (autoRefreshTimerRef.current) {
      clearTimeout(autoRefreshTimerRef.current)
    }
    autoRefreshTimerRef.current = setTimeout(() => {
      setHighlightAutoRefresh(false)
    }, 2400)
  }, [])

  const fetchTeamData = useCallback(async () => {
    if (dateError) return
    setLoading(true)
    try {
      const requestParams = {}
      if (filters.departmentId) requestParams.department_id = filters.departmentId
      if (filters.region) requestParams.region = filters.region.trim()
      if (filters.startDate) requestParams.start_date = filters.startDate
      if (filters.endDate) requestParams.end_date = filters.endDate

      const startDateValue = filters.startDate ? new Date(filters.startDate) : new Date(defaultRange.start)
      const endDateValue = filters.endDate ? new Date(filters.endDate) : new Date(defaultRange.end)
      const targetPeriodValue = filters.startDate
        ? filters.startDate.slice(0, 7)
        : `${startDateValue.getFullYear()}-${String(startDateValue.getMonth() + 1).padStart(2, '0')}`

      const [teamRes, summaryRes, targetRes, customerRes] = await Promise.allSettled([
        salesTeamApi.getTeam(requestParams),
        salesStatisticsApi.summary({
          start_date: filters.startDate || defaultRange.start,
          end_date: filters.endDate || defaultRange.end,
        }),
        salesTargetApi.list({
          target_scope: 'TEAM',
          target_period: 'MONTHLY',
          period_value: targetPeriodValue,
          status: 'ACTIVE',
          page: 1,
          page_size: 200,
        }),
        customerApi.list({
          page: 1,
          page_size: 200,
        }),
      ])

      let normalizedMembers = []
      if (teamRes.status === 'fulfilled') {
        const payload = teamRes.value.data?.data || teamRes.value.data || teamRes.value || {}
        const list = payload.team_members || payload.items || []
        normalizedMembers = Array.isArray(list) ? list.map(transformTeamMember) : []
      }

      if (!normalizedMembers.length) {
        throw new Error('TEAM_DATA_EMPTY')
      }

      setTeamMembers(normalizedMembers)
      updateRegionOptions(normalizedMembers)

      const summaryRaw = summaryRes.status === 'fulfilled'
        ? summaryRes.value.data?.data || summaryRes.value.data || summaryRes.value || {}
        : {}

      let targetSummary = null
      if (targetRes.status === 'fulfilled') {
        const payload = targetRes.value.data?.data || targetRes.value.data || targetRes.value || {}
        const list = payload.items || payload.data?.items || payload.team_targets || []
        targetSummary = aggregateTargets(Array.isArray(list) ? list : [])
      }

      let customerSummary = null
      if (customerRes.status === 'fulfilled') {
        const payload = customerRes.value.data?.data || customerRes.value.data || customerRes.value || {}
        const list = payload.items || payload.data?.items || []
        const totalCustomers = payload.total ?? payload.data?.total ?? payload.count ?? null
        const newCustomersInRange = Array.isArray(list)
          ? list.filter((customer) => {
              const createdAt = customer.created_at || customer.createdAt
              if (!createdAt) return false
              const createdDate = new Date(createdAt)
              return createdDate >= startDateValue && createdDate <= endDateValue
            }).length
          : null
        customerSummary = {
          totalCustomers,
          newCustomersThisMonth: newCustomersInRange,
        }
      }

      const enrichedSummary = {
        ...summaryRaw,
        team_target_value: targetSummary?.targetValue ?? summaryRaw?.team_target_value,
        team_actual_value: targetSummary?.actualValue ?? summaryRaw?.team_actual_value,
        team_completion_rate: targetSummary
          ? Number(targetSummary.completionRate.toFixed(1))
          : summaryRaw?.team_completion_rate,
        customer_total: customerSummary?.totalCustomers ?? summaryRaw?.customer_total,
        customer_new_this_month:
          customerSummary?.newCustomersThisMonth ?? summaryRaw?.customer_new_this_month,
      }

      setTeamStats(calculateTeamStats(normalizedMembers, enrichedSummary))
      setUsingMockData(false)
      triggerAutoRefreshToast()
    } catch (err) {
      console.error('Failed to fetch sales team data:', err)
      const fallbackMembers = mockTeamMembers.map(transformTeamMember)
      setTeamMembers(fallbackMembers)
      setTeamStats(calculateTeamStats(fallbackMembers, null))
      updateRegionOptions(fallbackMembers)
      setUsingMockData(true)
      triggerAutoRefreshToast()
    } finally {
      setLoading(false)
    }
  }, [
    filters.departmentId,
    filters.region,
    filters.startDate,
    filters.endDate,
    dateError,
    defaultRange,
    triggerAutoRefreshToast,
    updateRegionOptions,
  ])

  useEffect(() => {
    fetchTeamData()
  }, [fetchTeamData])

  // Fetch ranking data
  useEffect(() => {
    const fetchRanking = async () => {
      if (!showRanking || dateError) {
        if (dateError) {
          setRankingData([])
        }
        return
      }
      setRankingLoading(true)
      try {
        const params = {
          ranking_type: rankingType,
          limit: 20,
        }
        if (filters.departmentId) params.department_id = filters.departmentId
        if (filters.region) params.region = filters.region.trim()
        if (filters.startDate) params.start_date = filters.startDate
        if (filters.endDate) params.end_date = filters.endDate
        const res = await salesTeamApi.getRanking(params)
        const payload = res.data?.data || res.data || res
        setRankingData(payload.rankings || [])
      } catch (err) {
        console.error('Failed to fetch ranking data:', err)
        setRankingData([])
      } finally {
        setRankingLoading(false)
      }
    }
    fetchRanking()
  }, [showRanking, rankingType, filters.departmentId, filters.region, filters.startDate, filters.endDate, dateError])

  const handleFilterChange = (field, value) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleResetFilters = () => {
    const range = getDefaultDateRange()
    setFilters({
      departmentId: '',
      region: '',
      startDate: range.start,
      endDate: range.end,
    })
  }

  const handleNavigatePerformance = (member) => {
    if (!member?.id) return
    navigate(`/performance/results/${member.id}`)
  }

  const handleNavigateCRM = (member) => {
    if (!member?.id) return
    navigate(`/customers?owner_id=${member.id}`)
  }

  const handleExport = async () => {
    if (usingMockData || dateError) return
    try {
      setExporting(true)
      const params = {}
      if (filters.departmentId) params.department_id = filters.departmentId
      if (filters.region) params.region = filters.region.trim()
      if (filters.startDate) params.start_date = filters.startDate
      if (filters.endDate) params.end_date = filters.endDate
      const res = await salesTeamApi.exportTeam(params)
      const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      const filename = `sales-team-${(filters.startDate || defaultRange.start).replace(/-/g, '')}-${(filters.endDate || defaultRange.end).replace(/-/g, '')}.csv`
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('导出销售团队数据失败:', err)
    } finally {
      setExporting(false)
    }
  }

  const filteredMembers = useMemo(() => {
    if (!searchTerm) return teamMembers
    const keyword = searchTerm.toLowerCase()
    return teamMembers.filter(member => {
      const name = member.name?.toLowerCase?.() || ''
      const role = member.role?.toLowerCase?.() || ''
      const regionText = member.region?.toLowerCase?.() || ''
      return name.includes(keyword) || role.includes(keyword) || regionText.includes(keyword)
    })
  }, [teamMembers, searchTerm])

  const headerDescription = `团队规模: ${teamStats.totalMembers}人 | 活跃成员: ${teamStats.activeMembers}人 | 平均完成率: ${teamStats.avgAchievementRate}% | 统计区间: ${filters.startDate} ~ ${filters.endDate}${
    usingMockData ? ' | 当前展示演示环境备用数据' : ''
  }`

  const handleViewMember = (member) => {
    setSelectedMember(member)
    setShowMemberDialog(true)
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
        title="团队管理"
        description={headerDescription}
        actions={
          <motion.div variants={fadeIn} className="flex flex-wrap gap-2 justify-end">
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={() => setShowRanking(!showRanking)}
            >
              <BarChart3 className="w-4 h-4" />
              {showRanking ? '隐藏排名' : '业绩排名'}
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={handleExport}
              loading={exporting}
              disabled={usingMockData || exporting || !!dateError}
            >
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={() => navigate('/performance')}
            >
              <TrendingUp className="w-4 h-4" />
              绩效中心
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={() => navigate('/customers')}
            >
              <Users className="w-4 h-4" />
              CRM
            </Button>
            <Button className="flex items-center gap-2">
              <UserPlus className="w-4 h-4" />
              添加成员
            </Button>
          </motion.div>
        }
      />
      {usingMockData && (
        <p className="text-xs text-amber-400 px-1">
          接口不可用时已自动启用“演示环境备用数据”兜底，真实数据可用时将立即恢复。
        </p>
      )}

      <motion.div variants={fadeIn}>
        <Card>
          <CardContent className="p-4 space-y-4">
            <div className="flex items-center justify-between text-sm text-slate-300">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4" />
                <span>筛选条件</span>
              </div>
              {dateError && <span className="text-xs text-red-400">{dateError}</span>}
            </div>
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <p className="text-xs text-slate-400 mb-1">部门</p>
                <Select value={filters.departmentId} onValueChange={(value) => handleFilterChange('departmentId', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="全部部门" />
                  </SelectTrigger>
                  <SelectContent>
                    {departmentOptions.map((dept) => (
                      <SelectItem key={dept.value} value={dept.value}>
                        {dept.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">区域</p>
                <Input
                  placeholder="输入区域（如华东、华南）"
                  value={filters.region}
                  onChange={(e) => handleFilterChange('region', e.target.value)}
                  list={regionOptions.length ? 'region-suggestions' : undefined}
                />
                {regionOptions.length > 0 && (
                  <datalist id="region-suggestions">
                    {regionOptions.map((option) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                )}
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">开始日期</p>
                <Input
                  type="date"
                  value={filters.startDate}
                  onChange={(e) => handleFilterChange('startDate', e.target.value)}
                />
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">结束日期</p>
                <Input
                  type="date"
                  value={filters.endDate}
                  onChange={(e) => handleFilterChange('endDate', e.target.value)}
                />
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
              <Button variant="ghost" size="sm" onClick={handleResetFilters}>
                重置筛选
              </Button>
              <div
                className={cn(
                  'flex items-center gap-1 transition-colors',
                  highlightAutoRefresh ? 'text-emerald-400' : 'text-slate-400'
                )}
              >
                <RefreshCw className={cn('w-3 h-3', highlightAutoRefresh && 'animate-spin')} />
                {lastAutoRefreshAt ? (
                  <>
                    <span>已自动刷新</span>
                    <span className="text-slate-500">
                      ({formatAutoRefreshTime(lastAutoRefreshAt)})
                    </span>
                  </>
                ) : (
                  <span>筛选更新后自动刷新数据</span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Team Stats */}
      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">团队目标</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(teamStats.totalTarget)}
                </p>
                <p className="text-xs text-slate-500 mt-1">本月总目标</p>
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
                <p className="text-sm text-slate-400">团队完成</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(teamStats.totalAchieved)}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">
                    {teamStats.avgAchievementRate}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">进行中项目</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {teamStats.totalProjects}
                </p>
                <p className="text-xs text-slate-500 mt-1">团队项目总数</p>
              </div>
              <div className="p-2 bg-purple-500/20 rounded-lg">
                <Activity className="w-5 h-5 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">客户总数</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {teamStats.totalCustomers}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  本月新增 {teamStats.newCustomersThisMonth}
                </p>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <Users className="w-5 h-5 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Ranking Section */}
      {showRanking && (
        <motion.div variants={fadeIn}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Award className="h-5 w-5 text-amber-400" />
                  销售业绩排名
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={rankingType}
                    onChange={(e) => setRankingType(e.target.value)}
                    className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="lead_count">线索数量</option>
                    <option value="opportunity_count">商机数量</option>
                    <option value="contract_amount">合同金额</option>
                    <option value="collection_amount">回款金额</option>
                  </select>
                </div>
              </CardTitle>
              <p className="text-xs text-slate-500">
                统计区间：{filters.startDate} ~ {filters.endDate}
              </p>
            </CardHeader>
            <CardContent>
              {rankingLoading ? (
                <div className="text-center py-8 text-slate-400">加载中...</div>
              ) : rankingData.length === 0 ? (
                <div className="text-center py-8 text-slate-400">暂无排名数据</div>
              ) : (
                <div className="space-y-2">
                  {rankingData.map((item, index) => (
                    <div
                      key={item.user_id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-4">
                        <div className={cn(
                          'w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold',
                          index === 0 && 'bg-gradient-to-br from-amber-500 to-orange-500',
                          index === 1 && 'bg-gradient-to-br from-blue-500 to-cyan-500',
                          index === 2 && 'bg-gradient-to-br from-purple-500 to-pink-500',
                          index >= 3 && 'bg-slate-600',
                        )}>
                          {item.rank}
                        </div>
                      <div>
                        <div className="font-medium text-white">{item.user_name}</div>
                        <div className="text-xs text-slate-400">{item.department_name || '未知部门'}</div>
                        <div className="text-[11px] text-slate-500">
                          {item.region || item.department_name || '未分配'}
                        </div>
                      </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-white">
                          {rankingType === 'lead_count' && `${item.lead_count || 0} 个`}
                          {rankingType === 'opportunity_count' && `${item.opportunity_count || 0} 个`}
                          {rankingType === 'contract_amount' && formatCurrency(item.contract_amount || 0)}
                          {rankingType === 'collection_amount' && formatCurrency(item.collection_amount || 0)}
                        </div>
                        <div className="text-xs text-slate-400">
                          {rankingType === 'lead_count' && '线索数量'}
                          {rankingType === 'opportunity_count' && '商机数量'}
                          {rankingType === 'contract_amount' && '合同金额'}
                          {rankingType === 'collection_amount' && '回款金额'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Search and Filter */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Input
                  placeholder="搜索团队成员..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
                <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Team Members List */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-400" />
              团队成员 ({filteredMembers.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-10 text-slate-400">加载中...</div>
            ) : filteredMembers.length === 0 ? (
              <div className="text-center py-10 text-slate-500">暂无团队成员</div>
            ) : (
              <div className="space-y-4">
                {filteredMembers.map((member, index) => {
                  const status = statusConfig[member.status] || statusConfig.good
                  const avatarInitial = member.name?.[0] || member.role?.[0] || '员'
                  const personalMonthly = member.personalTargets?.monthly
                  const recentFollowUp = member.recentFollowUp
                  const distribution = member.customerDistribution || []
                  return (
                    <div
                      key={member.id}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3 flex-1">
                        <div className={cn(
                          'w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold',
                          index === 0 && 'bg-gradient-to-br from-amber-500 to-orange-500',
                          index === 1 && 'bg-gradient-to-br from-blue-500 to-cyan-500',
                          index === 2 && 'bg-gradient-to-br from-purple-500 to-pink-500',
                          index >= 3 && 'bg-slate-600',
                        )}>
                          {avatarInitial}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-white">{member.name}</span>
                            <Badge variant="outline" className="text-xs bg-slate-700/40">
                              {member.role}
                            </Badge>
                            <Badge
                              variant="outline"
                              className={cn('text-xs', status.textColor)}
                            >
                              {status.label}
                            </Badge>
                            <Badge variant="outline" className="text-xs text-slate-300 bg-slate-800/60">
                              {member.region || '未分配'}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-slate-400">
                            <span>{member.leadCount || 0} 个线索</span>
                            <span>{member.opportunityCount || 0} 个商机</span>
                            <span>{member.contractCount || 0} 个合同</span>
                            {member.activeProjects > 0 && <span>{member.activeProjects} 个项目</span>}
                          </div>
                        </div>
                      </div>
                      <div className="text-right mr-4">
                        <div className="text-lg font-bold text-white">
                          {formatCurrency(member.monthlyAchieved)}
                        </div>
                        <div className="text-xs text-slate-400">
                          目标: {formatCurrency(member.monthlyTarget)}
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewMember(member)}>
                            <BarChart3 className="w-4 h-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleNavigatePerformance(member)}>
                            <TrendingUp className="w-4 h-4 mr-2" />
                            跳转绩效
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleNavigateCRM(member)}>
                            <Users className="w-4 h-4 mr-2" />
                            打开CRM
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Edit className="w-4 h-4 mr-2" />
                            编辑目标
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <Mail className="w-4 h-4 mr-2" />
                            发送邮件
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Phone className="w-4 h-4 mr-2" />
                            拨打电话
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {/* Performance Metrics */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">本月完成率</span>
                        <span className={cn(
                          'font-medium',
                          member.achievementRate >= 90 ? 'text-emerald-400' :
                          member.achievementRate >= 70 ? 'text-amber-400' :
                          'text-red-400'
                        )}>
                          {member.achievementRate}%
                        </span>
                      </div>
                      <Progress
                        value={member.achievementRate}
                        className="h-1.5 bg-slate-700/50"
                      />
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">年度进度</span>
                        <span className="text-slate-400">
                          {formatCurrency(member.yearAchieved)} / {formatCurrency(member.yearTarget)}
                        </span>
                      </div>
                      <Progress
                        value={member.yearProgress}
                        className="h-1.5 bg-slate-700/50"
                      />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={() => handleNavigatePerformance(member)}
                      >
                        <TrendingUp className="w-3 h-3" />
                        绩效分析
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-xs"
                        onClick={() => handleNavigateCRM(member)}
                      >
                        <Users className="w-3 h-3" />
                        CRM客户
                      </Button>
                    </div>
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-400">
                      <div className="bg-slate-900/30 rounded-md p-3 border border-slate-800/60">
                        <p className="mb-1">个人目标完成率</p>
                        {personalMonthly ? (
                          <>
                            <p className="text-sm font-semibold text-white">
                              {personalMonthly.completion_rate ?? member.achievementRate}%
                            </p>
                            <p className="text-slate-500 mt-1">
                              {formatCurrency(personalMonthly.actual_value || member.monthlyAchieved)} / {formatCurrency(personalMonthly.target_value || member.monthlyTarget)}
                            </p>
                            <p className="text-slate-500 text-[11px]">
                              周期：{personalMonthly.period_value || '本月'}
                            </p>
                          </>
                        ) : (
                          <p className="text-slate-500">暂无个人目标数据</p>
                        )}
                      </div>
                      <div className="bg-slate-900/30 rounded-md p-3 border border-slate-800/60">
                        <p className="mb-1">最近跟进</p>
                        {recentFollowUp ? (
                          <>
                            <p className="text-sm font-semibold text-white">
                              {recentFollowUp.leadName || '线索'} · {formatFollowUpType(recentFollowUp.followUpType)}
                            </p>
                            <p className="text-slate-500 mt-1">
                              {formatTimeAgo(recentFollowUp.createdAt)}
                            </p>
                            {recentFollowUp.content && (
                              <p className="text-slate-500 text-[11px] mt-1 truncate">
                                {recentFollowUp.content}
                              </p>
                            )}
                          </>
                        ) : (
                          <p className="text-slate-500">暂无跟进记录</p>
                        )}
                      </div>
                      <div className="bg-slate-900/30 rounded-md p-3 border border-slate-800/60">
                        <p className="mb-1">客户分布</p>
                        {distribution.length ? (
                          <div className="flex flex-wrap gap-1">
                            {distribution.slice(0, 3).map((item) => (
                              <Badge
                                key={`${member.id}-${item.label}`}
                                variant="outline"
                                className="text-[11px] bg-slate-900 border-slate-700/70 text-slate-200"
                              >
                                {item.label} · {item.value} ({item.percentage}%)
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <p className="text-slate-500">暂无客户分布数据</p>
                        )}
                        <p className="text-slate-500 text-[11px] mt-1">
                          客户数：{member.customerTotal || 0}，本月新增 {member.newCustomers || 0}
                        </p>
                      </div>
                    </div>
                    </div>
                )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Member Detail Dialog */}
      <Dialog open={showMemberDialog} onOpenChange={setShowMemberDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedMember?.name} - 详细信息</DialogTitle>
            <DialogDescription>
              查看团队成员的详细业绩和活动信息
            </DialogDescription>
          </DialogHeader>
          {selectedMember && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">角色</p>
                  <p className="text-white font-medium">{selectedMember.role}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">部门</p>
                  <p className="text-white font-medium">{selectedMember.department}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">所属区域</p>
                  <p className="text-white font-medium">{selectedMember.region || '未分配'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">邮箱</p>
                  <p className="text-white font-medium">{selectedMember.email}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">电话</p>
                  <p className="text-white font-medium">{selectedMember.phone}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">入职日期</p>
                  <p className="text-white font-medium">{selectedMember.joinDate}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">最后活动</p>
                  <p className="text-white font-medium">{selectedMember.lastActivity}</p>
                </div>
              </div>
              <div className="pt-4 border-t border-slate-700">
                <h4 className="text-sm font-medium text-white mb-3">业绩概览</h4>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-slate-400">本月完成</span>
                      <span className="text-white font-medium">
                        {formatCurrency(selectedMember.monthlyAchieved)} / {formatCurrency(selectedMember.monthlyTarget)}
                      </span>
                    </div>
                    <Progress value={selectedMember.achievementRate} className="h-2" />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-slate-400">年度完成</span>
                      <span className="text-white font-medium">
                        {formatCurrency(selectedMember.yearAchieved)} / {formatCurrency(selectedMember.yearTarget)}
                      </span>
                    </div>
                    <Progress value={selectedMember.yearProgress} className="h-2" />
                  </div>
                </div>
              </div>
              <div className="pt-4 border-t border-slate-700">
                <h4 className="text-sm font-medium text-white mb-3">客户洞察与跟进</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                    <p className="text-slate-400 text-xs mb-1">个人目标完成率</p>
                    {selectedMember.personalTargets?.monthly ? (
                      <>
                        <p className="text-white font-semibold">
                          {selectedMember.personalTargets.monthly.completion_rate ?? selectedMember.achievementRate}%
                        </p>
                        <p className="text-slate-500 text-xs mt-1">
                          {formatCurrency(selectedMember.personalTargets.monthly.actual_value || selectedMember.monthlyAchieved)} / {formatCurrency(selectedMember.personalTargets.monthly.target_value || selectedMember.monthlyTarget)}
                        </p>
                        <p className="text-slate-500 text-[11px] mt-1">
                          周期：{selectedMember.personalTargets.monthly.period_value || '本月'}
                        </p>
                      </>
                    ) : (
                      <p className="text-slate-500 text-xs">暂无个人目标数据</p>
                    )}
                  </div>
                  <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                    <p className="text-slate-400 text-xs mb-1">最近跟进</p>
                    {selectedMember.recentFollowUp ? (
                      <>
                        <p className="text-white font-semibold">
                          {selectedMember.recentFollowUp.leadName || '线索'} · {formatFollowUpType(selectedMember.recentFollowUp.followUpType)}
                        </p>
                        <p className="text-slate-500 text-xs mt-1">
                          {formatDateTime(selectedMember.recentFollowUp.createdAt)}
                        </p>
                        {selectedMember.recentFollowUp.content && (
                          <p className="text-slate-500 text-[11px] mt-1">
                            {selectedMember.recentFollowUp.content}
                          </p>
                        )}
                      </>
                    ) : (
                      <p className="text-slate-500 text-xs">暂无跟进记录</p>
                    )}
                  </div>
                  <div className="md:col-span-2 bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                    <p className="text-slate-400 text-xs mb-2">客户分布</p>
                    {selectedMember.customerDistribution?.length ? (
                      <div className="flex flex-wrap gap-2">
                        {selectedMember.customerDistribution.map((item) => (
                          <Badge
                            key={`${selectedMember.id}-${item.label}`}
                            variant="outline"
                            className="text-[11px] bg-slate-900 border-slate-700/70 text-slate-200"
                          >
                            {item.label} · {item.value} ({item.percentage}%)
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <p className="text-slate-500 text-xs">暂无客户分布数据</p>
                    )}
                    <p className="text-slate-500 text-[11px] mt-2">
                      客户总数：{selectedMember.customerTotal || 0}，本月新增 {selectedMember.newCustomers || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                size="sm"
                className="text-xs"
                onClick={() => handleNavigatePerformance(selectedMember)}
              >
                <TrendingUp className="w-3 h-3" />
                绩效详情
              </Button>
              <Button
                variant="secondary"
                size="sm"
                className="text-xs"
                onClick={() => handleNavigateCRM(selectedMember)}
              >
                <Users className="w-3 h-3" />
                CRM详情
              </Button>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowMemberDialog(false)}>
                关闭
              </Button>
              <Button>编辑目标</Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}
