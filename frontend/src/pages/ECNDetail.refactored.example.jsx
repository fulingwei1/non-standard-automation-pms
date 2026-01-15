/**
 * ECN Detail Page - 重构示例
 * 
 * 这是重构后的 ECNDetail 页面示例
 * 原始文件: ECNDetail.jsx (3,546 行)
 * 重构后: ECNDetail.refactored.jsx (预计 < 300 行)
 * 
 * 使用方法:
 * 1. 完成所有子组件拆分后
 * 2. 将此文件重命名为 ECNDetail.jsx 替换原文件
 * 3. 删除原 ECNDetail.jsx (或重命名为 ECNDetail.legacy.jsx 备份)
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { toast } from "sonner";
import { ecnApi } from "../services/api";

// 导入拆分后的组件
import {
  ECNDetailHeader,
  ECNInfoTab,
  // TODO: 导入其他拆分的组件
  // ECNEvaluationsTab,
  // ECNApprovalsTab,
  // ECNTasksTab,
  // ECNImpactAnalysisTab,
  // ECNLogsTab,
} from "../components/ecn";

export default function ECNDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  // ==================== 状态管理 ====================
  const [ecn, setECN] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("info");
  const [permissions, setPermissions] = useState({
    canEdit: false,
    canSubmit: false,
    canWithdraw: false,
    canStartEval: false,
    canApprove: false,
    canExecute: false,
    canVerify: false,
    canClose: false,
  });

  // ==================== 数据获取 ====================
  const fetchECN = async () => {
    try {
      setLoading(true);
      const res = await ecnApi.getECN(id);
      setECN(res.data);
      calculatePermissions(res.data);
    } catch (error) {
      console.error("Failed to fetch ECN:", error);
      toast.error("获取ECN详情失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchECN();
    }
  }, [id]);

  // ==================== 权限计算 ====================
  const calculatePermissions = (ecnData) => {
    if (!ecnData) return;

    // TODO: 根据当前用户角色和ECN状态计算权限
    // 这里是简化版本，实际应该从后端获取或根据业务规则计算
    const newPermissions = {
      canEdit: ecnData.status === "DRAFT",
      canSubmit: ecnData.status === "DRAFT",
      canWithdraw: ["SUBMITTED", "EVALUATING"].includes(ecnData.status),
      canStartEval: ecnData.status === "SUBMITTED",
      canApprove: ecnData.status === "PENDING_APPROVAL",
      canExecute: ecnData.status === "APPROVED",
      canVerify: ecnData.status === "EXECUTING",
      canClose: ecnData.status === "COMPLETED",
    };

    setPermissions(newPermissions);
  };

  // ==================== 事件处理 ====================
  const handleBack = () => {
    navigate(-1);
  };

  const handleRefresh = () => {
    fetchECN();
  };

  const handleEdit = () => {
    // TODO: 打开编辑对话框或跳转编辑页面
    toast.info("编辑功能开发中");
  };

  const handleSubmit = async () => {
    try {
      await ecnApi.submitECN(id);
      toast.success("提交成功");
      fetchECN();
    } catch (error) {
      toast.error("提交失败");
    }
  };

  const handleWithdraw = async () => {
    try {
      await ecnApi.withdrawECN(id);
      toast.success("撤回成功");
      fetchECN();
    } catch (error) {
      toast.error("撤回失败");
    }
  };

  const handleStartEval = async () => {
    try {
      await ecnApi.startEvaluation(id);
      toast.success("已开始评估");
      fetchECN();
    } catch (error) {
      toast.error("操作失败");
    }
  };

  const handleApprove = async () => {
    // TODO: 打开审批对话框
    toast.info("审批功能开发中");
  };

  const handleReject = async () => {
    // TODO: 打开驳回对话框
    toast.info("驳回功能开发中");
  };

  const handleExecute = async () => {
    try {
      await ecnApi.startExecution(id);
      toast.success("已开始执行");
      fetchECN();
    } catch (error) {
      toast.error("操作失败");
    }
  };

  const handleVerify = async () => {
    // TODO: 打开验证对话框
    toast.info("验证功能开发中");
  };

  const handleClose = async () => {
    try {
      await ecnApi.closeECN(id);
      toast.success("ECN已关闭");
      fetchECN();
    } catch (error) {
      toast.error("操作失败");
    }
  };

  // ==================== 渲染 ====================
  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <ECNDetailHeader
        ecn={ecn}
        loading={loading}
        onBack={handleBack}
        onRefresh={handleRefresh}
        onEdit={handleEdit}
        onSubmit={handleSubmit}
        onWithdraw={handleWithdraw}
        onStartEval={handleStartEval}
        onApprove={handleApprove}
        onReject={handleReject}
        onExecute={handleExecute}
        onVerify={handleVerify}
        onClose={handleClose}
        {...permissions}
      />

      {/* 标签页内容 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="info">基本信息</TabsTrigger>
          <TabsTrigger value="evaluations">评估管理</TabsTrigger>
          <TabsTrigger value="approvals">审批流程</TabsTrigger>
          <TabsTrigger value="tasks">执行任务</TabsTrigger>
          <TabsTrigger value="impact">影响分析</TabsTrigger>
          <TabsTrigger value="logs">变更日志</TabsTrigger>
        </TabsList>

        <TabsContent value="info" className="mt-6">
          <ECNInfoTab ecn={ecn} />
        </TabsContent>

        <TabsContent value="evaluations" className="mt-6">
          {/* TODO: 使用 ECNEvaluationsTab 组件 */}
          <div className="text-center py-12 text-slate-500">
            评估管理组件待拆分
          </div>
        </TabsContent>

        <TabsContent value="approvals" className="mt-6">
          {/* TODO: 使用 ECNApprovalsTab 组件 */}
          <div className="text-center py-12 text-slate-500">
            审批流程组件待拆分
          </div>
        </TabsContent>

        <TabsContent value="tasks" className="mt-6">
          {/* TODO: 使用 ECNTasksTab 组件 */}
          <div className="text-center py-12 text-slate-500">
            执行任务组件待拆分
          </div>
        </TabsContent>

        <TabsContent value="impact" className="mt-6">
          {/* TODO: 使用 ECNImpactAnalysisTab 组件 */}
          <div className="text-center py-12 text-slate-500">
            影响分析组件待拆分
          </div>
        </TabsContent>

        <TabsContent value="logs" className="mt-6">
          {/* TODO: 使用 ECNLogsTab 组件 */}
          <div className="text-center py-12 text-slate-500">
            变更日志组件待拆分
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

/**
 * 重构总结
 * 
 * 拆分前:
 * - ECNDetail.jsx: 3,546 行
 * - 所有逻辑混在一起
 * - 难以维护和测试
 * 
 * 拆分后:
 * - ECNDetail.jsx: ~250 行（主组件）
 * - ecnConstants.js: 67 行（配置）
 * - ECNDetailHeader.jsx: 154 行（头部）
 * - ECNInfoTab.jsx: 213 行（基本信息）
 * - ECNEvaluationsTab.jsx: ~250 行（评估）
 * - ECNApprovalsTab.jsx: ~250 行（审批）
 * - ECNTasksTab.jsx: ~300 行（任务）
 * - ECNImpactAnalysisTab.jsx: ~200 行（影响分析）
 * - ECNLogsTab.jsx: ~150 行（日志）
 * 
 * 效益:
 * - ✅ 代码量减少 90%（单文件）
 * - ✅ 职责清晰，易于理解
 * - ✅ 独立测试和维护
 * - ✅ 提高代码复用性
 * - ✅ 改善性能（配合懒加载）
 */
