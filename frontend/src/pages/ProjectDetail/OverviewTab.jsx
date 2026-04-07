import { cn } from "../../lib/utils";
import { formatDate, formatCurrency } from "../../lib/utils";




import { STATUS_CONFIG, PRIORITY_CONFIG } from "./constants";

function StatusBadge({ status }) {
  const config = STATUS_CONFIG[status];
  return config ? (
    <Badge className={cn(config.color, "text-white")}>{config.label}</Badge>
  ) : (
    <Badge variant="secondary">{status}</Badge>
  );
}

function PriorityBadge({ priority }) {
  const config = PRIORITY_CONFIG[priority];
  return config ? (
    <Badge className={cn(config.color, "text-white")}>{config.label}</Badge>
  ) : (
    <Badge variant="secondary">{priority}</Badge>
  );
}

export default function OverviewTab({
  project,
  normalizedProject: p,
  stages,
  members,
  progress,
  budgetUtilization,
  onOpenAddMember,
  onRefresh,
}) {
  return (
    <div className="space-y-6">
      {/* 项目概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">项目状态</p>
                <div className="mt-2">
                  <StatusBadge status={p.status} />
                </div>
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
                <div className="mt-2">
                  <PriorityBadge priority={p.priority} />
                </div>
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
                <p className="text-2xl font-bold">{progress}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
            <Progress value={progress} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">预算使用</p>
                <p className="text-2xl font-bold">{budgetUtilization}%</p>
              </div>
              <DollarSign className="h-8 w-8 text-yellow-500" />
            </div>
            <Progress value={budgetUtilization} className="mt-2" />
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
                <Button variant="outline" size="sm" onClick={onOpenAddMember}>
                  <Plus className="mr-2 h-4 w-4" />
                  添加成员
                </Button>
              </div>
              <div className="space-y-3">
                {(members || []).map((member) => (
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
                ))}
                {members.length === 0 && (
                  <p className="text-center text-gray-500 py-4">暂无团队成员</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* 项目阶段 */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold mb-4">项目阶段</h3>
              <div className="space-y-3">
                {(stages || []).map((stage, index) => (
                  <div key={stage.id} className="flex items-center space-x-4">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium",
                        stage.status === "completed"
                          ? "bg-green-500"
                          : stage.status === "in_progress"
                          ? "bg-blue-500"
                          : "bg-gray-400"
                      )}
                    >
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{stage.name}</p>
                      <p className="text-sm text-gray-600">{stage.description}</p>
                    </div>
                    <Badge
                      variant={stage.status === "completed" ? "default" : "secondary"}
                    >
                      {stage.status === "completed"
                        ? "已完成"
                        : stage.status === "in_progress"
                        ? "进行中"
                        : "未开始"}
                    </Badge>
                  </div>
                ))}
                {stages.length === 0 && (
                  <p className="text-center text-gray-500 py-4">暂无项目阶段</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {/* 利润分析 */}
          <ProfitAnalysisCard projectId={project.id} />

          {/* 快速操作 */}
          <QuickActionPanel project={project} onRefresh={onRefresh} />

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
    </div>
  );
}
