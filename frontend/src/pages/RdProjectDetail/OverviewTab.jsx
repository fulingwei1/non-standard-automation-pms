import { useNavigate } from "react-router-dom";




import { formatDate, formatCurrency } from "../../lib/utils";

export default function OverviewTab({
  project,
  linkedProject,
  status,
  categoryType,
  id,
}) {
  const navigate = useNavigate();

  return (
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
  );
}
