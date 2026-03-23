/**
 * 评估结果标签页 - 评分详情、趋势、对比、风险、案例、AI 分析
 * 仅在评估状态为 COMPLETED 时渲染
 */





import {
  dimensionLabels,
  formatDate,
  normalizeDimensionScores,
} from "../constants";

export function AssessmentResultTabs({
  selectedAssessment,
  dimensionScores,
  selectedDecision,
  conditions,
  trendSeries,
  assessments,
  comparisonSeries,
  legacyRisks,
  similarCases,
}) {
  return (
    <Card className="bg-gray-900 border-gray-800">
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
            {dimensionScores ? (
              <div className="space-y-6">
                <div className="flex justify-center">
                  <RadarChart data={dimensionScores} size={400} maxScore={20} />
                </div>

                <div className="space-y-3">
                  {Object.entries(dimensionLabels).map(([dimension, label]) => (
                    <div key={dimension} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-300">{label}</span>
                        <span className="font-semibold">{dimensionScores[dimension] ?? 0} / 20</span>
                      </div>
                      <Progress value={((dimensionScores[dimension] ?? 0) / 20) * 100} className="h-2" />
                    </div>
                  ))}
                </div>

                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <Target className="h-5 w-5 text-blue-400" />
                    <span className="font-semibold">决策建议</span>
                  </div>
                  <Badge className={selectedDecision.color}>{selectedDecision.label}</Badge>
                  {conditions.length > 0 && (
                    <div className="mt-4 space-y-2 text-sm text-gray-300">
                      {conditions.map((condition, index) => (
                        <div key={`${condition}-${index}`} className="rounded bg-gray-900 px-3 py-2">
                          {condition}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-gray-400">暂无评分详情</div>
            )}
          </TabsContent>

          <TabsContent value="trend" className="mt-4">
            {trendSeries.length > 1 ? (
              <div className="space-y-6">
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="mb-4 text-sm font-semibold">评估分数趋势</div>
                  <TrendChart data={trendSeries} height={250} />
                </div>

                {dimensionScores && (
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-4 text-sm font-semibold">维度分数趋势</div>
                    <div className="space-y-4">
                      {Object.entries(dimensionLabels).map(([dimension, label]) => {
                        const series = assessments
                          .filter((item) => item.dimension_scores)
                          .map((item, index) => {
                            const scores = normalizeDimensionScores(item.dimension_scores) || {};
                            return {
                              date: item.evaluated_at || item.created_at,
                              value: scores[dimension] || 0,
                              label: `评估${index + 1}`,
                            };
                          })
                          .sort((left, right) => new Date(left.date) - new Date(right.date));

                        if (series.length === 0) {
                          return null;
                        }

                        return (
                          <div key={dimension} className="space-y-2">
                            <div className="text-sm text-gray-300">{label}</div>
                            <TrendChart data={series} height={150} />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-8 text-center text-gray-400">需要至少 2 次评估才能显示趋势分析</div>
            )}
          </TabsContent>

          <TabsContent value="comparison" className="mt-4">
            {comparisonSeries.length > 1 ? (
              <div className="space-y-6">
                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="mb-4 text-sm font-semibold">评估维度对比</div>
                  <ComparisonChart data={comparisonSeries} height={300} />
                </div>

                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="mb-4 text-sm font-semibold">总分对比</div>
                  <div className="space-y-3">
                    {assessments
                      .filter((item) => item.total_score !== null && item.total_score !== undefined)
                      .map((item, index) => (
                        <div key={item.id} className="flex items-center gap-4">
                          <div className="w-20 text-sm text-gray-300">评估{index + 1}</div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <div
                                className="h-6 rounded bg-blue-500"
                                style={{ width: `${item.total_score}%` }}
                              />
                              <span className="w-12 text-right text-sm font-semibold">
                                {item.total_score}
                              </span>
                            </div>
                          </div>
                          <div className="w-28 text-right text-xs text-gray-500">
                            {formatDate(item.evaluated_at || item.created_at, false)}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-gray-400">需要至少 2 次评估才能显示对比分析</div>
            )}
          </TabsContent>

          <TabsContent value="risks" className="mt-4">
            {legacyRisks.length > 0 ? (
              <div className="space-y-3">
                {legacyRisks.map((risk, index) => (
                  <div key={`${risk.description || "risk"}-${index}`} className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-2 flex items-center gap-2">
                      <AlertTriangle
                        className={`h-5 w-5 ${
                          risk.level === "HIGH" ? "text-red-400" : "text-yellow-400"
                        }`}
                      />
                      <Badge className={risk.level === "HIGH" ? "bg-red-500" : "bg-yellow-500"}>
                        {risk.level || "未评级"}
                      </Badge>
                      <span className="text-sm text-gray-400">{risk.dimension || "未分类"}</span>
                    </div>
                    <div className="text-sm text-gray-200">{risk.description}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-gray-400">无风险记录</div>
            )}
          </TabsContent>

          <TabsContent value="cases" className="mt-4">
            {similarCases.length > 0 ? (
              <div className="space-y-3">
                {similarCases.map((caseItem, index) => (
                  <div key={`${caseItem.project_name || "case"}-${index}`} className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <div className="font-semibold">{caseItem.project_name || "未命名案例"}</div>
                      <Badge>
                        相似度: {((caseItem.similarity_score || 0) * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <div className="mb-2 text-sm text-gray-300">
                      {caseItem.core_failure_reason || "无失败原因说明"}
                    </div>
                    <div className="text-sm text-gray-400">
                      {caseItem.lesson_learned || "无经验教训"}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-gray-400">无相似案例</div>
            )}
          </TabsContent>

          <TabsContent value="ai" className="mt-4">
            {selectedAssessment.ai_analysis ? (
              <div className="whitespace-pre-wrap rounded-lg bg-gray-800 p-4 text-sm text-gray-200">
                {selectedAssessment.ai_analysis}
              </div>
            ) : (
              <div className="text-gray-400">未启用 AI 分析</div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
