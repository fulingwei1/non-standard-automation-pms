/**
 * 客服工作台页面 - 薄壳组件
 * 1,329 行单体拆分为: constants + hook + 7 个 UI 组件
 */

import { RefreshCw, UserRound } from "lucide-react";



import { TEAM_OVERVIEW_KEY } from "./constants";
import { useCustomerServiceWorkbench } from "./hooks/useCustomerServiceWorkbench";

export default function CustomerServiceWorkbench() {
  const ctx = useCustomerServiceWorkbench();

  if (ctx.loading) {
    return <WorkbenchLoading />;
  }

  if (ctx.error) {
    return (
      <ErrorMessage
        title="客服工作台加载失败"
        message={ctx.error}
        onRetry={ctx.loadWorkbenchData}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={ctx.canViewTeam ? "客服工作台" : "我的售后工作台"}
        description={
          ctx.canViewTeam
            ? "从客服部经理视角快速切换工程师，查看个人数据、全部服务工单和项目情况。"
            : "查看自己负责项目的服务工单、具体问题和解决状态。"
        }
        actions={{
          label: "刷新数据",
          icon: RefreshCw,
          variant: "outline",
          onClick: ctx.loadWorkbenchData,
        }}
      />

      <ScopeSummary title={ctx.scopeTitle} description={ctx.scopeDescription} stats={ctx.stats} />

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
        {ctx.canViewTeam ? (
          <EngineerRoster
            engineers={ctx.engineers}
            selectedKey={ctx.selectedEngineerKey}
            onSelect={ctx.setSelectedEngineerKey}
            canViewTeam={ctx.canViewTeam}
          />
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>当前工程师</CardTitle>
              <CardDescription>登录后默认聚焦本人负责的项目与售后任务。</CardDescription>
            </CardHeader>
            <CardContent>
              {ctx.selectedEngineer ? (
                <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-violet-500/15 text-lg font-semibold text-white">
                      {(ctx.selectedEngineer.name || "?").slice(0, 1)}
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-white">
                        {ctx.selectedEngineer.name}
                      </div>
                      <div className="text-sm text-slate-400">
                        {ctx.selectedEngineer.position || ctx.selectedEngineer.department || "售后服务工程师"}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Badge variant="secondary">项目 {ctx.selectedEngineer.projectCount}</Badge>
                    <Badge variant="warning">待办 {ctx.selectedEngineer.activeLoad}</Badge>
                    <Badge variant="outline">服务记录 {ctx.selectedEngineer.recordCount}</Badge>
                  </div>
                </div>
              ) : (
                <EmptyState
                  icon={UserRound}
                  title="暂未识别到个人画像"
                  message="当前账号还没有产生售后服务数据，后续有工单或服务记录后会自动展示。"
                />
              )}
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>
              {ctx.selectedEngineerKey === TEAM_OVERVIEW_KEY && ctx.canViewTeam
                ? "团队运营明细"
                : `${ctx.selectedEngineer?.name || "当前工程师"}明细`}
            </CardTitle>
            <CardDescription>{ctx.scopeDescription}</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={ctx.activeTab} onValueChange={ctx.setActiveTab}>
              <TabsList
                className="grid w-full gap-2"
                style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}
              >
                <TabsTrigger value="projects">项目情况</TabsTrigger>
                <TabsTrigger value="tickets">服务工单</TabsTrigger>
                <TabsTrigger value="issues">项目问题</TabsTrigger>
                <TabsTrigger value="field">现场任务</TabsTrigger>
              </TabsList>

              <TabsContent value="projects" className="mt-6">
                <ProjectTable projects={ctx.scope.projects} />
              </TabsContent>

              <TabsContent value="tickets" className="mt-6">
                <TicketTable tickets={ctx.scope.tickets} />
              </TabsContent>

              <TabsContent value="issues" className="mt-6">
                <IssueTable issues={ctx.scope.issues} />
              </TabsContent>

              <TabsContent value="field" className="mt-6">
                <FieldTaskTables records={ctx.scope.records} orders={ctx.scope.orders} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
