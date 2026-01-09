/**
 * ECNKnowledgeTab Component
 * ECN 知识库 Tab 组件
 */
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { FileText, Search, Lightbulb, Plus } from 'lucide-react'
import { useECNKnowledge } from './hooks/useECNKnowledge'
import SolutionTemplateDialog from './dialogs/SolutionTemplateDialog'

export default function ECNKnowledgeTab({ ecnId, ecn, refetch }) {
  const {
    similarEcns,
    solutionRecommendations,
    extractedSolution,
    loadingKnowledge,
    showSolutionTemplateDialog,
    setShowSolutionTemplateDialog,
    solutionTemplateForm,
    setSolutionTemplateForm,
    handleExtractSolution,
    handleFindSimilarEcns,
    handleRecommendSolutions,
    handleApplySolutionTemplate,
    handleCreateSolutionTemplate,
  } = useECNKnowledge(ecnId, ecn, refetch)

  // 处理提取解决方案
  const handleExtractClick = async () => {
    const result = await handleExtractSolution()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 处理查找相似ECN
  const handleFindSimilarClick = async () => {
    const result = await handleFindSimilarEcns()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 处理推荐解决方案
  const handleRecommendClick = async () => {
    const result = await handleRecommendSolutions()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 处理应用解决方案
  const handleApplyClick = async (templateId) => {
    const result = await handleApplySolutionTemplate(templateId)
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 处理创建模板
  const handleCreateTemplateClick = async () => {
    const result = await handleCreateSolutionTemplate()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 判断是否可以创建模板
  const canCreateTemplate =
    (ecn?.status === 'COMPLETED' || ecn?.status === 'CLOSED') && ecn?.solution

  return (
    <div className="space-y-4">
      {/* 操作工具栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleExtractClick}
              disabled={loadingKnowledge}
            >
              <FileText className="w-4 h-4 mr-2" />
              {loadingKnowledge ? '提取中...' : '提取解决方案'}
            </Button>
            <Button
              variant="outline"
              onClick={handleFindSimilarClick}
              disabled={loadingKnowledge}
            >
              <Search className="w-4 h-4 mr-2" />
              {loadingKnowledge ? '查找中...' : '查找相似ECN'}
            </Button>
            <Button
              variant="outline"
              onClick={handleRecommendClick}
              disabled={loadingKnowledge}
            >
              <Lightbulb className="w-4 h-4 mr-2" />
              {loadingKnowledge ? '推荐中...' : '推荐解决方案'}
            </Button>
            {canCreateTemplate && (
              <Button
                variant="outline"
                onClick={() => {
                  setSolutionTemplateForm({
                    template_name: `${ecn.ecn_title} - 解决方案模板`,
                    template_category: ecn.ecn_type || '',
                    keywords: [],
                  })
                  setShowSolutionTemplateDialog(true)
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                创建解决方案模板
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 提取的解决方案 */}
      {extractedSolution && (
        <Card className="border-blue-200 bg-blue-50/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-600" />
              提取的解决方案
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-slate-500 mb-1">解决方案描述</div>
                <div className="p-3 bg-white rounded whitespace-pre-wrap">
                  {extractedSolution.solution}
                </div>
              </div>
              {extractedSolution.solution_steps &&
                extractedSolution.solution_steps.length > 0 && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">解决步骤</div>
                    <ol className="list-decimal list-inside space-y-1 p-3 bg-white rounded">
                      {extractedSolution.solution_steps.map((step, idx) => (
                        <li key={idx} className="text-sm">
                          {step}
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              {extractedSolution.keywords &&
                extractedSolution.keywords.length > 0 && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">关键词</div>
                    <div className="flex flex-wrap gap-2">
                      {extractedSolution.keywords.map((kw, idx) => (
                        <Badge key={idx} variant="outline">
                          {kw}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 相似ECN */}
      {similarEcns.length > 0 && (
        <Card className="border-green-200 bg-green-50/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Search className="w-5 h-5 text-green-600" />
              相似ECN
              <Badge className="bg-green-500">{similarEcns.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {similarEcns.map((similar, idx) => (
                <Card key={idx} className="p-3">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="font-semibold">{similar.ecn_title}</div>
                      <div className="text-sm text-slate-500 font-mono">
                        {similar.ecn_no}
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className="bg-green-500">
                        相似度:{' '}
                        {(similar.similarity_score * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </div>
                  <div className="text-sm text-slate-500 mb-2">
                    {similar.match_reasons?.join('、')}
                  </div>
                  {similar.solution && (
                    <div className="p-2 bg-slate-50 rounded text-sm line-clamp-2">
                      {similar.solution}
                    </div>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                    <span>类型: {similar.ecn_type}</span>
                    <span>
                      成本影响: ¥{similar.cost_impact?.toLocaleString()}
                    </span>
                    <span>交期影响: {similar.schedule_impact_days}天</span>
                  </div>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 推荐解决方案 */}
      {solutionRecommendations.length > 0 && (
        <Card className="border-purple-200 bg-purple-50/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-purple-600" />
              推荐解决方案
              <Badge className="bg-purple-500">
                {solutionRecommendations.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {solutionRecommendations.map((rec, idx) => (
                <Card key={idx} className="p-3">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="font-semibold">{rec.template_name}</div>
                      <div className="text-sm text-slate-500">
                        {rec.template_category}
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className="bg-purple-500">评分: {rec.score}</Badge>
                    </div>
                  </div>
                  <div className="text-sm text-slate-500 mb-2">
                    {rec.match_reasons?.join('、')}
                  </div>
                  <div className="p-2 bg-slate-50 rounded text-sm line-clamp-2 mb-2">
                    {rec.solution_description}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-500 mb-2">
                    <span>成功率: {rec.success_rate}%</span>
                    <span>使用次数: {rec.usage_count}</span>
                    <span>
                      预估成本: ¥{rec.estimated_cost?.toLocaleString()}
                    </span>
                    <span>预估天数: {rec.estimated_days}天</span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleApplyClick(rec.template_id)}
                    className="w-full"
                  >
                    应用此方案
                  </Button>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 当前ECN的解决方案 */}
      {ecn?.solution && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">当前解决方案</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="p-3 bg-slate-50 rounded whitespace-pre-wrap">
              {ecn.solution}
            </div>
            {ecn.solution_source && (
              <div className="mt-2 text-sm text-slate-500">
                来源:{' '}
                {ecn.solution_source === 'MANUAL'
                  ? '手动填写'
                  : ecn.solution_source === 'AUTO_EXTRACT'
                  ? '自动提取'
                  : ecn.solution_source === 'KNOWLEDGE_BASE'
                  ? '知识库'
                  : ecn.solution_source}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 创建解决方案模板对话框 */}
      <SolutionTemplateDialog
        open={showSolutionTemplateDialog}
        onOpenChange={setShowSolutionTemplateDialog}
        form={solutionTemplateForm}
        setForm={setSolutionTemplateForm}
        onSubmit={handleCreateTemplateClick}
        ecn={ecn}
      />
    </div>
  )
}
