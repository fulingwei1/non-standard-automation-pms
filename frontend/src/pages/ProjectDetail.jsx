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
  financialCostApi,
} from "../services/api";
import { formatDate, formatCurrency, getStageName } from "../lib/utils";
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
  DialogFooter,
} from "../components/ui";
import ProjectLeadsPanel from "../components/project/ProjectLeadsPanel";
import GateCheckPanel from "../components/project/GateCheckPanel";
import ProjectTimeline from "../components/project/ProjectTimeline";
import QuickActionPanel from "../components/project/QuickActionPanel";
import ProjectBonusPanel from "../components/project/ProjectBonusPanel";
import ProjectMeetingPanel from "../components/project/ProjectMeetingPanel";
import ProjectIssuePanel from "../components/project/ProjectIssuePanel";
import SolutionLibrary from "../components/project/SolutionLibrary";
import { projectWorkspaceApi } from "../services/api";
import {
  ArrowLeft,
  Edit2,
  MoreHorizontal,
  Briefcase,
  Box,
  CheckCircle2,
  Circle,
  Users,
  UserCog,
  DollarSign,
  FileText,
  Calendar,
  Clock,
  Plus,
  Activity,
  Target,
  TrendingUp,
  AlertTriangle,
  FolderOpen,
  Upload,
  AlertCircle,
} from "lucide-react";

// Tab data
const tabs = [
  { id: "overview", name: "概览", icon: Activity },
  { id: "stages", name: "进度计划", icon: Clock },
  { id: "machines", name: "设备列表", icon: Box },
  { id: "team", name: "项目团队", icon: Users },
  { id: "workspace", name: "工作空间", icon: FolderOpen },
  { id: "leads", name: "负责人", icon: UserCog },
  { id: "finance", name: "财务成本", icon: DollarSign },
  { id: "docs", name: "文档中心", icon: FileText },
  { id: "timeline", name: "时间线", icon: Calendar }, // Sprint 3.3: 新增时间线标签
];

// Animation variants
const fadeIn = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

export default function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [stages, setStages] = useState([]);
  const [machines, setMachines] = useState([]);
  const [members, setMembers] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [costs, setCosts] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [statusLogs, setStatusLogs] = useState([]); // Sprint 3.3: 状态变更日志
  const [workspaceData, setWorkspaceData] = useState(null); // 工作空间数据
  const [workspaceLoading, setWorkspaceLoading] = useState(false); // 工作空间加载状态
  const [workspaceError, setWorkspaceError] = useState(null); // 工作空间加载错误
  const [demoMode, setDemoMode] = useState(false); // 演示模式
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // 使用 Promise.allSettled 而不是 Promise.all，这样单个失败不会导致全部失败
        const results = await Promise.allSettled([
          projectApi.get(id),
          stageApi.list(id),
          machineApi.list({ project_id: id }),
          memberApi.list(id),
          milestoneApi.list(id),
          costApi.list({ project_id: id }), // 修复：传递project_id作为查询参数
          documentApi.list(id),
          projectApi.getStatusLogs(id, { limit: 50 }), // Sprint 3.3: 加载状态日志
        ]);

        // 处理项目详情（必须成功，否则显示错误）
        const projRes = results[0];
        if (projRes.status === "fulfilled") {
          // FastAPI直接返回对象，axios包装在response.data中
          const responseData = projRes.value.data;
          console.log("[ProjectDetail] 项目详情API响应:", {
            hasData: !!responseData,
            dataType: typeof responseData,
            isObject: typeof responseData === "object",
            keys:
              responseData && typeof responseData === "object"
                ? Object.keys(responseData)
                : null,
            projectId: responseData?.id,
            projectCode: responseData?.project_code,
            projectName: responseData?.project_name,
          });

          // 尝试多种格式：可能是直接对象，也可能是嵌套在data中
          const projectData = responseData?.data || responseData || null;
          if (
            projectData &&
            typeof projectData === "object" &&
            projectData.id
          ) {
            console.log("[ProjectDetail] ✅ 项目数据解析成功:", {
              id: projectData.id,
              code: projectData.project_code,
              name: projectData.project_name,
            });
            setProject(projectData);
          } else {
            console.error("[ProjectDetail] ❌ 项目数据格式错误:", {
              projectData,
              type: typeof projectData,
              hasId: projectData?.id,
            });
            setProject(null);
          }
        } else {
          console.error("[ProjectDetail] ❌ 获取项目详情失败:", {
            reason: projRes.reason,
            message: projRes.reason?.message,
            response: projRes.reason?.response?.data,
            status: projRes.reason?.response?.status,
          });
          setProject(null);
          // 不在这里 return，继续处理其他数据
        }

        // 处理其他数据（允许失败，使用默认值）
        const machinesRes = results[2];
        if (machinesRes.status === "fulfilled") {
          const machinesData =
            machinesRes.value.data?.items || machinesRes.value.data || [];
          setMachines(Array.isArray(machinesData) ? machinesData : []);
        } else {
          console.warn("获取机台列表失败:", machinesRes.reason);
          setMachines([]);
        }

        const stagesRes = results[1];
        if (stagesRes.status === "fulfilled") {
          setStages(
            Array.isArray(stagesRes.value.data) ? stagesRes.value.data : [],
          );
        } else {
          console.warn("获取阶段列表失败:", stagesRes.reason);
          setStages([]);
        }

        const membersRes = results[3];
        if (membersRes.status === "fulfilled") {
          setMembers(
            Array.isArray(membersRes.value.data) ? membersRes.value.data : [],
          );
        } else {
          console.warn("获取成员列表失败:", membersRes.reason);
          setMembers([]);
        }

        const milestonesRes = results[4];
        if (milestonesRes.status === "fulfilled") {
          setMilestones(
            Array.isArray(milestonesRes.value.data)
              ? milestonesRes.value.data
              : [],
          );
        } else {
          console.warn("获取里程碑列表失败:", milestonesRes.reason);
          setMilestones([]);
        }

        const costsRes = results[5];
        if (costsRes.status === "fulfilled") {
          // 成本API返回PaginatedResponse格式：{ items, total, page, page_size, pages }
          const costsData = costsRes.value.data;
          const costsList =
            costsData?.items || (Array.isArray(costsData) ? costsData : []);
          setCosts(Array.isArray(costsList) ? costsList : []);
        } else {
          console.warn("获取成本列表失败:", costsRes.reason);
          setCosts([]);
        }

        const docsRes = results[6];
        if (docsRes.status === "fulfilled") {
          // 文档API返回PaginatedResponse格式：{ items, total, page, page_size, pages }
          const docsData = docsRes.value.data;
          const docsList =
            docsData?.items || (Array.isArray(docsData) ? docsData : []);
          setDocuments(Array.isArray(docsList) ? docsList : []);
        } else {
          console.warn("获取文档列表失败:", docsRes.reason);
          setDocuments([]);
        }

        const logsRes = results[7];
        if (logsRes.status === "fulfilled") {
          const logsData =
            logsRes.value.data?.items || logsRes.value.data || [];
          setStatusLogs(Array.isArray(logsData) ? logsData : []);
        } else {
          console.warn("获取状态日志失败:", logsRes.reason);
          setStatusLogs([]);
        }
      } catch (err) {
        // 这个 catch 应该不会被执行，因为使用了 Promise.allSettled
        // 但保留作为安全网
        console.error("Unexpected error in fetchData:", err);
        setProject(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  // 生成演示数据
  const generateDemoWorkspaceData = () => {
    const now = new Date();
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);

    return {
      project: {
        id: parseInt(id) || 1,
        project_code: "PJ250101001",
        project_name: "演示项目 - 自动化测试设备",
        stage: "S5",
        status: "IN_PROGRESS",
        health: "H1",
        progress_pct: 65.5,
        contract_amount: 1500000,
        pm_name: "张经理",
      },
      team: [
        {
          user_id: 1,
          user_name: "张三",
          role_code: "PM",
          allocation_pct: 100,
          start_date: "2025-01-01",
          end_date: "2025-06-30",
        },
        {
          user_id: 2,
          user_name: "李四",
          role_code: "ENGINEER",
          allocation_pct: 80,
          start_date: "2025-01-15",
          end_date: "2025-05-30",
        },
        {
          user_id: 3,
          user_name: "王五",
          role_code: "DESIGNER",
          allocation_pct: 60,
          start_date: "2025-02-01",
          end_date: "2025-04-30",
        },
        {
          user_id: 4,
          user_name: "赵六",
          role_code: "QA",
          allocation_pct: 50,
          start_date: "2025-03-01",
          end_date: "2025-05-30",
        },
      ],
      tasks: [
        {
          id: 1,
          title: "机械结构设计",
          status: "COMPLETED",
          assignee_name: "王五",
          progress: 100,
        },
        {
          id: 2,
          title: "电气控制系统开发",
          status: "IN_PROGRESS",
          assignee_name: "李四",
          progress: 75,
        },
        {
          id: 3,
          title: "软件功能测试",
          status: "IN_PROGRESS",
          assignee_name: "赵六",
          progress: 40,
        },
        {
          id: 4,
          title: "设备组装调试",
          status: "PENDING",
          assignee_name: "李四",
          progress: 0,
        },
      ],
      meetings: {
        meetings: [
          {
            id: 1,
            meeting_name: "项目启动会",
            meeting_date: "2025-01-10",
            rhythm_level: "WEEKLY",
            status: "COMPLETED",
            organizer_name: "张三",
            minutes:
              "会议纪要内容：\n1. 项目目标确认\n2. 团队成员介绍\n3. 项目计划讨论\n4. 下一步行动项：\n   - 完成需求分析（负责人：李四，截止日期：2025-01-20）\n   - 准备技术方案（负责人：王五，截止日期：2025-01-25）",
            has_minutes: true,
          },
          {
            id: 2,
            meeting_name: "周例会",
            meeting_date: "2025-01-17",
            rhythm_level: "WEEKLY",
            status: "COMPLETED",
            organizer_name: "张三",
            minutes:
              "本周进展：\n1. 机械设计已完成80%\n2. 电气控制方案已确定\n3. 下周计划：开始软件开发",
            has_minutes: true,
          },
        ],
        statistics: {
          total_meetings: 8,
          completed_meetings: 6,
          completion_rate: 75,
          total_action_items: 12,
        },
      },
      issues: {
        issues: [
          {
            id: 1,
            issue_no: "ISS001",
            title: "传感器精度不足",
            status: "RESOLVED",
            severity: "MEDIUM",
            priority: "HIGH",
            has_solution: true,
            assignee_name: "李四",
            report_date: "2025-01-15",
          },
          {
            id: 2,
            issue_no: "ISS002",
            title: "机械结构需要优化",
            status: "IN_PROGRESS",
            severity: "LOW",
            priority: "MEDIUM",
            has_solution: false,
            assignee_name: "王五",
            report_date: "2025-01-20",
          },
          {
            id: 3,
            issue_no: "ISS003",
            title: "软件兼容性问题",
            status: "OPEN",
            severity: "HIGH",
            priority: "HIGH",
            has_solution: false,
            assignee_name: "赵六",
            report_date: "2025-01-22",
          },
        ],
      },
      documents: [
        {
          id: 1,
          doc_name: "项目需求文档",
          doc_type: "REQUIREMENT",
          version: "1.0",
          status: "APPROVED",
          created_at: "2025-01-05",
        },
        {
          id: 2,
          doc_name: "技术方案设计",
          doc_type: "DESIGN",
          version: "2.1",
          status: "APPROVED",
          created_at: "2025-01-12",
        },
        {
          id: 3,
          doc_name: "测试计划",
          doc_type: "TEST",
          version: "1.0",
          status: "DRAFT",
          created_at: "2025-01-18",
        },
        {
          id: 4,
          doc_name: "用户手册",
          doc_type: "MANUAL",
          version: "0.5",
          status: "DRAFT",
          created_at: "2025-01-20",
        },
      ],
    };
  };

  // 当切换到工作空间标签时，加载工作空间数据
  useEffect(() => {
    if (activeTab === "workspace" && !workspaceData && !workspaceLoading) {
      // 如果项目不存在，直接启用演示模式
      if (!project) {
        setDemoMode(true);
        setWorkspaceData(generateDemoWorkspaceData());
        return;
      }

      setWorkspaceLoading(true);
      setWorkspaceError(null);
      const fetchWorkspaceData = async () => {
        try {
          const response = await projectWorkspaceApi.getWorkspace(id);
          setWorkspaceData(response.data);
          setDemoMode(false);
        } catch (error) {
          console.error("Failed to load workspace data:", error);
          setWorkspaceError(error);
          // 如果项目不存在或加载失败，启用演示模式
          if (
            error.response?.status === 404 ||
            error.response?.status === 403
          ) {
            setDemoMode(true);
            setWorkspaceData(generateDemoWorkspaceData());
          }
        } finally {
          setWorkspaceLoading(false);
        }
      };
      fetchWorkspaceData();
    }
  }, [activeTab, id, workspaceData, workspaceLoading, project]);

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-12 w-12 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4">
          {Array(4)
            .fill(null)
            .map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-2xl" />
            ))}
        </div>
        <Skeleton className="h-96 rounded-2xl" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-20">
        <h2 className="text-xl font-semibold text-white mb-2">未找到项目</h2>
        <p className="text-slate-400 mb-6">该项目可能已被删除或不存在</p>
        <Button onClick={() => navigate("/projects")}>返回项目列表</Button>
      </div>
    );
  }

  // Stats cards data
  const statCards = [
    {
      label: "整体进度",
      value: `${project.progress_pct || 0}%`,
      icon: TrendingUp,
      color: "primary",
    },
    {
      label: "当前阶段",
      value: project.stage || "S1",
      subtext: getStageName(project.stage),
      icon: Target,
      color: "emerald",
    },
    {
      label: "机台总数",
      value: machines.length,
      subtext: `已完成 ${machines.filter((m) => m.progress_pct === 100).length} 个`,
      icon: Box,
      color: "indigo",
    },
    {
      label: "交付日期",
      value: project.planned_end_date
        ? formatDate(project.planned_end_date)
        : "未设置",
      icon: Calendar,
      color: "amber",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="flex items-start gap-4 mb-8">
        <button
          onClick={() => navigate("/projects")}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>

        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-white">
              {project.project_name}
            </h1>
            <HealthBadge health={project.health || "H1"} />
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span>{project.project_code}</span>
            <span>•</span>
            <span>客户: {project.customer_name}</span>
            <span>•</span>
            <span>负责人: {project.pm_name || "未指定"}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Sprint 3.3: 快速操作面板 */}
          <QuickActionPanel
            project={project}
            onRefresh={() => {
              // 重新加载数据
              projectApi
                .get(id)
                .then((res) => {
                  const projectData = res.data?.data || res.data || null;
                  setProject(projectData);
                })
                .catch((err) => {
                  console.error("Failed to refresh project:", err);
                });
            }}
          />
          <Button variant="secondary" size="icon">
            <Edit2 className="h-4 w-4" />
          </Button>
          <Button variant="secondary" size="icon">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat, i) => (
          <Card key={i} className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div
                className={cn(
                  "p-2 rounded-lg",
                  stat.color === "primary" && "bg-primary/20",
                  stat.color === "emerald" && "bg-emerald-500/20",
                  stat.color === "indigo" && "bg-indigo-500/20",
                  stat.color === "amber" && "bg-amber-500/20",
                )}
              >
                <stat.icon
                  className={cn(
                    "h-4 w-4",
                    stat.color === "primary" && "text-primary",
                    stat.color === "emerald" && "text-emerald-400",
                    stat.color === "indigo" && "text-indigo-400",
                    stat.color === "amber" && "text-amber-400",
                  )}
                />
              </div>
            </div>
            <p className="text-xs text-slate-400 mb-1">{stat.label}</p>
            <p className="text-xl font-semibold text-white">{stat.value}</p>
            {stat.subtext && (
              <p className="text-xs text-slate-500 mt-1">{stat.subtext}</p>
            )}
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 rounded-xl bg-white/[0.03] border border-white/5 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex items-center justify-center gap-2 flex-1 px-4 py-2.5 rounded-lg",
              "text-sm font-medium transition-all duration-200",
              activeTab === tab.id
                ? "bg-primary text-white shadow-lg shadow-primary/30"
                : "text-slate-400 hover:text-white hover:bg-white/[0.05]",
            )}
          >
            <tab.icon className="h-4 w-4" />
            <span className="hidden sm:inline">{tab.name}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} {...fadeIn} transition={{ duration: 0.2 }}>
          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* Progress Overview */}
                <Card>
                  <CardContent>
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Activity className="h-5 w-5 text-primary" />
                      进度概览
                    </h3>
                    <div className="flex items-center gap-8">
                      <CircularProgress
                        value={project.progress_pct || 0}
                        size={100}
                      />
                      <div className="flex-1">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="p-3 rounded-xl bg-white/[0.03]">
                            <p className="text-xs text-slate-400 mb-1">
                              已完成阶段
                            </p>
                            <p className="text-lg font-semibold text-white">
                              {
                                stages.filter((s) => s.status === "COMPLETED")
                                  .length
                              }{" "}
                              / {stages.length}
                            </p>
                          </div>
                          <div className="p-3 rounded-xl bg-white/[0.03]">
                            <p className="text-xs text-slate-400 mb-1">
                              已完成机台
                            </p>
                            <p className="text-lg font-semibold text-white">
                              {
                                machines.filter((m) => m.progress_pct === 100)
                                  .length
                              }{" "}
                              / {machines.length}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Milestones */}
                <Card>
                  <CardContent>
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Target className="h-5 w-5 text-primary" />
                      关键里程碑
                    </h3>
                    {milestones.length > 0 ? (
                      <div className="space-y-3">
                        {milestones.map((m) => (
                          <div
                            key={m.id}
                            className="flex items-center gap-4 p-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                          >
                            <div
                              className={cn(
                                "p-2 rounded-lg",
                                m.is_completed
                                  ? "bg-emerald-500/20"
                                  : "bg-slate-500/20",
                              )}
                            >
                              {m.is_completed ? (
                                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                              ) : (
                                <Circle className="h-5 w-5 text-slate-400" />
                              )}
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-white">
                                {m.milestone_name}
                              </p>
                              <p className="text-xs text-slate-500">
                                计划: {m.planned_date}
                              </p>
                            </div>
                            <Badge variant="secondary">
                              {m.milestone_type}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-slate-500">
                        暂无里程碑
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Sprint 3.3: 阶段门校验面板 */}
                <GateCheckPanel
                  projectId={parseInt(id)}
                  currentStage={project.stage}
                  onAdvance={() => {
                    // 重新加载项目数据
                    projectApi
                      .get(id)
                      .then((res) => {
                        const projectData = res.data?.data || res.data || null;
                        setProject(projectData);
                      })
                      .catch((err) => {
                        console.error("Failed to refresh project:", err);
                      });
                  }}
                />

                {/* Project Info */}
                <Card>
                  <CardContent>
                    <h3 className="text-sm font-medium text-slate-400 mb-4">
                      项目信息
                    </h3>
                    <div className="space-y-4">
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">项目经理</span>
                        <span className="text-sm text-white">
                          {project.pm_name || "未指定"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">合同编号</span>
                        <span className="text-sm text-white">
                          {project.contract_no || "无"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">预算金额</span>
                        <span className="text-sm text-primary font-medium">
                          {project.budget_amount
                            ? formatCurrency(project.budget_amount)
                            : "未设置"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">创建日期</span>
                        <span className="text-sm text-white">
                          {project.created_at
                            ? formatDate(project.created_at)
                            : "-"}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Team */}
                <Card>
                  <CardContent>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-medium text-slate-400">
                        项目团队
                      </h3>
                      <span className="text-xs text-slate-500">
                        {members.length} 人
                      </span>
                    </div>
                    {members.length > 0 ? (
                      <AvatarGroup
                        users={members.map((m) => ({
                          ...m,
                          name: m.name || m.member_name,
                        }))}
                        max={5}
                      />
                    ) : (
                      <p className="text-sm text-slate-500">暂无成员</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* Stages Tab */}
          {activeTab === "stages" && (
            <Card>
              <CardContent>
                <div className="relative">
                  {/* Timeline line */}
                  <div className="absolute left-[19px] top-0 bottom-0 w-0.5 bg-white/10" />

                  <div className="space-y-4">
                    {stages.map((stage, idx) => (
                      <div key={stage.id} className="relative flex gap-4">
                        {/* Dot */}
                        <div
                          className={cn(
                            "relative z-10 w-10 h-10 rounded-full flex items-center justify-center",
                            stage.status === "COMPLETED"
                              ? "bg-primary"
                              : stage.status === "IN_PROGRESS"
                                ? "bg-primary/30 border-2 border-primary"
                                : "bg-white/5 border border-white/10",
                          )}
                        >
                          {stage.status === "COMPLETED" ? (
                            <CheckCircle2 className="h-5 w-5 text-white" />
                          ) : (
                            <span className="text-sm font-medium">
                              {stage.stage_code}
                            </span>
                          )}
                        </div>

                        {/* Content */}
                        <div
                          className={cn(
                            "flex-1 p-4 rounded-xl",
                            "bg-white/[0.03] border border-white/5",
                            stage.status === "IN_PROGRESS" &&
                              "border-primary/30",
                          )}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-semibold text-white">
                              {stage.stage_name}
                            </h4>
                            <span className="text-xs text-slate-500">
                              {stage.planned_start_date &&
                                formatDate(stage.planned_start_date)}{" "}
                              ~{" "}
                              {stage.planned_end_date &&
                                formatDate(stage.planned_end_date)}
                            </span>
                          </div>
                          {stage.description && (
                            <p className="text-sm text-slate-400 mb-3">
                              {stage.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4">
                            <div className="flex-1">
                              <Progress
                                value={stage.progress_pct || 0}
                                size="sm"
                              />
                            </div>
                            <span className="text-sm font-medium text-white">
                              {stage.progress_pct || 0}%
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Machines Tab */}
          {activeTab === "machines" && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  设备列表 ({machines.length})
                </h3>
                <Button size="sm">
                  <Plus className="h-4 w-4" />
                  添加设备
                </Button>
              </div>

              {machines.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {machines.map((machine) => (
                    <Card
                      key={machine.id}
                      className="overflow-hidden cursor-pointer hover:bg-white/[0.04] transition-colors"
                      onClick={() =>
                        navigate(
                          `/projects/${id}/machines?machine_id=${machine.id}`,
                        )
                      }
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="p-2 rounded-lg bg-indigo-500/20">
                            <Box className="h-5 w-5 text-indigo-400" />
                          </div>
                          <Badge variant="secondary">{machine.stage}</Badge>
                        </div>
                        <h4 className="font-semibold text-white mb-1">
                          {machine.machine_name}
                        </h4>
                        <p className="text-xs text-slate-500 mb-3">
                          {machine.machine_code}
                        </p>
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="text-slate-400">进度</span>
                          <span className="text-white">
                            {machine.progress_pct || 0}%
                          </span>
                        </div>
                        <Progress
                          value={machine.progress_pct || 0}
                          size="sm"
                          color="primary"
                        />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <Card className="p-12 text-center">
                  <Box className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">
                    暂无设备
                  </h3>
                  <p className="text-slate-400 mb-6">点击上方按钮添加设备</p>
                  <Button>
                    <Plus className="h-4 w-4" />
                    添加设备
                  </Button>
                </Card>
              )}
            </div>
          )}

          {/* Workspace Tab */}
          {activeTab === "workspace" &&
            (workspaceLoading ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-24 rounded-xl" />
                  ))}
                </div>
                <Skeleton className="h-96 rounded-xl" />
              </div>
            ) : workspaceData ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-400 mb-1">
                            项目进度
                          </p>
                          <p className="text-2xl font-bold text-white">
                            {workspaceData.project?.progress_pct?.toFixed(1) ||
                              0}
                            %
                          </p>
                        </div>
                        <TrendingUp className="h-8 w-8 text-primary" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-400 mb-1">
                            团队成员
                          </p>
                          <p className="text-2xl font-bold text-white">
                            {workspaceData.team?.length || 0}
                          </p>
                        </div>
                        <Users className="h-8 w-8 text-emerald-400" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-400 mb-1">
                            进行中任务
                          </p>
                          <p className="text-2xl font-bold text-white">
                            {workspaceData.tasks?.filter(
                              (t) => t.status === "IN_PROGRESS",
                            ).length || 0}
                          </p>
                        </div>
                        <Activity className="h-8 w-8 text-indigo-400" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-400 mb-1">
                            待解决问题
                          </p>
                          <p className="text-2xl font-bold text-white">
                            {workspaceData.issues?.issues?.filter(
                              (i) =>
                                i.status === "OPEN" ||
                                i.status === "IN_PROGRESS",
                            ).length || 0}
                          </p>
                        </div>
                        <AlertTriangle className="h-8 w-8 text-amber-400" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {}
                {demoMode && (
                  <Card className="border-amber-500/50 bg-amber-500/10 mb-6">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className="h-5 w-5 text-amber-400" />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-amber-400">
                            演示模式
                          </p>
                          <p className="text-xs text-slate-400 mt-1">
                            当前显示的是演示数据。创建项目后，将显示真实的项目工作空间数据。
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate("/projects")}
                        >
                          去创建项目
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* 项目成员名单 */}
                {workspaceData.team && workspaceData.team.length > 0 && (
                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                          <Users className="h-5 w-5" />
                          项目成员名单
                        </h3>
                        <Badge variant="outline">
                          {workspaceData.team.length} 人
                        </Badge>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {workspaceData.team.map((member) => (
                          <div
                            key={member.user_id}
                            className="p-4 border rounded-lg hover:bg-white/[0.02] transition-colors"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <UserAvatar
                                  user={{ name: member.user_name }}
                                  size="sm"
                                />
                                <div>
                                  <p className="font-medium text-white">
                                    {member.user_name}
                                  </p>
                                  {member.role_code && (
                                    <p className="text-xs text-slate-400">
                                      {member.role_code}
                                    </p>
                                  )}
                                </div>
                              </div>
                              <Badge variant="outline" className="text-xs">
                                {member.allocation_pct || 100}%
                              </Badge>
                            </div>
                            {(member.start_date || member.end_date) && (
                              <div className="flex items-center gap-2 text-xs text-slate-500 mt-2">
                                {member.start_date && (
                                  <span>{formatDate(member.start_date)}</span>
                                )}
                                {member.start_date && member.end_date && (
                                  <span>~</span>
                                )}
                                {member.end_date && (
                                  <span>{formatDate(member.end_date)}</span>
                                )}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ProjectBonusPanel projectId={parseInt(id)} />
                  <ProjectMeetingPanel projectId={parseInt(id)} />
                </div>

                <ProjectIssuePanel projectId={parseInt(id)} />

                {/* 会议纪要详情 */}
                {workspaceData.meetings?.meetings &&
                  workspaceData.meetings.meetings.length > 0 && (
                    <Card>
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            会议纪要
                          </h3>
                        </div>
                        <div className="space-y-4">
                          {workspaceData.meetings.meetings
                            .filter((m) => m.minutes)
                            .map((meeting) => (
                              <div
                                key={meeting.id}
                                className="p-4 border rounded-lg hover:bg-white/[0.02] transition-colors"
                              >
                                <div className="flex items-start justify-between mb-3">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                      <h4 className="font-semibold text-white">
                                        {meeting.meeting_name}
                                      </h4>
                                      <Badge variant="outline">
                                        {meeting.rhythm_level}
                                      </Badge>
                                      {meeting.meeting_date && (
                                        <span className="text-sm text-slate-400">
                                          {formatDate(meeting.meeting_date)}
                                        </span>
                                      )}
                                    </div>
                                    {meeting.organizer_name && (
                                      <p className="text-sm text-slate-400">
                                        组织者: {meeting.organizer_name}
                                      </p>
                                    )}
                                  </div>
                                  <Badge
                                    variant={
                                      meeting.status === "COMPLETED"
                                        ? "default"
                                        : "secondary"
                                    }
                                  >
                                    {meeting.status}
                                  </Badge>
                                </div>
                                {meeting.minutes && (
                                  <div>
                                    <p className="text-sm font-medium text-slate-300 mb-1">
                                      会议纪要：
                                    </p>
                                    <div className="p-3 bg-white/[0.03] rounded-lg text-sm text-slate-300 whitespace-pre-wrap max-h-60 overflow-y-auto">
                                      {meeting.minutes}
                                    </div>
                                  </div>
                                )}
                              </div>
                            ))}
                          {workspaceData.meetings.meetings.filter(
                            (m) => m.minutes,
                          ).length === 0 && (
                            <div className="text-center py-8 text-slate-500">
                              暂无会议纪要
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                {/* 项目文档 */}
                {workspaceData.documents &&
                  workspaceData.documents.length > 0 && (
                    <Card>
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-semibold flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            项目资料文档
                          </h3>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {workspaceData.documents.map((doc) => (
                            <div
                              key={doc.id}
                              className="p-4 border rounded-lg hover:bg-white/[0.02] transition-colors cursor-pointer"
                              onClick={() => {
                                // TODO: 打开文档详情或下载
                                console.log("View document:", doc.id);
                              }}
                            >
                              <div className="flex items-start gap-3">
                                <div className="p-2 rounded-lg bg-primary/20">
                                  <FileText className="h-5 w-5 text-primary" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-white truncate mb-1">
                                    {doc.doc_name}
                                  </p>
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <Badge
                                      variant="outline"
                                      className="text-xs"
                                    >
                                      {doc.doc_type}
                                    </Badge>
                                    {doc.version && (
                                      <span className="text-xs text-slate-400">
                                        v{doc.version}
                                      </span>
                                    )}
                                  </div>
                                  {doc.created_at && (
                                    <p className="text-xs text-slate-500 mt-2">
                                      {formatDate(doc.created_at)}
                                    </p>
                                  )}
                                </div>
                                {doc.status && (
                                  <Badge
                                    variant={
                                      doc.status === "APPROVED"
                                        ? "default"
                                        : "secondary"
                                    }
                                    className="text-xs"
                                  >
                                    {doc.status}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-semibold">解决方案库</h3>
                    </div>
                    <SolutionLibrary
                      projectId={parseInt(id)}
                      onApplyTemplate={(template) => {
                        console.log("Apply template:", template);
                      }}
                    />
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="space-y-6">
                <Card>
                  <CardContent className="p-12 text-center">
                    <div className="text-5xl mb-4">📁</div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                      无法加载项目工作空间
                    </h3>
                    <p className="text-slate-400 mb-6">
                      {workspaceError?.response?.status === 404
                        ? "项目不存在，已切换到演示模式"
                        : "加载失败，请稍后重试"}
                    </p>
                    <Button
                      onClick={() => {
                        setWorkspaceData(null);
                        setWorkspaceLoading(false);
                        setWorkspaceError(null);
                      }}
                    >
                      重新加载
                    </Button>
                  </CardContent>
                </Card>
              </div>
            ))}

          {activeTab === "team" && (
            <div className="space-y-6">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">项目团队</h3>
                    <Button
                      size="sm"
                      onClick={() => {
                        // TODO: 打开添加成员对话框
                        console.log("Add member");
                      }}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      添加成员
                    </Button>
                  </div>
                  {members.length > 0 ? (
                    <div className="space-y-4">
                      {members.map((member) => (
                        <div
                          key={member.id}
                          className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors border border-white/5"
                        >
                          <div className="flex items-center gap-4 flex-1">
                            <UserAvatar
                              user={{
                                name:
                                  member.real_name ||
                                  member.name ||
                                  member.member_name,
                              }}
                              size="lg"
                            />
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <p className="font-medium text-white">
                                  {member.real_name ||
                                    member.name ||
                                    member.member_name}
                                </p>
                                <Badge variant="outline">
                                  {member.role_code ||
                                    member.role ||
                                    "团队成员"}
                                </Badge>
                                {member.commitment_level && (
                                  <Badge variant="secondary">
                                    {member.commitment_level}
                                  </Badge>
                                )}
                              </div>
                              <div className="flex items-center gap-4 text-sm text-slate-400">
                                <span>
                                  投入: {member.allocation_pct || 100}%
                                </span>
                                {member.start_date && member.end_date && (
                                  <span>
                                    {formatDate(member.start_date)} ~{" "}
                                    {formatDate(member.end_date)}
                                  </span>
                                )}
                                {member.reporting_to_pm !== false && (
                                  <Badge variant="outline" className="text-xs">
                                    向PM汇报
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={async () => {
                                // 检查冲突
                                try {
                                  const response =
                                    await memberApi.checkConflicts(
                                      id,
                                      member.user_id,
                                      {
                                        start_date: member.start_date,
                                        end_date: member.end_date,
                                      },
                                    );
                                  if (response.data.has_conflict) {
                                    alert(
                                      `发现时间冲突：${response.data.conflict_count} 个冲突项目`,
                                    );
                                  } else {
                                    alert("未发现时间冲突");
                                  }
                                } catch (err) {
                                  console.error(
                                    "Failed to check conflicts:",
                                    err,
                                  );
                                }
                              }}
                            >
                              <AlertTriangle className="h-4 w-4" />
                              检查冲突
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                navigate(`/projects/${id}/workspace`)
                              }
                            >
                              查看详情
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12 text-slate-500">
                      暂无团队成员
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Leads Tab - 项目负责人配置 */}
          {activeTab === "leads" && (
            <ProjectLeadsPanel projectId={parseInt(id)} />
          )}

          {/* Finance Tab */}
          {activeTab === "finance" && (
            <Card>
              <CardContent className="space-y-4">
                {/* 上传成本按钮 */}
                <div className="flex justify-end">
                  <Button
                    variant="outline"
                    onClick={() =>
                      navigate(`/financial-costs?project_id=${id}`)
                    }
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    上传成本数据
                  </Button>
                </div>

                {(() => {
                  // 成本类型中文映射
                  const costTypeMap = {
                    MATERIAL: "物料",
                    LABOR: "人工",
                    OUTSOURCE: "外协",
                    OTHER: "其他",
                  };

                  // 按成本类型分组汇总，区分财务修正数据
                  const costSummary = costs.reduce((acc, cost) => {
                    const type = cost.cost_type || "OTHER";
                    if (!acc[type]) {
                      acc[type] = {
                        type,
                        label: costTypeMap[type] || type,
                        amount: 0,
                        count: 0,
                        financialCount: 0, // 财务修正数据数量
                        hasFinancialCorrection: false, // 是否有财务修正数据
                      };
                    }
                    acc[type].amount += parseFloat(cost.amount || 0);
                    acc[type].count += 1;
                    if (cost.is_financial_correction) {
                      acc[type].financialCount += 1;
                      acc[type].hasFinancialCorrection = true;
                    }
                    return acc;
                  }, {});

                  const costTypes = Object.values(costSummary);

                  if (costTypes.length > 0) {
                    return (
                      <div className="space-y-4">
                        {costTypes.map((summary) => (
                          <div
                            key={summary.type}
                            onClick={() => {
                              // 跳转到成本核算页面，并传递项目ID和成本类型作为查询参数
                              navigate(
                                `/costs?project_id=${id}&cost_type=${summary.type}`,
                              );
                            }}
                            className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer"
                          >
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <p className="font-medium text-white">
                                  {summary.label}
                                </p>
                                {summary.hasFinancialCorrection && (
                                  <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-xs">
                                    <AlertCircle className="h-3 w-3 mr-1" />
                                    财务修正
                                  </Badge>
                                )}
                              </div>
                              <p className="text-sm text-slate-500">
                                {summary.count} 项记录
                                {summary.financialCount > 0 && (
                                  <span className="text-amber-400 ml-2">
                                    （{summary.financialCount} 项财务修正）
                                  </span>
                                )}
                              </p>
                            </div>
                            <p className="text-lg font-semibold text-primary">
                              {formatCurrency(summary.amount)}
                            </p>
                          </div>
                        ))}
                      </div>
                    );
                  } else {
                    return (
                      <div className="text-center py-12 space-y-4">
                        <p className="text-slate-500">暂无财务数据</p>
                        <Button
                          variant="outline"
                          onClick={() =>
                            navigate(`/financial-costs?project_id=${id}`)
                          }
                        >
                          <Upload className="h-4 w-4 mr-2" />
                          上传成本数据
                        </Button>
                      </div>
                    );
                  }
                })()}
              </CardContent>
            </Card>
          )}

          {/* Documents Tab */}
          {activeTab === "docs" && (
            <Card>
              <CardContent>
                {documents.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="flex items-center gap-3 p-4 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors cursor-pointer"
                      >
                        <div className="p-2 rounded-lg bg-blue-500/20">
                          <FileText className="h-5 w-5 text-blue-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-white truncate">
                            {doc.doc_name ||
                              doc.document_name ||
                              doc.file_name ||
                              "未命名文档"}
                          </p>
                          <p className="text-xs text-slate-500">
                            {doc.doc_type || doc.document_type || "未知类型"}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500">
                    暂无文档
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Sprint 3.3: Timeline Tab */}
          {activeTab === "timeline" && (
            <ProjectTimeline
              projectId={parseInt(id)}
              statusLogs={statusLogs}
              milestones={milestones}
              documents={documents}
            />
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}
