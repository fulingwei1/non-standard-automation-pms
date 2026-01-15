/**
 * ECN Management Page - Refactored Version
 * ECN管理页面 - 重构版本
 * 
 * 拆分后的主组件，负责整体状态管理和组件协调
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "../components/layout";
import {
  ECNListHeader,
  ECNStatsCards,
  ECNListTable,
  ECNBatchActions,
  ECNCreateDialog,
} from "../components/ecn";
import { Card, CardContent } from "../components/ui/card";
import { Dialog } from "../components/ui/dialog";
import { ecnApi, projectApi, materialApi, purchaseApi } from "../services/api";
import { formatDate } from "../lib/utils";
import { 
  statusConfigs,
  typeConfigs,
  priorityConfigs,
  filterOptions
} from "../components/ecn/ecnManagementConstants";

export default function ECNManagement() {
  const navigate = useNavigate();

  // 核心数据状态
  const [loading, setLoading] = useState(true);
  const [ecns, setEcns] = useState([]);
  const [projects, setProjects] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);

  // 筛选状态
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");

  // 对话框状态
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedECN, setSelectedECN] = useState(null);
  const [activeTab, setActiveTab] = useState("info");

  // 批量操作状态
  const [selectedECNIds, setSelectedECNIds] = useState(new Set());
  const [showBatchDialog, setShowBatchDialog] = useState(false);
  const [batchOperation, setBatchOperation] = useState("");
  const [exporting, setExporting] = useState(false);

  // 详情数据状态
  const [evaluations, setEvaluations] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [affectedMaterials, setAffectedMaterials] = useState([]);
  const [affectedOrders, setAffectedOrders] = useState([]);
  const [logs, setLogs] = useState([]);
  const [evaluationSummary, setEvaluationSummary] = useState(null);

  // 初始化数据
  useEffect(() => {
    fetchProjects();
    fetchECNs();
  }, [filterProject, filterType, filterStatus, filterPriority, searchKeyword]);

  // 获取项目列表
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  // 获取ECN列表
  const fetchECNs = async () => {
    try {
      setLoading(true);
      const params = {};
      
      if (filterProject && filterProject !== "all") {
        params.project_id = filterProject;
      }
      if (filterType && filterType !== "all") {
        params.ecn_type = filterType;
      }
      if (filterStatus && filterStatus !== "all") {
        params.status = filterStatus;
      }
      if (filterPriority && filterPriority !== "all") {
        params.priority = filterPriority;
      }
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }

      const res = await ecnApi.list(params);
      const ecnList = res.data?.items || res.data || [];
      setEcns(ecnList);
    } catch (error) {
      console.error("Failed to fetch ECNs:", error);
    } finally {
      setLoading(false);
    }
  };

  // 查看ECN详情
  const handleViewDetail = async (ecn) => {
    setSelectedECN(ecn);
    setShowDetailDialog(true);
    setActiveTab("info");

    try {
      // 并行获取详情数据
      const [
        evaluationsRes,
        approvalsRes,
        tasksRes,
        materialsRes,
        ordersRes,
        logsRes,
      ] = await Promise.all([
        ecnApi.getEvaluations(ecn.id),
        ecnApi.getApprovals(ecn.id),
        ecnApi.getTasks(ecn.id),
        ecnApi.getAffectedMaterials(ecn.id),
        ecnApi.getAffectedOrders(ecn.id),
        ecnApi.getLogs(ecn.id),
      ]);

      setEvaluations(evaluationsRes.data || []);
      setApprovals(approvalsRes.data || []);
      setTasks(tasksRes.data || []);
      setAffectedMaterials(materialsRes.data || []);
      setAffectedOrders(ordersRes.data || []);
      setLogs(logsRes.data || []);

      // 计算评估汇总
      if (evaluationsRes.data?.length > 0) {
        const summary = {
          total: evaluationsRes.data.length,
          approved: evaluationsRes.data.filter(e => e.eval_result === 'APPROVED').length,
          conditional: evaluationsRes.data.filter(e => e.eval_result === 'CONDITIONAL').length,
          rejected: evaluationsRes.data.filter(e => e.eval_result === 'REJECTED').length,
        };
        setEvaluationSummary(summary);
      }
    } catch (error) {
      console.error("Failed to fetch ECN details:", error);
    }
  };

  // 创建ECN
  const handleCreateECN = async (formData) => {
    try {
      await ecnApi.create(formData);
      setShowCreateDialog(false);
      fetchECNs();
    } catch (error) {
      console.error("Failed to create ECN:", error);
      throw error;
    }
  };

  // 批量操作处理函数
  const handleBatchSubmit = async (ecnIds, comment) => {
    try {
      await Promise.all(
        Array.from(ecnIds).map(id => ecnApi.submit(id, { comment }))
      );
      fetchECNs();
    } catch (error) {
      console.error("Failed to submit ECNs:", error);
      throw error;
    }
  };

  const handleBatchApprove = async (ecnIds, comment) => {
    try {
      await Promise.all(
        Array.from(ecnIds).map(id => ecnApi.approve(id, { comment }))
      );
      fetchECNs();
    } catch (error) {
      console.error("Failed to approve ECNs:", error);
      throw error;
    }
  };

  const handleBatchReject = async (ecnIds, comment) => {
    try {
      await Promise.all(
        Array.from(ecnIds).map(id => ecnApi.reject(id, { comment }))
      );
      fetchECNs();
    } catch (error) {
      console.error("Failed to reject ECNs:", error);
      throw error;
    }
  };

  const handleBatchClose = async (ecnIds, comment) => {
    try {
      await Promise.all(
        Array.from(ecnIds).map(id => ecnApi.close(id, { comment }))
      );
      fetchECNs();
    } catch (error) {
      console.error("Failed to close ECNs:", error);
      throw error;
    }
  };

  const handleBatchExport = async (ecnIds) => {
    try {
      setExporting(true);
      const ecnList = Array.from(ecnIds).map(id => 
        ecns.find(ecn => ecn.id === id)
      ).filter(Boolean);
      
      // 这里可以调用导出API或下载功能
      await ecnApi.export({ ecn_ids: Array.from(ecnIds) });
    } catch (error) {
      console.error("Failed to export ECNs:", error);
      throw error;
    } finally {
      setExporting(false);
    }
  };

  // 清除选择
  const handleClearSelection = () => {
    setSelectedECNIds(new Set());
  };

  // 计算统计数据
  const stats = useMemo(() => {
    const total = ecns.length;
    const pending = ecns.filter(ecn => 
      ['SUBMITTED', 'EVALUATING', 'PENDING_APPROVAL'].includes(ecn.status)
    ).length;
    const inProgress = ecns.filter(ecn => 
      ['EXECUTING', 'PENDING_VERIFY'].includes(ecn.status)
    ).length;
    const completed = ecns.filter(ecn => ecn.status === 'COMPLETED').length;
    const urgent = ecns.filter(ecn => ecn.priority === 'URGENT').length;
    const high = ecns.filter(ecn => ecn.priority === 'HIGH').length;
    
    return {
      total,
      pending,
      inProgress,
      completed,
      urgent,
      high,
    };
  }, [ecns]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="ECN变更管理"
        description="管理工程变更通知单的创建、评估、审批和执行"
      />

      <div className="space-y-6">
        {/* 统计卡片 */}
        <ECNStatsCards stats={stats} ecns={ecns} />

        {/* 列表头部 - 搜索和筛选 */}
        <ECNListHeader
          searchKeyword={searchKeyword}
          onSearchChange={setSearchKeyword}
          filterProject={filterProject}
          onProjectChange={setFilterProject}
          filterType={filterType}
          onTypeChange={setFilterType}
          filterStatus={filterStatus}
          onStatusChange={setFilterStatus}
          filterPriority={filterPriority}
          onPriorityChange={setFilterPriority}
          projects={projects}
          filterOptions={filterOptions}
          onCreateECN={() => setShowCreateDialog(true)}
          onRefresh={fetchECNs}
          exporting={exporting}
          onExport={() => handleBatchExport(selectedECNIds)}
        />

        {/* 批量操作栏 */}
        <ECNBatchActions
          selectedECNIds={selectedECNIds}
          ecns={ecns}
          onBatchSubmit={handleBatchSubmit}
          onBatchApprove={handleBatchApprove}
          onBatchReject={handleBatchReject}
          onBatchClose={handleBatchClose}
          onBatchExport={handleBatchExport}
          onClearSelection={handleClearSelection}
        />

        {/* ECN列表表格 */}
        <Card>
          <CardContent className="p-0">
            <ECNListTable
              ecns={ecns}
              loading={loading}
              selectedECNIds={selectedECNIds}
              onSelectionChange={setSelectedECNIds}
              onViewDetail={handleViewDetail}
            />
          </CardContent>
        </Card>
      </div>

      {/* 创建ECN对话框 */}
      <ECNCreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        projects={projects}
        materials={materials}
        onCreateECN={handleCreateECN}
      />

      {/* ECN详情对话框 - 这里可以继续拆分 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <div className="max-w-6xl max-h-[90vh] overflow-y-auto bg-white dark:bg-slate-950 rounded-lg">
          {/* TODO: 这里可以集成之前拆分的ECNDetail组件 */}
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">ECN详情</h2>
            <p>ECN详情内容待实现...</p>
          </div>
        </div>
      </Dialog>
    </div>
  );
}