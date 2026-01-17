/**
 * Technical Assessment Page - 技术评估页面
 * 支持线索和商机的技术评估
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  User,
  FileText,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Shield,
  Target,
  Download } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui";
import { technicalAssessmentApi } from "../services/api";
import { RadarChart } from "../components/assessment/RadarChart";
import { TrendChart } from "../components/assessment/TrendChart";
import { ComparisonChart } from "../components/assessment/ComparisonChart";

const decisionConfig = {
  RECOMMEND: {
    label: "推荐立项",
    color: "bg-green-500",
    textColor: "text-green-400"
  },
  CONDITIONAL: {
    label: "有条件立项",
    color: "bg-yellow-500",
    textColor: "text-yellow-400"
  },
  DEFER: {
    label: "暂缓",
    color: "bg-orange-500",
    textColor: "text-orange-400"
  },
  NOT_RECOMMEND: {
    label: "不建议立项",
    color: "bg-red-500",
    textColor: "text-red-400"
  }
};

const statusConfig = {
  PENDING: {
    label: "待评估",
    color: "bg-gray-500",
    textColor: "text-gray-400"
  },
  IN_PROGRESS: {
    label: "评估中",
    color: "bg-blue-500",
    textColor: "text-blue-400"
  },
  COMPLETED: {
    label: "已完成",
    color: "bg-green-500",
    textColor: "text-green-400"
  },
  CANCELLED: {
    label: "已取消",
    color: "bg-red-500",
    textColor: "text-red-400"
  }
};

export default function TechnicalAssessment() {
  const { sourceType, sourceId } = useParams(); // sourceType: 'lead' or 'opportunity', sourceId: ID
  const _navigate = useNavigate();

  const [assessment, setAssessment] = useState(null);
  const [assessments, setAssessments] = useState([]); // 所有评估记录
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [requirementData, setRequirementData] = useState({});
  const [enableAI, setEnableAI] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    loadAssessment();
  }, [sourceType, sourceId]);

  const loadAssessment = async () => {
    try {
      setLoading(true);
      let assessments = [];

      if (sourceType === "lead") {
        const response = await technicalAssessmentApi.getLeadAssessments(
          parseInt(sourceId)
        );
        assessments = response.data.items || response.data || [];
      } else if (sourceType === "opportunity") {
        const response = await technicalAssessmentApi.getOpportunityAssessments(
          parseInt(sourceId)
        );
        assessments = response.data.items || response.data || [];
      }

      setAssessments(assessments);
      if (assessments.length > 0) {
        setAssessment(assessments[0]); // 显示最新的评估
      }
    } catch (error) {
      console.error("加载评估失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyAssessment = async () => {
    try {
      let response;
      if (sourceType === "lead") {
        response = await technicalAssessmentApi.applyForLead(
          parseInt(sourceId),
          {}
        );
      } else {
        response = await technicalAssessmentApi.applyForOpportunity(
          parseInt(sourceId),
          {}
        );
      }

      if (response.data?.data?.assessment_id) {
        await loadAssessment();
        alert("技术评估申请已提交");
      }
    } catch (error) {
      console.error("申请评估失败:", error);
      alert("申请评估失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleEvaluate = async () => {
    if (!requirementData || Object.keys(requirementData).length === 0) {
      alert("请先填写需求数据");
      return;
    }

    if (!assessment) {
      alert("请先申请技术评估");
      return;
    }

    try {
      setEvaluating(true);
      const response = await technicalAssessmentApi.evaluate(assessment.id, {
        requirement_data: requirementData,
        enable_ai: enableAI
      });

      setAssessment(response.data);
      await loadAssessment(); // 重新加载评估列表
      alert("技术评估完成");
    } catch (error) {
      console.error("执行评估失败:", error);
      alert("执行评估失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setEvaluating(false);
    }
  };

  const handleExportReport = () => {
    if (!assessment) return;

    const report = {
      评估编号: assessment.id,
      来源类型: assessment.source_type === "LEAD" ? "线索" : "商机",
      来源ID: assessment.source_id,
      评估状态: statusConfig[assessment.status]?.label || assessment.status,
      总分: assessment.total_score,
      决策建议:
      decisionConfig[assessment.decision]?.label || assessment.decision,
      评估时间: assessment.evaluated_at ?
      new Date(assessment.evaluated_at).toLocaleString() :
      "未评估",
      评估人: assessment.evaluator_name || "未知"
    };

    if (dimensionScores) {
      report["维度评分"] = dimensionScores;
    }

    if (risks.length > 0) {
      report["风险分析"] = risks;
    }

    if (similarCases.length > 0) {
      report["相似案例"] = similarCases;
    }

    if (conditions.length > 0) {
      report["立项条件"] = conditions;
    }

    // 导出为JSON文件
    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `技术评估报告_${assessment.id}_${new Date().toISOString().split("T")[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  const dimensionScores = assessment?.dimension_scores ?
  JSON.parse(assessment.dimension_scores) :
  null;
  const risks = assessment?.risks ? JSON.parse(assessment.risks) : [];
  const similarCases = assessment?.similar_cases ?
  JSON.parse(assessment.similar_cases) :
  [];
  const conditions = assessment?.conditions ?
  JSON.parse(assessment.conditions) :
  [];

  const dimensionLabels = {
    technology: "技术",
    business: "商务",
    resource: "资源",
    delivery: "交付",
    customer: "客户关系"
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <PageHeader
        title="技术评估"
        breadcrumbs={[
        { label: "销售管理", path: "/sales" },
        {
          label: sourceType === "lead" ? "线索管理" : "商机管理",
          path: sourceType === "lead" ? "/leads" : "/opportunities"
        },
        { label: "技术评估", path: "" }]
        } />


      <div className="mt-6 space-y-6">
        {/* 评估状态卡片 */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>评估状态</CardTitle>
              <div className="flex gap-2">
                {assessments.length > 1 &&
                <Button
                  onClick={() => setShowHistory(!showHistory)}
                  variant="outline">

                    {showHistory ? "隐藏历史" : "查看历史"}
                  </Button>
                }
                {assessment && assessment.status === "COMPLETED" &&
                <Button
                  onClick={handleExportReport}
                  variant="outline"
                  className="border-blue-500 text-blue-400 hover:bg-blue-500/10">

                    <Download className="w-4 h-4 mr-2" />
                    导出报告
                  </Button>
                }
                {!assessment &&
                <Button
                  onClick={handleApplyAssessment}
                  className="bg-blue-600 hover:bg-blue-700">

                    申请技术评估
                  </Button>
                }
                {assessment && assessment.status === "PENDING" &&
                <Button
                  onClick={handleEvaluate}
                  disabled={evaluating}
                  className="bg-green-600 hover:bg-green-700">

                    {evaluating ? "评估中..." : "执行评估"}
                  </Button>
                }
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {assessment ?
            <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <Badge
                  className={
                  statusConfig[assessment.status]?.color || "bg-gray-500"
                  }>

                    {statusConfig[assessment.status]?.label ||
                  assessment.status}
                  </Badge>
                  {assessment.evaluator_name &&
                <span className="text-gray-400">
                      评估人: {assessment.evaluator_name}
                    </span>
                }
                  {assessment.evaluated_at &&
                <span className="text-gray-400">
                      评估时间:{" "}
                      {new Date(assessment.evaluated_at).toLocaleString()}
                    </span>
                }
                </div>

                {assessment.total_score !== null &&
              <div className="flex items-center gap-4">
                    <div className="text-3xl font-bold">
                      {assessment.total_score}
                    </div>
                    <div className="text-gray-400">总分 / 100</div>
                    <Progress
                  value={assessment.total_score}
                  className="flex-1" />

                  </div>
              }
              </div> :

            <div className="text-gray-400">尚未申请技术评估</div>
            }
          </CardContent>
        </Card>

        {/* 评估历史记录 */}
        {showHistory && assessments.length > 1 &&
        <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle>评估历史记录</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {assessments.map((item, _idx) => {
                const itemScores = item.dimension_scores ?
                JSON.parse(item.dimension_scores) :
                null;
                return (
                  <div
                    key={item.id}
                    className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                    item.id === assessment?.id ?
                    "bg-blue-900/30 border-blue-500" :
                    "bg-gray-700 border-gray-600 hover:border-gray-500"}`
                    }
                    onClick={() => setAssessment(item)}>

                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge
                          className={
                          statusConfig[item.status]?.color || "bg-gray-500"
                          }>

                            {statusConfig[item.status]?.label || item.status}
                          </Badge>
                          {item.total_score !== null &&
                        <span className="text-lg font-bold">
                              {item.total_score}分
                            </span>
                        }
                          {item.decision &&
                        <Badge
                          className={
                          decisionConfig[item.decision]?.color ||
                          "bg-gray-500"
                          }>

                              {decisionConfig[item.decision]?.label ||
                          item.decision}
                            </Badge>
                        }
                        </div>
                        <span className="text-xs text-gray-400">
                          {item.evaluated_at ?
                        new Date(item.evaluated_at).toLocaleString() :
                        "未评估"}
                        </span>
                      </div>
                      {itemScores &&
                    <div className="grid grid-cols-5 gap-2 mt-2">
                          {Object.entries(itemScores).map(([dim, score]) =>
                      <div key={dim} className="text-center">
                              <div className="text-xs text-gray-400">{dim}</div>
                              <div className="text-sm font-semibold">
                                {score}
                              </div>
                            </div>
                      )}
                        </div>
                    }
                    </div>);

              })}
              </div>
            </CardContent>
          </Card>
        }

        {assessment && assessment.status === "COMPLETED" &&
        <>
            {/* 评估结果 */}
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle>评估结果</CardTitle>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="scores" className="w-full">
                  <TabsList className="grid w-full grid-cols-6">
                    <TabsTrigger value="scores">评分详情</TabsTrigger>
                    <TabsTrigger value="trend">趋势分析</TabsTrigger>
                    <TabsTrigger value="comparison">对比分析</TabsTrigger>
                    <TabsTrigger value="risks">风险分析</TabsTrigger>
                    <TabsTrigger value="cases">相似案例</TabsTrigger>
                    <TabsTrigger value="ai">AI分析</TabsTrigger>
                  </TabsList>

                  <TabsContent value="scores" className="mt-4">
                    {dimensionScores &&
                  <div className="space-y-6">
                        {/* 雷达图 */}
                        <div className="flex justify-center">
                          <RadarChart
                        data={dimensionScores}
                        size={400}
                        maxScore={20} />

                        </div>

                        {/* 柱状图 */}
                        <div className="space-y-2">
                          <h4 className="text-sm font-semibold mb-4">
                            维度评分详情
                          </h4>
                          {Object.entries(dimensionScores).map(
                        ([dimension, score]) => {
                          const dimensionNames = {
                            technology: "技术维度",
                            business: "商务维度",
                            resource: "资源维度",
                            delivery: "交付维度",
                            customer: "客户关系维度"
                          };
                          return (
                            <div key={dimension} className="space-y-1">
                                  <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-300">
                                      {dimensionNames[dimension] || dimension}
                                    </span>
                                    <span className="font-semibold">
                                      {score} / 20
                                    </span>
                                  </div>
                                  <Progress
                                value={score / 20 * 100}
                                className="h-2" />

                                </div>);

                        }
                      )}
                        </div>

                        {assessment.decision &&
                    <div className="mt-6 p-4 bg-gray-700 rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                              <Target className="w-5 h-5" />
                              <span className="font-semibold">决策建议</span>
                            </div>
                            <Badge
                        className={
                        decisionConfig[assessment.decision]?.color ||
                        "bg-gray-500"
                        }>

                              {decisionConfig[assessment.decision]?.label ||
                        assessment.decision}
                            </Badge>
                            {conditions.length > 0 &&
                      <div className="mt-4">
                                <div className="text-sm font-semibold mb-2">
                                  立项条件:
                                </div>
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-300">
                                  {conditions.map((condition, idx) =>
                          <li key={idx}>{condition}</li>
                          )}
                                </ul>
                              </div>
                      }
                          </div>
                    }
                      </div>
                  }
                  </TabsContent>

                  <TabsContent value="trend" className="mt-4">
                    {assessments.length > 1 ?
                  <div className="space-y-4">
                        <div className="p-4 bg-gray-700 rounded-lg">
                          <h4 className="text-sm font-semibold mb-4">
                            评估分数趋势
                          </h4>
                          <TrendChart
                        data={assessments.
                        filter((a) => a.total_score !== null).
                        map((a, idx) => ({
                          date: a.evaluated_at || a.created_at,
                          value: a.total_score,
                          label: `评估${idx + 1}`
                        })).
                        sort(
                          (a, b) => new Date(a.date) - new Date(b.date)
                        )}
                        height={250} />

                        </div>

                        {/* 维度趋势 */}
                        {dimensionScores &&
                    <div className="p-4 bg-gray-700 rounded-lg">
                            <h4 className="text-sm font-semibold mb-4">
                              维度分数趋势
                            </h4>
                            <div className="space-y-4">
                              {Object.keys(dimensionLabels).map((dim) => {
                          const dimensionNames = {
                            technology: "技术维度",
                            business: "商务维度",
                            resource: "资源维度",
                            delivery: "交付维度",
                            customer: "客户关系维度"
                          };
                          const trendData = assessments.
                          filter((a) => a.dimension_scores).
                          map((a, idx) => {
                            const scores = JSON.parse(
                              a.dimension_scores
                            );
                            return {
                              date: a.evaluated_at || a.created_at,
                              value: scores[dim] || 0,
                              label: `评估${idx + 1}`
                            };
                          }).
                          sort(
                            (a, b) =>
                            new Date(a.date) - new Date(b.date)
                          );

                          if (trendData.length === 0) return null;

                          return (
                            <div key={dim} className="space-y-2">
                                    <div className="text-sm text-gray-300">
                                      {dimensionNames[dim]}
                                    </div>
                                    <TrendChart data={trendData} height={150} />
                                  </div>);

                        })}
                            </div>
                          </div>
                    }
                      </div> :

                  <div className="text-gray-400 text-center py-8">
                        需要至少2次评估才能显示趋势分析
                      </div>
                  }
                  </TabsContent>

                  <TabsContent value="comparison" className="mt-4">
                    {assessments.length > 1 ?
                  <div className="space-y-4">
                        <div className="p-4 bg-gray-700 rounded-lg">
                          <h4 className="text-sm font-semibold mb-4">
                            评估维度对比
                          </h4>
                          <ComparisonChart
                        data={assessments.
                        filter((a) => a.dimension_scores).
                        slice(0, 5) // 最多对比5个评估
                        .map((a, idx) => ({
                          name: `评估${idx + 1} (${a.total_score}分)`,
                          scores: JSON.parse(a.dimension_scores)
                        }))}
                        height={300} />

                        </div>

                        {/* 总分对比 */}
                        <div className="p-4 bg-gray-700 rounded-lg">
                          <h4 className="text-sm font-semibold mb-4">
                            总分对比
                          </h4>
                          <div className="space-y-2">
                            {assessments.
                        filter((a) => a.total_score !== null).
                        map((a, idx) =>
                        <div
                          key={a.id}
                          className="flex items-center gap-4">

                                  <div className="w-24 text-sm text-gray-300">
                                    评估{idx + 1}
                                  </div>
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2">
                                      <div
                                className="h-6 bg-blue-500 rounded"
                                style={{
                                  width: `${a.total_score / 100 * 100}%`
                                }} />

                                      <span className="text-sm font-semibold w-12 text-right">
                                        {a.total_score}分
                                      </span>
                                    </div>
                                  </div>
                                  <div className="text-xs text-gray-400 w-32">
                                    {a.evaluated_at ?
                            new Date(
                              a.evaluated_at
                            ).toLocaleDateString() :
                            "未评估"}
                                  </div>
                                </div>
                        )}
                          </div>
                        </div>
                      </div> :

                  <div className="text-gray-400 text-center py-8">
                        需要至少2次评估才能显示对比分析
                      </div>
                  }
                  </TabsContent>

                  <TabsContent value="risks" className="mt-4">
                    {risks.length > 0 ?
                  <div className="space-y-3">
                        {risks.map((risk, idx) =>
                    <div key={idx} className="p-4 bg-gray-700 rounded-lg">
                            <div className="flex items-center gap-2 mb-2">
                              <AlertTriangle
                          className={`w-5 h-5 ${
                          risk.level === "HIGH" ?
                          "text-red-400" :
                          "text-yellow-400"}`
                          } />

                              <Badge
                          className={
                          risk.level === "HIGH" ?
                          "bg-red-500" :
                          "bg-yellow-500"
                          }>

                                {risk.level}
                              </Badge>
                              <span className="text-sm text-gray-400">
                                {risk.dimension}
                              </span>
                            </div>
                            <div className="text-sm">{risk.description}</div>
                          </div>
                    )}
                      </div> :

                  <div className="text-gray-400">无风险记录</div>
                  }
                  </TabsContent>

                  <TabsContent value="cases" className="mt-4">
                    {similarCases.length > 0 ?
                  <div className="space-y-3">
                        {similarCases.map((case_, idx) =>
                    <div key={idx} className="p-4 bg-gray-700 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <div className="font-semibold">
                                {case_.project_name}
                              </div>
                              <Badge>
                                相似度:{" "}
                                {(case_.similarity_score * 100).toFixed(0)}%
                              </Badge>
                            </div>
                            <div className="text-sm text-gray-300 mb-2">
                              {case_.core_failure_reason}
                            </div>
                            <div className="text-sm text-gray-400">
                              {case_.lesson_learned}
                            </div>
                          </div>
                    )}
                      </div> :

                  <div className="text-gray-400">无相似案例</div>
                  }
                  </TabsContent>

                  <TabsContent value="ai" className="mt-4">
                    {assessment.ai_analysis ?
                  <div className="p-4 bg-gray-700 rounded-lg whitespace-pre-wrap">
                        {assessment.ai_analysis}
                      </div> :

                  <div className="text-gray-400">未启用AI分析</div>
                  }
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </>
        }

        {assessment && assessment.status === "PENDING" &&
        <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle>需求数据</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    需求数据 (JSON格式)
                  </label>
                  <textarea
                  className="w-full h-64 p-3 bg-gray-700 border border-gray-600 rounded text-white font-mono text-sm"
                  value={JSON.stringify(requirementData, null, 2)}
                  onChange={(e) => {
                    try {
                      setRequirementData(JSON.parse(e.target.value));
                    } catch (_err) {

                      // 忽略解析错误
                    }}}
                  placeholder='{"industry": "新能源", "budgetStatus": "明确", ...}' />

                </div>
                <div className="flex items-center gap-2">
                  <input
                  type="checkbox"
                  id="enableAI"
                  checked={enableAI}
                  onChange={(e) => setEnableAI(e.target.checked)} />

                  <label htmlFor="enableAI" className="text-sm">
                    启用AI分析（需要配置API密钥）
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        }
      </div>
    </div>);

}