import { useState, useCallback, useEffect } from "react";
import {
  projectApi,
  salesStatisticsApi,
  productionApi,
  contractApi,
  pmoApi,
  ecnApi,
  purchaseApi,
  departmentApi
} from "../../services/api";

export default function useGMDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [businessStats, setBusinessStats] = useState(null);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [projectHealth, setProjectHealth] = useState([]);
  const [departmentStatus, setDepartmentStatus] = useState([]);
  const [keyMetrics, setKeyMetrics] = useState([]);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const projectsResponse = await projectApi.list({
        page: 1,
        page_size: 100
      });
      const projectsData = projectsResponse.data?.items || [];

      const totalProjects = projectsData.length;
      const activeProjects = projectsData.filter(
        (p) => p.is_active && p.stage !== "S9"
      ).length;
      const completedProjects = projectsData.filter(
        (p) => p.stage === "S9"
      ).length;

      const healthGood = projectsData.filter(
        (p) => p.health === "H1" || p.health === "H2"
      ).length;
      const healthWarning = projectsData.filter(
        (p) => p.health === "H3"
      ).length;
      const healthCritical = projectsData.filter(
        (p) => p.health === "H4"
      ).length;

      const now = new Date();
      const startDate = new Date(now.getFullYear(), now.getMonth(), 1)
        .toISOString()
        .split("T")[0];
      const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0)
        .toISOString()
        .split("T")[0];

      let monthlyRevenue = 0;
      let totalContracts = 0;
      let activeContracts = 0;
      try {
        const salesResponse = await salesStatisticsApi.performance({
          start_date: startDate,
          end_date: endDate
        });
        monthlyRevenue = salesResponse.data?.total_contract_amount || 0;
      } catch (err) {
        console.error("Failed to load sales stats:", err);
      }

      try {
        const contractsResponse = await contractApi.list({
          page: 1,
          page_size: 100
        });
        const contractsData = contractsResponse.data?.items || [];
        totalContracts = contractsData.length;
        activeContracts = contractsData.filter(
          (c) => c.status === "SIGNED" || c.status === "EXECUTING"
        ).length;
      } catch (err) {
        console.error("Failed to load contracts:", err);
      }

      let productionCapacity = 0;
      let qualityPassRate = 0;
      try {
        const productionResponse = await productionApi.dashboard();
        const productionData =
          productionResponse.data || productionResponse || {};
        productionCapacity = productionData.capacity_utilization || 0;
        qualityPassRate = productionData.pass_rate || 0;
      } catch (err) {
        console.error("Failed to load production stats:", err);
      }

      const yearTarget = 150000000;
      const yearRevenue = monthlyRevenue * 12;
      const yearProgress =
        yearTarget > 0 ? (yearRevenue / yearTarget) * 100 : 0;
      const profit = yearRevenue * 0.2;
      const profitMargin = 20;

      setBusinessStats({
        monthlyRevenue,
        monthlyTarget: monthlyRevenue,
        monthlyProgress: 100,
        yearRevenue,
        yearTarget,
        yearProgress,
        profit,
        profitMargin,
        totalProjects,
        activeProjects,
        completedProjects,
        projectHealthGood: healthGood,
        projectHealthWarning: healthWarning,
        projectHealthCritical: healthCritical,
        totalContracts,
        activeContracts,
        pendingApproval: 0,
        totalCustomers: 0,
        newCustomersThisMonth: 0,
        productionCapacity,
        qualityPassRate,
        onTimeDeliveryRate: 0,
        materialArrivalRate: 0,
        revenueGrowth: 0,
        customerGrowth: 0,
        projectGrowth: 0
      });

      const healthData = projectsData.slice(0, 4).map((p) => ({
        id: p.project_code || p.id?.toString(),
        name: p.project_name || "",
        customer: p.customer_name || "",
        stage: p.stage || "",
        stageLabel: p.stage_name || "",
        progress: p.progress || 0,
        health:
          p.health === "H1"
            ? "good"
            : p.health === "H2"
              ? "good"
              : p.health === "H3"
                ? "warning"
                : "critical",
        dueDate: p.planned_end_date || "",
        amount: parseFloat(p.budget_amount || 0),
        risk: p.health === "H4" ? "high" : p.health === "H3" ? "medium" : "low"
      }));
      setProjectHealth(healthData);

      const allApprovals = [];

      try {
        const ecnRes = await ecnApi.list({
          status: "SUBMITTED",
          page_size: 10
        });
        const ecnData = ecnRes.data || ecnRes;
        const ecns = ecnData.items || ecnData || [];
        ecns.forEach((ecn) => {
          allApprovals.push({
            id: `ecn-${ecn.id}`,
            type: "project",
            title: `设计变更申请 - ${ecn.ecn_no || "ECN"}`,
            projectName: ecn.project_name || "",
            amount: parseFloat(ecn.cost_impact || 0),
            department: ecn.department || "未知部门",
            submitter: ecn.created_by_name || "未知",
            submitTime: ecn.created_at
              ? new Date(ecn.created_at).toLocaleString("zh-CN", {
                  year: "numeric",
                  month: "2-digit",
                  day: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit"
                })
              : "",
            priority:
              ecn.priority === "URGENT"
                ? "high"
                : ecn.priority === "HIGH"
                  ? "high"
                  : "medium",
            status: "pending"
          });
        });
      } catch (err) {
        console.error("Failed to load ECN approvals:", err);
      }

      try {
        const prRes = await purchaseApi.requests.list({
          status: "SUBMITTED",
          page_size: 10
        });
        const prData = prRes.data || prRes;
        const prs = prData.items || prData || [];
        prs.forEach((pr) => {
          allApprovals.push({
            id: `pr-${pr.id}`,
            type: "purchase",
            title: `采购申请 - ${pr.request_no || pr.id}`,
            item: pr.items?.map((i) => i.material_name).join(", ") || "",
            amount: parseFloat(pr.total_amount || 0),
            department: pr.department || "未知部门",
            submitter: pr.created_by_name || "未知",
            submitTime: pr.created_at
              ? new Date(pr.created_at).toLocaleString("zh-CN", {
                  year: "numeric",
                  month: "2-digit",
                  day: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit"
                })
              : "",
            priority: pr.urgent ? "high" : "medium",
            status: "pending"
          });
        });
      } catch (err) {
        console.error("Failed to load purchase request approvals:", err);
      }

      try {
        const initRes = await pmoApi.initiations.list({
          status: "SUBMITTED",
          page_size: 10
        });
        const initData = initRes.data || initRes;
        const inits = initData.items || initData || [];
        inits.forEach((init) => {
          allApprovals.push({
            id: `init-${init.id}`,
            type: "project",
            title: `项目立项申请 - ${init.project_name || init.id}`,
            projectName: init.project_name || "",
            amount: parseFloat(init.budget_amount || 0),
            department: init.department || "未知部门",
            submitter: init.created_by_name || "未知",
            submitTime: init.created_at
              ? new Date(init.created_at).toLocaleString("zh-CN", {
                  year: "numeric",
                  month: "2-digit",
                  day: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit"
                })
              : "",
            priority: init.priority === "HIGH" ? "high" : "medium",
            status: "pending"
          });
        });
      } catch (err) {
        console.error("Failed to load PMO initiation approvals:", err);
      }

      try {
        const contractRes = await contractApi.list({
          status: "PENDING_APPROVAL",
          page_size: 10
        });
        const contractData = contractRes.data || contractRes;
        const contracts = contractData.items || contractData || [];
        contracts.forEach((contract) => {
          allApprovals.push({
            id: `contract-${contract.id}`,
            type: "contract",
            title: `合同审批 - ${contract.contract_no || contract.id}`,
            customer: contract.customer_name || "",
            amount: parseFloat(contract.total_amount || 0),
            department: "销售部",
            submitter: contract.created_by_name || "未知",
            submitTime: contract.created_at
              ? new Date(contract.created_at).toLocaleString("zh-CN", {
                  year: "numeric",
                  month: "2-digit",
                  day: "2-digit",
                  hour: "2-digit",
                  minute: "2-digit"
                })
              : "",
            priority:
              parseFloat(contract.total_amount || 0) > 5000000
                ? "high"
                : "medium",
            status: "pending"
          });
        });
      } catch (err) {
        console.error("Failed to load contract approvals:", err);
      }

      allApprovals.sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        if (priorityOrder[b.priority] !== priorityOrder[a.priority]) {
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        }
        return new Date(b.submitTime) - new Date(a.submitTime);
      });
      setPendingApprovals(allApprovals.slice(0, 5));

      setBusinessStats((prev) => ({
        ...prev,
        pendingApproval: allApprovals.length
      }));

      try {
        const deptRes = await departmentApi.getStatistics({});
        const deptStats = deptRes.data || deptRes;
        if (deptStats?.departments || Array.isArray(deptStats)) {
          const departments = deptStats.departments || deptStats;
          const transformedDepts = departments.map((dept) => ({
            id: dept.id || dept.department_id,
            name: dept.name || dept.department_name || "",
            manager: dept.manager || dept.manager_name || "",
            projects: dept.projects || dept.project_count || 0,
            revenue: dept.revenue || dept.total_revenue || 0,
            target: dept.target || dept.revenue_target || 0,
            achievement:
              dept.target > 0 ? ((dept.revenue || 0) / dept.target) * 100 : 0,
            status:
              dept.status ||
              (dept.achievement >= 90
                ? "excellent"
                : dept.achievement >= 70
                  ? "good"
                  : "warning"),
            issues: dept.issues || dept.issue_count || 0,
            onTimeRate: dept.on_time_rate || dept.on_time_delivery_rate || 0,
            arrivalRate: dept.arrival_rate || dept.material_arrival_rate || 0,
            passRate: dept.pass_rate || dept.quality_pass_rate || 0
          }));
          setDepartmentStatus(transformedDepts);
        }
      } catch (err) {
        console.error("Failed to load department statistics:", err);
      }

      const metrics = [];
      const onTimeProjects = projectsData.filter((p) => {
        if (!p.planned_end_date) return false;
        const plannedDate = new Date(p.planned_end_date);
        const today = new Date();
        return plannedDate >= today || p.stage === "S9";
      }).length;
      const onTimeRate =
        totalProjects > 0 ? (onTimeProjects / totalProjects) * 100 : 0;

      metrics.push(
        {
          label: "项目按时交付率",
          value: onTimeRate,
          unit: "%",
          target: 90,
          trend: 0,
          color:
            onTimeRate >= 90
              ? "text-emerald-400"
              : onTimeRate >= 80
                ? "text-amber-400"
                : "text-red-400"
        },
        {
          label: "质量合格率",
          value: qualityPassRate,
          unit: "%",
          target: 95,
          trend: 0,
          color:
            qualityPassRate >= 95
              ? "text-emerald-400"
              : qualityPassRate >= 90
                ? "text-amber-400"
                : "text-red-400"
        },
        {
          label: "物料到货及时率",
          value: 0,
          unit: "%",
          target: 95,
          trend: 0,
          color: "text-amber-400"
        },
        {
          label: "客户满意度",
          value: 0,
          unit: "%",
          target: 95,
          trend: 0,
          color: "text-blue-400"
        }
      );
      setKeyMetrics(metrics);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
      setError(err);
      setBusinessStats(null);
      setPendingApprovals([]);
      setProjectHealth([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return {
    loading,
    error,
    businessStats,
    pendingApprovals,
    projectHealth,
    departmentStatus,
    keyMetrics,
    loadDashboard
  };
}
