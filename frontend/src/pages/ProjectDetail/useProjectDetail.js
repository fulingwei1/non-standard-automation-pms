import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import {
  projectApi,
  machineApi,
  stageApi,
  milestoneApi,
  memberApi,
  userApi,
  costApi,
  documentApi,
} from "../../services/api";
import { toast } from "../../components/ui";

export function useProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [_machines, setMachines] = useState([]);
  const [stages, setStages] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [members, setMembers] = useState([]);
  const [costs, setCosts] = useState([]);
  const [documents, setDocuments] = useState([]);

  const [_showEditDialog, setShowEditDialog] = useState(false);
  const [showAddMemberDialog, setShowAddMemberDialog] = useState(false);
  const [newMember, setNewMember] = useState({ user_id: "", role: "member", status: "active" });
  const [addingMember, setAddingMember] = useState(false);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  // Tab 状态
  const [activeTab, setActiveTab] = useState(() => searchParams.get("tab") || "overview");

  // 同步 Tab 到 URL
  useEffect(() => {
    const currentTab = searchParams.get("tab");
    if (currentTab !== activeTab && activeTab !== "overview") {
      setSearchParams({ tab: activeTab }, { replace: true });
    } else if (activeTab === "overview" && currentTab) {
      // 清除 URL 中的 tab 参数（概览是默认）
      searchParams.delete("tab");
      setSearchParams(searchParams, { replace: true });
    }
  }, [activeTab]);  

  useEffect(() => {
    fetchProjectData();
  }, [id]);  

  const fetchProjectData = async () => {
    setLoading(true);
    try {
      // 使用 Promise.allSettled 确保即使部分 API 失败也能显示项目基本信息
      const [
        projectRes,
        machinesRes,
        stagesRes,
        milestonesRes,
        membersRes,
        costsRes,
        documentsRes,
      ] = await Promise.allSettled([
        projectApi.get(id),
        machineApi.list(id),
        stageApi.list({ project_id: id }),
        milestoneApi.list({ project_id: id }),
        memberApi.list({ project_id: id }),
        costApi.list(id, {}),
        documentApi.list({ project_id: id }),
      ]);

      // 提取成功的响应数据，失败的使用默认值
      const getResultData = (result, defaultValue = []) => {
        if (result.status === "fulfilled") {
          const data = result.value?.data;
          // 处理分页响应格式 {items: [], total: ...}
          if (data && typeof data === "object" && Array.isArray(data.items)) {
            return data.items;
          }
          return data || defaultValue;
        }
        console.warn("API call failed:", result.reason?.message || result.reason);
        return defaultValue;
      };

      // 项目数据是必需的，其他数据可选
      if (projectRes.status === "fulfilled" && projectRes.value?.data) {
        setProject(projectRes.value.data);
      } else {
        console.error("Failed to fetch project:", projectRes.reason);
        setProject(null);
      }

      setMachines(getResultData(machinesRes, []));
      setStages(getResultData(stagesRes, []));
      setMilestones(getResultData(milestonesRes, []));
      setMembers(getResultData(membersRes, []));
      setCosts(getResultData(costsRes, []));
      setDocuments(getResultData(documentsRes, []));
    } catch (error) {
      console.error("Failed to fetch project data:", error);
      setProject(null);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableUsers = async () => {
    setLoadingUsers(true);
    try {
      const res = await userApi.list({ page: 1, page_size: 200, is_active: true });
      const users = res.data?.items || res.data || [];
      // 过滤掉已在项目中的成员
      const memberIds = new Set((members || []).map((m) => m.user_id));
      setAvailableUsers(users.filter((u) => !memberIds.has(u.id)));
    } catch (error) {
      console.error("加载用户列表失败:", error);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleOpenAddMember = () => {
    setShowAddMemberDialog(true);
    loadAvailableUsers();
  };

  const handleAddMember = async () => {
    if (!newMember.user_id) {
      toast.warning("请先选择要添加的成员");
      return;
    }
    setAddingMember(true);
    try {
      await memberApi.add({
        project_id: parseInt(id),
        user_id: parseInt(newMember.user_id),
        role: newMember.role,
        status: newMember.status,
      });
      setShowAddMemberDialog(false);
      setNewMember({ user_id: "", role: "member", status: "active" });
      fetchProjectData();
      toast.success("成员添加成功");
    } catch (error) {
      console.error("添加成员失败:", error);
      const status = error.response?.status;
      if (status === 409) {
        toast.error("该成员已在项目中，无需重复添加");
      } else if (status === 403) {
        toast.error("您没有添加成员的权限，请联系项目负责人");
      } else {
        toast.error("添加成员失败，请检查网络后重试");
      }
    } finally {
      setAddingMember(false);
    }
  };

  const calculateProgress = () => {
    if (!stages || stages.length === 0) return 0;
    const completedStages = (stages || []).filter((stage) => stage.status === "completed").length;
    return Math.round((completedStages / stages.length) * 100);
  };

  const calculateBudgetUtilization = (normalizedProject) => {
    const budget = normalizedProject?.budget || 0;
    if (!normalizedProject || !budget) return 0;
    const totalCosts = (costs || []).reduce((sum, cost) => sum + (cost.amount || 0), 0);
    return Math.round((totalCosts / budget) * 100);
  };

  // 标准化项目数据字段（兼容API字段名）
  const normalizedProject = project
    ? {
        ...project,
        name: project.project_name || project.name || "未命名项目",
        description: project.description || project.remark || "",
        project_number: project.project_code || project.project_number || "-",
        budget: project.budget_amount || project.budget || 0,
        start_date: project.planned_start_date || project.start_date,
        end_date: project.planned_end_date || project.end_date,
        manager_name: project.pm_name || project.manager?.name || "-",
        customer_name: project.customer_name || project.customer?.name || "-",
        priority: project.priority || "medium",
      }
    : null;

  return {
    id,
    navigate,
    loading,
    project,
    normalizedProject,
    stages,
    milestones,
    members,
    costs,
    documents,
    activeTab,
    setActiveTab,
    showAddMemberDialog,
    setShowAddMemberDialog,
    newMember,
    setNewMember,
    addingMember,
    availableUsers,
    loadingUsers,
    setShowEditDialog,
    fetchProjectData,
    handleOpenAddMember,
    handleAddMember,
    calculateProgress,
    calculateBudgetUtilization,
  };
}
