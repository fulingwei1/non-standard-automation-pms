/**
 * Payment Management Page - Accounts receivable tracking for sales
 * Features: Payment schedule, aging analysis, invoice management, collection reminders
 */

import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  DollarSign,
  Search,
  Filter,
  Plus,
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle2,
  FileText,
  TrendingUp,
  TrendingDown,
  Building2,
  ChevronRight,
  Download,
  Send,
  Bell,
  BarChart3,
  PieChart,
  List,
  LayoutGrid,
  Eye,
  Edit,
  Receipt,
  CreditCard,
  Banknote,
  X,
  Phone,
  Mail,
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
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { PaymentTimeline, PaymentStats } from '../components/sales'
import { paymentApi, invoiceApi, receivableApi, paymentPlanApi } from '../services/api'

// Payment type configuration
const paymentTypes = {
  deposit: { label: '签约款', color: 'bg-blue-500', ratio: '30%' },
  progress: { label: '进度款', color: 'bg-amber-500', ratio: '40%' },
  delivery: { label: '发货款', color: 'bg-purple-500', ratio: '20%' },
  acceptance: { label: '验收款', color: 'bg-emerald-500', ratio: '5%' },
  warranty: { label: '质保金', color: 'bg-slate-500', ratio: '5%' },
}

const statusConfig = {
  paid: { label: '已到账', color: 'bg-emerald-500', textColor: 'text-emerald-400', icon: CheckCircle2 },
  pending: { label: '待收款', color: 'bg-blue-500', textColor: 'text-blue-400', icon: Clock },
  overdue: { label: '已逾期', color: 'bg-red-500', textColor: 'text-red-400', icon: AlertTriangle },
  invoiced: { label: '已开票', color: 'bg-amber-500', textColor: 'text-amber-400', icon: FileText },
}

// Mock payment data
const mockPayments = [
  {
    id: 'PAY001',
    type: 'progress',
    projectId: 'PJ250106002',
    projectName: 'EOL功能测试设备',
    contractNo: 'HT2025-012',
    customerName: '东莞市精密电子有限公司',
    customerShort: '东莞精密',
    amount: 150000,
    dueDate: '2026-01-08',
    status: 'pending',
    invoiceNo: null,
    invoiceDate: null,
    paidAmount: 0,
    paidDate: null,
    notes: '设备装配完成后支付',
    createdAt: '2025-11-20',
  },
  {
    id: 'PAY002',
    type: 'deposit',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    contractNo: 'HT2026-001',
    customerName: '深圳市新能源科技有限公司',
    customerShort: '深圳新能源',
    amount: 200000,
    dueDate: '2026-01-05',
    status: 'paid',
    invoiceNo: 'FP2026010001',
    invoiceDate: '2025-12-28',
    paidAmount: 200000,
    paidDate: '2026-01-05',
    notes: '已收到签约款',
    createdAt: '2025-12-20',
  },
  {
    id: 'PAY003',
    type: 'acceptance',
    projectId: 'PJ250103003',
    projectName: 'ICT在线测试设备',
    contractNo: 'HT2025-008',
    customerName: '惠州市储能电池科技有限公司',
    customerShort: '惠州储能',
    amount: 180000,
    dueDate: '2026-01-20',
    status: 'pending',
    invoiceNo: null,
    invoiceDate: null,
    paidAmount: 0,
    paidDate: null,
    notes: '等待现场验收',
    createdAt: '2025-10-15',
  },
  {
    id: 'PAY004',
    type: 'warranty',
    projectId: 'PJ240820001',
    projectName: '旧设备项目',
    contractNo: 'HT2024-032',
    customerName: '广州市汽车零部件有限公司',
    customerShort: '广州汽车',
    amount: 50000,
    dueDate: '2025-12-30',
    status: 'overdue',
    invoiceNo: 'FP2025120012',
    invoiceDate: '2025-12-15',
    paidAmount: 0,
    paidDate: null,
    notes: '质保期已到，需催收',
    overdueDay: 5,
    createdAt: '2024-08-20',
  },
  {
    id: 'PAY005',
    type: 'progress',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    contractNo: 'HT2026-001',
    customerName: '深圳市新能源科技有限公司',
    customerShort: '深圳新能源',
    amount: 280000,
    dueDate: '2026-02-01',
    status: 'pending',
    invoiceNo: null,
    invoiceDate: null,
    paidAmount: 0,
    paidDate: null,
    notes: '设计评审通过后支付',
    createdAt: '2025-12-20',
  },
  {
    id: 'PAY006',
    type: 'delivery',
    projectId: 'PJ250106002',
    projectName: 'EOL功能测试设备',
    contractNo: 'HT2025-012',
    customerName: '东莞市精密电子有限公司',
    customerShort: '东莞精密',
    amount: 124000,
    dueDate: '2026-01-25',
    status: 'invoiced',
    invoiceNo: 'FP2026010015',
    invoiceDate: '2026-01-03',
    paidAmount: 0,
    paidDate: null,
    notes: '发票已开，等待客户付款',
    createdAt: '2025-11-20',
  },
  {
    id: 'PAY007',
    type: 'deposit',
    projectId: 'PJ250103003',
    projectName: 'ICT在线测试设备',
    contractNo: 'HT2025-008',
    customerName: '惠州市储能电池科技有限公司',
    customerShort: '惠州储能',
    amount: 135000,
    dueDate: '2025-10-20',
    status: 'paid',
    invoiceNo: 'FP2025100032',
    invoiceDate: '2025-10-15',
    paidAmount: 135000,
    paidDate: '2025-10-22',
    notes: '',
    createdAt: '2025-10-10',
  },
]

export default function PaymentManagement() {
  const [viewMode, setViewMode] = useState('list') // 'list', 'timeline', 'aging'
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState('all')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [selectedPayment, setSelectedPayment] = useState(null)
  const [showInvoiceDialog, setShowInvoiceDialog] = useState(false)
  const [showCollectionDialog, setShowCollectionDialog] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 20
  
  // 新增状态：回款提醒、统计分析
  const [reminders, setReminders] = useState([])
  const [remindersLoading, setRemindersLoading] = useState(false)
  const [statistics, setStatistics] = useState(null)
  const [statisticsLoading, setStatisticsLoading] = useState(false)
  const [showReminders, setShowReminders] = useState(false)

  // Load payments from API
  const loadPayments = async () => {
    setLoading(true)
    try {
      const params = {
        page,
        page_size: pageSize,
        payment_status: selectedStatus !== 'all' ? selectedStatus.toUpperCase() : undefined,
      }
      
      if (searchTerm) {
        // 如果搜索关键词是项目编码或合同编码，可以通过project_id或contract_id筛选
        // 这里简化处理，只搜索项目名称
        params.keyword = searchTerm
      }

      const response = await paymentApi.list(params)
      const data = response.data || {}
      
      // 转换数据格式
      const transformedPayments = (data.items || []).map((item) => {
        // 根据payment_status确定状态
        const statusMap = {
          PAID: 'paid',
          PENDING: 'pending',
          PARTIAL: 'pending',
          OVERDUE: 'overdue',
        }
        
        // 根据合同类型确定payment type（这里简化处理，从合同或项目中获取）
        const type = 'progress' // 默认类型，可以从合同payment_plan中获取

        return {
          id: item.id || item.invoice_id,
          type: type,
          projectId: item.project_code || item.project_id,
          projectName: item.project_name || item.project_code || '',
          contractNo: item.contract_code || '',
          customerName: item.customer_name || '',
          customerShort: item.customer_name || '',
          amount: parseFloat(item.invoice_amount || item.amount || 0),
          dueDate: item.due_date || '',
          status: statusMap[item.payment_status] || 'pending',
          invoiceNo: item.invoice_code || '',
          invoiceDate: item.issue_date || '',
          paidAmount: parseFloat(item.paid_amount || 0),
          paidDate: item.paid_date || '',
          notes: item.remark || '',
          overdueDay: item.overdue_days || null,
          createdAt: item.created_at || '',
          raw: item, // 保存原始数据
        }
      })

      setPayments(transformedPayments)
      setTotal(data.total || 0)
    } catch (error) {
      // 如果API失败，使用mock数据作为fallback
      setPayments(mockPayments)
      setTotal(mockPayments.length)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPayments()
  }, [page, selectedStatus])

  // 搜索防抖
  useEffect(() => {
    const timer = setTimeout(() => {
      if (page === 1) {
        loadPayments()
      } else {
        setPage(1)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [searchTerm])

  // Filter payments (前端筛选，用于类型筛选)
  const filteredPayments = useMemo(() => {
    return payments.filter(payment => {
      const matchesType = selectedType === 'all' || payment.type === selectedType
      return matchesType
    })
  }, [payments, selectedType])

  // Stats calculation
  const stats = useMemo(() => {
    const paid = payments.filter(p => p.status === 'paid')
    const pending = payments.filter(p => p.status === 'pending')
    const overdue = payments.filter(p => p.status === 'overdue')
    
    return {
      totalPaid: paid.reduce((sum, p) => sum + (p.paidAmount || 0), 0),
      paidCount: paid.length,
      totalPending: pending.reduce((sum, p) => sum + (p.amount - (p.paidAmount || 0)), 0),
      pendingCount: pending.length,
      totalOverdue: overdue.reduce((sum, p) => sum + (p.amount - (p.paidAmount || 0)), 0),
      overdueCount: overdue.length,
      invoicedCount: payments.filter(p => p.invoiceNo).length,
      thisMonthTarget: 450000, // 可以从配置或API获取
      thisMonthAchieved: paid.reduce((sum, p) => {
        const paidDate = p.paidDate ? new Date(p.paidDate) : null
        if (paidDate) {
          const now = new Date()
          if (paidDate.getMonth() === now.getMonth() && paidDate.getFullYear() === now.getFullYear()) {
            return sum + (p.paidAmount || 0)
          }
        }
        return sum
      }, 0),
    }
  }, [payments])

  // Load aging analysis from API
  const [agingData, setAgingData] = useState({
    current: { amount: 0, count: 0 },
    '1-30': { amount: 0, count: 0 },
    '31-60': { amount: 0, count: 0 },
    '61-90': { amount: 0, count: 0 },
    '90+': { amount: 0, count: 0 },
  })

  useEffect(() => {
    const loadAging = async () => {
      try {
        const response = await receivableApi.getAging({})
        const data = response.data || {}
        
        // 转换API返回的账龄数据
        setAgingData({
          current: { amount: parseFloat(data.current || 0), count: data.current_count || 0 },
          '1-30': { amount: parseFloat(data.days_1_30 || 0), count: data.days_1_30_count || 0 },
          '31-60': { amount: parseFloat(data.days_31_60 || 0), count: data.days_31_60_count || 0 },
          '61-90': { amount: parseFloat(data.days_61_90 || 0), count: data.days_61_90_count || 0 },
          '90+': { amount: parseFloat(data.days_over_90 || 0), count: data.days_over_90_count || 0 },
        })
      } catch (error) {
        // 使用本地计算作为fallback
        const now = new Date()
        const aging = {
          current: { amount: 0, count: 0 },
          '1-30': { amount: 0, count: 0 },
          '31-60': { amount: 0, count: 0 },
          '61-90': { amount: 0, count: 0 },
          '90+': { amount: 0, count: 0 },
        }

        payments.filter(p => p.status !== 'paid' && p.dueDate).forEach(payment => {
          const dueDate = new Date(payment.dueDate)
          const daysDiff = Math.floor((now - dueDate) / (1000 * 60 * 60 * 24))
          const unpaidAmount = payment.amount - (payment.paidAmount || 0)

          if (daysDiff < 0) {
            aging.current.amount += unpaidAmount
            aging.current.count++
          } else if (daysDiff <= 30) {
            aging['1-30'].amount += unpaidAmount
            aging['1-30'].count++
          } else if (daysDiff <= 60) {
            aging['31-60'].amount += unpaidAmount
            aging['31-60'].count++
          } else if (daysDiff <= 90) {
            aging['61-90'].amount += unpaidAmount
            aging['61-90'].count++
          } else {
            aging['90+'].amount += unpaidAmount
            aging['90+'].count++
          }
        })
        setAgingData(aging)
      }
    }
    loadAging()
  }, [payments])

  const handlePaymentClick = async (payment) => {
    if (payment.raw && payment.raw.id) {
      try {
        const response = await paymentApi.get(payment.raw.id)
        if (response.data && response.data.data) {
          setSelectedPayment({
            ...payment,
            raw: response.data.data,
          })
        } else {
          setSelectedPayment(payment)
        }
      } catch (error) {
        setSelectedPayment(payment)
      }
    } else {
      setSelectedPayment(payment)
    }
    setShowDetailDialog(true)
  }

  // 登记回款
  const handleRecordPayment = async (payment, paymentData) => {
    try {
      await paymentApi.create({
        invoice_id: payment.raw?.id || payment.id,
        paid_amount: paymentData.amount,
        paid_date: paymentData.date,
        payment_method: paymentData.method,
        bank_account: paymentData.account,
        remark: paymentData.remark,
      })
      
      // 重新加载数据
      loadPayments()
      setShowCollectionDialog(false)
      setSelectedPayment(null)
    } catch (error) {
      alert('登记回款失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 加载回款提醒
  const loadReminders = async () => {
    setRemindersLoading(true)
    try {
      const response = await paymentApi.getReminders({
        page: 1,
        page_size: 20,
        days_before: 7,
      })
      const data = response.data || {}
      setReminders(data.items || [])
    } catch (error) {
      // axios timeout 或连接错误时，静默处理，使用空数据
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.message?.includes('Network Error')) {
      } else {
      }
      setReminders([])
    } finally {
      setRemindersLoading(false)
    }
  }

  // 加载统计分析
  const loadStatistics = async () => {
    setStatisticsLoading(true)
    try {
      const response = await paymentApi.getStatistics({})
      const data = response.data || {}
      setStatistics(data)
    } catch (error) {
      // axios timeout 或连接错误时，静默处理，使用本地计算数据
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout') || error.message?.includes('Network Error')) {
      } else {
      }
      setStatistics(null)
    } finally {
      setStatisticsLoading(false)
    }
  }

  // 导出回款记录
  const handleExportPayments = async () => {
    try {
      const params = {
        payment_status: selectedStatus !== 'all' ? selectedStatus.toUpperCase() : undefined,
      }
      
      if (searchTerm) {
        params.keyword = searchTerm
      }

      const response = await paymentApi.exportInvoices(params)
      
      // 创建下载链接
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `回款记录_${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      alert('导出失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 组件加载时获取提醒和统计（延迟加载，避免阻塞页面渲染）
  useEffect(() => {
    // 使用 setTimeout 延迟加载，确保页面先渲染
    const timer = setTimeout(() => {
      loadReminders()
      loadStatistics()
    }, 100)
    return () => clearTimeout(timer)
  }, [])

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="回款管理"
        description="跟踪应收账款、管理开票和催收"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button 
              variant="outline" 
              className="flex items-center gap-2"
              onClick={handleExportPayments}
            >
              <Download className="w-4 h-4" />
              导出报表
            </Button>
            <Button variant="outline" className="flex items-center gap-2" onClick={() => setShowInvoiceDialog(true)}>
              <FileText className="w-4 h-4" />
              申请开票
            </Button>
            <Button className="flex items-center gap-2" onClick={() => setShowCollectionDialog(true)}>
              <Bell className="w-4 h-4" />
              批量催收
            </Button>
          </motion.div>
        }
      />

      {/* 回款提醒卡片 */}
      {reminders.length > 0 && (
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Bell className="w-5 h-5 text-amber-400" />
                  回款提醒
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowReminders(!showReminders)}
                >
                  {showReminders ? '收起' : '展开'}
                </Button>
              </div>
            </CardHeader>
            {showReminders && (
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {reminders.map((reminder) => (
                    <div
                      key={reminder.id}
                      className={cn(
                        "p-3 rounded-lg border",
                        reminder.reminder_level === 'urgent' 
                          ? "bg-red-500/10 border-red-500/20" 
                          : reminder.reminder_level === 'warning'
                          ? "bg-amber-500/10 border-amber-500/20"
                          : "bg-blue-500/10 border-blue-500/20"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-white">
                              {reminder.customer_name || '未知客户'}
                            </span>
                            <Badge
                              variant={
                                reminder.reminder_level === 'urgent' ? 'destructive' :
                                reminder.reminder_level === 'warning' ? 'default' : 'secondary'
                              }
                            >
                              {reminder.is_overdue 
                                ? `逾期${reminder.overdue_days}天` 
                                : `还有${reminder.days_until_due}天到期`}
                            </Badge>
                          </div>
                          <div className="mt-1 text-sm text-slate-400">
                            {reminder.contract_code && `合同：${reminder.contract_code} | `}
                            {reminder.project_code && `项目：${reminder.project_code} | `}
                            未收金额：¥{(reminder.unpaid_amount / 10000).toFixed(2)}万
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium text-white">
                            {reminder.due_date}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        </motion.div>
      )}

      {/* Stats Row */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">已回款</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">
                  ¥{statistics?.summary?.total_paid 
                    ? (statistics.summary.total_paid / 10000).toFixed(0) 
                    : (stats.totalPaid / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-xs text-slate-500">
                    {statistics?.summary?.paid_count || stats.paidCount}笔
                  </span>
                </div>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">待回款</p>
                <p className="text-2xl font-bold text-blue-400 mt-1">
                  ¥{statistics?.summary?.total_unpaid 
                    ? (statistics.summary.total_unpaid / 10000).toFixed(0) 
                    : (stats.totalPending / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-xs text-slate-500">
                    {statistics?.summary?.pending_count || stats.pendingCount}笔
                  </span>
                  <span className="text-xs text-amber-400">
                    ({statistics?.summary?.invoice_count || stats.invoicedCount}已开票)
                  </span>
                </div>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Clock className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-500/10 to-rose-500/5 border-red-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">已逾期</p>
                <p className="text-2xl font-bold text-red-400 mt-1">
                  ¥{statistics?.summary?.total_overdue 
                    ? (statistics.summary.total_overdue / 10000).toFixed(0) 
                    : (stats.totalOverdue / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">
                    {statistics?.summary?.overdue_count || stats.overdueCount}笔需催收
                  </span>
                </div>
              </div>
              <div className="p-2 bg-red-500/20 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">本月目标</p>
                <p className="text-2xl font-bold text-white mt-1">
                  ¥{(stats.thisMonthTarget / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <Progress 
                    value={(stats.thisMonthAchieved / stats.thisMonthTarget) * 100} 
                    className="w-16 h-1.5"
                  />
                  <span className="text-xs text-slate-400">
                    {((stats.thisMonthAchieved / stats.thisMonthTarget) * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn} className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex flex-wrap gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索项目、客户、合同号..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">全部类型</option>
            {Object.entries(paymentTypes).map(([key, val]) => (
              <option key={key} value={key}>{val.label}</option>
            ))}
          </select>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">全部状态</option>
            {Object.entries(statusConfig).map(([key, val]) => (
              <option key={key} value={key}>{val.label}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex border border-white/10 rounded-lg overflow-hidden">
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode('list')}
            >
              <List className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'timeline' ? 'default' : 'ghost'}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode('timeline')}
            >
              <Calendar className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'aging' ? 'default' : 'ghost'}
              size="sm"
              className="rounded-none"
              onClick={() => setViewMode('aging')}
            >
              <BarChart3 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Content */}
      <motion.div variants={fadeIn}>
        {viewMode === 'list' && (
          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    <th className="text-left p-4 text-sm font-medium text-slate-400">项目/合同</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">客户</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">类型</th>
                    <th className="text-right p-4 text-sm font-medium text-slate-400">金额</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">到期日</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">发票</th>
                    <th className="text-left p-4 text-sm font-medium text-slate-400">状态</th>
                    <th className="text-center p-4 text-sm font-medium text-slate-400">操作</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan={8} className="p-8 text-center text-slate-400">
                        加载中...
                      </td>
                    </tr>
                  ) : filteredPayments.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="p-8 text-center text-slate-400">
                        暂无回款记录
                      </td>
                    </tr>
                  ) : (
                    filteredPayments.map((payment) => {
                    const typeConf = paymentTypes[payment.type]
                    const statusConf = statusConfig[payment.status]
                    const StatusIcon = statusConf.icon
                    const isOverdue = payment.status === 'overdue' || 
                      (payment.status === 'pending' && new Date(payment.dueDate) < new Date())

                    return (
                      <tr
                        key={payment.id}
                        onClick={() => handlePaymentClick(payment)}
                        className="border-b border-white/5 hover:bg-surface-100 cursor-pointer transition-colors"
                      >
                        <td className="p-4">
                          <div>
                            <div className="font-medium text-white">{payment.projectName}</div>
                            <div className="text-xs text-slate-500">{payment.contractNo}</div>
                          </div>
                        </td>
                        <td className="p-4 text-sm text-slate-400">{payment.customerShort}</td>
                        <td className="p-4">
                          <Badge variant="secondary" className="text-xs">
                            {typeConf?.label}
                          </Badge>
                        </td>
                        <td className="p-4 text-right">
                          <span className="text-amber-400 font-medium">
                            ¥{(payment.amount / 10000).toFixed(1)}万
                          </span>
                        </td>
                        <td className="p-4">
                          <span className={cn(
                            'text-sm',
                            isOverdue ? 'text-red-400' : 'text-slate-400'
                          )}>
                            {payment.dueDate}
                          </span>
                          {payment.overdueDay && (
                            <div className="text-xs text-red-400">逾期{payment.overdueDay}天</div>
                          )}
                        </td>
                        <td className="p-4">
                          {payment.invoiceNo ? (
                            <div className="text-sm text-white">{payment.invoiceNo}</div>
                          ) : (
                            <span className="text-sm text-slate-500">未开票</span>
                          )}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <StatusIcon className={cn('w-4 h-4', statusConf.textColor)} />
                            <span className={cn('text-sm', statusConf.textColor)}>
                              {statusConf.label}
                            </span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex justify-center gap-1">
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-8 w-8"
                              onClick={() => handlePaymentClick(payment)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {payment.status !== 'paid' && (
                              <Button 
                                variant="ghost" 
                                size="icon" 
                                className="h-8 w-8"
                                onClick={() => {
                                  setSelectedPayment(payment)
                                  setShowCollectionDialog(true)
                                }}
                              >
                                <Bell className="w-4 h-4 text-amber-400" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  }))}
                </tbody>
              </table>
            </CardContent>
            {/* Pagination */}
            {!loading && total > pageSize && (
              <div className="flex items-center justify-between p-4 border-t border-white/5">
                <div className="text-sm text-slate-400">
                  共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage(page - 1)}
                  >
                    上一页
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= Math.ceil(total / pageSize)}
                    onClick={() => setPage(page + 1)}
                  >
                    下一页
                  </Button>
                </div>
              </div>
            )}
          </Card>
        )}

        {viewMode === 'timeline' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>回款时间轴</CardTitle>
              </CardHeader>
              <CardContent>
                <PaymentTimeline payments={filteredPayments} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>回款统计</CardTitle>
              </CardHeader>
              <CardContent>
                <PaymentStats payments={payments} />
                
                {/* 新增：统计分析数据 */}
                {statistics && (
                  <div className="mt-6 pt-6 border-t border-white/5">
                    <h4 className="text-sm font-medium text-slate-400 mb-4">详细统计</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400">回款率</span>
                        <span className="text-sm font-medium text-white">
                          {statistics.summary?.collection_rate?.toFixed(2) || 0}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400">总开票金额</span>
                        <span className="text-sm font-medium text-white">
                          ¥{(statistics.summary?.total_invoiced / 10000 || 0).toFixed(2)}万
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400">总已收金额</span>
                        <span className="text-sm font-medium text-emerald-400">
                          ¥{(statistics.summary?.total_paid / 10000 || 0).toFixed(2)}万
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400">总未收金额</span>
                        <span className="text-sm font-medium text-amber-400">
                          ¥{(statistics.summary?.total_unpaid / 10000 || 0).toFixed(2)}万
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-400">逾期金额</span>
                        <span className="text-sm font-medium text-red-400">
                          ¥{(statistics.summary?.total_overdue / 10000 || 0).toFixed(2)}万
                        </span>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Type breakdown */}
                <div className="mt-6 pt-6 border-t border-white/5">
                  <h4 className="text-sm font-medium text-slate-400 mb-4">按类型分布</h4>
                  <div className="space-y-3">
                    {Object.entries(paymentTypes).map(([key, conf]) => {
                      const typePayments = payments.filter(p => p.type === key && p.status !== 'paid')
                      const total = typePayments.reduce((sum, p) => sum + p.amount - p.paidAmount, 0)
                      
                      return (
                        <div key={key} className="flex items-center gap-3">
                          <div className={cn('w-3 h-3 rounded-full', conf.color)} />
                          <span className="text-sm text-slate-400 w-16">{conf.label}</span>
                          <div className="flex-1">
                            <Progress 
                              value={stats.totalPending > 0 ? (total / stats.totalPending) * 100 : 0} 
                              className="h-2"
                            />
                          </div>
                          <span className="text-sm text-white w-20 text-right">
                            ¥{(total / 10000).toFixed(0)}万
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {viewMode === 'aging' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Aging Chart */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>账龄分析</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(agingData).map(([key, data]) => {
                    const labels = {
                      current: '未到期',
                      '1-30': '1-30天',
                      '31-60': '31-60天',
                      '61-90': '61-90天',
                      '90+': '90天以上',
                    }
                    const colors = {
                      current: 'bg-emerald-500',
                      '1-30': 'bg-blue-500',
                      '31-60': 'bg-amber-500',
                      '61-90': 'bg-orange-500',
                      '90+': 'bg-red-500',
                    }
                    const totalUnpaid = Object.values(agingData).reduce((sum, d) => sum + d.amount, 0)
                    const percentage = totalUnpaid > 0 ? (data.amount / totalUnpaid * 100) : 0

                    return (
                      <div key={key} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className={cn('w-3 h-3 rounded-full', colors[key])} />
                            <span className="text-sm text-white">{labels[key]}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-sm text-slate-400">{data.count}笔</span>
                            <span className="text-sm font-medium text-white w-24 text-right">
                              ¥{(data.amount / 10000).toFixed(0)}万
                            </span>
                          </div>
                        </div>
                        <Progress value={percentage} className="h-3" />
                      </div>
                    )
                  })}
                </div>

                {/* Summary */}
                <div className="mt-6 pt-6 border-t border-white/5 grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-emerald-400">
                      {((agingData.current.amount / (stats.totalPending + stats.totalOverdue)) * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-slate-400">正常账款占比</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-amber-400">
                      {agingData['1-30'].count + agingData['31-60'].count}
                    </div>
                    <div className="text-xs text-slate-400">1-60天逾期笔数</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-400">
                      ¥{((agingData['61-90'].amount + agingData['90+'].amount) / 10000).toFixed(0)}万
                    </div>
                    <div className="text-xs text-slate-400">高风险账款</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Overdue List */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  逾期提醒
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {payments
                  .filter(p => p.status === 'overdue' || 
                    (p.status === 'pending' && new Date(p.dueDate) < new Date()))
                  .map(payment => (
                    <div
                      key={payment.id}
                      onClick={() => handlePaymentClick(payment)}
                      className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg cursor-pointer hover:bg-red-500/20 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="font-medium text-white text-sm">{payment.projectName}</div>
                          <div className="text-xs text-slate-400">{payment.customerShort}</div>
                        </div>
                        <span className="text-sm font-medium text-red-400">
                          ¥{(payment.amount / 10000).toFixed(1)}万
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-2 text-xs text-red-400">
                        <AlertTriangle className="w-3 h-3" />
                        <span>
                          逾期{payment.overdueDay || Math.floor((new Date() - new Date(payment.dueDate)) / (1000 * 60 * 60 * 24))}天
                        </span>
                      </div>
                    </div>
                  ))}
                {payments.filter(p => p.status === 'overdue').length === 0 && (
                  <div className="text-center py-8 text-slate-500 text-sm">
                    暂无逾期账款
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </motion.div>

      {/* Payment Detail Panel */}
      <AnimatePresence>
        {selectedPayment && (
          <PaymentDetailPanel
            payment={selectedPayment}
            onClose={() => setSelectedPayment(null)}
          />
        )}
      </AnimatePresence>

      {/* Invoice Request Dialog */}
      <Dialog open={showInvoiceDialog} onOpenChange={setShowInvoiceDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>申请开票</DialogTitle>
            <DialogDescription>
              选择需要开票的回款记录
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-400">选择回款 *</label>
              <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                <option value="">请选择待开票回款</option>
                {payments.filter(p => !p.invoiceNo && p.status !== 'paid').map(p => (
                  <option key={p.id} value={p.id}>
                    {p.projectName} - {paymentTypes[p.type]?.label} - ¥{(p.amount / 10000).toFixed(1)}万
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">开票金额</label>
              <Input type="number" placeholder="请输入开票金额" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">备注</label>
              <textarea
                placeholder="请输入备注信息"
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-20"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInvoiceDialog(false)}>
              取消
            </Button>
            <Button onClick={() => setShowInvoiceDialog(false)}>
              提交申请
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Payment Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Receipt className="w-5 h-5 text-primary" />
              回款详情
            </DialogTitle>
            <DialogDescription>
              {selectedPayment ? `查看回款记录 "${selectedPayment.projectName}" 的详细信息` : ''}
            </DialogDescription>
          </DialogHeader>

          {selectedPayment && (
            <div className="space-y-6 py-4">
              {/* 基本信息 */}
              <Card className="bg-surface-50/50 border border-white/5">
                <CardHeader>
                  <CardTitle className="text-sm text-white">基本信息</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">发票编号</span>
                      <p className="text-white font-medium">{selectedPayment.invoiceNo || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">状态</span>
                      <p>
                        <Badge className={cn('text-xs', statusConfig[selectedPayment.status]?.color, statusConfig[selectedPayment.status]?.textColor)}>
                          {statusConfig[selectedPayment.status]?.label}
                        </Badge>
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">项目名称</span>
                      <p className="text-white">{selectedPayment.projectName || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">合同编号</span>
                      <p className="text-white">{selectedPayment.contractNo || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">客户名称</span>
                      <p className="text-white">{selectedPayment.customerName || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">回款类型</span>
                      <p className="text-white">{paymentTypes[selectedPayment.type]?.label || '-'}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">发票金额</span>
                      <p className="text-white font-semibold">¥{(selectedPayment.amount / 10000).toFixed(2)}万</p>
                    </div>
                    <div>
                      <span className="text-slate-400">已收金额</span>
                      <p className="text-white font-semibold text-emerald-400">¥{((selectedPayment.paidAmount || 0) / 10000).toFixed(2)}万</p>
                    </div>
                    <div>
                      <span className="text-slate-400">未收金额</span>
                      <p className="text-white font-semibold text-amber-400">
                        ¥{(((selectedPayment.amount || 0) - (selectedPayment.paidAmount || 0)) / 10000).toFixed(2)}万
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">到期日期</span>
                      <p className="text-white">{selectedPayment.dueDate || '-'}</p>
                    </div>
                    {selectedPayment.paidDate && (
                      <div>
                        <span className="text-slate-400">收款日期</span>
                        <p className="text-white">{selectedPayment.paidDate}</p>
                      </div>
                    )}
                    {selectedPayment.overdueDay && (
                      <div>
                        <span className="text-slate-400">逾期天数</span>
                        <p className="text-red-400 font-semibold">{selectedPayment.overdueDay}天</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* 备注 */}
              {selectedPayment.notes && (
                <Card className="bg-surface-50/50 border border-white/5">
                  <CardHeader>
                    <CardTitle className="text-sm text-white">备注</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-300 whitespace-pre-wrap">{selectedPayment.notes}</p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
            {selectedPayment && selectedPayment.status !== 'paid' && (
              <Button onClick={() => {
                setShowDetailDialog(false)
                setShowCollectionDialog(true)
              }}>
                <Send className="w-4 h-4 mr-2" />
                登记回款
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Collection Dialog */}
      <Dialog open={showCollectionDialog} onOpenChange={setShowCollectionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>批量催收</DialogTitle>
            <DialogDescription>
              向逾期客户发送催收提醒
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
              <div className="flex items-center gap-2 text-amber-400 text-sm">
                <AlertTriangle className="w-4 h-4" />
                <span>共有 {stats.overdueCount} 笔逾期账款待催收</span>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">催收方式</label>
              <div className="flex gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="rounded" defaultChecked />
                  <span className="text-sm text-white">系统消息</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="rounded" defaultChecked />
                  <span className="text-sm text-white">邮件提醒</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="rounded" />
                  <span className="text-sm text-white">短信提醒</span>
                </label>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">催收说明</label>
              <textarea
                placeholder="请输入催收说明..."
                defaultValue="尊敬的客户，您有一笔账款已逾期，请尽快安排付款。如有疑问请联系我们。"
                className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white resize-none h-24"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCollectionDialog(false)}>
              取消
            </Button>
            <Button onClick={() => setShowCollectionDialog(false)}>
              发送催收
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

// Payment Detail Panel
function PaymentDetailPanel({ payment, onClose }) {
  const typeConf = paymentTypes[payment.type]
  const statusConf = statusConfig[payment.status]
  const StatusIcon = statusConf.icon

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[450px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="secondary">{typeConf?.label}</Badge>
              <div className="flex items-center gap-1">
                <StatusIcon className={cn('w-4 h-4', statusConf.textColor)} />
                <span className={cn('text-sm', statusConf.textColor)}>{statusConf.label}</span>
              </div>
            </div>
            <h2 className="text-lg font-semibold text-white">{payment.projectName}</h2>
            <p className="text-sm text-slate-400">{payment.contractNo}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Amount */}
        <div className="p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 rounded-xl">
          <div className="text-sm text-slate-400 mb-1">应收金额</div>
          <div className="text-3xl font-bold text-amber-400">
            ¥{(payment.amount / 10000).toFixed(2)}万
          </div>
          {payment.paidAmount > 0 && (
            <div className="flex items-center gap-2 mt-2 text-sm">
              <span className="text-emerald-400">已收: ¥{(payment.paidAmount / 10000).toFixed(2)}万</span>
              <span className="text-slate-500">|</span>
              <span className="text-blue-400">
                待收: ¥{((payment.amount - payment.paidAmount) / 10000).toFixed(2)}万
              </span>
            </div>
          )}
        </div>

        {/* Customer Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">客户信息</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-3 text-sm">
              <Building2 className="w-4 h-4 text-slate-500" />
              <span className="text-white">{payment.customerName}</span>
            </div>
          </div>
        </div>

        {/* Payment Details */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">回款信息</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-slate-400">到期日期</span>
              <span className={cn(
                payment.status === 'overdue' ? 'text-red-400' : 'text-white'
              )}>
                {payment.dueDate}
              </span>
            </div>
            {payment.paidDate && (
              <div className="flex items-center justify-between">
                <span className="text-slate-400">实际到账</span>
                <span className="text-emerald-400">{payment.paidDate}</span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span className="text-slate-400">发票号</span>
              <span className="text-white">{payment.invoiceNo || '未开票'}</span>
            </div>
            {payment.invoiceDate && (
              <div className="flex items-center justify-between">
                <span className="text-slate-400">开票日期</span>
                <span className="text-white">{payment.invoiceDate}</span>
              </div>
            )}
          </div>
        </div>

        {/* Notes */}
        {payment.notes && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-400">备注</h3>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {payment.notes}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">操作</h3>
          <div className="grid grid-cols-2 gap-2">
            {!payment.invoiceNo && payment.status !== 'paid' && (
              <Button variant="outline" size="sm" className="justify-start">
                <FileText className="w-4 h-4 mr-2 text-amber-400" />
                申请开票
              </Button>
            )}
            {payment.status !== 'paid' && (
              <Button variant="outline" size="sm" className="justify-start">
                <Bell className="w-4 h-4 mr-2 text-blue-400" />
                发送催收
              </Button>
            )}
            <Button variant="outline" size="sm" className="justify-start">
              <Phone className="w-4 h-4 mr-2 text-green-400" />
              联系客户
            </Button>
            {payment.status !== 'paid' && (
              <Button variant="outline" size="sm" className="justify-start">
                <CreditCard className="w-4 h-4 mr-2 text-emerald-400" />
                确认到账
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        <Button className="flex-1">
          <Edit className="w-4 h-4 mr-2" />
          编辑
        </Button>
      </div>
    </motion.div>
  )
}

