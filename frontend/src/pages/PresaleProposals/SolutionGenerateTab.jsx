



import {
  TYPE_OPTIONS,
  INDUSTRY_OPTIONS,
  TEST_TYPE_OPTIONS,
  AI_TEMPLATE_SUGGESTIONS,
} from "./constants";

export default function SolutionGenerateTab({
  generatorForm,
  handleGenerateFieldChange,
  applyTemplateSuggestion,
  generationError,
  generating,
  handleGenerateProposal,
  setGeneratorForm,
  latestGenerated,
  navigate,
}) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2 border-white/10 bg-white/5 backdrop-blur">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-cyan-200">
              <Sparkles className="h-5 w-5" />
              AI 方案生成
            </CardTitle>
            <CardDescription>
              按业务需求快速产出技术方案，并自动生成可评审版本
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <p className="text-xs text-slate-400">方案名称</p>
                <Input
                  placeholder="例如：新能源PACK线FCT测试方案"
                  value={generatorForm.name}
                  onChange={(event) => handleGenerateFieldChange("name", event.target.value)}
                />
              </div>

              <div className="space-y-2">
                <p className="text-xs text-slate-400">方案类型</p>
                <Select
                  value={generatorForm.solutionType}
                  onValueChange={(value) => handleGenerateFieldChange("solutionType", value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TYPE_OPTIONS.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-slate-400">所属行业</p>
                <Select
                  value={generatorForm.industry}
                  onValueChange={(value) => handleGenerateFieldChange("industry", value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {INDUSTRY_OPTIONS.map((industry) => (
                      <SelectItem key={industry} value={industry}>
                        {industry}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <p className="text-xs text-slate-400">测试类型</p>
                <Select
                  value={generatorForm.testType}
                  onValueChange={(value) => handleGenerateFieldChange("testType", value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TEST_TYPE_OPTIONS.map((item) => (
                      <SelectItem key={item.value} value={item.value}>
                        {item.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-xs text-slate-400">需求摘要</p>
              <Textarea
                placeholder="填写产线痛点、交付目标、关键性能指标，AI会自动生成方案结构"
                rows={5}
                value={generatorForm.requirementSummary}
                onChange={(event) =>
                  handleGenerateFieldChange("requirementSummary", event.target.value)
                }
              />
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <p className="text-xs text-slate-400">预估成本 (元)</p>
                <Input
                  type="number"
                  placeholder="1200000"
                  value={generatorForm.estimatedCost}
                  onChange={(event) =>
                    handleGenerateFieldChange("estimatedCost", event.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <p className="text-xs text-slate-400">建议报价 (元)</p>
                <Input
                  type="number"
                  placeholder="1680000"
                  value={generatorForm.suggestedPrice}
                  onChange={(event) =>
                    handleGenerateFieldChange("suggestedPrice", event.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <p className="text-xs text-slate-400">预估工时</p>
                <Input
                  type="number"
                  placeholder="220"
                  value={generatorForm.estimatedHours}
                  onChange={(event) =>
                    handleGenerateFieldChange("estimatedHours", event.target.value)
                  }
                />
              </div>
              <div className="space-y-2">
                <p className="text-xs text-slate-400">预估周期 (天)</p>
                <Input
                  type="number"
                  placeholder="45"
                  value={generatorForm.estimatedDuration}
                  onChange={(event) =>
                    handleGenerateFieldChange("estimatedDuration", event.target.value)
                  }
                />
              </div>
            </div>

            {generationError && (
              <Alert className="border-red-500/30 bg-red-500/10 text-red-100">
                <AlertTitle>生成失败</AlertTitle>
                <AlertDescription>{generationError}</AlertDescription>
              </Alert>
            )}

            <div className="flex items-center gap-2">
              <Button onClick={handleGenerateProposal} disabled={generating}>
                <Sparkles className={`mr-2 h-4 w-4 ${generating ? "animate-pulse" : ""}`} />
                {generating ? "正在生成..." : "生成并保存方案"}
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setGeneratorForm((previous) => ({
                    ...previous,
                    name: "",
                    requirementSummary: "",
                  }));
                }}
              >
                清空输入
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/10 bg-slate-900/70">
          <CardHeader>
            <CardTitle className="text-base">推荐生成模板</CardTitle>
            <CardDescription>一键填入常用生成参数</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {AI_TEMPLATE_SUGGESTIONS.map((template) => (
              <button
                key={template.title}
                type="button"
                className="w-full rounded-lg border border-white/10 bg-white/5 p-3 text-left transition-colors hover:border-cyan-400/40 hover:bg-cyan-500/10"
                onClick={() => applyTemplateSuggestion(template)}
              >
                <p className="text-sm font-medium text-slate-100">{template.title}</p>
                <p className="mt-1 text-xs text-slate-400">{template.description}</p>
                <p className="mt-2 text-xs text-cyan-200">交付周期参考：{template.days}</p>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>

      {latestGenerated && (
        <Card className="border-cyan-400/30 bg-cyan-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-cyan-200">
              <CheckCircle2 className="h-5 w-5" />
              最近生成方案
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-xs text-slate-400">方案名称</p>
              <p className="mt-1 text-sm text-slate-100">{latestGenerated.name}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">方案编号</p>
              <p className="mt-1 text-sm text-slate-100">{latestGenerated.solutionNo}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">版本号</p>
              <p className="mt-1 text-sm text-slate-100">{latestGenerated.version}</p>
            </div>
            <div className="md:col-span-3">
              <Button
                variant="outline"
                onClick={() => navigate(`/solutions/${latestGenerated.id}`)}
              >
                打开方案详情
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
