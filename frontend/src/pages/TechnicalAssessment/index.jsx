/**
 * 技术评估工作台 - 薄壳组件
 * 1,348 行单体拆分为: constants + hook + 2 个标签页组件
 */

import {
  Clock3,
  Download,
  GitBranch,
  Layers3,
  ShieldAlert,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
} from "../../components/ui";
import {
  dimensionLabels,
  funnelEntityLabels,
  formatDate,
  formatSourceType,
  getDecisionMeta,
  getStatusMeta,
} from "./constants";
import { useTechnicalAssessment } from "./hooks/useTechnicalAssessment";
import { AssessmentResultTabs } from "./components/AssessmentResultTabs";
import { WorkbenchContextTabs } from "./components/WorkbenchContextTabs";

export default function TechnicalAssessment() {
  const ctx = useTechnicalAssessment();

  if (ctx.loading) {
    return <div className="p-6 text-slate-300">加载中...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <PageHeader
        title="技术评估工作台"
        breadcrumbs={[
          { label: "销售管理", path: "/sales" },
          {
            label: ctx.normalizedSourceType === "lead" ? "线索管理" : "商机管理",
            path: ctx.normalizedSourceType === "lead" ? "/sales/leads" : "/sales/opportunities",
          },
          { label: "技术评估", path: "" },
        ]}
      />

      <div className="mt-6 space-y-6">
        {ctx.error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {ctx.error}
          </div>
        )}

        {ctx.partialFailures.length > 0 && (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            部分数据加载失败：
            {ctx.partialFailures.map((item) => ` ${item.key}(${item.message})`).join("；")}
          </div>
        )}

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">评估记录</div>
                  <div className="text-3xl font-semibold">{ctx.assessments.length}</div>
                </div>
                <Layers3 className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">风险台账</div>
                  <div className="text-3xl font-semibold">{ctx.totalRiskCount}</div>
                </div>
                <ShieldAlert className="h-8 w-8 text-red-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">模板资产</div>
                  <div className="text-3xl font-semibold">
                    {ctx.assessmentTemplates.length + ctx.technicalTemplates.length}
                  </div>
                </div>
                <GitBranch className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">活跃预警</div>
                  <div className="text-3xl font-semibold">{ctx.dwellAlerts.length}</div>
                </div>
                <Clock3 className="h-8 w-8 text-amber-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 评估主状态卡片 */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-2">
                <CardTitle>评估主状态</CardTitle>
                <div className="flex flex-wrap gap-2 text-sm text-gray-400">
                  <span>来源: {formatSourceType(ctx.normalizedSourceType)} #{ctx.numericSourceId}</span>
                  {ctx.workbench?.ticket?.ticket_no && <span>工单: {ctx.workbench.ticket.ticket_no}</span>}
                  <span>流程实体: {funnelEntityLabels[ctx.workbench?.funnel?.entityType] || "未识别"}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {ctx.assessments.length > 1 && (
                  <Button variant="outline" onClick={() => ctx.setShowHistory((value) => !value)}>
                    {ctx.showHistory ? "隐藏历史" : "查看历史"}
                  </Button>
                )}
                {ctx.selectedAssessment?.status === "COMPLETED" && (
                  <Button
                    variant="outline"
                    className="border-blue-500 text-blue-300 hover:bg-blue-500/10"
                    onClick={ctx.handleExportReport}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    导出报告
                  </Button>
                )}
                {!ctx.selectedAssessment && (
                  <Button className="bg-blue-600 hover:bg-blue-700" onClick={ctx.handleApplyAssessment}>
                    申请技术评估
                  </Button>
                )}
                {ctx.selectedAssessment?.status === "PENDING" && (
                  <Button
                    className="bg-green-600 hover:bg-green-700"
                    disabled={ctx.evaluating}
                    onClick={ctx.handleEvaluate}
                  >
                    {ctx.evaluating ? "评估中..." : "执行评估"}
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {ctx.selectedAssessment ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Badge className={ctx.selectedAssessmentStatus.color}>
                    {ctx.selectedAssessmentStatus.label}
                  </Badge>
                  {ctx.selectedAssessment.decision && (
                    <Badge className={ctx.selectedDecision.color}>{ctx.selectedDecision.label}</Badge>
                  )}
                  <span className="text-sm text-gray-400">
                    评估人: {ctx.selectedAssessment.evaluator_name || "未分配"}
                  </span>
                  <span className="text-sm text-gray-400">
                    更新时间: {formatDate(ctx.selectedAssessment.evaluated_at || ctx.selectedAssessment.updated_at)}
                  </span>
                </div>

                {ctx.selectedAssessment.total_score !== null &&
                  ctx.selectedAssessment.total_score !== undefined && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-4">
                        <div className="text-3xl font-semibold">{ctx.selectedAssessment.total_score}</div>
                        <div className="text-sm text-gray-400">总分 / 100</div>
                        <Progress value={ctx.selectedAssessment.total_score} className="flex-1" />
                      </div>
                      {ctx.dimensionScores && (
                        <div className="grid grid-cols-2 gap-3 text-sm text-gray-300 md:grid-cols-5">
                          {Object.entries(dimensionLabels).map(([key, label]) => (
                            <div key={key} className="rounded-lg bg-gray-800 px-3 py-2">
                              <div className="text-gray-400">{label}</div>
                              <div className="text-lg font-semibold">{ctx.dimensionScores[key] ?? 0}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
              </div>
            ) : (
              <div className="text-gray-400">尚未申请技术评估</div>
            )}
          </CardContent>
        </Card>

        {/* 评估历史 */}
        {ctx.showHistory && ctx.assessments.length > 1 && (
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle>评估历史</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {ctx.assessments.map((item, index) => {
                  const itemStatus = getStatusMeta(item.status);
                  const itemDecision = getDecisionMeta(item.decision);
                  return (
                    <button
                      key={item.id}
                      type="button"
                      className={`w-full rounded-lg border px-4 py-3 text-left transition-colors ${
                        item.id === ctx.selectedAssessment?.id
                          ? "border-blue-500 bg-blue-500/10"
                          : "border-gray-800 bg-gray-950 hover:border-gray-700"
                      }`}
                      onClick={() => ctx.setSelectedAssessmentId(item.id)}
                    >
                      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm text-gray-400">评估{index + 1}</span>
                          <Badge className={itemStatus.color}>{itemStatus.label}</Badge>
                          {item.decision && <Badge className={itemDecision.color}>{itemDecision.label}</Badge>}
                          <span className="text-sm font-semibold">{item.total_score ?? "--"}分</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {formatDate(item.evaluated_at || item.created_at)}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 评估结果（已完成时显示） */}
        {ctx.selectedAssessment?.status === "COMPLETED" && (
          <AssessmentResultTabs
            selectedAssessment={ctx.selectedAssessment}
            dimensionScores={ctx.dimensionScores}
            selectedDecision={ctx.selectedDecision}
            conditions={ctx.conditions}
            trendSeries={ctx.trendSeries}
            assessments={ctx.assessments}
            comparisonSeries={ctx.comparisonSeries}
            legacyRisks={ctx.legacyRisks}
            similarCases={ctx.similarCases}
          />
        )}

        {/* 工作台上下文 */}
        <WorkbenchContextTabs
          normalizedSourceType={ctx.normalizedSourceType}
          requirementDetail={ctx.requirementDetail}
          requirementText={ctx.requirementText}
          setRequirementText={ctx.setRequirementText}
          requirementDirty={ctx.requirementDirty}
          setRequirementDirty={ctx.setRequirementDirty}
          enableAI={ctx.enableAI}
          setEnableAI={ctx.setEnableAI}
          savingRequirement={ctx.savingRequirement}
          handleSaveRequirement={ctx.handleSaveRequirement}
          assessmentTemplates={ctx.assessmentTemplates}
          technicalTemplates={ctx.technicalTemplates}
          solutions={ctx.solutions}
          selectedAssessment={ctx.selectedAssessment}
          artifactFailures={ctx.artifactFailures}
          artifactLoading={ctx.artifactLoading}
          structuredRisks={ctx.structuredRisks}
          versions={ctx.versions}
          stages={ctx.stages}
          dwellAlerts={ctx.dwellAlerts}
          gateConfigs={ctx.gateConfigs}
          transitionLogs={ctx.transitionLogs}
        />
      </div>
    </div>
  );
}
