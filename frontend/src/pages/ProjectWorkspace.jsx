import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn as _cn } from "../lib/utils";
import { projectWorkspaceApi, projectContributionApi as _projectContributionApi } from "../services/api";
import { formatDate, formatCurrency } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  HealthBadge,
  Progress,
  Skeleton,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  toast } from
"../components/ui";
import ProjectBonusPanel from "../components/project/ProjectBonusPanel";
import ProjectMeetingPanel from "../components/project/ProjectMeetingPanel";
import ProjectIssuePanel from "../components/project/ProjectIssuePanel";
import SolutionLibrary from "../components/project/SolutionLibrary";
import {
  ArrowLeft,
  Briefcase,
  Users,
  DollarSign,
  FileText,
  Calendar,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Award,
  MessageSquare,
  BookOpen,
  Activity } from
"lucide-react";

export default function ProjectWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [workspaceData, setWorkspaceData] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchWorkspaceData();
  }, [id]);

  const fetchWorkspaceData = async () => {
    try {
      setLoading(true);
      const response = await projectWorkspaceApi.getWorkspace(id);
      setWorkspaceData(response.data);
    } catch (error) {
      console.error("Failed to load workspace data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <Skeleton className="h-12 w-64 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) =>
          <Skeleton key={i} className="h-48" />
          )}
        </div>
      </div>);

  }

  if (!workspaceData) {
    return (
      <div className="p-6">
        <PageHeader title="项目工作空间" />
        <Card>
          <CardContent className="p-6 text-center text-gray-500">
            无法加载项目数据
          </CardContent>
        </Card>
      </div>);

  }

  const {
    project,
    team,
    tasks,
    bonus: _bonus,
    meetings: _meetings,
    issues: _issues,
    solutions: _solutions,
    documents
  } = workspaceData;

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        title={
        <div className="flex items-center gap-3">
            <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(-1)}
            className="p-0 h-auto">

              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold">{project.project_name}</h1>
              <p className="text-sm text-gray-500">{project.project_code}</p>
            </div>
        </div>
        } />


      {/* 项目概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">项目进度</p>
                <p className="text-2xl font-bold">{project.progress_pct}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
            <Progress value={project.progress_pct} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">健康度</p>
                <HealthBadge health={project.health} className="mt-1" />
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">团队成员</p>
                <p className="text-2xl font-bold">{team.length}</p>
              </div>
              <Users className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">合同金额</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(project.contract_amount)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 标签页 */}
      <Tabs value={activeTab || "unknown"} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="bonus">奖金</TabsTrigger>
          <TabsTrigger value="meetings">会议</TabsTrigger>
          <TabsTrigger value="issues">问题</TabsTrigger>
          <TabsTrigger value="solutions">解决方案</TabsTrigger>
          <TabsTrigger value="documents">文档</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* 团队概览 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                项目团队
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(team || []).map((member) =>
                <div
                  key={member.user_id}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors">

                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{member.user_name}</p>
                        <p className="text-sm text-gray-500">
                          {member.role_code}
                        </p>
                      </div>
                      <Badge variant="outline">{member.allocation_pct}%</Badge>
                    </div>
                    {member.start_date && member.end_date &&
                  <p className="text-xs text-gray-400 mt-2">
                        {member.start_date} ~ {member.end_date}
                  </p>
                  }
                </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 任务概览 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="h-5 w-5" />
                最近任务
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {tasks.slice(0, 10).map((task) =>
                <div
                  key={task.id}
                  className="flex items-center justify-between p-3 border rounded-lg">

                    <div className="flex-1">
                      <p className="font-medium">{task.title}</p>
                      <p className="text-sm text-gray-500">
                        {task.assignee_name}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                      variant={
                      task.status === "COMPLETED" ? "default" : "secondary"
                      }>

                        {task.status}
                      </Badge>
                      <Progress value={task.progress} className="w-20" />
                    </div>
                </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bonus" className="space-y-6">
          <ProjectBonusPanel projectId={id} />
        </TabsContent>

        <TabsContent value="meetings" className="space-y-6">
          <ProjectMeetingPanel projectId={id} />
        </TabsContent>

        <TabsContent value="issues" className="space-y-6">
          <ProjectIssuePanel projectId={id} />
        </TabsContent>

        <TabsContent value="solutions" className="space-y-6">
          <SolutionLibrary
            projectId={id}
            onApplyTemplate={async (template) => {
              const text =
                template?.solution ||
                template?.solution_template ||
                template?.description_template ||
                "";
              if (!text) {
                toast.info("该模板暂无可复制内容");
                return;
              }
              try {
                await navigator.clipboard.writeText(text);
                toast.success("已复制模板内容到剪贴板");
              } catch {
                toast.info("复制失败，请手动复制模板内容");
              }
            }}
          />

        </TabsContent>

        <TabsContent value="documents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                项目文档
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {(documents || []).map((doc) =>
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 transition-colors">

                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="font-medium">{doc.doc_name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline">{doc.doc_type}</Badge>
                          <span className="text-sm text-gray-500">
                            v{doc.version}
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatDate(doc.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <Badge
                    variant={
                    doc.status === "APPROVED" ? "default" : "secondary"
                    }>

                      {doc.status}
                    </Badge>
                </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>);

}
