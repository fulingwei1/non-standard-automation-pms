

import {
  decisionConfig,
  dimensionLabels,
  dimensionNames,
} from "../utils/pageConstants";

export function AssessmentResults({
  assessment,
  assessments,
  dimensionScores,
  risks,
  similarCases,
  conditions,
}) {
  return (
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
            <ScoresTab
              assessment={assessment}
              dimensionScores={dimensionScores}
              conditions={conditions}
            />
          </TabsContent>

          <TabsContent value="trend" className="mt-4">
            <TrendTab
              assessments={assessments}
              dimensionScores={dimensionScores}
            />
          </TabsContent>

          <TabsContent value="comparison" className="mt-4">
            <ComparisonTab assessments={assessments} />
          </TabsContent>

          <TabsContent value="risks" className="mt-4">
            <RisksTab risks={risks} />
          </TabsContent>

          <TabsContent value="cases" className="mt-4">
            <CasesTab similarCases={similarCases} />
          </TabsContent>

          <TabsContent value="ai" className="mt-4">
            {assessment.ai_analysis ? (
              <div className="p-4 bg-gray-700 rounded-lg whitespace-pre-wrap">
                {assessment.ai_analysis}
              </div>
            ) : (
              <div className="text-gray-400">未启用AI分析</div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}

function ScoresTab({ assessment, dimensionScores, conditions }) {
  if (!dimensionScores) return null;

  return (
    <div className="space-y-6">
      <div className="flex justify-center">
        <RadarChart data={dimensionScores} size={400} maxScore={20} />
      </div>

      <div className="space-y-2">
        <h4 className="text-sm font-semibold mb-4">维度评分详情</h4>
        {Object.entries(dimensionScores).map(([dimension, score]) => (
          <div key={dimension} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-300">
                {dimensionNames[dimension] || dimension}
              </span>
              <span className="font-semibold">{score} / 20</span>
            </div>
            <Progress value={(score / 20) * 100} className="h-2" />
          </div>
        ))}
      </div>

      {assessment.decision && (
        <div className="mt-6 p-4 bg-gray-700 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-5 h-5" />
            <span className="font-semibold">决策建议</span>
          </div>
          <Badge
            className={
              decisionConfig[assessment.decision]?.color || "bg-gray-500"
            }
          >
            {decisionConfig[assessment.decision]?.label || assessment.decision}
          </Badge>
          {conditions.length > 0 && (
            <div className="mt-4">
              <div className="text-sm font-semibold mb-2">立项条件:</div>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-300">
                {(conditions || []).map((condition, idx) => (
                  <li key={idx}>{condition}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function TrendTab({ assessments, dimensionScores }) {
  if (assessments.length <= 1) {
    return (
      <div className="text-gray-400 text-center py-8">
        需要至少2次评估才能显示趋势分析
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="p-4 bg-gray-700 rounded-lg">
        <h4 className="text-sm font-semibold mb-4">评估分数趋势</h4>
        <TrendChart
          data={assessments
            .filter((a) => a.total_score !== null)
            .map((a, idx) => ({
              date: a.evaluated_at || a.created_at,
              value: a.total_score,
              label: `评估${idx + 1}`,
            }))
            .sort((a, b) => new Date(a.date) - new Date(b.date))}
          height={250}
        />
      </div>

      {dimensionScores && (
        <div className="p-4 bg-gray-700 rounded-lg">
          <h4 className="text-sm font-semibold mb-4">维度分数趋势</h4>
          <div className="space-y-4">
            {Object.keys(dimensionLabels).map((dim) => {
              const trendData = assessments
                .filter((a) => a.dimension_scores)
                .map((a, idx) => {
                  const scores = JSON.parse(a.dimension_scores);
                  return {
                    date: a.evaluated_at || a.created_at,
                    value: scores[dim] || 0,
                    label: `评估${idx + 1}`,
                  };
                })
                .sort((a, b) => new Date(a.date) - new Date(b.date));

              if (trendData.length === 0) return null;

              return (
                <div key={dim} className="space-y-2">
                  <div className="text-sm text-gray-300">
                    {dimensionNames[dim]}
                  </div>
                  <TrendChart data={trendData} height={150} />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function ComparisonTab({ assessments }) {
  if (assessments.length <= 1) {
    return (
      <div className="text-gray-400 text-center py-8">
        需要至少2次评估才能显示对比分析
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="p-4 bg-gray-700 rounded-lg">
        <h4 className="text-sm font-semibold mb-4">评估维度对比</h4>
        <ComparisonChart
          data={assessments
            .filter((a) => a.dimension_scores)
            .slice(0, 5)
            .map((a, idx) => ({
              name: `评估${idx + 1} (${a.total_score}分)`,
              scores: JSON.parse(a.dimension_scores),
            }))}
          height={300}
        />
      </div>

      <div className="p-4 bg-gray-700 rounded-lg">
        <h4 className="text-sm font-semibold mb-4">总分对比</h4>
        <div className="space-y-2">
          {assessments
            .filter((a) => a.total_score !== null)
            .map((a, idx) => (
              <div key={a.id} className="flex items-center gap-4">
                <div className="w-24 text-sm text-gray-300">评估{idx + 1}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <div
                      className="h-6 bg-blue-500 rounded"
                      style={{
                        width: `${(a.total_score / 100) * 100}%`,
                      }}
                    />
                    <span className="text-sm font-semibold w-12 text-right">
                      {a.total_score}分
                    </span>
                  </div>
                </div>
                <div className="text-xs text-gray-400 w-32">
                  {a.evaluated_at
                    ? new Date(a.evaluated_at).toLocaleDateString()
                    : "未评估"}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}

function RisksTab({ risks }) {
  if (risks.length === 0) {
    return <div className="text-gray-400">无风险记录</div>;
  }

  return (
    <div className="space-y-3">
      {(risks || []).map((risk, idx) => (
        <div key={idx} className="p-4 bg-gray-700 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle
              className={`w-5 h-5 ${
                risk.level === "HIGH" ? "text-red-400" : "text-yellow-400"
              }`}
            />
            <Badge
              className={
                risk.level === "HIGH" ? "bg-red-500" : "bg-yellow-500"
              }
            >
              {risk.level}
            </Badge>
            <span className="text-sm text-gray-400">{risk.dimension}</span>
          </div>
          <div className="text-sm">{risk.description}</div>
        </div>
      ))}
    </div>
  );
}

function CasesTab({ similarCases }) {
  if (similarCases.length === 0) {
    return <div className="text-gray-400">无相似案例</div>;
  }

  return (
    <div className="space-y-3">
      {(similarCases || []).map((case_, idx) => (
        <div key={idx} className="p-4 bg-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold">{case_.project_name}</div>
            <Badge>
              相似度: {(case_.similarity_score * 100).toFixed(0)}%
            </Badge>
          </div>
          <div className="text-sm text-gray-300 mb-2">
            {case_.core_failure_reason}
          </div>
          <div className="text-sm text-gray-400">{case_.lesson_learned}</div>
        </div>
      ))}
    </div>
  );
}
