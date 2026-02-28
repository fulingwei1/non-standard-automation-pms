/**
 * ECN Management Page
 * 拆分后的主组件：负责状态管理与数据获取
 */
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "../components/layout";
import { Card, CardContent } from "../components/ui/card";
import { formatDate } from "../lib/utils";
import { ecnApi, projectApi, memberApi } from "../services/api";
import {
  ECNBatchActions,
  ECNCreateDialog,
  ECNListHeader,
  ECNListTable,
  ECNStatsCards,
} from "../components/ecn";
import {
  filterOptions,
  getPriorityLabel,
  getStatusLabel,
  getTypeLabel,
} from "@/lib/constants/ecn";

import { confirmAction } from "@/lib/confirmAction";
export default function ECNManagement() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [ecns, setEcns] = useState([]);
  const [projects, setProjects] = useState([]);
  const [userProjects, setUserProjects] = useState([]); // 用户参与的项目
  const [userMachines, setUserMachines] = useState([]); // 用户参与项目的设备

  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterPriority, setFilterPriority] = useState("");

  const [selectedECNIds, setSelectedECNIds] = useState(new Set());
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    fetchECNs();
  }, [filterProject, filterType, filterStatus, filterPriority, searchKeyword]);

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      const allProjects = res.data?.items || res.data?.items || res.data || [];
      setProjects(allProjects);

      // 获取用户参与的项目
      await fetchUserProjects(allProjects);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  // 获取当前用户参与的项目及其设备
  const fetchUserProjects = async (allProjects) => {
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) return;

      const user = JSON.parse(userStr);
      const userId = user?.id;
      if (!userId) return;

      // 获取每个项目的成员，筛选出用户参与的项目
      const userProjectIds = [];
      for (const project of allProjects) {
        try {
          const membersRes = await memberApi.list({ project_id: project.id });
          const members = membersRes.data?.items || membersRes.data?.items || membersRes.data || [];
          const isMember = members.some(m => m.user_id === userId);
          if (isMember) {
            userProjectIds.push(project.id);
          }
        } catch (_error) {
          // 忽略单个项目的成员获取失败
        }
      }

      // 筛选用户参与的项目
      const filteredProjects = allProjects.filter(p => userProjectIds.includes(p.id));
      setUserProjects(filteredProjects);

      // 获取这些项目的设备
      await fetchUserMachines(filteredProjects);
    } catch (error) {
      console.error("Failed to fetch user projects:", error);
    }
  };

  // 获取用户参与项目的设备
  const fetchUserMachines = async (projects) => {
    try {
      const allMachines = [];
      for (const project of projects) {
        try {
          const machinesRes = await projectApi.getMachines(project.id);
          const machines = machinesRes.data?.items || machinesRes.data?.items || machinesRes.data || [];
          allMachines.push(...machines);
        } catch (_error) {
          // 忽略单个项目的设备获取失败
        }
      }
      setUserMachines(allMachines);
    } catch (error) {
      console.error("Failed to fetch user machines:", error);
    }
  };

  const fetchECNs = async () => {
    try {
      setLoading(true);

      const params = { page_size: 1000 };
      if (filterProject && filterProject !== "all") {
        params.project_id = Number(filterProject);
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
      setEcns(res.data?.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch ECNs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = (ecn) => {
    if (!ecn?.id) {return;}
    navigate(`${ecn.id}`);
  };

  const handleSubmit = async (ecnId) => {
    if (!await confirmAction("确认提交此ECN？提交后将进入评估流程。")) {return;}
    try {
      await ecnApi.submit(ecnId, { remark: "" });
      await fetchECNs();
    } catch (error) {
      console.error("Failed to submit ECN:", error);
      alert("提交失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateECN = async (formData) => {
    try {
      await ecnApi.create(formData);
      setShowCreateDialog(false);
      await fetchECNs();
    } catch (error) {
      console.error("Failed to create ECN:", error);
      throw error;
    }
  };

  const exportECNsToCsv = (ecnList, filenamePrefix) => {
    const rows = [
      [
        "ECN编号",
        "ECN标题",
        "项目",
        "类型",
        "状态",
        "优先级",
        "申请人",
        "申请时间",
        "成本影响",
        "工期影响",
      ],
      ...ecnList.map((ecn) => [
        ecn.ecn_no || "",
        ecn.ecn_title || "",
        ecn.project_name || "",
        getTypeLabel(ecn.ecn_type),
        getStatusLabel(ecn.status),
        getPriorityLabel(ecn.priority),
        ecn.applicant_name || "",
        formatDate(ecn.applied_at || ecn.created_at) || "",
        ecn.cost_impact ? `¥${ecn.cost_impact}` : "¥0",
        ecn.schedule_impact_days ? `${ecn.schedule_impact_days}天` : "0天",
      ]),
    ];

    const escapeCell = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
    const csvContent = rows.map((row) => row.map(escapeCell).join(",")).join("\n");

    const BOM = "\uFEFF";
    const blob = new Blob([BOM + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filenamePrefix}_${new Date().toISOString().split("T")[0]}.csv`;
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleExportList = () => {
    try {
      setExporting(true);
      exportECNsToCsv(ecns, "ECN列表");
    } catch (error) {
      console.error("导出失败:", error);
      alert("导出失败: " + (error?.message || error));
    } finally {
      setExporting(false);
    }
  };

  const handleBatchSubmit = async (ecnIds, remark) => {
    await Promise.all(
      Array.from(ecnIds).map((id) => ecnApi.submit(id, { remark: remark || "批量提交" })),
    );
    await fetchECNs();
  };

  const handleBatchClose = async (ecnIds, closeNote) => {
    await Promise.all(
      Array.from(ecnIds).map((id) => ecnApi.close(id, { close_note: closeNote || "批量关闭" })),
    );
    await fetchECNs();
  };

  const handleBatchExport = async (ecnIds) => {
    const selected = ecns.filter((ecn) => ecnIds.has(ecn.id));
    exportECNsToCsv(selected, "ECN批量导出");
  };

  const handleClearSelection = () => {
    setSelectedECNIds(new Set());
  };

  const stats = useMemo(() => {
    const total = ecns.length;
    const pending = ecns.filter((ecn) =>
      ["SUBMITTED", "EVALUATING", "PENDING_APPROVAL"].includes(ecn.status),
    ).length;
    const inProgress = ecns.filter((ecn) =>
      ["EXECUTING", "PENDING_VERIFY"].includes(ecn.status),
    ).length;
    const completed = ecns.filter((ecn) => ecn.status === "COMPLETED").length;
    const urgent = ecns.filter((ecn) => ecn.priority === "URGENT").length;
    const high = ecns.filter((ecn) => ecn.priority === "HIGH").length;

    return { total, pending, inProgress, completed, urgent, high };
  }, [ecns]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="ECN变更管理"
        description="管理工程变更通知单的创建、评估、审批和执行"
      />

      <ECNStatsCards stats={stats} ecns={ecns} />

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
        onExport={handleExportList}
      />

      <ECNBatchActions
        selectedECNIds={selectedECNIds}
        ecns={ecns}
        onBatchSubmit={handleBatchSubmit}
        onBatchClose={handleBatchClose}
        onBatchExport={handleBatchExport}
        onClearSelection={handleClearSelection}
      />

      <Card>
        <CardContent className="p-0">
          <ECNListTable
            ecns={ecns}
            loading={loading}
            selectedECNIds={selectedECNIds}
            onSelectionChange={setSelectedECNIds}
            onViewDetail={handleViewDetail}
            onSubmit={handleSubmit}
          />
        </CardContent>
      </Card>

      <ECNCreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        projects={userProjects.length > 0 ? userProjects : projects}
        machines={userMachines}
        onCreateECN={handleCreateECN}
      />
    </div>
  );
}
