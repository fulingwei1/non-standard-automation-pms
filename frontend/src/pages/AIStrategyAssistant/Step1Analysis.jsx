



import { staggerContainer } from "@/lib/animations";

export default function Step1Analysis({
  analysisInput,
  setAnalysisInput,
  analysisResult,
  loading,
  onAnalyze,
  onAdoptAndContinue,
}) {
  return (
    <motion.div {...staggerContainer} className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-400" />
            公司信息输入
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-300">公司简介</Label>
            <Textarea
              value={analysisInput.companyInfo}
              onChange={(e) => setAnalysisInput({ ...analysisInput, companyInfo: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[100px]"
              placeholder="请输入公司简介，包括主营业务、核心产品、市场定位等"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-gray-300 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-green-400" />
                财务数据
              </Label>
              <Textarea
                value={analysisInput.financialData}
                onChange={(e) => setAnalysisInput({ ...analysisInput, financialData: e.target.value })}
                className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
                placeholder="营收、利润、增长率等"
              />
            </div>
            <div>
              <Label className="text-gray-300 flex items-center gap-2">
                <Globe className="w-4 h-4 text-blue-400" />
                市场信息
              </Label>
              <Textarea
                value={analysisInput.marketInfo}
                onChange={(e) => setAnalysisInput({ ...analysisInput, marketInfo: e.target.value })}
                className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
                placeholder="市场规模、竞争格局、趋势等"
              />
            </div>
          </div>
          <div>
            <Label className="text-gray-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400" />
              当前挑战
            </Label>
            <Textarea
              value={analysisInput.challenges}
              onChange={(e) => setAnalysisInput({ ...analysisInput, challenges: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
              placeholder="面临的主要挑战和痛点"
            />
          </div>
          <Button
            onClick={onAnalyze}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI 分析中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI 战略分析
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {analysisResult && (
        <motion.div {...staggerContainer} className="space-y-6">
          {/* SWOT 四象限 */}
          <div className="grid grid-cols-2 gap-4">
            <Card className="bg-green-900/20 border-green-700/50">
              <CardHeader>
                <CardTitle className="text-green-400 text-lg">优势 (Strengths)</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analysisResult.swot?.strengths?.map((item, i) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <Check className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-red-900/20 border-red-700/50">
              <CardHeader>
                <CardTitle className="text-red-400 text-lg">劣势 (Weaknesses)</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analysisResult.swot?.weaknesses?.map((item, i) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-blue-900/20 border-blue-700/50">
              <CardHeader>
                <CardTitle className="text-blue-400 text-lg">机会 (Opportunities)</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analysisResult.swot?.opportunities?.map((item, i) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <TrendingUp className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-yellow-900/20 border-yellow-700/50">
              <CardHeader>
                <CardTitle className="text-yellow-400 text-lg">威胁 (Threats)</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {analysisResult.swot?.threats?.map((item, i) => (
                    <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                      <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* 战略定位 */}
          <Card className="bg-purple-900/20 border-purple-700/50">
            <CardHeader>
              <CardTitle className="text-purple-400 text-lg">战略定位建议</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-300">{analysisResult.strategic_positioning}</p>
            </CardContent>
          </Card>

          {/* 核心竞争力 */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                核心竞争力分析
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {analysisResult.core_competencies?.map((item, i) => (
                  <Badge key={i} variant="secondary" className="bg-blue-500/20 text-blue-300 border-blue-500/30">
                    {item}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 战略方向建议 */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">战略方向建议</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {analysisResult.strategic_directions?.map((item, i) => (
                <div key={i} className="p-3 bg-gray-900/50 rounded-lg border border-gray-700">
                  <div className="font-medium text-white mb-1">{item.direction}</div>
                  <div className="text-sm text-gray-400">{item.description}</div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Button
            onClick={onAdoptAndContinue}
            className="w-full"
          >
            采纳建议并继续
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </motion.div>
      )}
    </motion.div>
  );
}
