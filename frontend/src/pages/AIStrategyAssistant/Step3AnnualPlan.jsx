



import { staggerContainer } from "@/lib/animations";
import { getPriorityLabel, getPriorityColor } from "@/services/api/aiStrategy";

export default function Step3AnnualPlan({
  annualPlanInput,
  setAnnualPlanInput,
  annualPlanResult,
  loading,
  onGenerate,
  onApply,
  onPrev,
  onNext,
}) {
  return (
    <motion.div {...staggerContainer} className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-400" />
            年度经营计划输入
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-300">年度</Label>
            <Input
              type="number"
              value={annualPlanInput.year}
              onChange={(e) => setAnnualPlanInput({ ...annualPlanInput, year: parseInt(e.target.value) })}
              className="bg-gray-900 border-gray-700 text-white"
            />
          </div>
          <div>
            <Label className="text-gray-300">年度营收目标（万元）</Label>
            <Input
              type="number"
              value={annualPlanInput.revenueTarget}
              onChange={(e) => setAnnualPlanInput({ ...annualPlanInput, revenueTarget: parseFloat(e.target.value) })}
              className="bg-gray-900 border-gray-700 text-white"
              placeholder="如：50000"
            />
          </div>
          <div>
            <Label className="text-gray-300">补充信息</Label>
            <Textarea
              value={annualPlanInput.additionalInfo}
              onChange={(e) => setAnnualPlanInput({ ...annualPlanInput, additionalInfo: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
              placeholder="其他需要说明的信息"
            />
          </div>
          <Button
            onClick={onGenerate}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI 生成中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI 生成年度计划
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {annualPlanResult && (
        <motion.div {...staggerContainer} className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">重点工作（{annualPlanResult.annual_works?.length || 0}项）</h3>
            <Button onClick={onApply} size="sm" variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              导入系统
            </Button>
          </div>

          <div className="grid gap-4">
            {annualPlanResult.annual_works?.map((work, i) => (
              <Card key={i} className="bg-gray-800/50 border-gray-700">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="font-semibold text-white text-lg">{work.name}</div>
                      <div className="text-sm text-gray-400 mt-1">{work.description}</div>
                    </div>
                    <Badge className={getPriorityColor(work.priority)}>
                      {getPriorityLabel(work.priority)}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="text-gray-400">
                      <span className="text-gray-500">目标：</span>
                      {work.target}
                    </div>
                    <div className="text-gray-400">
                      <span className="text-gray-500">时间：</span>
                      {work.start_date} ~ {work.end_date}
                    </div>
                    <div className="text-gray-400">
                      <span className="text-gray-500">预算：</span>
                      {work.budget ? `${work.budget.toLocaleString()}元` : "待定"}
                    </div>
                    <div className="text-gray-400">
                      <span className="text-gray-500">关联 CSF：</span>
                      {work.csf_code}
                    </div>
                  </div>
                  {work.pain_point && (
                    <div className="mt-3 p-2 bg-red-900/20 rounded border border-red-700/30">
                      <div className="text-xs text-red-400 font-medium mb-1">痛点：</div>
                      <div className="text-sm text-gray-300">{work.pain_point}</div>
                    </div>
                  )}
                  {work.solution && (
                    <div className="mt-2 p-2 bg-green-900/20 rounded border border-green-700/30">
                      <div className="text-xs text-green-400 font-medium mb-1">解决方案：</div>
                      <div className="text-sm text-gray-300">{work.solution}</div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex gap-4">
            <Button onClick={onPrev} variant="outline" className="flex-1">
              <ArrowLeft className="w-4 h-4 mr-2" />
              上一步
            </Button>
            <Button onClick={onNext} className="flex-1">
              下一步
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
