import { Download } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
} from "../../../components/ui";
import { statusConfig } from "../utils/pageConstants";

function getTemplateOptionId(template) {
  return template?.id ?? template?.template_id ?? template?.templateId ?? "";
}

function getTemplateOptionName(template) {
  const name = template?.template_name || template?.templateName || template?.name || "未命名模板";
  return template?.version ? `${name} (${template.version})` : name;
}

function TemplateSelector({ templates, selectedTemplateId, onTemplateChange }) {
  return (
    <label htmlFor="assessment-template" className="block max-w-md space-y-1">
      <span className="text-xs text-slate-400">评估模板</span>
      <select
        id="assessment-template"
        aria-label="评估模板"
        value={selectedTemplateId}
        onChange={(event) => onTemplateChange?.(event.target.value)}
        className="h-10 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 text-sm text-white focus:border-blue-500 focus:outline-none"
      >
        <option value="">默认评分规则</option>
        {templates.map((template) => (
          <option key={getTemplateOptionId(template)} value={getTemplateOptionId(template)}>
            {getTemplateOptionName(template)}
          </option>
        ))}
      </select>
    </label>
  );
}

export function AssessmentStatusCard({
  assessment,
  assessments,
  showHistory,
  setShowHistory,
  evaluating,
  assessmentTemplates = [],
  selectedTemplateId = "",
  onTemplateChange,
  onExportReport,
  onApplyAssessment,
  onEvaluate,
}) {
  const selectedTemplate = assessmentTemplates.find(
    (template) => String(getTemplateOptionId(template)) === String(selectedTemplateId),
  );
  const selectedTemplateName = selectedTemplate
    ? getTemplateOptionName(selectedTemplate).replace(/\s*\(([^)]+)\)$/, " $1")
    : selectedTemplateId
      ? `模板 #${selectedTemplateId}`
      : "";
  const canSelectTemplate =
    assessmentTemplates.length > 0 &&
    (!assessment || ["PENDING", "IN_PROGRESS"].includes(String(assessment.status || "").toUpperCase()));

  return (
    <Card className="bg-gray-800 border-gray-700">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>评估状态</CardTitle>
          <div className="flex gap-2">
            {assessments.length > 1 && (
              <Button
                onClick={() => setShowHistory(!showHistory)}
                variant="outline"
              >
                {showHistory ? "隐藏历史" : "查看历史"}
              </Button>
            )}
            {assessment && assessment.status === "COMPLETED" && (
              <Button
                onClick={onExportReport}
                variant="outline"
                className="border-blue-500 text-blue-400 hover:bg-blue-500/10"
              >
                <Download className="w-4 h-4 mr-2" />
                导出报告
              </Button>
            )}
            {!assessment && (
              <Button
                onClick={onApplyAssessment}
                className="bg-blue-600 hover:bg-blue-700"
              >
                申请技术评估
              </Button>
            )}
            {assessment && assessment.status === "PENDING" && (
              <Button
                onClick={onEvaluate}
                disabled={evaluating}
                className="bg-green-600 hover:bg-green-700"
              >
                {evaluating ? "评估中..." : "执行评估"}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {assessment ? (
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <Badge
                className={
                  statusConfig[assessment.status]?.color || "bg-gray-500"
                }
              >
                {statusConfig[assessment.status]?.label || assessment.status}
              </Badge>
              {assessment.evaluator_name && (
                <span className="text-gray-400">
                  评估人: {assessment.evaluator_name}
                </span>
              )}
              {assessment.evaluated_at && (
                <span className="text-gray-400">
                  评估时间:{" "}
                  {new Date(assessment.evaluated_at).toLocaleString()}
                </span>
              )}
            </div>

            {canSelectTemplate && (
              <TemplateSelector
                templates={assessmentTemplates}
                selectedTemplateId={selectedTemplateId}
                onTemplateChange={onTemplateChange}
              />
            )}

            {!canSelectTemplate && selectedTemplateName && (
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <span className="text-slate-400">评估模板</span>
                <Badge variant="outline">{selectedTemplateName}</Badge>
              </div>
            )}

            {assessment.total_score !== null && (
              <div className="flex items-center gap-4">
                <div className="text-3xl font-bold">
                  {assessment.total_score}
                </div>
                <div className="text-gray-400">总分 / 100</div>
                <Progress value={assessment.total_score} className="flex-1" />
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {canSelectTemplate && (
              <TemplateSelector
                templates={assessmentTemplates}
                selectedTemplateId={selectedTemplateId}
                onTemplateChange={onTemplateChange}
              />
            )}
            <div className="text-gray-400">尚未申请技术评估</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
