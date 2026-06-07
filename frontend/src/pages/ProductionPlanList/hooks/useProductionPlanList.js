import { useState, useEffect, useMemo, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { productionApi, projectApi } from "../../../services/api";
import { getProjectContextFilters } from "../../../lib/projectContext";
import { confirmAction } from "@/lib/confirmAction";
import { INITIAL_NEW_PLAN } from "../constants";

const toContextProjectIdNumber = (projectId) => {
  const parsed = Number(projectId);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
};

export function useProductionPlanList() {
  const [searchParams] = useSearchParams();
  const projectContextFilters = useMemo(
    () => getProjectContextFilters(searchParams),
    [searchParams],
  );
  const contextProjectId = projectContextFilters.project_id || "";
  const contextProjectIdNumber = toContextProjectIdNumber(contextProjectId);
  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState([]);
  const [projects, setProjects] = useState([]);
  const [workshops, setWorkshops] = useState([]);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterProject, setFilterProject] = useState(contextProjectId);
  const [filterWorkshop, setFilterWorkshop] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  // Create form state
  const [newPlan, setNewPlan] = useState({
    ...INITIAL_NEW_PLAN,
    project_id: contextProjectIdNumber,
  });

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page_size: 1000, ...projectContextFilters });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  }, [projectContextFilters]);

  const fetchWorkshops = useCallback(async () => {
    try {
      const res = await productionApi.workshops.list({ page_size: 1000 });
      setWorkshops(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch workshops:", error);
    }
  }, []);

  const fetchPlans = useCallback(async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterType)     params.plan_type   = filterType;
      if (filterProject)  params.project_id  = filterProject;
      if (filterWorkshop) params.workshop_id = filterWorkshop;
      if (filterStatus)   params.status      = filterStatus;
      if (searchKeyword)  params.search      = searchKeyword;
      const res = await productionApi.productionPlans.list(params);
      setPlans(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch plans:", error);
    } finally {
      setLoading(false);
    }
  }, [filterType, filterProject, filterWorkshop, filterStatus, searchKeyword]);

  useEffect(() => {
    fetchProjects();
    fetchWorkshops();
  }, [fetchProjects, fetchWorkshops]);

  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  useEffect(() => {
    if (contextProjectId) {
      setFilterProject(contextProjectId);
      setNewPlan((prev) => ({
        ...prev,
        project_id: contextProjectIdNumber,
      }));
    }
  }, [contextProjectId, contextProjectIdNumber]);

  const filteredPlans = useMemo(() => {
    return (plans || []).filter((plan) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          plan.plan_no?.toLowerCase().includes(keyword) ||
          plan.plan_name?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [plans, searchKeyword]);

  const handleCreatePlan = async () => {
    if (!newPlan.plan_name || !newPlan.plan_start_date || !newPlan.plan_end_date) {
      alert("请填写计划名称和日期");
      return;
    }
    try {
      await productionApi.productionPlans.create(newPlan);
      setShowCreateDialog(false);
      setNewPlan({
        ...INITIAL_NEW_PLAN,
        project_id: contextProjectIdNumber,
      });
      fetchPlans();
    } catch (error) {
      console.error("Failed to create plan:", error);
      alert("创建计划失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (planId) => {
    try {
      const res = await productionApi.productionPlans.get(planId);
      setSelectedPlan(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch plan detail:", error);
    }
  };

  const handlePublish = async (planId) => {
    if (!await confirmAction("确认发布此生产计划？")) return;
    try {
      await productionApi.productionPlans.publish(planId);
      fetchPlans();
      if (showDetailDialog) {
        handleViewDetail(planId);
      }
    } catch (error) {
      console.error("Failed to publish plan:", error);
      alert("发布失败: " + (error.response?.data?.detail || error.message));
    }
  };

  return {
    // data
    loading,
    filteredPlans,
    projects,
    workshops,
    // filters
    searchKeyword, setSearchKeyword,
    filterType,    setFilterType,
    filterProject, setFilterProject,
    filterWorkshop, setFilterWorkshop,
    filterStatus,  setFilterStatus,
    // dialogs
    showCreateDialog, setShowCreateDialog,
    showDetailDialog, setShowDetailDialog,
    selectedPlan,
    // form
    newPlan, setNewPlan,
    // actions
    handleCreatePlan,
    handleViewDetail,
    handlePublish,
  };
}
