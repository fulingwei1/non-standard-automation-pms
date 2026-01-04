/**
 * Payment Management Page - Accounts receivable tracking for sales
 * Features: Payment schedule, aging analysis, invoice management, collection reminders
 */

import { useState, useMemo } from 'react'
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

  // Filter payments
  const filteredPayments = useMemo(() => {
    return mockPayments.filter(payment => {
      const matchesSearch = !searchTerm || 
        payment.projectName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        payment.customerShort.toLowerCase().includes(searchTerm.toLowerCase()) ||
        payment.contractNo.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesType = selectedType === 'all' || payment.type === selectedType
      const matchesStatus = selectedStatus === 'all' || payment.status === selectedStatus

      return matchesSearch && matchesType && matchesStatus
    })
  }, [searchTerm, selectedType, selectedStatus])

  // Stats calculation
  const stats = useMemo(() => {
    const paid = mockPayments.filter(p => p.status === 'paid')
    const pending = mockPayments.filter(p => p.status === 'pending' || p.status === 'invoiced')
    const overdue = mockPayments.filter(p => p.status === 'overdue')
    
    return {
      totalPaid: paid.reduce((sum, p) => sum + p.paidAmount, 0),
      paidCount: paid.length,
      totalPending: pending.reduce((sum, p) => sum + p.amount - p.paidAmount, 0),
      pendingCount: pending.length,
      totalOverdue: overdue.reduce((sum, p) => sum + p.amount, 0),
      overdueCount: overdue.length,
      invoicedCount: mockPayments.filter(p => p.status === 'invoiced').length,
      thisMonthTarget: 450000,
      thisMonthAchieved: 200000,
    }
  }, [])

  // Aging analysis
  const agingData = useMemo(() => {
    const now = new Date()
    const aging = {
      current: { amount: 0, count: 0 }, // Not due
      '1-30': { amount: 0, count: 0 },
      '31-60': { amount: 0, count: 0 },
      '61-90': { amount: 0, count: 0 },
      '90+': { amount: 0, count: 0 },
    }

    mockPayments.filter(p => p.status !== 'paid').forEach(payment => {
      const dueDate = new Date(payment.dueDate)
      const daysDiff = Math.floor((now - dueDate) / (1000 * 60 * 60 * 24))
      const unpaidAmount = payment.amount - payment.paidAmount

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

    return aging
  }, [])

  const handlePaymentClick = (payment) => {
    setSelectedPayment(payment)
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
        title="回款管理"
        description="跟踪应收账款、管理开票和催收"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
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

      {/* Stats Row */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">已回款</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">
                  ¥{(stats.totalPaid / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-xs text-slate-500">{stats.paidCount}笔</span>
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
                  ¥{(stats.totalPending / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-xs text-slate-500">{stats.pendingCount}笔</span>
                  <span className="text-xs text-amber-400">({stats.invoicedCount}已开票)</span>
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
                  ¥{(stats.totalOverdue / 10000).toFixed(0)}万
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{stats.overdueCount}笔需催收</span>
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
                  {filteredPayments.map((payment) => {
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
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <Eye className="w-4 h-4" />
                            </Button>
                            {payment.status !== 'paid' && (
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <Bell className="w-4 h-4 text-amber-400" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </CardContent>
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
                <PaymentStats payments={mockPayments} />
                
                {/* Type breakdown */}
                <div className="mt-6 pt-6 border-t border-white/5">
                  <h4 className="text-sm font-medium text-slate-400 mb-4">按类型分布</h4>
                  <div className="space-y-3">
                    {Object.entries(paymentTypes).map(([key, conf]) => {
                      const typePayments = mockPayments.filter(p => p.type === key && p.status !== 'paid')
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
                {mockPayments
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
                {mockPayments.filter(p => p.status === 'overdue').length === 0 && (
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
                {mockPayments.filter(p => !p.invoiceNo && p.status !== 'paid').map(p => (
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

