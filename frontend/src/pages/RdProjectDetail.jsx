import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../lib/utils";
import { rdProjectApi, projectApi } from "../services/api";
import { formatDate, formatCurrency } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Progress,
  CircularProgress,
  Skeleton,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "../components/ui";
import {
  ArrowLeft,
  Edit2,
  FlaskConical,
  Calendar,
  Users,
  DollarSign,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  TrendingUp,
  Activity,
  Target,
  BookOpen,
  Calculator,
  BarChart3,
  FileCheck,
  FolderOpen,
} from "lucide-react";

// Animation variants
const fadeIn = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

// Tab data
const tabs = [
  { id: "overview", name: "概览", icon: Activity },
  { id: "costs", name: "费用归集", icon: DollarSign },
  { id: "timesheet", name: "工时汇总", icon: Clock },
  { id: "worklogs", name: "工作日志", icon: FileCheck },
  { id: "documents", name: "文档管理", icon: FolderOpen },
  { id: "reports", name: "费用报表", icon: BarChart3 },
];

// Status mapping
const statusMap = {
  DRAFT: { label: "草稿", color: "secondary", icon: FileText },
  APPROVED: { label: "已审批", color: "success", icon: CheckCircle2 },
  IN_PROGRESS: { label: "进行中", color: "primary", icon: Clock },
  COMPLETED: { label: "已完成", color: "success", icon: CheckCircle2 },
  CANCELLED: { label: "已取消", color: "danger", icon: XCircle },
};

const categoryTypeMap = {
  SELF: { label: "自主研发", color: "primary" },
  ENTRUST: { label: "委托研发", color: "info" },
  COOPERATION: { label: "合作研发", color: "success" },
};

export default function RdProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [costs, setCosts] = useState([]);
  const [costSummary, setCostSummary] = useState(null);
  const [timesheetSummary, setTimesheetSummary] = useState(null);
  const [linkedProject, setLinkedProject] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    if (id) {
      fetchProject();
      if (activeTab === "costs") {
        fetchCosts();
        fetchCostSummary();
      } else if (activeTab === "timesheet") {
        fetchTimesheetSummary();
      }
    }
  }, [id, activeTab]);

  const fetchProject = async () => {
    try {
      setLoading(true);
      const response = await rdProjectApi.get(id);
      const projectData = response.data?.data || response.data || response;
      setProject(projectData);

      // 如果有关联的非标项目，获取项目信息
      if (projectData.linked_project_id) {
        try {
          const linkedRes = await projectApi.get(projectData.linked_project_id);
          setLinkedProject(linkedRes.data?.data || linkedRes.data || linkedRes);
        } catch (err) {
          console.error("Failed to fetch linked project:", err);
        }
      }
    } catch (err) {
      console.error("Failed to fetch project:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCosts = async () => {
    try {
      const response = await rdProjectApi.getCosts({
        rd_project_id: id,
        page_size: 100,
      });
      const data = response.data || response;
      setCosts(data.items || data || []);
    } catch (err) {
      console.error("Failed to fetch costs:", err);
      setCosts([]);
    }
  };

  const fetchCostSummary = async () => {
    try {
      const response = await rdProjectApi.getCostSummary(id);
      const data = response.data?.data || response.data || response;
      setCostSummary(data);
    } catch (err) {
      console.error("Failed to fetch cost summary:", err);
    }
  };

  const fetchTimesheetSummary = async () => {
    try {
      const response = await rdProjectApi.getTimesheetSummary(id);
      const data = response.data?.data || response.data || response;
      setTimesheetSummary(data);
    } catch (err) {
      console.error("Failed to fetch timesheet summary:", err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400">研发项目不存在</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate("/rd-projects")}
        >
          返回列表
        </Button>
      </div>
    );
  }

  const status = statusMap[project.status] || statusMap.DRAFT;
  const categoryType =
    categoryTypeMap[project.category_type] || categoryTypeMap.SELF;

  // Stat cards for overview
  const statCards = [
    {
      label: "预算金额",
      value: formatCurrency(project.budget_amount || 0),
      icon: DollarSign,
      color: "primary",
    },
    {
      label: "已归集费用",
      value: formatCurrency(project.total_cost || 0),
      icon: Calculator,
      color: "emerald",
      subtext: costSummary
        ? `人工: ${formatCurrency(costSummary.labor_cost || 0)}`
        : undefined,
    },
    {
      label: "总工时",
      value: project.total_hours
        ? `${project.total_hours.toFixed(1)} 小时`
        : "0 小时",
      icon: Clock,
      color: "indigo",
      subtext: timesheetSummary
        ? `${timesheetSummary.total_participants || 0} 人参与`
        : undefined,
    },
    {
      label: "参与人数",
      value: project.participant_count || 0,
      icon: Users,
      color: "amber",
    },
  ];

  return (
    <motion.div initial="hidden" animate="visible" variants={fadeIn}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate("/rd-projects")}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 rounded-lg bg-primary/20">
                <FlaskConical className="h-5 w-5 text-primary" />
              </div>
              <h1 className="text-2xl font-bold text-white">
                {project.project_name}
              </h1>
              <Badge variant={status.color}>{status.label}</Badge>
              <Badge variant="outline">{categoryType.label}</Badge>
            </div>
            <div className="flex items-center gap-4 text-sm text-slate-400">
              <span>{project.project_no}</span>
              <span>•</span>
              <span>负责人: {project.project_manager_name || "未指定"}</span>
              {project.planned_start_date && (
                <>
                  <span>•</span>
                  <span>
                    {formatDate(project.planned_start_date)} ~{" "}
                    {formatDate(project.planned_end_date)}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="icon">
            <Edit2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {(statCards || []).map((stat, i) => (
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
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid w-full grid-cols-6">
          {(tabs || []).map((tab) => (
            <TabsTrigger
              key={tab.id}
              value={tab.id}
              className="flex items-center gap-2"
            >
              <tab.icon className="h-4 w-4"  />
              {tab.name}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Project Info */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Target className="h-5 w-5 text-primary" />
                    项目信息
                  </h3>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-slate-400 mb-1">立项日期</p>
                        <p className="text-white">
                          {project.initiation_date
                            ? formatDate(project.initiation_date)
                            : "未设置"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-slate-400 mb-1">项目类型</p>
                        <Badge variant="outline">{categoryType.label}</Badge>
                      </div>
                      <div>
                        <p className="text-sm text-slate-400 mb-1">审批状态</p>
                        <Badge
                          variant={
                            project.approval_status === "APPROVED"
                              ? "success"
                              : project.approval_status === "REJECTED"
                                ? "danger"
                                : "warning"
                          }
                        >
                          {project.approval_status === "APPROVED"
                            ? "已通过"
                            : project.approval_status === "REJECTED"
                              ? "已驳回"
                              : "待审批"}
                        </Badge>
                      </div>
                      <div>
                        <p className="text-sm text-slate-400 mb-1">项目状态</p>
                        <Badge variant={status.color}>{status.label}</Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Research Content */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <BookOpen className="h-5 w-5 text-primary" />
                    研究内容
                  </h3>
                  <div className="space-y-4">
                    {project.initiation_reason && (
                      <div>
                        <p className="text-sm text-slate-400 mb-2">立项原因</p>
                        <p className="text-white">
                          {project.initiation_reason}
                        </p>
                      </div>
                    )}
                    {project.research_goal && (
                      <div>
                        <p className="text-sm text-slate-400 mb-2">研究目标</p>
                        <p className="text-white">{project.research_goal}</p>
                      </div>
                    )}
                    {project.research_content && (
                      <div>
                        <p className="text-sm text-slate-400 mb-2">研究内容</p>
                        <p className="text-white whitespace-pre-wrap">
                          {project.research_content}
                        </p>
                      </div>
                    )}
                    {project.expected_result && (
                      <div>
                        <p className="text-sm text-slate-400 mb-2">预期结果</p>
                        <p className="text-white">{project.expected_result}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Linked Project */}
              {linkedProject && (
                <Card>
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Target className="h-5 w-5 text-primary" />
                      关联非标项目
                    </h3>
                    <div className="p-4 rounded-lg bg-white/[0.03] border border-white/5">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-white">
                            {linkedProject.project_name}
                          </p>
                          <p className="text-sm text-slate-400">
                            {linkedProject.project_code}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            navigate(`/projects/${linkedProject.id}`)
                          }
                        >
                          查看详情
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Budget Progress */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    预算执行
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-400">已归集费用</span>
                        <span className="text-white font-medium">
                          {formatCurrency(project.total_cost || 0)}
                        </span>
                      </div>
                      <Progress
                        value={
                          project.budget_amount && project.budget_amount > 0
                            ? ((project.total_cost || 0) /
                                project.budget_amount) *
                              100
                            : 0
                        }
                        color={
                          project.budget_amount &&
                          project.total_cost > project.budget_amount
                            ? "danger"
                            : "primary"
                        }
                      />
                      <p className="text-xs text-slate-500 mt-1">
                        预算: {formatCurrency(project.budget_amount || 0)}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    快速操作
                  </h3>
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => navigate(`/rd-projects/${id}/costs/entry`)}
                    >
                      <DollarSign className="h-4 w-4 mr-2" />
                      录入费用
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() =>
                        navigate(`/rd-projects/${id}/costs/summary`)
                      }
                    >
                      <Calculator className="h-4 w-4 mr-2" />
                      费用汇总
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => navigate(`/rd-projects/${id}/worklogs`)}
                    >
                      <FileCheck className="h-4 w-4 mr-2" />
                      工作日志
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => navigate(`/rd-projects/${id}/documents`)}
                    >
                      <FolderOpen className="h-4 w-4 mr-2" />
                      文档管理
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => navigate(`/rd-projects/${id}/reports`)}
                    >
                      <BarChart3 className="h-4 w-4 mr-2" />
                      费用报表
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Costs Tab */}
        <TabsContent value="costs" className="space-y-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">费用归集</h3>
            <Button onClick={() => navigate(`/rd-projects/${id}/costs/entry`)}>
              录入费用
            </Button>
          </div>

          {/* Cost Summary */}
          {costSummary && (
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">
                  费用汇总
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-white/[0.03]">
                    <p className="text-sm text-slate-400 mb-1">总费用</p>
                    <p className="text-xl font-semibold text-white">
                      {formatCurrency(costSummary.total_cost || 0)}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/[0.03]">
                    <p className="text-sm text-slate-400 mb-1">人工费用</p>
                    <p className="text-xl font-semibold text-emerald-400">
                      {formatCurrency(costSummary.labor_cost || 0)}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/[0.03]">
                    <p className="text-sm text-slate-400 mb-1">材料费用</p>
                    <p className="text-xl font-semibold text-blue-400">
                      {formatCurrency(costSummary.material_cost || 0)}
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/[0.03]">
                    <p className="text-sm text-slate-400 mb-1">加计扣除</p>
                    <p className="text-xl font-semibold text-primary">
                      {formatCurrency(costSummary.deductible_amount || 0)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Cost List */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                费用明细
              </h3>
              {costs.length > 0 ? (
                <div className="space-y-3">
                  {(costs || []).map((cost) => (
                    <div
                      key={cost.id}
                      className="flex items-center justify-between p-4 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium text-white">
                            {cost.cost_no}
                          </p>
                          <Badge variant="outline" className="text-xs">
                            {cost.cost_date ? formatDate(cost.cost_date) : ""}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-400">
                          {cost.cost_description || "无描述"}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-white">
                          {formatCurrency(cost.cost_amount || 0)}
                        </p>
                        {cost.deductible_amount && (
                          <p className="text-xs text-primary">
                            扣除: {formatCurrency(cost.deductible_amount)}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  暂无费用记录
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timesheet Tab */}
        <TabsContent value="timesheet" className="space-y-6">
          {timesheetSummary ? (
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">
                  工时汇总
                </h3>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="p-4 rounded-lg bg-white/[0.03]">
                    <p className="text-sm text-slate-400 mb-1">总工时</p>
                    <p className="text-2xl font-semibold text-white">
                      {timesheetSummary.total_hours?.toFixed(1) || 0} 小时
                    </p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/[0.03]">
                    <p className="text-sm text-slate-400 mb-1">参与人数</p>
                    <p className="text-2xl font-semibold text-white">
                      {timesheetSummary.total_participants || 0} 人
                    </p>
                  </div>
                </div>

                {timesheetSummary.by_user &&
                  timesheetSummary.by_user?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-slate-400 mb-3">
                        按人员统计
                      </h4>
                      <div className="space-y-2">
                        {(timesheetSummary.by_user || []).map((user, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02]"
                          >
                            <div>
                              <p className="font-medium text-white">
                                {user.user_name}
                              </p>
                              <p className="text-xs text-slate-500">
                                {user.days} 天
                              </p>
                            </div>
                            <p className="text-lg font-semibold text-white">
                              {user.total_hours?.toFixed(1) || 0} 小时
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-6">
                <div className="text-center py-12 text-slate-500">
                  {project.linked_project_id ? (
                    <>
                      <Clock className="h-12 w-12 mx-auto mb-4 text-slate-600" />
                      <p>暂无工时数据</p>
                      <p className="text-xs mt-2">
                        工时数据从关联的非标项目中统计
                      </p>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="h-12 w-12 mx-auto mb-4 text-slate-600" />
                      <p>未关联非标项目</p>
                      <p className="text-xs mt-2">
                        关联非标项目后可统计工时数据
                      </p>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Worklogs Tab */}
        <TabsContent value="worklogs" className="space-y-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  研发人员工作日志
                </h3>
                <Button onClick={() => navigate(`/rd-projects/${id}/worklogs`)}>
                  查看全部
                </Button>
              </div>
              <div className="text-center py-12 text-slate-500">
                <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
                <p>工作日志管理</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => navigate(`/rd-projects/${id}/worklogs`)}
                >
                  进入工作日志页面
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents" className="space-y-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">
                  研发项目文档
                </h3>
                <Button
                  onClick={() => navigate(`/rd-projects/${id}/documents`)}
                >
                  查看全部
                </Button>
              </div>
              <div className="text-center py-12 text-slate-500">
                <FileText className="h-12 w-12 mx-auto mb-4 text-slate-600" />
                <p>文档管理</p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => navigate(`/rd-projects/${id}/documents`)}
                >
                  进入文档管理页面
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="space-y-6">
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                研发费用报表
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-start"
                  onClick={() =>
                    navigate(`/rd-projects/${id}/reports/auxiliary-ledger`)
                  }
                >
                  <FileText className="h-5 w-5 mb-2" />
                  <span className="font-medium">研发费用辅助账</span>
                  <span className="text-xs text-slate-500 mt-1">
                    税务要求的辅助账格式
                  </span>
                </Button>
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-start"
                  onClick={() =>
                    navigate(`/rd-projects/${id}/reports/deduction-detail`)
                  }
                >
                  <Calculator className="h-5 w-5 mb-2" />
                  <span className="font-medium">加计扣除明细</span>
                  <span className="text-xs text-slate-500 mt-1">
                    按项目、按类型汇总
                  </span>
                </Button>
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-start"
                  onClick={() =>
                    navigate(`/rd-projects/${id}/reports/high-tech`)
                  }
                >
                  <TrendingUp className="h-5 w-5 mb-2" />
                  <span className="font-medium">高新企业费用表</span>
                  <span className="text-xs text-slate-500 mt-1">
                    按六大费用类型汇总
                  </span>
                </Button>
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-start"
                  onClick={() =>
                    navigate(`/rd-projects/${id}/reports/intensity`)
                  }
                >
                  <BarChart3 className="h-5 w-5 mb-2" />
                  <span className="font-medium">研发投入强度</span>
                  <span className="text-xs text-slate-500 mt-1">
                    研发费用/营业收入
                  </span>
                </Button>
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-start"
                  onClick={() =>
                    navigate(`/rd-projects/${id}/reports/personnel`)
                  }
                >
                  <Users className="h-5 w-5 mb-2" />
                  <span className="font-medium">研发人员统计</span>
                  <span className="text-xs text-slate-500 mt-1">
                    研发人员占比、工时分配
                  </span>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
