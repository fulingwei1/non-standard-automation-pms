/**
 * ECN Detail Page - Refactored Version
 * ECN详情页面 - 重构版本
 * 
 * Features: ECN完整信息展示、评估管理、审批流程可视化、执行任务看板、影响分析、变更日志
 */

import { useState, useEffect, useMemo as _useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";

import { PageHeader } from "../components/layout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Skeleton } from "../components/ui/skeleton";

// Import ECN components
import {
  ECNBasicInfo,
  ECNEvaluationManager,
  ECNApprovalFlow,
  ECNTaskBoard,
  ECNImpactAnalysis,
  ECNChangeLog,
  tabConfigs,
  getStatusConfig,
  formatDate } from
"../components/ecn";

// Import services
import { ecnApi } from "../services/api";

export default function ECNDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  // State management
  const [ecn, setEcn] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Data state
  const [evaluations, setEvaluations] = useState([]);
  const [evaluationSummary, setEvaluationSummary] = useState(null);
  const [approvals, setApprovals] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [bomImpactSummary, setBomImpactSummary] = useState(null);
  const [obsoleteRisks, setObsoleteRisks] = useState([]);
  const [logs, setLogs] = useState([]);
  const [_knowledge, setKnowledge] = useState([]);
  const [_integrations, setIntegrations] = useState([]);

  // UI state
  const [analyzingBom, setAnalyzingBom] = useState(false);
  const [activeTab, setActiveTab] = useState("info");

  // Mock current user - should come from auth context
  const currentUser = {
    id: "current_user_id",
    name: "当前用户",
    role: "MANAGER"
  };

  // Load ECN data
  const loadECN = async () => {
    try {
      setLoading(true);
      const response = await ecnApi.getDetail(id);
      setEcn(response.data);
    } catch (error) {
      console.error("Failed to load ECN:", error);
      toast.error("加载ECN详情失败: " + (error.message || "请稍后重试"));
    } finally {
      setLoading(false);
    }
  };

  // Load related data
  const loadRelatedData = async () => {
    try {
      // Load evaluations
      const evalResponse = await ecnApi.getEvaluations(id);
      setEvaluations(evalResponse.data?.items || []);

      // Load evaluation summary
      const summaryResponse = await ecnApi.getEvaluationSummary(id);
      setEvaluationSummary(summaryResponse.data);

      // Load approvals
      const approvalResponse = await ecnApi.getApprovals(id);
      setApprovals(approvalResponse.data?.items || []);

      // Load tasks
      const taskResponse = await ecnApi.getTasks(id);
      setTasks(taskResponse.data?.items || []);

      // Load logs
      const logResponse = await ecnApi.getLogs(id);
      setLogs(logResponse.data?.items || []);

      // Load knowledge
      const knowledgeResponse = await ecnApi.getKnowledge(id);
      setKnowledge(knowledgeResponse.data?.items || []);

      // Load integrations
      const integrationResponse = await ecnApi.getIntegrations(id);
      setIntegrations(integrationResponse.data?.items || []);

    } catch (error) {
      console.error("Failed to load related data:", error);
    }
  };

  // Initialize data
  useEffect(() => {
    if (id) {
      loadECN();
    }
  }, [id]);

  useEffect(() => {
    if (ecn) {
      loadRelatedData();
    }
  }, [ecn]);

  // Event handlers
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadECN();
      await loadRelatedData();
      toast.success("数据已刷新");
    } catch (_error) {
      toast.error("刷新失败");
    } finally {
      setRefreshing(false);
    }
  };

  const handleAnalyzeBomImpact = async () => {
    if (analyzingBom) {return;}

    try {
      setAnalyzingBom(true);
      const response = await ecnApi.analyzeBomImpact(ecn.id);
      setBomImpactSummary(response.data);
      toast.success("BOM影响分析完成");
    } catch (error) {
      console.error("BOM analysis failed:", error);
      toast.error("BOM影响分析失败");
    } finally {
      setAnalyzingBom(false);
    }
  };

  const handleCheckObsoleteRisk = async () => {
    try {
      const response = await ecnApi.checkObsoleteRisk(ecn.id);
      setObsoleteRisks(response.data?.risks || []);
      toast.success("呆滞料风险分析完成");
    } catch (error) {
      console.error("Risk analysis failed:", error);
      toast.error("风险分析失败");
    }
  };

  const handleResponsibilityAllocation = (_allocationData) => {
    // Implement responsibility allocation logic
    toast.success("责任分摊已保存");
  };

  const handleRcaAnalysis = (_rcaData) => {
    // Implement RCA analysis logic
    toast.success("RCA分析已保存");
  };

  const handleCreateEvaluation = (evaluationData) => {
    // Implement evaluation creation logic
    setEvaluations((prev) => [...prev, { ...evaluationData, id: Date.now() }]);
    toast.success("评估创建成功");
  };

  const handleApprove = async (approvalData) => {
    try {
      // 使用新的统一审批API
      if (approvals.length > 0 && approvals[0].id) {
        const { approveApproval } = await import("../services/api/approval.js");
        await approveApproval(approvals[0].id, approvalData.comment || "");
        toast.success("ECN已批准");
        // 刷新ECN数据
        await loadECN();
      } else {
        setEcn((prev) => ({ ...prev, status: "APPROVED" }));
        toast.success("ECN已批准");
      }
    } catch (error) {
      console.error("Approval failed:", error);
      toast.error("审批失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleReject = async (rejectionData) => {
    try {
      // 使用新的统一审批API
      if (approvals.length > 0 && approvals[0].id) {
        const { rejectApproval } = await import("../services/api/approval.js");
        await rejectApproval(approvals[0].id, rejectionData.comment || "");
        toast.success("ECN已驳回");
        // 刷新ECN数据
        await loadECN();
      } else {
        setEcn((prev) => ({ ...prev, status: "REJECTED" }));
        toast.success("ECN已驳回");
      }
    } catch (error) {
      console.error("Rejection failed:", error);
      toast.error("驳回失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleRefreshApprovals = async () => {
    try {
      const approvalResponse = await ecnApi.getApprovals(id);
      setApprovals(approvalResponse.data?.items || []);
    } catch (error) {
      console.error("Failed to refresh approvals:", error);
    }
  };

  const handleCreateTask = (taskData) => {
    // Implement task creation logic
    setTasks((prev) => [...prev, { ...taskData, id: Date.now() }]);
    toast.success("任务创建成功");
  };

  const handleUpdateTask = (taskId, updateData) => {
    // Implement task update logic
    setTasks((prev) => prev.map((task) =>
    task.id === taskId ? { ...task, ...updateData } : task
    ));
    toast.success("任务更新成功");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
        <PageHeader
          title="ECN详情"
          subtitle="加载中..."
          actions={
          <button
            onClick={() => navigate("/ecn")}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">

              <ArrowLeft className="w-4 h-4" />
              返回列表
          </button>
          } />

        <div className="max-w-[1600px] mx-auto space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-40 bg-slate-800" />
            <Skeleton className="h-40 bg-slate-800" />
          </div>
          <Skeleton className="h-80 bg-slate-800" />
        </div>
      </div>);

  }

  if (!ecn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">ECN未找到</h2>
          <button
            onClick={() => navigate("/ecn")}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors mx-auto">

            <ArrowLeft className="w-4 h-4" />
            返回列表
          </button>
        </div>
      </div>);

  }

  const statusConfig = getStatusConfig(ecn.status);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">

      <PageHeader
        title={
        <div className="flex items-center gap-3">
            <span>ECN详情</span>
            <span className="font-mono text-xl">{ecn.ecn_no}</span>
            <span className={`px-3 py-1 rounded-full text-sm ${statusConfig.color} ${statusConfig.textColor}`}>
              {statusConfig.label}
            </span>
        </div>
        }
        subtitle={`创建时间: ${formatDate(ecn.created_time)} | 创建人: ${ecn.created_by_name || ecn.created_by}`}
        actions={
        <div className="flex items-center gap-3">
            <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors disabled:opacity-50">

              {refreshing ? "刷新中..." : "刷新"}
            </button>
            <button
            onClick={() => navigate("/ecn")}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors">

              <ArrowLeft className="w-4 h-4" />
              返回列表
            </button>
        </div>
        } />


      <div className="max-w-[1600px] mx-auto">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid grid-cols-8 w-full bg-slate-800/50 border border-slate-700">
            {tabConfigs.map((tab) =>
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className="flex items-center gap-2 data-[state=active]:bg-slate-700">

                <span>{tab.icon}</span>
                <span className="hidden sm:inline">{tab.label}</span>
            </TabsTrigger>
            )}
          </TabsList>

          {/* 基本信息 */}
          <TabsContent value="info" className="space-y-4">
            <ECNBasicInfo ecn={ecn} loading={loading} />
          </TabsContent>

          {/* 评估管理 */}
          <TabsContent value="evaluations" className="space-y-4">
            <ECNEvaluationManager
              ecn={ecn}
              evaluations={evaluations}
              evaluationSummary={evaluationSummary}
              onCreateEvaluation={handleCreateEvaluation}
              loading={loading} />

          </TabsContent>

          {/* 审批流程 */}
          <TabsContent value="approvals" className="space-y-4">
            <ECNApprovalFlow
              approvals={approvals}
              ecn={ecn}
              onApprove={handleApprove}
              onReject={handleReject}
              currentUser={currentUser}
              loading={loading}
              approvalInstance={approvals.length > 0 ? approvals[0] : null}
              onRefreshApprovals={handleRefreshApprovals}
            />
 
          </TabsContent>

          {/* 执行任务 */}
          <TabsContent value="tasks" className="space-y-4">
            <ECNTaskBoard
              tasks={tasks}
              ecn={ecn}
              onCreateTask={handleCreateTask}
              onUpdateTask={handleUpdateTask}
              currentUser={currentUser}
              loading={loading} />

          </TabsContent>

          {/* 影响分析 */}
          <TabsContent value="affected" className="space-y-4">
            <ECNImpactAnalysis
              ecn={ecn}
              bomImpactSummary={bomImpactSummary}
              obsoleteRisks={obsoleteRisks}
              onAnalyzeBomImpact={handleAnalyzeBomImpact}
              onCheckObsoleteRisk={handleCheckObsoleteRisk}
              onResponsibilityAllocation={handleResponsibilityAllocation}
              onRcaAnalysis={handleRcaAnalysis}
              analyzingBom={analyzingBom} />

          </TabsContent>

          {/* 知识库 */}
          <TabsContent value="knowledge" className="space-y-4">
            <div className="text-center py-8 text-slate-400">
              知识库功能开发中...
            </div>
          </TabsContent>

          {/* 模块集成 */}
          <TabsContent value="integration" className="space-y-4">
            <div className="text-center py-8 text-slate-400">
              模块集成功能开发中...
            </div>
          </TabsContent>

          {/* 变更日志 */}
          <TabsContent value="logs" className="space-y-4">
            <ECNChangeLog
              logs={logs}
              ecn={ecn}
              loading={loading} />

          </TabsContent>
        </Tabs>
      </div>
    </motion.div>);

}