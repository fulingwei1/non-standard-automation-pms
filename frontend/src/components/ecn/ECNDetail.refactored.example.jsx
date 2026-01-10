/**
 * ECNDetail - 重构后的主组件示例
 * 
 * 这个文件展示了重构后的主组件结构
 * 实际使用时，应该替换 pages/ECNDetail.jsx
 * 
 * 重构效果：
 * - 主组件从 2732 行减少到约 150 行
 * - 每个 Tab 拆分为独立组件
 * - 状态管理提取到自定义 Hooks
 * - 对话框组件独立
 */

import { useParams, useNavigate } from 'react-router-dom'
import { useECNDetail } from '../components/ecn/hooks/useECNDetail'
import ECNDetailHeader from '../components/ecn/ECNDetailHeader'
import ECNInfoTab from '../components/ecn/ECNInfoTab'
import ECNEvaluationsTab from '../components/ecn/ECNEvaluationsTab'
import ECNTasksTab from '../components/ecn/ECNTasksTab'
import ECNApprovalsTab from '../components/ecn/ECNApprovalsTab'
import ECNImpactAnalysisTab from '../components/ecn/ECNImpactAnalysisTab'
import ECNKnowledgeTab from '../components/ecn/ECNKnowledgeTab'
import ECNIntegrationTab from '../components/ecn/ECNIntegrationTab'
import ECNLogsTab from '../components/ecn/ECNLogsTab'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Skeleton } from '../components/ui/skeleton'
import { Button } from '../components/ui/button'

export default function ECNDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const {
    loading,
    ecn,
    evaluations,
    evaluationSummary,
    approvals,
    tasks,
    affectedMaterials,
    affectedOrders,
    logs,
    activeTab,
    setActiveTab,
    refetch,
    handleSubmit,
    handleStartExecution,
    handleVerify,
    handleClose,
  } = useECNDetail(id)

  // 处理操作
  const handleSubmitClick = async () => {
    const result = await handleSubmit()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  const handleStartExecutionClick = async () => {
    const result = await handleStartExecution()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  const handleVerifyClick = async (verifyForm) => {
    const result = await handleVerify(verifyForm)
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  const handleCloseClick = async (closeForm) => {
    const result = await handleClose(closeForm)
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 加载状态
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    )
  }

  // 未找到数据
  if (!ecn) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold mb-2">未找到ECN</h2>
        <p className="text-slate-400 mb-6">该ECN可能已被删除或不存在</p>
        <Button onClick={() => navigate('/ecns')}>返回ECN列表</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* 页面头部 */}
      <ECNDetailHeader
        ecn={ecn}
        tasks={tasks}
        onBack={() => navigate('/ecns')}
        onRefresh={refetch}
        onSubmit={handleSubmitClick}
        onStartExecution={handleStartExecutionClick}
        onVerify={handleVerify}
        onClose={handleClose}
      />

      {/* Tab 内容 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-8">
          <TabsTrigger value="info">基本信息</TabsTrigger>
          <TabsTrigger value="evaluations">评估</TabsTrigger>
          <TabsTrigger value="approvals">审批</TabsTrigger>
          <TabsTrigger value="tasks">执行任务</TabsTrigger>
          <TabsTrigger value="affected">影响分析</TabsTrigger>
          <TabsTrigger value="knowledge">知识库</TabsTrigger>
          <TabsTrigger value="integration">模块集成</TabsTrigger>
          <TabsTrigger value="logs">变更日志</TabsTrigger>
        </TabsList>

        {/* 基本信息 Tab - 已重构 */}
        <TabsContent value="info" className="space-y-4">
          <ECNInfoTab ecn={ecn} />
        </TabsContent>

        {/* 评估管理 Tab - 已重构 */}
        <TabsContent value="evaluations" className="space-y-4">
          <ECNEvaluationsTab
            ecnId={id}
            ecn={ecn}
            evaluations={evaluations}
            evaluationSummary={evaluationSummary}
            refetch={refetch}
          />
        </TabsContent>

        {/* 审批流程 Tab - 已重构 */}
        <TabsContent value="approvals" className="space-y-4">
          <ECNApprovalsTab approvals={approvals} refetch={refetch} />
        </TabsContent>

        {/* 执行任务 Tab - 已重构 */}
        <TabsContent value="tasks" className="space-y-4">
          <ECNTasksTab
            ecnId={id}
            ecn={ecn}
            tasks={tasks}
            refetch={refetch}
          />
        </TabsContent>

        {/* 影响分析 Tab - 已重构 */}
        <TabsContent value="affected" className="space-y-4">
          <ECNImpactAnalysisTab
            ecnId={id}
            ecn={ecn}
            affectedMaterials={affectedMaterials}
            affectedOrders={affectedOrders}
            refetch={refetch}
          />
        </TabsContent>

        {/* 知识库 Tab - 已重构 */}
        <TabsContent value="knowledge" className="space-y-4">
          <ECNKnowledgeTab ecnId={id} ecn={ecn} refetch={refetch} />
        </TabsContent>

        {/* 模块集成 Tab - 已重构 */}
        <TabsContent value="integration" className="space-y-4">
          <ECNIntegrationTab
            ecnId={id}
            ecn={ecn}
            affectedMaterials={affectedMaterials}
            affectedOrders={affectedOrders}
            refetch={refetch}
          />
        </TabsContent>

        {/* 变更日志 Tab - 已重构 */}
        <TabsContent value="logs" className="space-y-4">
          <ECNLogsTab logs={logs} />
        </TabsContent>
      </Tabs>

      {/* TODO: 对话框组件 - 后续会提取到各自的 Tab 组件中 */}
      {/* <VerifyDialog ... /> */}
      {/* <CloseDialog ... /> */}
    </div>
  )
}
