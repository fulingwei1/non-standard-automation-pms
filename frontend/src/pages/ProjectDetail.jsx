import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../lib/utils";
import {
  projectApi,
  machineApi,
  stageApi,
  milestoneApi,
  memberApi,
  costApi,
  documentApi,
  financialCostApi as _financialCostApi,
  presaleExpenseApi as _presaleExpenseApi } from
"../services/api";
import { formatDate, formatCurrency, getStageName as _getStageName } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  HealthBadge,
  Progress,
  CircularProgress,
  Skeleton,
  UserAvatar,
  AvatarGroup,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter } from
"../components/ui";
import GateCheckPanel from "../components/project/GateCheckPanel";
import QuickActionPanel from "../components/project/QuickActionPanel";
import ProjectBonusPanel from "../components/project/ProjectBonusPanel";
import ProjectMeetingPanel from "../components/project/ProjectMeetingPanel";
import ProjectIssuePanel from "../components/project/ProjectIssuePanel";
import SolutionLibrary from "../components/project/SolutionLibrary";
import StageGantt from "../components/project/StageGantt";
import ProgressForecast from "./ProgressForecast";
import DependencyCheck from "./DependencyCheck";
import { projectWorkspaceApi as _projectWorkspaceApi } from "../services/api";
import {
  ArrowLeft,
  Edit2,
  MoreHorizontal,
  Briefcase,
  Users,
  Calendar,
  DollarSign,
  FileText,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  Target,
  Activity,
  Settings,
  Download,
  Share,
  Plus } from
"lucide-react";

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [_machines, setMachines] = useState([]);
  const [stages, setStages] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [members, setMembers] = useState([]);
  const [costs, setCosts] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showAddMemberDialog, setShowAddMemberDialog] = useState(false);
  const [newMember, setNewMember] = useState({ user_id: "", role: "member", status: "active" });
  const [addingMember, setAddingMember] = useState(false);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

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
      documentsRes] =
      await Promise.allSettled([
      projectApi.get(id),
      machineApi.list(id),
      stageApi.list({ project_id: id }),
      milestoneApi.list({ project_id: id }),
      memberApi.list({ project_id: id }),
      costApi.list(id, {}),
      documentApi.list({ project_id: id })]
      );

      // 提取成功的响应数据，失败的使用默认值
      const getResultData = (result, defaultValue = []) => {
        if (result.status === 'fulfilled') {
          const data = result.value?.data;
          // 处理分页响应格式 {items: [], total: ...}
          if (data && typeof data === 'object' && Array.isArray(data.items)) {
            return data.items;
          }
          return data || defaultValue;
        }
        console.warn('API call failed:', result.reason?.message || result.reason);
        return defaultValue;
      };

      // 项目数据是必需的，其他数据可选
      if (projectRes.status === 'fulfilled' && projectRes.value?.data) {
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

  const handleOpenAddMember = () => {
    setShowAddMemberDialog(true);
    loadAvailableUsers();
  };

  const handleAddMember = async () => {

  const loadAvailableUsers = async () => {
    setLoadingUsers(true);
    try {
      const res = await userApi.list({ page: 1, page_size: 200, is_active: true });
      const users = res.data?.items || res.data || [];
      // 过滤掉已在项目中的成员
      const memberIds = new Set((members || []).map(m => m.user_id));
      setAvailableUsers(users.filter(u => !memberIds.has(u.id)));
    } catch (error) {
      console.error("加载用户列表失败:", error);
    } finally {
      setLoadingUsers(false);
    }
  };
    if (!newMember.user_id) {
      alert("请选择成员");
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
      alert("成员添加成功");
    } catch (error) {
      console.error("添加成员失败:", error);
      alert("添加失败：" + (error.response?.data?.message || error.message));
    } finally {
      setAddingMember(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      planning: { label: "规划中", color: "bg-gray-500" },
      in_progress: { label: "进行中", color: "bg-blue-500" },
      on_hold: { label: "暂停", color: "bg-yellow-500" },
      completed: { label: "已完成", color: "bg-green-500" },
      cancelled: { label: "已取消", color: "bg-red-500" },
      archived: { label: "已归档", color: "bg-purple-500" }
    };

    const config = statusConfig[status];
    return config ?
    <Badge className={cn(config.color, "text-white")}>
        {config.label}
    </Badge> :

    <Badge variant="secondary">{status}</Badge>;

  };

  const getPriorityBadge = (priority) => {
    const priorityConfig = {
      low: { label: "低", color: "bg-green-500" },
      medium: { label: "中", color: "bg-yellow-500" },
      high: { label: "高", color: "bg-red-500" },
      critical: { label: "关键", color: "bg-red-600" }
    };

    const config = priorityConfig[priority];
    return config ?
    <Badge className={cn(config.color, "text-white")}>
        {config.label}
    </Badge> :

    <Badge variant="secondary">{priority}</Badge>;

  };

  const calculateProgress = () => {
    if (!stages || stages.length === 0) {return 0;}
    const completedStages = (stages || []).filter((stage) => stage.status === 'completed').length;
    return Math.round(completedStages / stages.length * 100);
  };

  const calculateBudgetUtilization = () => {
    const budget = project?.budget_amount || project?.budget || 0;
    if (!project || !budget) {return 0;}
    const totalCosts = (costs || []).reduce((sum, cost) => sum + (cost.amount || 0), 0);
    return Math.round(totalCosts / budget * 100);
  };

  // 标准化项目数据字段（兼容API字段名）
  const normalizedProject = project ? {
    ...project,
    name: project.project_name || project.name || '未命名项目',
    description: project.description || project.remark || '',
    project_number: project.project_code || project.project_number || '-',
    budget: project.budget_amount || project.budget || 0,
    start_date: project.planned_start_date || project.start_date,
    end_date: project.planned_end_date || project.end_date,
    manager_name: project.pm_name || project.manager?.name || '-',
    customer_name: project.customer_name || project.customer?.name || '-',
    priority: project.priority || 'medium'
  } : null;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <Skeleton className="h-10 w-10" />
          <Skeleton className="h-8 w-64" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, i) =>
          <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-4 w-24 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
          </Card>
          )}
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-6 w-32 mb-4" />
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) =>
              <div key={i} className="flex items-center space-x-4">
                  <Skeleton className="h-10 w-10" />
                  <div className="flex-1">
                    <Skeleton className="h-4 w-48 mb-2" />
                    <Skeleton className="h-3 w-32" />
                  </div>
              </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>);

  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">项目未找到</h3>
        <p className="text-gray-500 mb-4">请检查项目ID是否正确</p>
        <Button onClick={() => navigate("/projects")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回项目列表
        </Button>
      </div>);

  }

  // 使用标准化后的项目数据进行渲染
  const p = normalizedProject;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6">

      <PageHeader
        title={p.name}
        description={p.description}
        actions={
        <div className="flex space-x-2">
            <Button variant="outline" onClick={() => setShowEditDialog(true)}>
              <Edit2 className="mr-2 h-4 w-4" />
              编辑
            </Button>
            <Button variant="outline">
              <Share className="mr-2 h-4 w-4" />
              分享
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              导出
            </Button>
        </div>
        } />


      {/* 项目概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">项目状态</p>
                <div className="mt-2">{getStatusBadge(p.status)}</div>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">优先级</p>
                <div className="mt-2">{getPriorityBadge(p.priority)}</div>
              </div>
              <Target className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">进度</p>
                <p className="text-2xl font-bold">{calculateProgress()}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
            <Progress value={calculateProgress()} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">预算使用</p>
                <p className="text-2xl font-bold">{calculateBudgetUtilization()}%</p>
              </div>
              <DollarSign className="h-8 w-8 text-yellow-500" />
            </div>
            <Progress value={calculateBudgetUtilization()} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* 项目详情 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* 项目信息 */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-4">项目信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">项目编号</p>
                  <p className="font-medium">{p.project_number}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">项目经理</p>
                  <p className="font-medium">{p.manager_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">开始日期</p>
                  <p className="font-medium">{formatDate(p.start_date)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">结束日期</p>
                  <p className="font-medium">{formatDate(p.end_date)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">客户</p>
                  <p className="font-medium">{p.customer_name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">项目预算</p>
                  <p className="font-medium">{formatCurrency(p.budget)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 团队成员 */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">团队成员</h3>
                <Button variant="outline" size="sm" onClick={handleOpenAddMember}>
                  <Plus className="mr-2 h-4 w-4" />
                  添加成员
                </Button>
              </div>
              <div className="space-y-3">
                {(members || []).map((member) =>
                <div key={member.id} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <UserAvatar user={member.user} size="sm" />
                      <div>
                        <p className="font-medium">{member.user?.name}</p>
                        <p className="text-sm text-gray-600">{member.role}</p>
                      </div>
                    </div>
                    <Badge variant="outline">{member.status}</Badge>
                </div>
                )}
                {members.length === 0 &&
                <p className="text-center text-gray-500 py-4">暂无团队成员</p>
                }
              </div>
            </CardContent>
          </Card>

          {/* 项目阶段 */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-4">项目阶段</h3>
              <div className="space-y-3">
                {(stages || []).map((stage, index) =>
                <div key={stage.id} className="flex items-center space-x-4">
                    <div className={cn(
                    "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium",
                    stage.status === 'completed' ? "bg-green-500" :
                    stage.status === 'in_progress' ? "bg-blue-500" : "bg-gray-400"
                  )}>
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{stage.name}</p>
                      <p className="text-sm text-gray-600">{stage.description}</p>
                    </div>
                    <Badge variant={stage.status === 'completed' ? 'default' : 'secondary'}>
                      {stage.status === 'completed' ? '已完成' :
                    stage.status === 'in_progress' ? '进行中' : '未开始'}
                    </Badge>
                </div>
                )}
                {stages.length === 0 &&
                <p className="text-center text-gray-500 py-4">暂无项目阶段</p>
                }
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {/* 快速操作 */}
          <QuickActionPanel project={project} onRefresh={fetchProjectData} />

          {/* 项目问题 */}
          <ProjectIssuePanel projectId={project.id} />

          {/* 项目会议 */}
          <ProjectMeetingPanel projectId={project.id} />

          {/* 项目奖金 */}
          <ProjectBonusPanel projectId={project.id} />

          {/* 解决方案库 */}
          <SolutionLibrary projectId={project.id} />
        </div>
      </div>

      {/* 其他组件 */}
      <div className="space-y-6">
        {/* 甘特图 */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4">项目进度甘特图</h3>
            <StageGantt stages={stages} />
          </CardContent>
        </Card>

        {/* 里程碑 */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-semibold mb-4">项目里程碑</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(milestones || []).map((milestone) =>
              <div key={milestone.id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{milestone.name}</h4>
                    {milestone.status === 'completed' ?
                  <CheckCircle className="h-5 w-5 text-green-500" /> :

                  <Clock className="h-5 w-5 text-gray-400" />
                  }
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{milestone.description}</p>
                  <p className="text-sm font-medium">
                    {formatDate(milestone.target_date)}
                  </p>
              </div>
              )}
              {milestones.length === 0 &&
              <p className="text-center text-gray-500 py-4 col-span-3">暂无里程碑</p>
              }
            </div>
          </CardContent>
        </Card>

        {/* 项目文档 */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">项目文档</h3>
              <Button variant="outline" size="sm" onClick={handleOpenAddMember}>
                <Plus className="mr-2 h-4 w-4" />
                上传文档
              </Button>
            </div>
            <div className="space-y-3">
              {(documents || []).map((doc) =>
              <div key={doc.id} className="flex items-center justify-between p-3 border rounded">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-5 w-5 text-blue-500" />
                    <div>
                      <p className="font-medium">{doc.name}</p>
                      <p className="text-sm text-gray-600">{doc.type}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      {formatDate(doc.created_at)}
                    </span>
                    <Button variant="ghost" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
              </div>
              )}
              {documents?.length === 0 &&
              <p className="text-center text-gray-500 py-4">暂无文档</p>
              }
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 编辑对话框 */}

      {/* 添加成员对话框 */}
      <AnimatePresence>
        {showAddMemberDialog &&
        <Dialog open={showAddMemberDialog} onOpenChange={setShowAddMemberDialog}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>添加项目成员</DialogTitle>
                <DialogDescription>
                  为项目添加团队成员
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">选择成员</label>
                  <select
                    className="w-full px-3 py-2 border rounded-md text-sm"
                    value={newMember.user_id}
                    onChange={(e) => setNewMember({ ...newMember, user_id: e.target.value })}
                    disabled={loadingUsers}
                  >
                    <option value="">-- 选择用户 --</option>
                    {(availableUsers || []).map(user => (
                      <option key={user.id} value={user.id}>
                        {user.real_name || user.username} ({user.username})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">角色</label>
                  <select
                    className="w-full px-3 py-2 border rounded-md text-sm"
                    value={newMember.role}
                    onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                  >
                    <option value="member">成员</option>
                    <option value="lead">负责人</option>
                  </select>
                </div>

                <div className="flex justify-end space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowAddMemberDialog(false)}
                  >
                    取消
                  </Button>
                  <Button
                    onClick={handleAddMember}
                    disabled={loadingUsers || !newMember.user_id}
                  >
                    添加
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        }
      </AnimatePresence>
    </motion.div>
  );
}
