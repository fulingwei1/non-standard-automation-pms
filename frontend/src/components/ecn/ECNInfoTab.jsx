/**
 * ECNInfoTab Component
 * ECN 基本信息 Tab 组件
 */
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Badge } from '../ui/badge'
import { formatDate } from '../../lib/utils'

// 配置（从原文件提取）
const typeConfigs = {
  // 客户相关
  CUSTOMER_REQUIREMENT: { label: '客户需求变更', color: 'bg-blue-500' },
  CUSTOMER_SPEC: { label: '客户规格调整', color: 'bg-blue-400' },
  CUSTOMER_FEEDBACK: { label: '客户现场反馈', color: 'bg-blue-600' },
  // 设计变更
  MECHANICAL_STRUCTURE: { label: '机械结构变更', color: 'bg-cyan-500' },
  ELECTRICAL_SCHEME: { label: '电气方案变更', color: 'bg-cyan-400' },
  SOFTWARE_FUNCTION: { label: '软件功能变更', color: 'bg-cyan-600' },
  TECH_OPTIMIZATION: { label: '技术方案优化', color: 'bg-teal-500' },
  DESIGN_FIX: { label: '设计缺陷修复', color: 'bg-teal-600' },
  // 测试相关
  TEST_STANDARD: { label: '测试标准变更', color: 'bg-purple-500' },
  TEST_FIXTURE: { label: '测试工装变更', color: 'bg-purple-400' },
  CALIBRATION_SCHEME: { label: '校准方案变更', color: 'bg-purple-600' },
  TEST_PROGRAM: { label: '测试程序变更', color: 'bg-violet-500' },
  // 生产制造
  PROCESS_IMPROVEMENT: { label: '工艺改进', color: 'bg-orange-500' },
  MATERIAL_SUBSTITUTE: { label: '物料替代', color: 'bg-orange-400' },
  SUPPLIER_CHANGE: { label: '供应商变更', color: 'bg-orange-600' },
  COST_OPTIMIZATION: { label: '成本优化', color: 'bg-amber-500' },
  // 质量安全
  QUALITY_ISSUE: { label: '质量问题整改', color: 'bg-red-500' },
  SAFETY_COMPLIANCE: { label: '安全合规变更', color: 'bg-red-600' },
  RELIABILITY_IMPROVEMENT: { label: '可靠性改进', color: 'bg-rose-500' },
  // 项目管理
  SCHEDULE_ADJUSTMENT: { label: '进度调整', color: 'bg-green-500' },
  DOCUMENT_UPDATE: { label: '文档更新', color: 'bg-green-400' },
  DRAWING_CHANGE: { label: '图纸变更', color: 'bg-emerald-500' },
  // 兼容旧版本
  DESIGN: { label: '设计变更', color: 'bg-blue-500' },
  MATERIAL: { label: '物料变更', color: 'bg-amber-500' },
  PROCESS: { label: '工艺变更', color: 'bg-purple-500' },
  SPECIFICATION: { label: '规格变更', color: 'bg-green-500' },
  SCHEDULE: { label: '计划变更', color: 'bg-orange-500' },
  OTHER: { label: '其他', color: 'bg-slate-500' },
}

const priorityConfigs = {
  URGENT: { label: '紧急', color: 'bg-red-500' },
  HIGH: { label: '高', color: 'bg-orange-500' },
  MEDIUM: { label: '中', color: 'bg-amber-500' },
  LOW: { label: '低', color: 'bg-blue-500' },
}

export default function ECNInfoTab({ ecn }) {
  if (!ecn) {
    return (
      <div className="text-center py-10 text-slate-400">暂无数据</div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 基本信息卡片 */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">基本信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <div className="text-sm text-slate-500 mb-1">ECN编号</div>
              <div className="font-mono">{ecn.ecn_no}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">变更类型</div>
              <Badge className={typeConfigs[ecn.ecn_type]?.color}>
                {typeConfigs[ecn.ecn_type]?.label}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">优先级</div>
              <Badge className={priorityConfigs[ecn.priority]?.color}>
                {priorityConfigs[ecn.priority]?.label}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">项目</div>
              <div>{ecn.project_name || '-'}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">申请人</div>
              <div>{ecn.applicant_name || '-'}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">申请时间</div>
              <div>{ecn.applied_at ? formatDate(ecn.applied_at) : '-'}</div>
            </div>
          </CardContent>
        </Card>

        {/* 影响评估卡片 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">影响评估</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <div className="text-sm text-slate-500 mb-1">成本影响</div>
              <div className="text-xl font-semibold text-red-600">
                ¥{ecn.cost_impact || 0}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-500 mb-1">工期影响</div>
              <div className="text-xl font-semibold text-orange-600">
                {ecn.schedule_impact_days || 0} 天
              </div>
            </div>
            {ecn.quality_impact && (
              <div>
                <div className="text-sm text-slate-500 mb-1">质量影响</div>
                <div>{ecn.quality_impact}</div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 变更内容卡片 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">变更内容</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {ecn.change_reason && (
            <div>
              <div className="text-sm text-slate-500 mb-2">变更原因</div>
              <div className="p-3 bg-slate-50 rounded-lg">{ecn.change_reason}</div>
            </div>
          )}
          {ecn.change_description && (
            <div>
              <div className="text-sm text-slate-500 mb-2">变更描述</div>
              <div className="p-3 bg-slate-50 rounded-lg whitespace-pre-wrap">
                {ecn.change_description}
              </div>
            </div>
          )}
          {ecn.approval_note && (
            <div>
              <div className="text-sm text-slate-500 mb-2">审批意见</div>
              <div className="p-3 bg-slate-50 rounded-lg">{ecn.approval_note}</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
