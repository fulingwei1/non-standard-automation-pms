/**
 * Contract Approval Page - Contract approval workflow for sales directors
 * Features: Pending approvals, Approval history, Contract review, Approval actions
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileCheck,
  Search,
  Filter,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Eye,
  FileText,
  Building2,
  DollarSign,
  Calendar,
  User,
  ChevronRight,
  Download,
  Send,
  MessageSquare,
  History,
  Shield,
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Textarea,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock approval data
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

const typeConfig = {
  contract: { label: '合同', color: 'bg-blue-500', textColor: 'text-blue-400', icon: FileCheck },
  quotation: { label: '报价', color: 'bg-purple-500', textColor: 'text-purple-400', icon: FileText },
  discount: { label: '优惠', color: 'bg-red-500', textColor: 'text-red-400', icon: DollarSign },
}

const priorityConfig = {
  high: { label: '紧急', color: 'bg-red-500', textColor: 'text-red-400' },
  medium: { label: '普通', color: 'bg-amber-500', textColor: 'text-amber-400' },
  low: { label: '低', color: 'bg-slate-500', textColor: 'text-slate-400' },
}

export default function ContractApproval() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedApproval, setSelectedApproval] = useState(null)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [approvalComments, setApprovalComments] = useState('')
  const [activeTab, setActiveTab] = useState('pending')

// Mock data - 已移除，使用真实API
const [pendingApprovals, setPendingApprovals] = useState([])
const [approvalHistory, setApprovalHistory] = useState([])


  const filteredApprovals = useMemo(() => {
    const approvals = activeTab === 'pending' ? pendingApprovals : approvalHistory
    if (!searchTerm) return approvals
    return approvals.filter(item =>
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.submitter.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [searchTerm, activeTab])

  const handleViewDetail = (approval) => {
    setSelectedApproval(approval)
    setShowDetailDialog(true)
  }

  const handleApprove = () => {
    // TODO: Implement approval logic
    // TODO: Call API to approve
    setShowDetailDialog(false)
    setApprovalComments('')
  }

  const handleReject = () => {
    // TODO: Implement rejection logic
    // TODO: Call API to reject
    setShowDetailDialog(false)
    setApprovalComments('')
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
        title="合同审批"
        description={`待审批: ${mockPendingApprovals.length}项 | 已审批: ${mockApprovalHistory.length}项`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              筛选
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <History className="w-4 h-4" />
              审批历史
            </Button>
          </motion.div>
        }
      />

      {/* Stats Cards */}
      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/5 border-amber-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">待审批</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {mockPendingApprovals.length}
                </p>
                <p className="text-xs text-slate-500 mt-1">项待处理</p>
              </div>
              <div className="p-2 bg-amber-500/20 rounded-lg">
                <Clock className="w-5 h-5 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">待审批金额</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {formatCurrency(mockPendingApprovals.reduce((sum, a) => sum + a.totalAmount, 0))}
                </p>
                <p className="text-xs text-slate-500 mt-1">合同总金额</p>
              </div>
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <DollarSign className="w-5 h-5 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-500/10 to-green-500/5 border-emerald-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">已批准</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {mockApprovalHistory.filter(h => h.status === 'approved').length}
                </p>
                <p className="text-xs text-slate-500 mt-1">本月已批准</p>
              </div>
              <div className="p-2 bg-emerald-500/20 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-500/10 to-pink-500/5 border-red-500/20">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400">已拒绝</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {mockApprovalHistory.filter(h => h.status === 'rejected').length}
                </p>
                <p className="text-xs text-slate-500 mt-1">本月已拒绝</p>
              </div>
              <div className="p-2 bg-red-500/20 rounded-lg">
                <XCircle className="w-5 h-5 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Search */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardContent className="p-4">
            <div className="relative">
              <Input
                placeholder="搜索合同、客户或提交人..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Approval List */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList>
                <TabsTrigger value="pending">
                  待审批 ({mockPendingApprovals.length})
                </TabsTrigger>
                <TabsTrigger value="history">
                  审批历史 ({mockApprovalHistory.length})
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsContent value="pending" className="space-y-4">
                {filteredApprovals.map((approval) => {
                  const typeInfo = typeConfig[approval.type]
                  const priorityInfo = priorityConfig[approval.priority]
                  const TypeIcon = typeInfo.icon
                  return (
                    <div
                      key={approval.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-start gap-3 flex-1">
                          <div className={cn('p-2 rounded-lg', typeInfo.color + '/20')}>
                            <TypeIcon className={cn('w-5 h-5', typeInfo.textColor)} />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-white">{approval.title}</span>
                              <Badge
                                variant="outline"
                                className={cn('text-xs', typeInfo.textColor)}
                              >
                                {typeInfo.label}
                              </Badge>
                              <Badge
                                variant="outline"
                                className={cn('text-xs', priorityInfo.textColor)}
                              >
                                {priorityInfo.label}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-4 text-xs text-slate-400">
                              <span className="flex items-center gap-1">
                                <Building2 className="w-3 h-3" />
                                {approval.customerShort}
                              </span>
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {approval.submitter}
                              </span>
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {approval.submitTime}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right mr-4">
                          <div className="text-lg font-bold text-white">
                            {formatCurrency(approval.totalAmount)}
                          </div>
                          {approval.originalAmount && (
                            <div className="text-xs text-slate-400 line-through">
                              {formatCurrency(approval.originalAmount)}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewDetail(approval)}
                          className="flex items-center gap-2"
                        >
                          <Eye className="w-4 h-4" />
                          查看详情
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleViewDetail(approval)}
                          className="flex items-center gap-2"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                          审批
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </TabsContent>
              <TabsContent value="history" className="space-y-4">
                {filteredApprovals.map((approval) => {
                  const typeInfo = typeConfig[approval.type]
                  const TypeIcon = typeInfo.icon
                  return (
                    <div
                      key={approval.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <div className={cn('p-2 rounded-lg', typeInfo.color + '/20')}>
                            <TypeIcon className={cn('w-5 h-5', typeInfo.textColor)} />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-white">{approval.title}</span>
                              <Badge
                                variant="outline"
                                className={cn(
                                  'text-xs',
                                  approval.status === 'approved'
                                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                                    : 'bg-red-500/20 text-red-400 border-red-500/30'
                                )}
                              >
                                {approval.status === 'approved' ? '已批准' : '已拒绝'}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-4 text-xs text-slate-400">
                              <span>{approval.customerName}</span>
                              <span>{approval.submitter}</span>
                              <span>审批: {approval.approver}</span>
                              <span>{approval.approveTime}</span>
                            </div>
                            {approval.comments && (
                              <p className="text-xs text-slate-500 mt-2">{approval.comments}</p>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-white">
                            {formatCurrency(approval.amount)}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>

      {/* Approval Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>审批详情</DialogTitle>
            <DialogDescription>
              查看详细信息并做出审批决定
            </DialogDescription>
          </DialogHeader>
          {selectedApproval && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">类型</p>
                  <p className="text-white font-medium">
                    {typeConfig[selectedApproval.type].label}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">优先级</p>
                  <Badge
                    variant="outline"
                    className={cn(
                      'text-xs',
                      priorityConfig[selectedApproval.priority].textColor
                    )}
                  >
                    {priorityConfig[selectedApproval.priority].label}
                  </Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-400">客户</p>
                  <p className="text-white font-medium">{selectedApproval.customerName}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">项目</p>
                  <p className="text-white font-medium">{selectedApproval.projectName}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">提交人</p>
                  <p className="text-white font-medium">{selectedApproval.submitter}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">提交时间</p>
                  <p className="text-white font-medium">{selectedApproval.submitTime}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-sm text-slate-400">金额</p>
                  <p className="text-2xl font-bold text-white">
                    {formatCurrency(selectedApproval.totalAmount)}
                  </p>
                  {selectedApproval.originalAmount && (
                    <p className="text-sm text-slate-400 line-through">
                      原价: {formatCurrency(selectedApproval.originalAmount)}
                    </p>
                  )}
                </div>
              </div>

              {selectedApproval.description && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">描述</p>
                  <p className="text-white">{selectedApproval.description}</p>
                </div>
              )}

              {selectedApproval.paymentTerms && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">付款条款</p>
                  <div className="space-y-2">
                    {selectedApproval.paymentTerms.map((term, index) => (
                      <div
                        key={index}
                        className="p-2 bg-slate-800/40 rounded border border-slate-700/50"
                      >
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-white">
                            {term.type === 'deposit' ? '签约款' :
                             term.type === 'progress' ? '进度款' :
                             term.type === 'acceptance' ? '验收款' :
                             '质保金'} - {term.percent}%
                          </span>
                          <span className="text-white font-medium">
                            {formatCurrency(term.amount)}
                          </span>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                          到期日: {term.dueDate}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedApproval.attachments && selectedApproval.attachments.length > 0 && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">附件</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedApproval.attachments.map((file, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        <FileText className="w-4 h-4" />
                        {file}
                        <Download className="w-3 h-3" />
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              {selectedApproval.notes && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">备注</p>
                  <p className="text-white">{selectedApproval.notes}</p>
                </div>
              )}

              <div>
                <p className="text-sm text-slate-400 mb-2">审批意见</p>
                <Textarea
                  placeholder="请输入审批意见..."
                  value={approvalComments}
                  onChange={(e) => setApprovalComments(e.target.value)}
                  rows={4}
                />
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              className="flex items-center gap-2"
            >
              <XCircle className="w-4 h-4" />
              拒绝
            </Button>
            <Button onClick={handleApprove} className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              批准
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}

