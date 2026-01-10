/**
 * Contract List Page - Contract management for sales
 * Features: Contract list, status tracking, payment milestones
 */

import { useState, useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileSignature,
  Search,
  Plus,
  Filter,
  List,
  LayoutGrid,
  Calendar,
  DollarSign,
  Building2,
  User,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Download,
  Eye,
  Edit,
  ChevronRight,
  X,
  FileText,
  Milestone,
  Paperclip,
  Shield,
  Loader2,
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
import { contractApi } from '../services/api'

// Status configuration
const statusConfig = {
  draft: { label: '草稿', color: 'bg-slate-500', textColor: 'text-slate-400' },
  pending_sign: { label: '待签约', color: 'bg-amber-500', textColor: 'text-amber-400' },
  active: { label: '执行中', color: 'bg-blue-500', textColor: 'text-blue-400' },
  completed: { label: '已完成', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  terminated: { label: '已终止', color: 'bg-red-500', textColor: 'text-red-400' },
}

// Mock contract data
// Mock data - 已移除，使用真实API
const paymentTypeLabels = {
  deposit: '签约款',
  progress: '进度款',
  delivery: '发货款',
  acceptance: '验收款',
  warranty: '质保金',
}

export default function ContractList() {
  const [loading, setLoading] = useState(true)
  const [contracts, setContracts] = useState(mockContracts)
  const [viewMode, setViewMode] = useState('list')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [selectedContract, setSelectedContract] = useState(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)

  // Load data from API with fallback to mock data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const res = await contractApi.list()
        if (res.data?.items || res.data) {
          setContracts(res.data?.items || res.data)
        }
      } catch (err) {
        console.log('Contract API unavailable, using mock data')
      }
      setLoading(false)
    }
    fetchData()
  }, [])

  // Filter contracts
  const filteredContracts = useMemo(() => {
    return contracts.filter(contract => {
      const matchesSearch = !searchTerm ||
        contract.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        contract.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (contract.customerShort || '').toLowerCase().includes(searchTerm.toLowerCase())

      const matchesStatus = selectedStatus === 'all' || contract.status === selectedStatus

      return matchesSearch && matchesStatus
    })
  }, [contracts, searchTerm, selectedStatus])

  // Stats
  const stats = useMemo(() => {
    const active = contracts.filter(c => c.status === 'active')
    return {
      total: contracts.length,
      active: active.length,
      completed: contracts.filter(c => c.status === 'completed').length,
      totalValue: active.reduce((sum, c) => sum + (c.totalAmount || 0), 0),
      paidValue: active.reduce((sum, c) => sum + (c.paidAmount || 0), 0),
      pendingValue: active.reduce((sum, c) => sum + ((c.totalAmount || 0) - (c.paidAmount || 0)), 0),
    }
  }, [contracts])

  const handleContractClick = (contract) => {
    setSelectedContract(contract)
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
        title="合同管理"
        description="管理销售合同和付款条款"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出
            </Button>
            <Button className="flex items-center gap-2" onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4" />
              新建合同
            </Button>
          </motion.div>
        }
      />

      {/* Stats Row */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <FileSignature className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">{stats.active}</p>
              <p className="text-xs text-slate-400">执行中合同</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-amber-500/20 rounded-lg">
              <DollarSign className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                ¥{(stats.totalValue / 10000).toFixed(0)}万
              </p>
              <p className="text-xs text-slate-400">合同总额</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-emerald-500/20 rounded-lg">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-emerald-400">
                ¥{(stats.paidValue / 10000).toFixed(0)}万
              </p>
              <p className="text-xs text-slate-400">已回款</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Clock className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-400">
                ¥{(stats.pendingValue / 10000).toFixed(0)}万
              </p>
              <p className="text-xs text-slate-400">待回款</p>
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
              placeholder="搜索合同号、名称..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
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

        <span className="text-sm text-slate-400">
          共 {filteredContracts.length} 份合同
        </span>
      </motion.div>

      {/* Content */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardContent className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left p-4 text-sm font-medium text-slate-400">合同</th>
                  <th className="text-left p-4 text-sm font-medium text-slate-400">客户</th>
                  <th className="text-right p-4 text-sm font-medium text-slate-400">合同金额</th>
                  <th className="text-center p-4 text-sm font-medium text-slate-400">回款进度</th>
                  <th className="text-left p-4 text-sm font-medium text-slate-400">签约日期</th>
                  <th className="text-left p-4 text-sm font-medium text-slate-400">交付日期</th>
                  <th className="text-left p-4 text-sm font-medium text-slate-400">状态</th>
                  <th className="text-center p-4 text-sm font-medium text-slate-400">操作</th>
                </tr>
              </thead>
              <tbody>
                {filteredContracts.map((contract) => {
                  const statusConf = statusConfig[contract.status]
                  const paymentProgress = contract.totalAmount > 0 
                    ? (contract.paidAmount / contract.totalAmount * 100) 
                    : 0

                  return (
                    <tr
                      key={contract.id}
                      onClick={() => handleContractClick(contract)}
                      className="border-b border-white/5 hover:bg-surface-100 cursor-pointer transition-colors"
                    >
                      <td className="p-4">
                        <div>
                          <div className="font-medium text-white">{contract.name}</div>
                          <div className="text-xs text-slate-500">{contract.id}</div>
                        </div>
                      </td>
                      <td className="p-4 text-sm text-slate-400">{contract.customerShort}</td>
                      <td className="p-4 text-right">
                        <span className="font-medium text-amber-400">
                          ¥{(contract.totalAmount / 10000).toFixed(0)}万
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <Progress value={paymentProgress} className="w-20 h-2" />
                          <span className="text-xs text-slate-400">
                            {paymentProgress.toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="p-4 text-sm text-slate-400">
                        {contract.signDate || '-'}
                      </td>
                      <td className="p-4 text-sm text-slate-400">
                        {contract.deliveryDate || '-'}
                      </td>
                      <td className="p-4">
                        <Badge className={cn('text-xs', statusConf.textColor, 'bg-transparent border-0')}>
                          <div className={cn('w-2 h-2 rounded-full mr-1', statusConf.color)} />
                          {statusConf.label}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <div className="flex justify-center gap-1">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Download className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>

        {filteredContracts.length === 0 && (
          <div className="text-center py-16">
            <FileSignature className="w-12 h-12 mx-auto text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">暂无合同</h3>
            <p className="text-slate-400 mb-4">没有找到符合条件的合同</p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              新建合同
            </Button>
          </div>
        )}
      </motion.div>

      {/* Contract Detail Panel */}
      <AnimatePresence>
        {selectedContract && (
          <ContractDetailPanel
            contract={selectedContract}
            onClose={() => setSelectedContract(null)}
          />
        )}
      </AnimatePresence>

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建合同</DialogTitle>
            <DialogDescription>
              创建新的销售合同
            </DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="col-span-2 space-y-2">
              <label className="text-sm text-slate-400">合同名称 *</label>
              <Input placeholder="请输入合同名称" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">关联报价单</label>
              <select className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white">
                <option value="">请选择报价单</option>
                <option value="QT2026010001">QT2026010001 - BMS老化测试设备报价</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">合同金额</label>
              <Input type="number" placeholder="请输入合同金额" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">交付日期</label>
              <Input type="date" />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-400">质保期(月)</label>
              <Input type="number" defaultValue={12} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={() => setShowCreateDialog(false)}>
              创建合同
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

// Contract Detail Panel
function ContractDetailPanel({ contract, onClose }) {
  const statusConf = statusConfig[contract.status]
  const paymentProgress = contract.totalAmount > 0 
    ? (contract.paidAmount / contract.totalAmount * 100) 
    : 0

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-full md:w-[500px] bg-surface-100/95 backdrop-blur-xl border-l border-white/5 shadow-2xl z-50 flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-semibold text-white">{contract.name}</h2>
            </div>
            <p className="text-sm text-slate-400">{contract.id}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
        <div className="flex items-center gap-2 mt-3">
          <Badge className={cn('text-xs', statusConf.textColor, 'bg-transparent border-0')}>
            <div className={cn('w-2 h-2 rounded-full mr-1', statusConf.color)} />
            {statusConf.label}
          </Badge>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Amount Summary */}
        <div className="p-4 bg-gradient-to-br from-amber-500/10 to-orange-500/5 border border-amber-500/20 rounded-xl">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-sm text-slate-400">合同金额</div>
              <div className="text-2xl font-bold text-amber-400">
                ¥{(contract.totalAmount / 10000).toFixed(2)}万
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">回款进度</div>
              <div className="text-lg font-semibold text-emerald-400">
                {paymentProgress.toFixed(0)}%
              </div>
            </div>
          </div>
          <Progress value={paymentProgress} className="h-2" />
          <div className="flex justify-between text-xs text-slate-400 mt-2">
            <span>已收: ¥{(contract.paidAmount / 10000).toFixed(1)}万</span>
            <span>待收: ¥{((contract.totalAmount - contract.paidAmount) / 10000).toFixed(1)}万</span>
          </div>
        </div>

        {/* Basic Info */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-400">基本信息</h3>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-3">
              <Building2 className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">客户:</span>
              <span className="text-white">{contract.customerShort}</span>
            </div>
            {contract.projectName && (
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-slate-500" />
                <span className="text-slate-400">项目:</span>
                <span className="text-blue-400">{contract.projectName}</span>
              </div>
            )}
            <div className="flex items-center gap-3">
              <Calendar className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">签约日期:</span>
              <span className="text-white">{contract.signDate || '-'}</span>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">交付日期:</span>
              <span className="text-white">{contract.deliveryDate || '-'}</span>
            </div>
            <div className="flex items-center gap-3">
              <Shield className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">质保期:</span>
              <span className="text-white">{contract.warrantyMonths}个月 (至 {contract.warrantyEndDate || '-'})</span>
            </div>
            <div className="flex items-center gap-3">
              <User className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400">销售:</span>
              <span className="text-white">{contract.salesPerson}</span>
            </div>
          </div>
        </div>

        {/* Payment Terms */}
        {contract.paymentTerms.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">付款条款</h3>
            <div className="space-y-2">
              {contract.paymentTerms.map((term, index) => {
                const isPaid = term.status === 'paid'
                const isOverdue = term.status === 'overdue' || 
                  (term.status === 'pending' && term.dueDate && new Date(term.dueDate) < new Date())

                return (
                  <div 
                    key={index}
                    className={cn(
                      'p-3 rounded-lg border',
                      isPaid ? 'bg-emerald-500/10 border-emerald-500/20' :
                      isOverdue ? 'bg-red-500/10 border-red-500/20' :
                      'bg-surface-50 border-white/5'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {isPaid ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        ) : isOverdue ? (
                          <AlertTriangle className="w-4 h-4 text-red-400" />
                        ) : (
                          <Clock className="w-4 h-4 text-slate-400" />
                        )}
                        <span className="text-sm text-white">
                          {paymentTypeLabels[term.type]} ({term.percent}%)
                        </span>
                      </div>
                      <span className={cn(
                        'text-sm font-medium',
                        isPaid ? 'text-emerald-400' : 
                        isOverdue ? 'text-red-400' : 'text-amber-400'
                      )}>
                        ¥{(term.amount / 10000).toFixed(1)}万
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {isPaid ? (
                        <span className="text-emerald-400">已收款: {term.paidDate}</span>
                      ) : (
                        <span className={isOverdue ? 'text-red-400' : ''}>
                          应收日期: {term.dueDate || '-'}
                          {isOverdue && ' (已逾期)'}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Attachments */}
        {contract.attachments.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-slate-400">合同附件</h3>
            <div className="space-y-2">
              {contract.attachments.map((file, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 bg-surface-50 rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    <Paperclip className="w-4 h-4 text-slate-400" />
                    <span className="text-sm text-white">{file}</span>
                  </div>
                  <Button variant="ghost" size="sm">
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        {contract.notes && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-slate-400">备注</h3>
            <p className="text-sm text-white bg-surface-50 p-3 rounded-lg">
              {contract.notes}
            </p>
          </div>
        )}

        {/* Terminate Reason */}
        {contract.terminateReason && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <XCircle className="w-4 h-4" />
              终止原因: {contract.terminateReason}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-white/5 flex gap-2">
        <Button variant="outline" className="flex-1" onClick={onClose}>
          关闭
        </Button>
        {contract.status === 'active' && (
          <Button className="flex-1">
            <Edit className="w-4 h-4 mr-2" />
            编辑
          </Button>
        )}
      </div>
    </motion.div>
  )
}

