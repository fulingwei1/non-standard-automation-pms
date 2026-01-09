/**
 * ECNDetailHeader Component
 * ECN 详情页面头部组件（包含标题、状态、操作按钮）
 */
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Card, CardContent } from '../ui/card'
import { PageHeader } from '../layout'
import {
  ArrowLeft,
  CheckCircle2,
  Play,
  XCircle,
  Download,
  RefreshCw,
} from 'lucide-react'

const statusConfigs = {
  DRAFT: { label: '草稿', color: 'bg-slate-500' },
  SUBMITTED: { label: '已提交', color: 'bg-blue-500' },
  EVALUATING: { label: '评估中', color: 'bg-amber-500' },
  EVALUATED: { label: '评估完成', color: 'bg-amber-600' },
  PENDING_APPROVAL: { label: '待审批', color: 'bg-purple-500' },
  APPROVED: { label: '已批准', color: 'bg-emerald-500' },
  REJECTED: { label: '已驳回', color: 'bg-red-500' },
  EXECUTING: { label: '执行中', color: 'bg-violet-500' },
  PENDING_VERIFY: { label: '待验证', color: 'bg-indigo-500' },
  COMPLETED: { label: '已完成', color: 'bg-green-500' },
  CLOSED: { label: '已关闭', color: 'bg-gray-500' },
  CANCELLED: { label: '已取消', color: 'bg-gray-500' },
}

const statusFlow = [
  { status: 'DRAFT', label: '草稿' },
  { status: 'SUBMITTED', label: '已提交' },
  { status: 'EVALUATING', label: '评估中' },
  { status: 'PENDING_APPROVAL', label: '待审批' },
  { status: 'APPROVED', label: '已批准' },
  { status: 'EXECUTING', label: '执行中' },
  { status: 'COMPLETED', label: '已完成' },
  { status: 'CLOSED', label: '已关闭' },
]

export default function ECNDetailHeader({
  ecn,
  tasks = [],
  onBack,
  onRefresh,
  onSubmit,
  onStartExecution,
  onVerify,
  onClose,
}) {
  if (!ecn) return null

  const statusIndex = statusFlow.findIndex((s) => s.status === ecn.status)
  const isPast = (index) => statusIndex >= index

  return (
    <>
      <PageHeader
        title={
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
            </Button>
            <div>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold">{ecn.ecn_title}</span>
                <Badge className={statusConfigs[ecn.status]?.color}>
                  {statusConfigs[ecn.status]?.label}
                </Badge>
              </div>
              <div className="text-sm text-slate-400 mt-1">
                {ecn.ecn_no} · {ecn.project_name || '未关联项目'}
              </div>
            </div>
          </div>
        }
        description="ECN变更管理详情"
        actions={
          <div className="flex gap-2">
            {ecn.status === 'DRAFT' && (
              <Button onClick={onSubmit}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                提交ECN
              </Button>
            )}
            {ecn.status === 'APPROVED' && (
              <Button onClick={onStartExecution}>
                <Play className="w-4 h-4 mr-2" />
                开始执行
              </Button>
            )}
            {ecn.status === 'EXECUTING' &&
              tasks.every((t) => t.status === 'COMPLETED') && (
                <Button onClick={onVerify}>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  验证
                </Button>
              )}
            {ecn.status === 'COMPLETED' && (
              <Button onClick={onClose}>
                <XCircle className="w-4 h-4 mr-2" />
                关闭
              </Button>
            )}
            <Button variant="outline" onClick={() => window.print()}>
              <Download className="w-4 h-4 mr-2" />
              打印/导出
            </Button>
            <Button variant="outline" onClick={onRefresh}>
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
          </div>
        }
      />

      {/* 状态流程指示器 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {statusFlow.map((step, index) => {
              const isActive = ecn.status === step.status
              const past = isPast(index)

              return (
                <div key={step.status} className="flex items-center flex-1">
                  <div className="flex flex-col items-center flex-1">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isActive
                          ? 'bg-blue-500'
                          : past
                          ? 'bg-green-500'
                          : 'bg-slate-300'
                      } text-white font-bold text-sm`}
                    >
                      {index + 1}
                    </div>
                    <div
                      className={`text-xs mt-2 ${
                        isActive ? 'font-semibold' : 'text-slate-400'
                      }`}
                    >
                      {step.label}
                    </div>
                  </div>
                  {index < statusFlow.length - 1 && (
                    <div
                      className={`flex-1 h-0.5 mx-2 ${
                        past ? 'bg-green-500' : 'bg-slate-300'
                      }`}
                    />
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </>
  )
}
