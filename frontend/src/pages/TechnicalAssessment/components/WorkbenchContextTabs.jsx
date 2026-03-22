/**
 * 工作台上下文标签页 - 需求包、模板与方案、风险与版本、阶段门与漏斗
 */

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  FileJson,
  GitBranch,
  Layers3,
  Save,
  Target,
  Workflow,
} from "lucide-react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../../components/ui";
import { formatDate, getRiskLevelBadge } from "../constants";

export function WorkbenchContextTabs({
  normalizedSourceType,
  requirementDetail,
  requirementText,
  setRequirementText,
  requirementDirty,
  setRequirementDirty,
  enableAI,
  setEnableAI,
  savingRequirement,
  handleSaveRequirement,
  assessmentTemplates,
  technicalTemplates,
  solutions,
  selectedAssessment,
  artifactFailures,
  artifactLoading,
  structuredRisks,
  versions,
  stages,
  dwellAlerts,
  gateConfigs,
  transitionLogs,
}) {
  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle>工作台上下文</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="requirement" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="requirement">需求包</TabsTrigger>
            <TabsTrigger value="assets">模板与方案</TabsTrigger>
            <TabsTrigger value="risk-ledger">风险与版本</TabsTrigger>
            <TabsTrigger value="funnel">阶段门与漏斗</TabsTrigger>
          </TabsList>

          {/* 需求包 */}
          <TabsContent value="requirement" className="mt-4 space-y-4">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="text-sm text-gray-400">需求版本</div>
                <div className="mt-1 text-lg font-semibold">
                  {requirementDetail?.requirement_version || "未设置"}
                </div>
              </div>
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="text-sm text-gray-400">是否冻结</div>
                <div className="mt-1 text-lg font-semibold">
                  {requirementDetail?.is_frozen ? "已冻结" : "未冻结"}
                </div>
              </div>
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="text-sm text-gray-400">验收方式</div>
                <div className="mt-1 text-lg font-semibold">
                  {requirementDetail?.acceptance_method || "未填写"}
                </div>
              </div>
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="text-sm text-gray-400">目标节拍</div>
                <div className="mt-1 text-lg font-semibold">
                  {requirementDetail?.cycle_time_seconds
                    ? `${requirementDetail.cycle_time_seconds} 秒`
                    : "未填写"}
                </div>
              </div>
            </div>

            <div className="rounded-lg bg-gray-800 p-4">
              <div className="mb-3 flex items-center gap-2">
                <FileJson className="h-4 w-4 text-blue-400" />
                <span className="font-semibold">需求数据</span>
              </div>
              <textarea
                className="h-72 w-full rounded border border-gray-700 bg-gray-950 p-3 font-mono text-sm text-white"
                value={requirementText}
                onChange={(event) => {
                  setRequirementDirty(true);
                  setRequirementText(event.target.value);
                }}
                readOnly={normalizedSourceType === "lead" && requirementDetail?.is_frozen}
                placeholder='{"industry": "新能源", "budget_status": "明确"}'
              />
              <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    id="enable-ai"
                    type="checkbox"
                    checked={enableAI}
                    onChange={(event) => setEnableAI(event.target.checked)}
                  />
                  <label htmlFor="enable-ai">执行评估时启用 AI 分析</label>
                </div>
                {normalizedSourceType === "lead" && (
                  <Button
                    variant="outline"
                    className="border-blue-500 text-blue-300 hover:bg-blue-500/10"
                    disabled={
                      savingRequirement ||
                      !requirementDirty ||
                      Boolean(requirementDetail?.is_frozen)
                    }
                    onClick={handleSaveRequirement}
                  >
                    <Save className="mr-2 h-4 w-4" />
                    {savingRequirement ? "保存中..." : "保存需求"}
                  </Button>
                )}
              </div>
              {normalizedSourceType === "lead" && requirementDetail?.is_frozen && (
                <div className="mt-3 text-xs text-amber-200">
                  需求包已冻结，当前内容仅可查看，不能回写。
                </div>
              )}
              {normalizedSourceType === "opportunity" && (
                <div className="mt-3 text-xs text-gray-500">
                  商机来源暂不支持回写需求详情，当前 JSON 将直接用于本次评估。
                </div>
              )}
            </div>
          </TabsContent>

          {/* 模板与方案 */}
          <TabsContent value="assets" className="mt-4 space-y-4">
            <div className="grid gap-4 xl:grid-cols-3">
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Layers3 className="h-4 w-4 text-purple-400" />
                  <span className="font-semibold">评估模板</span>
                </div>
                <div className="space-y-2">
                  {assessmentTemplates.slice(0, 5).map((template) => (
                    <div key={template.id} className="rounded bg-gray-950 px-3 py-2">
                      <div className="font-medium">{template.template_name}</div>
                      <div className="text-xs text-gray-400">
                        {template.category} · {template.version}
                      </div>
                    </div>
                  ))}
                  {assessmentTemplates.length === 0 && (
                    <div className="text-sm text-gray-400">暂无评估模板</div>
                  )}
                </div>
              </div>

              <div className="rounded-lg bg-gray-800 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-cyan-400" />
                  <span className="font-semibold">技术参数模板</span>
                </div>
                <div className="space-y-2">
                  {technicalTemplates.slice(0, 5).map((template) => (
                    <div key={template.id} className="rounded bg-gray-950 px-3 py-2">
                      <div className="font-medium">{template.name}</div>
                      <div className="text-xs text-gray-400">
                        {template.industry || "未分类"} · {template.test_type || "未分类"}
                      </div>
                    </div>
                  ))}
                  {technicalTemplates.length === 0 && (
                    <div className="text-sm text-gray-400">暂无技术模板</div>
                  )}
                </div>
              </div>

              <div className="rounded-lg bg-gray-800 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                  <span className="font-semibold">关联方案</span>
                </div>
                <div className="space-y-2">
                  {solutions.slice(0, 5).map((solution) => (
                    <div key={solution.id} className="rounded bg-gray-950 px-3 py-2">
                      <div className="font-medium">
                        {solution.solution_name || solution.name || `方案 #${solution.id}`}
                      </div>
                      <div className="text-xs text-gray-400">
                        {solution.status || "未标记状态"}
                      </div>
                    </div>
                  ))}
                  {solutions.length === 0 && (
                    <div className="text-sm text-gray-400">暂无关联方案</div>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* 风险与版本 */}
          <TabsContent value="risk-ledger" className="mt-4 space-y-4">
            <div className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-3 text-sm text-slate-300">
              当前结构化风险和版本快照已跟随所选评估记录切换。
              {selectedAssessment?.id ? ` 当前评估 ID: ${selectedAssessment.id}` : ""}
            </div>
            {artifactFailures.length > 0 && (
              <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                评估结构化明细加载存在部分失败：
                {artifactFailures.map((item) => ` ${item.key}(${item.message})`).join("；")}
              </div>
            )}

            <div className="grid gap-4 xl:grid-cols-2">
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-400" />
                  <span className="font-semibold">结构化风险台账</span>
                </div>
                <div className="space-y-3">
                  {artifactLoading && structuredRisks.length === 0 && (
                    <div className="text-sm text-gray-400">结构化风险加载中...</div>
                  )}
                  {structuredRisks.map((risk) => (
                    <div key={risk.id} className="rounded bg-gray-950 px-3 py-3">
                      <div className="mb-2 flex items-center gap-2">
                        <Badge className={getRiskLevelBadge(risk.risk_level)}>
                          {risk.risk_level || "未评级"}
                        </Badge>
                        <span className="text-xs text-gray-500">{risk.risk_code}</span>
                      </div>
                      <div className="text-sm font-medium">
                        {risk.risk_title || risk.risk_type || "未命名风险"}
                      </div>
                      <div className="mt-1 text-sm text-gray-300">{risk.risk_description}</div>
                      {risk.mitigation_plan && (
                        <div className="mt-2 text-xs text-gray-400">
                          处置建议: {risk.mitigation_plan}
                        </div>
                      )}
                    </div>
                  ))}
                  {structuredRisks.length === 0 && (
                    <div className="text-sm text-gray-400">暂无结构化风险记录</div>
                  )}
                </div>
              </div>

              <div className="rounded-lg bg-gray-800 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Workflow className="h-4 w-4 text-blue-400" />
                  <span className="font-semibold">版本快照</span>
                </div>
                <div className="space-y-3">
                  {artifactLoading && versions.length === 0 && (
                    <div className="text-sm text-gray-400">版本快照加载中...</div>
                  )}
                  {versions.map((version) => (
                    <div key={version.id} className="rounded bg-gray-950 px-3 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-medium">{version.version_no}</div>
                        <div className="text-xs text-gray-500">{formatDate(version.created_at)}</div>
                      </div>
                      <div className="mt-2 text-sm text-gray-300">
                        {version.change_summary || "无变更说明"}
                      </div>
                    </div>
                  ))}
                  {versions.length === 0 && (
                    <div className="text-sm text-gray-400">暂无版本快照</div>
                  )}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* 阶段门与漏斗 */}
          <TabsContent value="funnel" className="mt-4 space-y-4">
            <div className="grid gap-4 xl:grid-cols-3">
              <div className="rounded-lg bg-gray-800 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Target className="h-4 w-4 text-green-400" />
                  <span className="font-semibold">阶段定义</span>
                </div>
                <div className="space-y-2">
                  {stages.map((stage) => (
                    <div key={stage.id} className="rounded bg-gray-950 px-3 py-2">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium">{stage.stage_name}</span>
                        <span className="text-xs text-gray-500">{stage.stage_code}</span>
                      </div>
                      <div className="mt-1 text-xs text-gray-400">
                        {stage.required_gate || "无阶段门"} ·
                        {stage.expected_duration_days
                          ? ` 预计 ${stage.expected_duration_days} 天`
                          : " 未配置停留时长"}
                      </div>
                    </div>
                  ))}
                  {stages.length === 0 && <div className="text-sm text-gray-400">暂无阶段配置</div>}
                </div>
              </div>

              <div className="rounded-lg bg-gray-800 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Clock3 className="h-4 w-4 text-amber-400" />
                  <span className="font-semibold">滞留预警</span>
                </div>
                <div className="space-y-2">
                  {dwellAlerts.map((alert) => (
                    <div key={alert.id} className="rounded bg-gray-950 px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Badge className={alert.severity === "CRITICAL" ? "bg-red-500" : "bg-yellow-500"}>
                          {alert.severity}
                        </Badge>
                        <span className="font-medium">{alert.stage || "未知阶段"}</span>
                      </div>
                      <div className="mt-1 text-xs text-gray-400">
                        已停留 {alert.dwell_hours} 小时 / 阈值 {alert.threshold_hours} 小时
                      </div>
                    </div>
                  ))}
                  {dwellAlerts.length === 0 && <div className="text-sm text-gray-400">暂无活跃预警</div>}
                </div>
              </div>

              <div className="rounded-lg bg-gray-800 p-4">
                <div className="mb-3 flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-purple-400" />
                  <span className="font-semibold">阶段门规则</span>
                </div>
                <div className="space-y-2">
                  {gateConfigs.map((gate) => (
                    <div key={gate.id} className="rounded bg-gray-950 px-3 py-2">
                      <div className="font-medium">{gate.gate_type}</div>
                      <div className="text-sm text-gray-300">{gate.gate_name}</div>
                      <div className="mt-1 text-xs text-gray-400">
                        {gate.description || "无规则说明"}
                      </div>
                    </div>
                  ))}
                  {gateConfigs.length === 0 && <div className="text-sm text-gray-400">暂无阶段门规则</div>}
                </div>
              </div>
            </div>

            <div className="rounded-lg bg-gray-800 p-4">
              <div className="mb-3 flex items-center gap-2">
                <Workflow className="h-4 w-4 text-cyan-400" />
                <span className="font-semibold">流转日志</span>
              </div>
              <div className="space-y-2">
                {transitionLogs.map((log) => (
                  <div key={log.id} className="rounded bg-gray-950 px-3 py-3">
                    <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                      <div className="font-medium">
                        {log.from_stage || "起点"} → {log.to_stage || "终点"}
                      </div>
                      <div className="text-xs text-gray-500">{formatDate(log.transitioned_at)}</div>
                    </div>
                    <div className="mt-1 text-sm text-gray-300">
                      {log.transition_reason || log.reason || "无变更原因"}
                    </div>
                  </div>
                ))}
                {transitionLogs.length === 0 && <div className="text-sm text-gray-400">暂无流转记录</div>}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
