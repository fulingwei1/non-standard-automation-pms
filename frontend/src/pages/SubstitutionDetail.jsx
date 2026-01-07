/**
 * Material Substitution Detail - 物料替代详情页
 * 显示物料替代申请的详细信息，支持技术审批、生产审批、执行等操作
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  Calendar,
  FileText,
  DollarSign,
  AlertTriangle,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Label,
} from '../components/ui'
import { cn, formatDate } from '../lib/utils'
import { fadeIn } from '../lib/animations'
import { shortageApi } from '../services/api'

const statusConfigs = {
  DRAFT: { label: '草稿', color: 'bg-slate-500', icon: FileText },
  TECH_PENDING: { label: '待技术审批', color: 'bg-blue-500', icon: Clock },
  PROD_PENDING: { label: '待生产审批', color: 'bg-amber-500', icon: Clock },
  APPROVED: { label: '已批准', color: 'bg-emerald-500', icon: CheckCircle2 },
  REJECTED: { label: '已拒绝', color: 'bg-red-500', icon: XCircle },
  EXECUTED: { label: '已执行', color: 'bg-purple-500', icon: CheckCircle2 },
}

export default function SubstitutionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [substitution, setSubstitution] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [showExecuteDialog, setShowExecuteDialog] = useState(false)
  const [approvalType, setApprovalType] = useState(null) // 'tech' or 'prod'
  const [approvalData, setApprovalData] = useState({
    approved: true,
    approval_note: '',
  })
  const [executionNote, setExecutionNote] = useState('')

  useEffect(() => {
    loadSubstitution()
  }, [id])

  const loadSubstitution = async () => {
    setLoading(true)
    try {
      const res = await shortageApi.substitutions.get(id)
      setSubstitution(res.data)
    } catch (error) {
      console.error('加载物料替代详情失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTechApprove = async () => {
    setActionLoading(true)
    try {
      await shortageApi.substitutions.techApprove(
        id,
        approvalData.approved,
        approvalData.approval_note
      )
      setShowApproveDialog(false)
      setApprovalData({ approved: true, approval_note: '' })
      await loadSubstitution()
    } catch (error) {
      console.error('技术审批失败', error)
      alert('技术审批失败：' + (error.response?.data?.detail || error.message))
    } finally {
      setActionLoading(false)
    }
  }

  const handleProdApprove = async () => {
    setActionLoading(true)
    try {
      await shortageApi.substitutions.prodApprove(
        id,
        approvalData.approved,
        approvalData.approval_note
      )
      setShowApproveDialog(false)
      setApprovalData({ approved: true, approval_note: '' })
      await loadSubstitution()
    } catch (error) {
      console.error('生产审批失败', error)
      alert('生产审批失败：' + (error.response?.data?.detail || error.message))
    } finally {
      setActionLoading(false)
    }
  }

  const handleExecute = async () => {
    setActionLoading(true)
    try {
      await shortageApi.substitutions.execute(id, executionNote)
      setShowExecuteDialog(false)
      setExecutionNote('')
      await loadSubstitution()
    } catch (error) {
      console.error('执行替代失败', error)
      alert('执行替代失败：' + (error.response?.data?.detail || error.message))
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">加载中...</div>
      </div>
    )
  }

  if (!substitution) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <XCircle className="h-12 w-12 text-muted-foreground" />
        <div className="text-muted-foreground">物料替代申请不存在</div>
        <Button variant="outline" onClick={() => navigate('/shortage')}>
          返回列表
        </Button>
      </div>
    )
  }

  const status = statusConfigs[substitution.status] || statusConfigs.DRAFT
  const StatusIcon = status.icon

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/shortage')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <PageHeader
          title={`物料替代 - ${substitution.substitution_no}`}
          description="查看物料替代申请的详细信息和审批流程"
        />
      </div>

      <motion.div
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-6 lg:grid-cols-3"
      >
        {/* 主要信息 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 基本信息 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>基本信息</CardTitle>
                <Badge variant="outline" className={cn(status.color, 'text-white')}>
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {status.label}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">替代单号</div>
                  <div className="font-medium">{substitution.substitution_no}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">项目名称</div>
                  <div className="font-medium">{substitution.project_name || '-'}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 物料信息 */}
          <Card>
            <CardHeader>
              <CardTitle>物料替代信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* 原物料 */}
              <div className="p-4 rounded-lg border border-border bg-red-500/5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                  <span className="font-medium text-red-400">原物料（缺料）</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">物料编码</div>
                    <div className="font-medium">{substitution.original_material_code}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">物料名称</div>
                    <div className="font-medium">{substitution.original_material_name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">数量</div>
                    <div className="font-medium">{substitution.original_qty}</div>
                  </div>
                </div>
              </div>

              {/* 替代物料 */}
              <div className="p-4 rounded-lg border border-border bg-emerald-500/5">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span className="font-medium text-emerald-400">替代物料</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">物料编码</div>
                    <div className="font-medium">{substitution.substitute_material_code}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">物料名称</div>
                    <div className="font-medium">{substitution.substitute_material_name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">数量</div>
                    <div className="font-medium">{substitution.substitute_qty}</div>
                  </div>
                </div>
              </div>

              {/* 替代原因和影响 */}
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-muted-foreground mb-2">替代原因</div>
                  <div className="p-3 rounded-lg bg-surface-2">{substitution.substitution_reason}</div>
                </div>
                {substitution.technical_impact && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-2">技术影响分析</div>
                    <div className="p-3 rounded-lg bg-surface-2 whitespace-pre-wrap">
                      {substitution.technical_impact}
                    </div>
                  </div>
                )}
                {substitution.cost_impact && parseFloat(substitution.cost_impact) !== 0 && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-2">成本影响</div>
                    <div className="p-3 rounded-lg bg-surface-2">
                      <span className={cn(
                        'font-medium',
                        parseFloat(substitution.cost_impact) > 0 ? 'text-red-400' : 'text-emerald-400'
                      )}>
                        {parseFloat(substitution.cost_impact) > 0 ? '+' : ''}
                        ¥{substitution.cost_impact}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 审批信息 */}
          {(substitution.tech_approver_id || substitution.prod_approver_id) && (
            <Card>
              <CardHeader>
                <CardTitle>审批信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {substitution.tech_approver_id && (
                  <div>
                    <div className="text-sm text-muted-foreground">技术审批</div>
                    <div className="font-medium">
                      {substitution.tech_approver_name} - {formatDate(substitution.tech_approved_at)}
                    </div>
                  </div>
                )}
                {substitution.prod_approver_id && (
                  <div>
                    <div className="text-sm text-muted-foreground">生产审批</div>
                    <div className="font-medium">
                      {substitution.prod_approver_name} - {formatDate(substitution.prod_approved_at)}
                    </div>
                  </div>
                )}
                {substitution.executed_at && (
                  <div>
                    <div className="text-sm text-muted-foreground">执行时间</div>
                    <div className="font-medium">{formatDate(substitution.executed_at)}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 备注 */}
          {substitution.remark && (
            <Card>
              <CardHeader>
                <CardTitle>备注</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm whitespace-pre-wrap">{substitution.remark}</div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 操作面板 */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>操作</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {substitution.status === 'DRAFT' && (
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => {
                    setApprovalType('tech')
                    setShowApproveDialog(true)
                  }}
                  disabled={actionLoading}
                >
                  <User className="h-4 w-4 mr-2" />
                  技术审批
                </Button>
              )}
              {substitution.status === 'PROD_PENDING' && (
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => {
                    setApprovalType('prod')
                    setShowApproveDialog(true)
                  }}
                  disabled={actionLoading}
                >
                  <User className="h-4 w-4 mr-2" />
                  生产审批
                </Button>
              )}
              {substitution.status === 'APPROVED' && (
                <Button
                  className="w-full"
                  onClick={() => setShowExecuteDialog(true)}
                  disabled={actionLoading}
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  执行替代
                </Button>
              )}
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate('/shortage')}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                返回列表
              </Button>
            </CardContent>
          </Card>

          {/* 状态时间线 */}
          <Card>
            <CardHeader>
              <CardTitle>状态时间线</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className={cn('rounded-full p-2', status.color, 'bg-opacity-10')}>
                    <StatusIcon className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{status.label}</div>
                    <div className="text-sm text-muted-foreground">
                      {formatDate(substitution.created_at)}
                    </div>
                  </div>
                </div>
                {substitution.tech_approved_at && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-blue-500/10 text-blue-400">
                      <User className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">技术审批</div>
                      <div className="text-sm text-muted-foreground">
                        {substitution.tech_approver_name} - {formatDate(substitution.tech_approved_at)}
                      </div>
                    </div>
                  </div>
                )}
                {substitution.prod_approved_at && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-amber-500/10 text-amber-400">
                      <User className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">生产审批</div>
                      <div className="text-sm text-muted-foreground">
                        {substitution.prod_approver_name} - {formatDate(substitution.prod_approved_at)}
                      </div>
                    </div>
                  </div>
                )}
                {substitution.executed_at && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-purple-500/10 text-purple-400">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">已执行</div>
                      <div className="text-sm text-muted-foreground">
                        {formatDate(substitution.executed_at)}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </motion.div>

      {/* 审批对话框 */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {approvalType === 'tech' ? '技术审批' : '生产审批'}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <Label>审批结果</Label>
                <div className="flex gap-2 mt-2">
                  <Button
                    type="button"
                    variant={approvalData.approved ? 'default' : 'outline'}
                    onClick={() => setApprovalData((prev) => ({ ...prev, approved: true }))}
                    className="flex-1"
                  >
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    批准
                  </Button>
                  <Button
                    type="button"
                    variant={!approvalData.approved ? 'default' : 'outline'}
                    onClick={() => setApprovalData((prev) => ({ ...prev, approved: false }))}
                    className="flex-1"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    拒绝
                  </Button>
                </div>
              </div>
              <div>
                <Label htmlFor="approval_note">审批意见</Label>
                <Textarea
                  id="approval_note"
                  placeholder="请输入审批意见..."
                  value={approvalData.approval_note}
                  onChange={(e) =>
                    setApprovalData((prev) => ({ ...prev, approval_note: e.target.value }))
                  }
                  rows={4}
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApproveDialog(false)}>
              取消
            </Button>
            <Button
              onClick={approvalType === 'tech' ? handleTechApprove : handleProdApprove}
              disabled={actionLoading}
            >
              {actionLoading ? '提交中...' : '提交'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 执行对话框 */}
      <Dialog open={showExecuteDialog} onOpenChange={setShowExecuteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>执行替代</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div>
              <Label htmlFor="execution_note">执行说明</Label>
              <Textarea
                id="execution_note"
                placeholder="请输入执行说明..."
                value={executionNote}
                onChange={(e) => setExecutionNote(e.target.value)}
                rows={4}
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExecuteDialog(false)}>
              取消
            </Button>
            <Button onClick={handleExecute} disabled={actionLoading}>
              {actionLoading ? '执行中...' : '确认执行'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}



