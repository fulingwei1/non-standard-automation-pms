/**
 * Material Transfer Detail - 物料调拨详情页
 * 显示物料调拨申请的详细信息，支持审批、执行等操作
 */

import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  ArrowRightLeft,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  Calendar,
  Package,
  AlertTriangle,
  FileText,
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
  Input,
  Label,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui'
import { cn, formatDate } from '../lib/utils'
import { fadeIn } from '../lib/animations'
import { shortageApi } from '../services/api'

const statusConfigs = {
  DRAFT: { label: '草稿', color: 'bg-slate-500', icon: FileText },
  PENDING: { label: '待审批', color: 'bg-blue-500', icon: Clock },
  APPROVED: { label: '已批准', color: 'bg-emerald-500', icon: CheckCircle2 },
  REJECTED: { label: '已拒绝', color: 'bg-red-500', icon: XCircle },
  EXECUTED: { label: '已执行', color: 'bg-purple-500', icon: CheckCircle2 },
  CANCELLED: { label: '已取消', color: 'bg-slate-400', icon: XCircle },
}

const urgentLevelConfigs = {
  NORMAL: { label: '普通', color: 'text-slate-400', bgColor: 'bg-slate-500/10' },
  URGENT: { label: '紧急', color: 'text-amber-400', bgColor: 'bg-amber-500/10' },
  CRITICAL: { label: '特急', color: 'text-red-400', bgColor: 'bg-red-500/10' },
}

export default function TransferDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [transfer, setTransfer] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [showExecuteDialog, setShowExecuteDialog] = useState(false)
  const [approvalData, setApprovalData] = useState({
    approved: true,
    approval_note: '',
  })
  const [executionData, setExecutionData] = useState({
    actual_qty: '',
    execution_note: '',
  })

  useEffect(() => {
    loadTransfer()
  }, [id])

  const loadTransfer = async () => {
    setLoading(true)
    try {
      const res = await shortageApi.transfers.get(id)
      setTransfer(res.data)
      if (res.data.transfer_qty) {
        setExecutionData((prev) => ({ ...prev, actual_qty: String(res.data.transfer_qty) }))
      }
    } catch (error) {
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    setActionLoading(true)
    try {
      await shortageApi.transfers.approve(
        id,
        approvalData.approved,
        approvalData.approval_note
      )
      setShowApproveDialog(false)
      setApprovalData({ approved: true, approval_note: '' })
      await loadTransfer()
    } catch (error) {
      alert('审批失败：' + (error.response?.data?.detail || error.message))
    } finally {
      setActionLoading(false)
    }
  }

  const handleExecute = async () => {
    if (!executionData.actual_qty || parseFloat(executionData.actual_qty) <= 0) {
      alert('请输入有效的实际调拨数量')
      return
    }
    setActionLoading(true)
    try {
      await shortageApi.transfers.execute(
        id,
        parseFloat(executionData.actual_qty),
        executionData.execution_note
      )
      setShowExecuteDialog(false)
      setExecutionData({ actual_qty: '', execution_note: '' })
      await loadTransfer()
    } catch (error) {
      alert('执行调拨失败：' + (error.response?.data?.detail || error.message))
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

  if (!transfer) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <XCircle className="h-12 w-12 text-muted-foreground" />
        <div className="text-muted-foreground">物料调拨申请不存在</div>
        <Button variant="outline" onClick={() => navigate('/shortage')}>
          返回列表
        </Button>
      </div>
    )
  }

  const status = statusConfigs[transfer.status] || statusConfigs.DRAFT
  const urgent = urgentLevelConfigs[transfer.urgent_level] || urgentLevelConfigs.NORMAL
  const StatusIcon = status.icon

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/shortage')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <PageHeader
          title={`物料调拨 - ${transfer.transfer_no}`}
          description="查看物料调拨申请的详细信息和审批流程"
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
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={cn(urgent.bgColor, urgent.color)}>
                    {urgent.label}
                  </Badge>
                  <Badge variant="outline" className={cn(status.color, 'text-white')}>
                    <StatusIcon className="h-3 w-3 mr-1" />
                    {status.label}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">调拨单号</div>
                  <div className="font-medium">{transfer.transfer_no}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">物料编码</div>
                  <div className="font-medium">{transfer.material_code}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">物料名称</div>
                  <div className="font-medium">{transfer.material_name}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">调拨数量</div>
                  <div className="font-medium">{transfer.transfer_qty}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 调拨信息 */}
          <Card>
            <CardHeader>
              <CardTitle>调拨信息</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">调出项目</div>
                  <div className="font-medium">{transfer.from_project_name || '总库存'}</div>
                  {transfer.from_location && (
                    <div className="text-xs text-muted-foreground mt-1">
                      位置：{transfer.from_location}
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">调入项目</div>
                  <div className="font-medium">{transfer.to_project_name}</div>
                  {transfer.to_location && (
                    <div className="text-xs text-muted-foreground mt-1">
                      位置：{transfer.to_location}
                    </div>
                  )}
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">可调拨数量</div>
                  <div className="font-medium">{transfer.available_qty}</div>
                </div>
                {transfer.actual_qty && (
                  <div>
                    <div className="text-sm text-muted-foreground">实际调拨数量</div>
                    <div className="font-medium">{transfer.actual_qty}</div>
                  </div>
                )}
              </div>
              <div>
                <div className="text-sm text-muted-foreground mb-2">调拨原因</div>
                <div className="p-3 rounded-lg bg-surface-2">{transfer.transfer_reason}</div>
              </div>
            </CardContent>
          </Card>

          {/* 审批和执行信息 */}
          {(transfer.approver_id || transfer.executed_at) && (
            <Card>
              <CardHeader>
                <CardTitle>审批和执行信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {transfer.approver_id && (
                  <div>
                    <div className="text-sm text-muted-foreground">审批人</div>
                    <div className="font-medium">
                      {transfer.approver_name} - {formatDate(transfer.approved_at)}
                    </div>
                  </div>
                )}
                {transfer.executed_at && (
                  <div>
                    <div className="text-sm text-muted-foreground">执行时间</div>
                    <div className="font-medium">{formatDate(transfer.executed_at)}</div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* 备注 */}
          {transfer.remark && (
            <Card>
              <CardHeader>
                <CardTitle>备注</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm whitespace-pre-wrap">{transfer.remark}</div>
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
              {transfer.status === 'DRAFT' && (
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => setShowApproveDialog(true)}
                  disabled={actionLoading}
                >
                  <User className="h-4 w-4 mr-2" />
                  审批
                </Button>
              )}
              {transfer.status === 'PENDING' && (
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => setShowApproveDialog(true)}
                  disabled={actionLoading}
                >
                  <User className="h-4 w-4 mr-2" />
                  审批
                </Button>
              )}
              {transfer.status === 'APPROVED' && (
                <Button
                  className="w-full"
                  onClick={() => setShowExecuteDialog(true)}
                  disabled={actionLoading}
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  执行调拨
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
                      {formatDate(transfer.created_at)}
                    </div>
                  </div>
                </div>
                {transfer.approved_at && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-emerald-500/10 text-emerald-400">
                      <User className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">已审批</div>
                      <div className="text-sm text-muted-foreground">
                        {transfer.approver_name} - {formatDate(transfer.approved_at)}
                      </div>
                    </div>
                  </div>
                )}
                {transfer.executed_at && (
                  <div className="flex items-start gap-3">
                    <div className="rounded-full p-2 bg-purple-500/10 text-purple-400">
                      <CheckCircle2 className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">已执行</div>
                      <div className="text-sm text-muted-foreground">
                        {formatDate(transfer.executed_at)}
                      </div>
                      {transfer.actual_qty && (
                        <div className="text-sm text-muted-foreground">
                          实际数量：{transfer.actual_qty}
                        </div>
                      )}
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
            <DialogTitle>调拨审批</DialogTitle>
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
            <Button onClick={handleApprove} disabled={actionLoading}>
              {actionLoading ? '提交中...' : '提交'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 执行对话框 */}
      <Dialog open={showExecuteDialog} onOpenChange={setShowExecuteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>执行调拨</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <Label htmlFor="actual_qty">实际调拨数量</Label>
                <Input
                  id="actual_qty"
                  type="number"
                  step="0.01"
                  min="0"
                  value={executionData.actual_qty}
                  onChange={(e) =>
                    setExecutionData((prev) => ({ ...prev, actual_qty: e.target.value }))
                  }
                  placeholder="请输入实际调拨数量"
                />
                <div className="text-xs text-muted-foreground mt-1">
                  计划数量：{transfer.transfer_qty}
                </div>
              </div>
              <div>
                <Label htmlFor="execution_note">执行说明</Label>
                <Textarea
                  id="execution_note"
                  placeholder="请输入执行说明..."
                  value={executionData.execution_note}
                  onChange={(e) =>
                    setExecutionData((prev) => ({ ...prev, execution_note: e.target.value }))
                  }
                  rows={4}
                />
              </div>
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

