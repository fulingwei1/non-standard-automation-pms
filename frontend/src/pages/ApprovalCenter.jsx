import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ClipboardCheck,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Search,
  Filter,
  FileText,
  Package,
  DollarSign,
  Users,
  Wrench,
  ChevronRight,
  MessageSquare,
  Eye,
  Check,
  X,
  RotateCcw,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog'
import { cn, formatDate } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { 
  ecnApi, 
  purchaseApi, 
  quoteApi,
  contractApi,
  invoiceApi,
  pmoApi
} from '../services/api'
import { toast } from '../components/ui/toast'
import { LoadingCard, ErrorMessage, EmptyState } from '../components/common'
import { ApiIntegrationError } from '../components/ui'

// Mock approval data - 已移除，使用真实API


const typeConfigs = {
  ecn: { label: '设计变更', icon: Wrench, color: 'text-purple-400', bgColor: 'bg-purple-500/10' },
  purchase: { label: '采购申请', icon: Package, color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  overtime: { label: '加班申请', icon: Clock, color: 'text-amber-400', bgColor: 'bg-amber-500/10' },
  leave: { label: '请假申请', icon: Users, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10' },
  payment: { label: '付款申请', icon: DollarSign, color: 'text-cyan-400', bgColor: 'bg-cyan-500/10' },
}

const statusConfigs = {
  pending: { label: '待审批', color: 'bg-amber-500', textColor: 'text-amber-400' },
  approved: { label: '已通过', color: 'bg-emerald-500', textColor: 'text-emerald-400' },
  rejected: { label: '已驳回', color: 'bg-red-500', textColor: 'text-red-400' },
  waiting: { label: '等待中', color: 'bg-slate-500', textColor: 'text-slate-400' },
}

const priorityConfigs = {
  normal: { label: '普通', color: 'border-slate-500 text-slate-400' },
  high: { label: '紧急', color: 'border-amber-500 text-amber-400' },
  urgent: { label: '特急', color: 'border-red-500 text-red-400' },
}

function ApprovalCard({ approval, onView, onApprove, onReject }) {
  const type = typeConfigs[approval.type]
  const status = statusConfigs[approval.status]
  const priority = priorityConfigs[approval.priority]
  const TypeIcon = type.icon

  const isPending = approval.status === 'pending'
  const currentStep = approval.approvalFlow.findIndex((step) => step.status === 'pending')

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className={cn(
        'rounded-xl border overflow-hidden transition-colors',
        isPending ? 'bg-surface-1 border-border' : 'bg-surface-1/50 border-border/50'
      )}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          <div className={cn('p-2 rounded-lg', type.bgColor)}>
            <TypeIcon className={cn('w-5 h-5', type.color)} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline" className={cn('text-[10px]', type.color)}>
                {type.label}
              </Badge>
              {approval.priority !== 'normal' && (
                <Badge variant="outline" className={cn('text-[10px] border', priority.color)}>
                  {priority.label}
                </Badge>
              )}
              <Badge className={cn('text-[10px] ml-auto', status.color)}>
                {status.label}
              </Badge>
            </div>
            <h3 className="font-medium text-white">{approval.title}</h3>
          </div>
        </div>

        {/* Project & Applicant */}
        <div className="text-sm text-slate-400 mb-3">
          <div className="flex items-center gap-4">
            <span>申请人：{approval.applicant}</span>
            <span>·</span>
            <span>{approval.applicantDept}</span>
          </div>
          {approval.projectId && (
            <div className="flex items-center gap-2 mt-1">
              <span className="text-accent">{approval.projectId}</span>
              <span>·</span>
              <span className="truncate">{approval.projectName}</span>
            </div>
          )}
        </div>

        {/* Description */}
        <p className="text-sm text-slate-300 mb-3 line-clamp-2">{approval.description}</p>

        {/* Impact (for ECN) */}
        {approval.impact && (
          <div className="flex gap-3 mb-3 text-xs">
            <span className="px-2 py-1 rounded bg-surface-2 text-slate-400">
              成本：<span className="text-amber-400">{approval.impact.cost}</span>
            </span>
            <span className="px-2 py-1 rounded bg-surface-2 text-slate-400">
              工期：<span className="text-amber-400">{approval.impact.schedule}</span>
            </span>
          </div>
        )}

        {/* Amount (for Purchase) */}
        {approval.amount && (
          <div className="mb-3">
            <span className="text-2xl font-bold text-white">
              ¥{approval.amount.toLocaleString()}
            </span>
          </div>
        )}

        {/* Reject Reason */}
        {approval.rejectReason && (
          <div className="p-2 rounded-lg bg-red-500/10 text-xs text-red-300 mb-3 flex items-center gap-2">
            <XCircle className="w-3 h-3" />
            驳回原因：{approval.rejectReason}
          </div>
        )}

        {/* Approval Flow Preview */}
        <div className="flex items-center gap-2 mb-3">
          {approval.approvalFlow.map((step, index) => (
            <div key={index} className="flex items-center gap-1">
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-[10px]',
                  step.status === 'approved'
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : step.status === 'rejected'
                    ? 'bg-red-500/20 text-red-400'
                    : step.status === 'pending'
                    ? 'bg-amber-500/20 text-amber-400 ring-2 ring-amber-500/50'
                    : 'bg-surface-2 text-slate-500'
                )}
              >
                {step.status === 'approved' ? (
                  <Check className="w-3 h-3" />
                ) : step.status === 'rejected' ? (
                  <X className="w-3 h-3" />
                ) : (
                  index + 1
                )}
              </div>
              {index < approval.approvalFlow.length - 1 && (
                <ChevronRight className="w-3 h-3 text-slate-600" />
              )}
            </div>
          ))}
        </div>

        {/* Time */}
        <div className="text-xs text-slate-500 mb-3">
          提交时间：{approval.submitTime}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-border/50">
          <Button variant="ghost" size="sm" onClick={() => onView(approval)}>
            <Eye className="w-4 h-4 mr-1" />
            查看详情
          </Button>
          {isPending && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="text-red-400 hover:text-red-300"
                onClick={() => onReject(approval)}
              >
                <X className="w-4 h-4 mr-1" />
                驳回
              </Button>
              <Button size="sm" onClick={() => onApprove(approval)}>
                <Check className="w-4 h-4 mr-1" />
                通过
              </Button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function ApprovalDetailDialog({ approval, open, onOpenChange, onApprove, onReject, comment, setComment }) {
  const [approvalHistory, setApprovalHistory] = useState([])
  const [approvalStatus, setApprovalStatus] = useState(null)
  const [loadingHistory, setLoadingHistory] = useState(false)
  
  useEffect(() => {
    if (open && approval) {
      loadApprovalDetails()
    }
  }, [open, approval])
  
  const loadApprovalDetails = async () => {
    if (!approval?.originalData) return
    
    try {
      setLoadingHistory(true)
      const { approvalType, originalData } = approval
      
      // Load approval status and history based on type
      if (approvalType === 'quote_workflow') {
        const statusRes = await quoteApi.getApprovalStatus(originalData.id)
        const historyRes = await quoteApi.getApprovalHistory(originalData.id)
        setApprovalStatus(statusRes.data || statusRes)
        setApprovalHistory(historyRes.data || historyRes || [])
      } else if (approvalType === 'contract_workflow') {
        const statusRes = await contractApi.getApprovalStatus(originalData.id)
        const historyRes = await contractApi.getApprovalHistory(originalData.id)
        setApprovalStatus(statusRes.data || statusRes)
        setApprovalHistory(historyRes.data || historyRes || [])
      } else if (approvalType === 'invoice_workflow') {
        const statusRes = await invoiceApi.getApprovalStatus(originalData.id)
        const historyRes = await invoiceApi.getApprovalHistory(originalData.id)
        setApprovalStatus(statusRes.data || statusRes)
        setApprovalHistory(historyRes.data || historyRes || [])
      }
    } catch (err) {
      console.error('Failed to load approval details:', err)
    } finally {
      setLoadingHistory(false)
    }
  }
  
  if (!approval) return null

  const type = typeConfigs[approval.type] || typeConfigs['ecn']
  const canApprove = approval.status === 'pending' && (
    approval.approvalType === 'quote_workflow' ||
    approval.approvalType === 'contract_workflow' ||
    approval.approvalType === 'invoice_workflow'
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <type.icon className={cn('w-5 h-5', type.color)} />
            {approval.title}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Basic Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <label className="text-xs text-slate-500">申请人</label>
              <p className="text-white">{approval.applicant} ({approval.applicantDept})</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">提交时间</label>
              <p className="text-white">{approval.submitTime}</p>
            </div>
            {approval.projectId && (
              <>
                <div>
                  <label className="text-xs text-slate-500">关联项目</label>
                  <p className="text-white">{approval.projectId}</p>
                </div>
                <div>
                  <label className="text-xs text-slate-500">项目名称</label>
                  <p className="text-white">{approval.projectName}</p>
                </div>
              </>
            )}
            {approval.amount && (
              <div>
                <label className="text-xs text-slate-500">金额</label>
                <p className="text-white">¥{(approval.amount / 10000).toFixed(0)}万</p>
              </div>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="text-xs text-slate-500">申请说明</label>
            <p className="text-white mt-1">{approval.description}</p>
          </div>

          {/* Approval Flow Progress - Issue 5.2: 审批流程进度可视化 */}
          {approval.approvalFlow && approval.approvalFlow.length > 0 && (
            <div>
              <label className="text-xs text-slate-500 mb-2 block">审批流程进度</label>
              <div className="space-y-2">
                {approval.approvalFlow.map((step, index) => {
                  const isCurrent = step.step_order === approval.currentStep?.step_order
                  const isCompleted = step.status === 'APPROVED'
                  const isRejected = step.status === 'REJECTED'
                  
                  return (
                    <div key={step.id || index} className="flex items-center gap-3 p-2 rounded-lg bg-surface-50">
                      <div className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold',
                        isCompleted ? 'bg-emerald-500 text-white' :
                        isRejected ? 'bg-red-500 text-white' :
                        isCurrent ? 'bg-amber-500 text-white' :
                        'bg-slate-600 text-slate-300'
                      )}>
                        {isCompleted ? '✓' : isRejected ? '✗' : index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-white">{step.step_name || `审批步骤 ${index + 1}`}</span>
                          <Badge variant={isCompleted ? 'default' : isRejected ? 'destructive' : isCurrent ? 'secondary' : 'outline'}>
                            {isCompleted ? '已通过' : isRejected ? '已驳回' : isCurrent ? '待审批' : '待处理'}
                          </Badge>
                        </div>
                        {step.approver_name && (
                          <span className="text-xs text-slate-400">审批人: {step.approver_name}</span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Approval History - Issue 5.2: 审批历史记录 */}
          {approvalHistory.length > 0 && (
            <div>
              <label className="text-xs text-slate-500 mb-2 block">审批历史</label>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {approvalHistory.map((history, index) => (
                  <div key={history.id || index} className="p-2 rounded-lg bg-surface-50 text-sm">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-white">{history.action || history.status}</span>
                      <span className="text-xs text-slate-400">
                        {history.created_at ? formatDate(history.created_at) : ''}
                      </span>
                    </div>
                    {history.approver_name && (
                      <span className="text-xs text-slate-400">审批人: {history.approver_name}</span>
                    )}
                    {history.comment && (
                      <p className="text-xs text-slate-300 mt-1">{history.comment}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Impact */}
          {approval.impact && (
            <div className="grid grid-cols-3 gap-4">
              <div className="p-3 rounded-lg bg-surface-2">
                <label className="text-xs text-slate-500">成本影响</label>
                <p className="text-amber-400 font-medium">{approval.impact.cost}</p>
              </div>
              <div className="p-3 rounded-lg bg-surface-2">
                <label className="text-xs text-slate-500">工期影响</label>
                <p className="text-amber-400 font-medium">{approval.impact.schedule}</p>
              </div>
              <div className="p-3 rounded-lg bg-surface-2">
                <label className="text-xs text-slate-500">影响范围</label>
                <p className="text-white font-medium">{approval.impact.scope}</p>
              </div>
            </div>
          )}

          {/* Approval Flow */}
          <div>
            <label className="text-xs text-slate-500 mb-2 block">审批流程</label>
            <div className="space-y-2">
              {approval.approvalFlow.map((step, index) => (
                <div
                  key={index}
                  className={cn(
                    'p-3 rounded-lg flex items-center justify-between',
                    step.status === 'pending'
                      ? 'bg-amber-500/10 border border-amber-500/30'
                      : 'bg-surface-2'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center',
                        step.status === 'approved'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : step.status === 'rejected'
                          ? 'bg-red-500/20 text-red-400'
                          : step.status === 'pending'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-surface-0 text-slate-500'
                      )}
                    >
                      {step.status === 'approved' ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : step.status === 'rejected' ? (
                        <XCircle className="w-4 h-4" />
                      ) : step.status === 'pending' ? (
                        <AlertCircle className="w-4 h-4" />
                      ) : (
                        <Clock className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm text-white">{step.role}</p>
                      <p className="text-xs text-slate-400">{step.user}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    {step.time && (
                      <p className="text-xs text-slate-500">{step.time}</p>
                    )}
                    {step.comment && (
                      <p className="text-xs text-slate-400">{step.comment}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Comment Input */}
          {approval.status === 'pending' && (
            <div>
              <label className="text-xs text-slate-500 mb-2 block">
                {onReject ? '审批意见（驳回时必填）' : '审批意见（可选）'}
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder={onReject ? '请输入驳回原因' : '请输入审批意见（可选）'}
                className="w-full h-20 px-3 py-2 rounded-lg bg-surface-2 border border-border text-white placeholder-slate-500 focus:border-accent focus:outline-none resize-none"
              />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {approval.status === 'pending' && (
            <>
              <Button
                variant="outline"
                className="text-red-400 hover:text-red-300"
                onClick={() => onReject(approval)}
              >
                驳回
              </Button>
              <Button onClick={() => onApprove(approval)}>通过</Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function ApprovalCenter() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [approvals, setApprovals] = useState([])
  const [statusFilter, setStatusFilter] = useState('pending')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedApproval, setSelectedApproval] = useState(null)
  const [showDetail, setShowDetail] = useState(false)
  const [approvalComment, setApprovalComment] = useState('')

  // Load approvals from various modules
  const loadApprovals = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const allApprovals = []
      
      // Load ECN approvals
      try {
        const ecnRes = await ecnApi.list({ status: 'SUBMITTED', page_size: 100 })
        const ecnData = ecnRes.data || ecnRes
        const ecns = ecnData.items || ecnData || []
        ecns.forEach(ecn => {
          allApprovals.push({
            id: `ecn-${ecn.id}`,
            type: 'ecn',
            title: `设计变更申请 - ${ecn.ecn_no || ecn.title || 'ECN'}`,
            applicant: ecn.created_by_name || '未知',
            applicantDept: ecn.department || '未知部门',
            submitTime: formatDate(ecn.created_at) || '',
            status: ecn.status === 'SUBMITTED' ? 'pending' : 
                    ecn.status === 'APPROVED' ? 'approved' : 
                    ecn.status === 'REJECTED' ? 'rejected' : 'waiting',
            priority: ecn.priority === 'URGENT' ? 'urgent' : 
                     ecn.priority === 'HIGH' ? 'high' : 'normal',
            projectId: ecn.project_code,
            projectName: ecn.project_name || '',
            description: ecn.description || ecn.change_reason || '',
            approvalFlow: [], // TODO: Load approval flow from API
            originalData: ecn,
            approvalType: 'ecn',
          })
        })
      } catch (err) {
        console.error('Failed to load ECN approvals:', err)
      }
      
      // Load Purchase Request approvals
      try {
        const prRes = await purchaseApi.requests.list({ status: 'SUBMITTED', page_size: 100 })
        const prData = prRes.data || prRes
        const prs = prData.items || prData || []
        prs.forEach(pr => {
          allApprovals.push({
            id: `pr-${pr.id}`,
            type: 'purchase',
            title: `采购申请 - ${pr.request_no || pr.id}`,
            applicant: pr.created_by_name || '未知',
            applicantDept: pr.department || '未知部门',
            submitTime: formatDate(pr.created_at) || '',
            status: pr.status === 'SUBMITTED' ? 'pending' : 
                    pr.status === 'APPROVED' ? 'approved' : 
                    pr.status === 'REJECTED' ? 'rejected' : 'waiting',
            priority: pr.urgent ? 'urgent' : 'normal',
            projectId: pr.project_code,
            projectName: pr.project_name || '',
            description: pr.remark || '',
            amount: parseFloat(pr.total_amount || 0),
            supplier: pr.supplier_name || '',
            approvalFlow: [],
            originalData: pr,
            approvalType: 'purchase_request',
          })
        })
      } catch (err) {
        console.error('Failed to load purchase request approvals:', err)
      }
      
      // Load Purchase Order approvals
      try {
        const poRes = await purchaseApi.orders.list({ status: 'SUBMITTED', page_size: 100 })
        const poData = poRes.data || poRes
        const pos = poData.items || poData || []
        pos.forEach(po => {
          allApprovals.push({
            id: `po-${po.id}`,
            type: 'purchase',
            title: `采购订单审批 - ${po.order_no || po.id}`,
            applicant: po.created_by_name || '未知',
            applicantDept: po.department || '未知部门',
            submitTime: formatDate(po.created_at) || '',
            status: po.status === 'SUBMITTED' ? 'pending' : 
                    po.status === 'APPROVED' ? 'approved' : 
                    po.status === 'REJECTED' ? 'rejected' : 'waiting',
            priority: po.urgent ? 'urgent' : 'normal',
            projectId: po.project_code,
            projectName: po.project_name || '',
            description: po.remark || '',
            amount: parseFloat(po.total_amount || po.amount_with_tax || 0),
            supplier: po.supplier_name || '',
            approvalFlow: [],
            originalData: po,
            approvalType: 'purchase_order',
          })
        })
      } catch (err) {
        console.error('Failed to load purchase order approvals:', err)
      }
      
      // Load Quote approvals (Sprint 2: New Approval Workflow)
      try {
        const quoteRes = await quoteApi.list({ status: 'SUBMITTED', page_size: 100 })
        const quoteData = quoteRes.data || quoteRes
        const quotes = quoteData.items || quoteData || []
        for (const quote of quotes) {
          // Check approval status
          let approvalStatus = null
          try {
            approvalStatus = await quoteApi.getApprovalStatus(quote.id)
          } catch (err) {
            console.warn(`Failed to get approval status for quote ${quote.id}:`, err)
          }
          
          const status = approvalStatus?.status || 'PENDING'
          const currentStep = approvalStatus?.current_step
          
          allApprovals.push({
            id: `quote-${quote.id}`,
            type: 'sales',
            title: `报价审批 - ${quote.quote_code || quote.id}`,
            applicant: quote.owner?.real_name || quote.owner_name || '未知',
            applicantDept: quote.department || '销售部',
            submitTime: formatDate(quote.created_at) || '',
            status: status === 'PENDING' ? 'pending' : 
                    status === 'APPROVED' ? 'approved' : 
                    status === 'REJECTED' ? 'rejected' : 'waiting',
            priority: parseFloat(quote.total_price || 0) > 1000000 ? 'urgent' : 'normal',
            projectId: quote.opportunity?.opp_code,
            projectName: quote.opportunity?.opp_name || quote.customer?.customer_name || '',
            description: quote.remark || '',
            amount: parseFloat(quote.total_price || 0),
            approvalFlow: approvalStatus?.steps || [],
            currentStep: currentStep,
            originalData: quote,
            approvalType: 'quote_workflow',
          })
        }
      } catch (err) {
        console.error('Failed to load quote approvals:', err)
      }
      
      // Load Contract approvals (Sprint 2: New Approval Workflow)
      try {
        const contractRes = await contractApi.list({ status: 'SUBMITTED', page_size: 100 })
        const contractData = contractRes.data || contractRes
        const contracts = contractData.items || contractData || []
        for (const contract of contracts) {
          let approvalStatus = null
          try {
            approvalStatus = await contractApi.getApprovalStatus(contract.id)
          } catch (err) {
            console.warn(`Failed to get approval status for contract ${contract.id}:`, err)
          }
          
          const status = approvalStatus?.status || 'PENDING'
          const currentStep = approvalStatus?.current_step
          
          allApprovals.push({
            id: `contract-${contract.id}`,
            type: 'sales',
            title: `合同审批 - ${contract.contract_code || contract.id}`,
            applicant: contract.owner?.real_name || contract.owner_name || '未知',
            applicantDept: contract.department || '销售部',
            submitTime: formatDate(contract.created_at) || '',
            status: status === 'PENDING' ? 'pending' : 
                    status === 'APPROVED' ? 'approved' : 
                    status === 'REJECTED' ? 'rejected' : 'waiting',
            priority: parseFloat(contract.contract_amount || 0) > 5000000 ? 'urgent' : 'normal',
            projectId: contract.project?.project_code,
            projectName: contract.project?.project_name || contract.customer?.customer_name || '',
            description: contract.contract_name || '',
            amount: parseFloat(contract.contract_amount || 0),
            approvalFlow: approvalStatus?.steps || [],
            currentStep: currentStep,
            originalData: contract,
            approvalType: 'contract_workflow',
          })
        }
      } catch (err) {
        console.error('Failed to load contract approvals:', err)
      }
      
      // Load Invoice approvals (Sprint 2: New Approval Workflow)
      try {
        const invoiceRes = await invoiceApi.list({ status: 'APPLIED', page_size: 100 })
        const invoiceData = invoiceRes.data || invoiceRes
        const invoices = invoiceData.items || invoiceData || []
        for (const invoice of invoices) {
          let approvalStatus = null
          try {
            approvalStatus = await invoiceApi.getApprovalStatus(invoice.id)
          } catch (err) {
            console.warn(`Failed to get approval status for invoice ${invoice.id}:`, err)
          }
          
          const status = approvalStatus?.status || 'PENDING'
          const currentStep = approvalStatus?.current_step
          
          allApprovals.push({
            id: `invoice-${invoice.id}`,
            type: 'sales',
            title: `发票审批 - ${invoice.invoice_code || invoice.id}`,
            applicant: invoice.created_by_name || '未知',
            applicantDept: invoice.department || '财务部',
            submitTime: formatDate(invoice.created_at) || '',
            status: status === 'PENDING' ? 'pending' : 
                    status === 'APPROVED' ? 'approved' : 
                    status === 'REJECTED' ? 'rejected' : 'waiting',
            priority: parseFloat(invoice.amount || invoice.total_amount || 0) > 500000 ? 'urgent' : 'normal',
            projectId: invoice.contract?.contract_code,
            projectName: invoice.contract?.customer?.customer_name || '',
            description: invoice.invoice_type || '',
            amount: parseFloat(invoice.amount || invoice.total_amount || 0),
            approvalFlow: approvalStatus?.steps || [],
            currentStep: currentStep,
            originalData: invoice,
            approvalType: 'invoice_workflow',
          })
        }
      } catch (err) {
        console.error('Failed to load invoice approvals:', err)
      }
      
      // Load Project Initiation approvals
      try {
        const initRes = await pmoApi.initiations.list({ status: 'SUBMITTED', page_size: 100 })
        const initData = initRes.data || initRes
        const inits = initData.items || initData || []
        inits.forEach(init => {
          allApprovals.push({
            id: `init-${init.id}`,
            type: 'ecn',
            title: `项目启动审批 - ${init.project_name || init.id}`,
            applicant: init.created_by_name || '未知',
            applicantDept: init.department || '未知部门',
            submitTime: formatDate(init.created_at) || '',
            status: init.status === 'SUBMITTED' ? 'pending' : 
                    init.status === 'APPROVED' ? 'approved' : 
                    init.status === 'REJECTED' ? 'rejected' : 'waiting',
            priority: 'normal',
            projectId: init.project_code,
            projectName: init.project_name || '',
            description: init.description || '',
            approvalFlow: [],
            originalData: init,
            approvalType: 'initiation',
          })
        })
      } catch (err) {
        console.error('Failed to load initiation approvals:', err)
      }
      
      setApprovals(allApprovals)
    } catch (err) {
      console.error('Failed to load approvals:', err)
      setError(err)
      setApprovals([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadApprovals()
  }, [loadApprovals])

  const filteredApprovals = approvals.filter((approval) => {
    if (statusFilter !== 'all' && approval.status !== statusFilter) return false
    if (searchQuery && !approval.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    return true
  })

  const stats = {
    pending: approvals.filter((a) => a.status === 'pending').length,
    approved: approvals.filter((a) => a.status === 'approved').length,
    rejected: approvals.filter((a) => a.status === 'rejected').length,
  }

  const handleView = (approval) => {
    setSelectedApproval(approval)
    setApprovalComment('')
    setShowDetail(true)
  }

  const handleApprove = async (approval) => {
    if (!approval || !approval.originalData) return
    
    try {
      const { approvalType, originalData } = approval
      const approvalData = approvalComment ? { comment: approvalComment } : {}
      
      // Call appropriate approval API based on type
      switch (approvalType) {
        case 'ecn':
          await ecnApi.approve(originalData.id, approvalData)
          break
        case 'purchase_request':
          await purchaseApi.requests.approve(originalData.id, approvalData)
          break
        case 'purchase_order':
          await purchaseApi.orders.approve(originalData.id, approvalData)
          break
        case 'quote':
          await quoteApi.approve(originalData.id, approvalData)
          break
        case 'quote_workflow':
          await quoteApi.approvalAction(originalData.id, { action: 'APPROVE', comment: approvalComment })
          break
        case 'contract_workflow':
          await contractApi.approvalAction(originalData.id, { action: 'APPROVE', comment: approvalComment })
          break
        case 'invoice_workflow':
          await invoiceApi.approvalAction(originalData.id, { action: 'APPROVE', comment: approvalComment })
          break
        case 'initiation':
          await pmoApi.initiations.approve(originalData.id, approvalData)
          break
        default:
          toast.error('未知的审批类型')
          return
      }
      
      toast.success('审批通过')
      setShowDetail(false)
      setApprovalComment('')
      await loadApprovals()
    } catch (err) {
      console.error('Failed to approve:', err)
      const errorMessage = err.response?.data?.detail || err.message || '审批失败，请稍后重试'
      toast.error(errorMessage)
    }
  }

  const handleReject = async (approval) => {
    if (!approval || !approval.originalData) return
    
    if (!approvalComment.trim()) {
      toast.error('请输入驳回原因')
      return
    }
    
    try {
      const { approvalType, originalData } = approval
      const rejectData = { comment: approvalComment, reason: approvalComment }
      
      // Call appropriate reject API based on type
      switch (approvalType) {
        case 'ecn':
          await ecnApi.reject(originalData.id, rejectData)
          break
        case 'purchase_request':
          await purchaseApi.requests.approve(originalData.id, { ...rejectData, approved: false })
          break
        case 'purchase_order':
          await purchaseApi.orders.approve(originalData.id, { ...rejectData, approved: false })
          break
        case 'quote':
          // Quote might not have reject, use approve with false
          await quoteApi.approve(originalData.id, { ...rejectData, approved: false })
          break
        case 'quote_workflow':
          await quoteApi.approvalAction(originalData.id, { action: 'REJECT', comment: approvalComment })
          break
        case 'contract_workflow':
          await contractApi.approvalAction(originalData.id, { action: 'REJECT', comment: approvalComment })
          break
        case 'invoice_workflow':
          await invoiceApi.approvalAction(originalData.id, { action: 'REJECT', comment: approvalComment })
          break
        case 'initiation':
          await pmoApi.initiations.reject(originalData.id, rejectData)
          break
        default:
          toast.error('未知的审批类型')
          return
      }
      
      toast.success('已驳回')
      setShowDetail(false)
      setApprovalComment('')
      await loadApprovals()
    } catch (err) {
      console.error('Failed to reject:', err)
      const errorMessage = err.response?.data?.detail || err.message || '驳回失败，请稍后重试'
      toast.error(errorMessage)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="container mx-auto px-4 py-6 space-y-6"
      >
      <PageHeader
        title="审批中心"
        description="处理待审批事项，查看审批记录"
      />

      {loading && approvals.length === 0 ? (
        <LoadingCard rows={5} />
      ) : error && approvals.length === 0 ? (
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/approvals"
          onRetry={loadApprovals}
        />
      ) : (
        <>

      {/* Stats */}
      <motion.div variants={fadeIn} className="grid grid-cols-3 gap-4">
        {[
          { label: '待审批', value: stats.pending, icon: Clock, color: 'text-amber-400' },
          { label: '已通过', value: stats.approved, icon: CheckCircle2, color: 'text-emerald-400' },
          { label: '已驳回', value: stats.rejected, icon: XCircle, color: 'text-red-400' },
        ].map((stat, index) => (
          <Card key={index} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <stat.icon className={cn('w-8 h-8', stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="flex items-center gap-2">
                {[
                  { value: 'pending', label: '待审批' },
                  { value: 'approved', label: '已通过' },
                  { value: 'rejected', label: '已驳回' },
                  { value: 'all', label: '全部' },
                ].map((filter) => (
                  <Button
                    key={filter.value}
                    variant={statusFilter === filter.value ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setStatusFilter(filter.value)}
                  >
                    {filter.label}
                  </Button>
                ))}
              </div>
              <div className="relative w-full md:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="搜索审批..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Approval List */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredApprovals.map((approval) => (
          <ApprovalCard
            key={approval.id}
            approval={approval}
            onView={handleView}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        ))}
      </motion.div>

      {/* Empty State */}
      {filteredApprovals.length === 0 && (
        <motion.div variants={fadeIn} className="text-center py-16">
          <ClipboardCheck className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400">暂无审批</h3>
          <p className="text-sm text-slate-500 mt-1">
            {statusFilter === 'pending' ? '没有待处理的审批事项' : '没有符合条件的审批记录'}
          </p>
        </motion.div>
      )}

      {/* Detail Dialog */}
      <ApprovalDetailDialog
        approval={selectedApproval}
        open={showDetail}
        onOpenChange={setShowDetail}
        onApprove={handleApprove}
        onReject={handleReject}
        comment={approvalComment}
        setComment={setApprovalComment}
      />
        </>
      )}
      </motion.div>
    </div>
  )
}

