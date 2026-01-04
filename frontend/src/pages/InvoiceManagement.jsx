/**
 * Invoice Management Page - Accounts receivable and invoicing management
 * Handles invoice creation, tracking, and reconciliation
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Receipt,
  Search,
  Filter,
  Plus,
  Download,
  Send,
  Check,
  X,
  AlertTriangle,
  Clock,
  FileText,
  DollarSign,
  Building2,
  Calendar,
  ChevronRight,
  TrendingUp,
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
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui'
import { cn, formatCurrency, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock invoice data
const mockInvoices = [
  {
    id: 'INV-2025-0001',
    contractId: 'HT2026-001',
    projectName: 'BMS老化测试设备',
    customerName: '深圳XX科技',
    amount: 255000,
    taxRate: 13,
    taxAmount: 33150,
    totalAmount: 288150,
    invoiceType: '专票',
    status: 'issued', // draft | applied | approved | issued | void
    issueDate: '2025-12-01',
    dueDate: '2026-01-01',
    paymentStatus: 'paid', // pending | partial | paid | overdue
    paidAmount: 255000,
    paidDate: '2025-12-05',
    notes: '签约款发票',
  },
  {
    id: 'INV-2025-0002',
    contractId: 'HT2025-012',
    projectName: 'EOL功能测试设备',
    customerName: '东莞精密电子',
    amount: 186000,
    taxRate: 13,
    taxAmount: 24180,
    totalAmount: 210180,
    invoiceType: '专票',
    status: 'issued',
    issueDate: '2025-11-30',
    dueDate: '2025-12-30',
    paymentStatus: 'paid',
    paidAmount: 186000,
    paidDate: '2025-12-02',
    notes: '签约款发票',
  },
  {
    id: 'INV-2025-0003',
    contractId: 'HT2026-001',
    projectName: 'BMS老化测试设备',
    customerName: '深圳XX科技',
    amount: 340000,
    taxRate: 13,
    taxAmount: 44200,
    totalAmount: 384200,
    invoiceType: '专票',
    status: 'approved',
    issueDate: null,
    dueDate: '2026-01-30',
    paymentStatus: 'pending',
    paidAmount: 0,
    paidDate: null,
    notes: '进度款发票',
  },
  {
    id: 'INV-2025-0004',
    contractId: 'HT2025-008',
    projectName: 'ICT在线测试设备',
    customerName: '惠州XX电池',
    amount: 135000,
    taxRate: 13,
    taxAmount: 17550,
    totalAmount: 152550,
    invoiceType: '普票',
    status: 'draft',
    issueDate: null,
    dueDate: '2026-01-20',
    paymentStatus: 'pending',
    paidAmount: 0,
    paidDate: null,
    notes: '签约款发票',
  },
]

const statusConfig = {
  draft: { label: '草稿', color: 'bg-slate-500/20 text-slate-400', icon: FileText },
  applied: { label: '申请中', color: 'bg-blue-500/20 text-blue-400', icon: Clock },
  approved: {
    label: '已批准',
    color: 'bg-purple-500/20 text-purple-400',
    icon: Check,
  },
  issued: {
    label: '已开票',
    color: 'bg-emerald-500/20 text-emerald-400',
    icon: Check,
  },
  void: { label: '作废', color: 'bg-red-500/20 text-red-400', icon: X },
}

const paymentStatusConfig = {
  pending: {
    label: '未收款',
    color: 'bg-slate-500/20 text-slate-400',
    icon: Clock,
  },
  partial: {
    label: '部分收款',
    color: 'bg-amber-500/20 text-amber-400',
    icon: TrendingUp,
  },
  paid: {
    label: '已收款',
    color: 'bg-emerald-500/20 text-emerald-400',
    icon: Check,
  },
  overdue: {
    label: '已逾期',
    color: 'bg-red-500/20 text-red-400',
    icon: AlertTriangle,
  },
}

const InvoiceRow = ({ invoice, onView, onEdit, onDelete }) => {
  const invoiceConfig = statusConfig[invoice.status]
  const paymentConfig = paymentStatusConfig[invoice.paymentStatus]
  const InvoiceIcon = invoiceConfig.icon
  const PaymentIcon = paymentConfig.icon

  return (
    <motion.div
      variants={fadeIn}
      className="group flex items-center justify-between rounded-lg border border-slate-700/50 bg-slate-800/40 px-4 py-3 transition-all hover:border-slate-600 hover:bg-slate-800/60"
    >
      <div className="flex flex-1 items-center gap-4">
        {/* Checkbox */}
        <input type="checkbox" className="h-4 w-4 rounded cursor-pointer" />

        {/* Invoice Info */}
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <span className="font-semibold text-slate-100">{invoice.id}</span>
            <span className="text-sm text-slate-400">{invoice.projectName}</span>
          </div>
          <div className="mt-1 flex items-center gap-3 text-sm">
            <span className="text-slate-500">{invoice.customerName}</span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-500">{invoice.invoiceType}</span>
            {invoice.issueDate && (
              <>
                <span className="text-slate-600">|</span>
                <span className="text-slate-500">{invoice.issueDate}</span>
              </>
            )}
          </div>
        </div>

        {/* Amount */}
        <div className="flex flex-col items-end gap-1">
          <p className="font-semibold text-amber-400">
            {formatCurrency(invoice.totalAmount)}
          </p>
          <p className="text-xs text-slate-500">含税</p>
        </div>

        {/* Status Badges */}
        <div className="ml-4 flex flex-col gap-2">
          <Badge className={cn('text-xs', invoiceConfig.color)}>
            <InvoiceIcon className="mr-1 h-3 w-3" />
            {invoiceConfig.label}
          </Badge>
          <Badge className={cn('text-xs', paymentConfig.color)}>
            <PaymentIcon className="mr-1 h-3 w-3" />
            {paymentConfig.label}
          </Badge>
        </div>

        {/* Actions */}
        <div className="ml-4 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <Button
            size="sm"
            variant="ghost"
            className="h-8 w-8 p-0"
            onClick={() => onView(invoice)}
          >
            <FileText className="h-4 w-4 text-blue-400" />
          </Button>
          {invoice.status === 'draft' && (
            <Button
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              onClick={() => onEdit(invoice)}
            >
              <FileText className="h-4 w-4 text-amber-400" />
            </Button>
          )}
          <Button size="sm" variant="ghost" className="h-8 w-8 p-0">
            <Download className="h-4 w-4 text-slate-400" />
          </Button>
        </div>
      </div>
    </motion.div>
  )
}

export default function InvoiceManagement() {
  const [invoices] = useState(mockInvoices)
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterPayment, setFilterPayment] = useState('all')

  const filteredInvoices = useMemo(() => {
    return invoices.filter((invoice) => {
      const matchSearch =
        invoice.id.toLowerCase().includes(searchText.toLowerCase()) ||
        invoice.projectName.toLowerCase().includes(searchText.toLowerCase()) ||
        invoice.customerName.toLowerCase().includes(searchText.toLowerCase())

      const matchStatus =
        filterStatus === 'all' || invoice.status === filterStatus
      const matchPayment =
        filterPayment === 'all' || invoice.paymentStatus === filterPayment

      return matchSearch && matchStatus && matchPayment
    })
  }, [invoices, searchText, filterStatus, filterPayment])

  const stats = {
    totalInvoices: invoices.length,
    totalAmount: invoices.reduce((sum, inv) => sum + inv.totalAmount, 0),
    paidAmount: invoices.reduce(
      (sum, inv) => sum + (inv.paymentStatus === 'paid' ? inv.totalAmount : 0),
      0
    ),
    pendingAmount: invoices.reduce(
      (sum, inv) =>
        sum +
        (inv.paymentStatus === 'pending' || inv.paymentStatus === 'overdue'
          ? inv.totalAmount
          : 0),
      0
    ),
  }

  return (
    <div className="space-y-6 pb-8">
      <PageHeader
        title="对账开票管理"
        description="发票申请、开票、收款跟踪"
        action={{
          label: '新建发票',
          icon: Plus,
          onClick: () => console.log('New invoice'),
        }}
      />

      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4"
      >
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">发票总数</p>
              <p className="text-3xl font-bold text-blue-400">
                {stats.totalInvoices}
              </p>
              <p className="text-xs text-slate-500">份</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">发票总金额</p>
              <p className="text-2xl font-bold text-amber-400">
                {formatCurrency(stats.totalAmount)}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">已收款</p>
              <p className="text-2xl font-bold text-emerald-400">
                {formatCurrency(stats.paidAmount)}
              </p>
              <p className="text-xs text-slate-500">
                {(
                  (stats.paidAmount / stats.totalAmount) *
                  100
                ).toFixed(1)}%
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="space-y-2">
              <p className="text-sm text-slate-400">待收款</p>
              <p className="text-2xl font-bold text-red-400">
                {formatCurrency(stats.pendingAmount)}
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
              <Input
                placeholder="搜索发票号、项目名、客户名..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filter Buttons */}
            <div className="flex flex-wrap gap-2">
              <Button
                variant={filterStatus === 'all' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilterStatus('all')}
              >
                全部状态
              </Button>
              {Object.entries(statusConfig).map(([key, config]) => (
                <Button
                  key={key}
                  variant={filterStatus === key ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setFilterStatus(key)}
                  className={cn(filterStatus === key && config.color)}
                >
                  {config.label}
                </Button>
              ))}
              <div className="w-full border-t border-slate-700/30" />
              <Button
                variant={filterPayment === 'all' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setFilterPayment('all')}
              >
                全部收款状态
              </Button>
              {Object.entries(paymentStatusConfig).map(([key, config]) => (
                <Button
                  key={key}
                  variant={filterPayment === key ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setFilterPayment(key)}
                  className={cn(filterPayment === key && config.color)}
                >
                  {config.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Invoice List */}
      <Card>
        <CardHeader>
          <CardTitle>发票列表</CardTitle>
          <p className="mt-2 text-sm text-slate-400">
            共 {filteredInvoices.length} 份发票
          </p>
        </CardHeader>
        <CardContent>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-2"
          >
            <AnimatePresence>
              {filteredInvoices.length > 0 ? (
                filteredInvoices.map((invoice) => (
                  <InvoiceRow
                    key={invoice.id}
                    invoice={invoice}
                    onView={(inv) => console.log('View', inv)}
                    onEdit={(inv) => console.log('Edit', inv)}
                    onDelete={(inv) => console.log('Delete', inv)}
                  />
                ))
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="py-12 text-center"
                >
                  <p className="text-slate-400">没有符合条件的发票</p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {filteredInvoices.length > 0 && (
        <Card className="bg-blue-500/10 border-blue-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-300">
                已选择 0 / {filteredInvoices.length} 份发票
              </p>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-2"
                >
                  <Send className="h-4 w-4" />
                  批量发送
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  批量下载
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-2 text-red-400 hover:text-red-300"
                >
                  <X className="h-4 w-4" />
                  取消选择
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
