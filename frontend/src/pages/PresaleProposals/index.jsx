/**
 * 售前方案管理页面
 * 方案列表、AI生成、方案评审与版本管理一体化协同
 */

import { useNavigate } from "react-router-dom";
import {
  Sparkles, FileText, ClipboardCheck, GitBranch,
  Search, RefreshCw, PlusCircle, CheckCircle2, XCircle,
  ArrowRight, CalendarClock, Coins, Layers, MessageSquareText,
} from "lucide-react";
import { motion } from "framer-motion";
import { PageHeader } from "../../components/layout";
import {
  Alert, AlertDescription, AlertTitle,
  Badge, Button, Card, CardContent, CardDescription, CardHeader, CardTitle,
  Input, Progress, Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  Tabs, TabsContent, TabsList, TabsTrigger, Textarea,
} from "../../components/ui";
import { usePresaleProposals } from './hooks/usePresaleProposals';
import {
  STATUS_CONFIG,
  TYPE_OPTIONS,
  INDUSTRY_OPTIONS,
  TEST_TYPE_OPTIONS,
  AI_TEMPLATE_SUGGESTIONS,
  getStatusConfig,
  formatDate,
  formatWan,
  calculateCompleteness,
} from './constants';

export default function PresaleProposals() {
  const navigate = useNavigate();
  const pp = usePresaleProposals();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="售前方案管理"
          description="方案列表、AI生成、方案评审与版本管理一体化协同"
          actions={
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={pp.loadSolutions} disabled={pp.loading}>
                <RefreshCw className={`mr-2 h-4 w-4 ${pp.loading ? "animate-spin" : ""}`} />
                刷新数据
              </Button>
              <Button onClick={() => pp.setActiveTab("generate")}>
                <PlusCircle className="mr-2 h-4 w-4" />
                新建方案
              </Button>
            </div>
          }
        />

        {pp.error && (
          <Alert className="mb-4 border-red-500/30 bg-red-500/10 text-red-100">
            <AlertTitle>操作提醒</AlertTitle>
            <AlertDescription>{pp.error}</AlertDescription>
          </Alert>
        )}

        <Tabs value={pp.activeTab} onValueChange={pp.setActiveTab} className="mt-6 space-y-6">
          <TabsList className="grid h-auto w-full grid-cols-2 gap-2 lg:w-[760px] lg:grid-cols-4">
            <TabsTrigger value="list" className="gap-2 py-2"><FileText className="h-4 w-4" />方案列表</TabsTrigger>
            <TabsTrigger value="generate" className="gap-2 py-2"><Sparkles className="h-4 w-4" />方案生成</TabsTrigger>
            <TabsTrigger value="review" className="gap-2 py-2"><ClipboardCheck className="h-4 w-4" />方案评审</TabsTrigger>
            <TabsTrigger value="versions" className="gap-2 py-2"><GitBranch className="h-4 w-4" />版本管理</TabsTrigger>
          </TabsList>

          {/* 方案列表 Tab */}
          <TabsContent value="list" className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: "总方案数", value: pp.stats.total, icon: Layers, color: "text-slate-100" },
                { label: "草稿", value: pp.stats.draft, icon: FileText, color: "text-slate-300" },
                { label: "评审中", value: pp.stats.reviewing, icon: ClipboardCheck, color: "text-amber-300" },
                { label: "已通过", value: pp.stats.approved, icon: CheckCircle2, color: "text-emerald-300" },
              ].map((item) => (
                <Card key={item.label} className="border-white/10 bg-white/5 backdrop-blur">
                  <CardContent className="pt-5">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-xs text-slate-400">{item.label}</p>
                      <item.icon className={`h-4 w-4 ${item.color}`} />
                    </div>
                    <p className={`text-3xl font-semibold ${item.color}`}>{item.value}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card className="border-white/10 bg-white/5 backdrop-blur">
              <CardContent className="pt-6">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div className="relative w-full md:max-w-md">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                    <Input className="pl-9" placeholder="搜索方案名称 / 编号" value={pp.searchKeyword} onChange={(e) => pp.setSearchKeyword(e.target.value)} />
                  </div>
                  <Select value={pp.statusFilter} onValueChange={pp.setStatusFilter}>
                    <SelectTrigger className="w-full md:w-[200px]"><SelectValue placeholder="筛选状态" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      {Object.entries(STATUS_CONFIG).map(([key, config]) => (<SelectItem key={key} value={key}>{config.label}</SelectItem>))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {pp.loading ? (
              <div className="rounded-xl border border-white/10 bg-white/5 py-14 text-center text-slate-300"><RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin" />正在加载方案列表...</div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {pp.solutions.length > 0 ? pp.solutions.map((solution) => {
                  const statusConfig = getStatusConfig(solution.status);
                  return (
                    <motion.div key={solution.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
                      <Card className="h-full border-white/10 bg-slate-900/70 transition-colors hover:border-cyan-400/50 hover:bg-slate-900">
                        <CardHeader>
                          <div className="mb-2 flex items-center justify-between gap-3">
                            <Badge className={statusConfig.className}>{statusConfig.label}</Badge>
                            <Badge variant="outline" className="border-white/20 text-slate-200">{solution.version}</Badge>
                          </div>
                          <CardTitle className="line-clamp-2 text-base">{solution.name}</CardTitle>
                          <CardDescription className="text-xs text-slate-400">{solution.solutionNo} · {solution.industry}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <p className="line-clamp-3 text-sm text-slate-300">{solution.requirementSummary}</p>
                          <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                            <div className="rounded-lg border border-white/10 bg-white/5 p-2">
                              <div className="mb-1 flex items-center gap-1"><Coins className="h-3.5 w-3.5" />预估成本</div>
                              <div className="text-sm font-medium text-slate-100">{formatWan(solution.estimatedCost)} 万</div>
                            </div>
                            <div className="rounded-lg border border-white/10 bg-white/5 p-2">
                              <div className="mb-1 flex items-center gap-1"><MessageSquareText className="h-3.5 w-3.5" />建议报价</div>
                              <div className="text-sm font-medium text-cyan-200">{formatWan(solution.suggestedPrice)} 万</div>
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs text-slate-400">
                            <span className="inline-flex items-center gap-1"><CalendarClock className="h-3.5 w-3.5" />{formatDate(solution.updatedAt || solution.createdAt)}</span>
                            <span>{solution.testType}</span>
                          </div>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" className="flex-1" onClick={() => navigate(`/solutions/${solution.id}`)}>查看详情</Button>
                            <Button size="sm" className="flex-1" onClick={() => { pp.setSelectedSolutionId(String(solution.id)); pp.setActiveTab("versions"); }}>版本管理</Button>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                }) : (
                  <div className="col-span-full rounded-xl border border-dashed border-white/20 py-16 text-center text-slate-400">暂无符合条件的方案，尝试调整筛选条件</div>
                )}
              </div>
            )}
          </TabsContent>

          {/* 方案生成 Tab */}
          <TabsContent value="generate" className="space-y-6">
            <div className="grid gap-4 xl:grid-cols-3">
              <Card className="xl:col-span-2 border-white/10 bg-white/5 backdrop-blur">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-cyan-200"><Sparkles className="h-5 w-5" />AI 方案生成</CardTitle>
                  <CardDescription>按业务需求快速产出技术方案，并自动生成可评审版本</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2"><p className="text-xs text-slate-400">方案名称</p><Input placeholder="例如：新能源PACK线FCT测试方案" value={pp.generatorForm.name} onChange={(e) => pp.handleGenerateFieldChange("name", e.target.value)} /></div>
                    <div className="space-y-2"><p className="text-xs text-slate-400">方案类型</p><Select value={pp.generatorForm.solutionType} onValueChange={(v) => pp.handleGenerateFieldChange("solutionType", v)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{TYPE_OPTIONS.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent></Select></div>
                    <div className="space-y-2"><p className="text-xs text-slate-400">所属行业</p><Select value={pp.generatorForm.industry} onValueChange={(v) => pp.handleGenerateFieldChange("industry", v)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{INDUSTRY_OPTIONS.map((i) => <SelectItem key={i} value={i}>{i}</SelectItem>)}</SelectContent></Select></div>
                    <div className="space-y-2"><p className="text-xs text-slate-400">测试类型</p><Select value={pp.generatorForm.testType} onValueChange={(v) => pp.handleGenerateFieldChange("testType", v)}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{TEST_TYPE_OPTIONS.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent></Select></div>
                  </div>
                  <div className="space-y-2"><p className="text-xs text-slate-400">需求摘要</p><Textarea placeholder="填写产线痛点、交付目标、关键性能指标，AI会自动生成方案结构" rows={5} value={pp.generatorForm.requirementSummary} onChange={(e) => pp.handleGenerateFieldChange("requirementSummary", e.target.value)} /></div>
                  <div className="grid gap-4 md:grid-cols-4">
                    {[["预估成本 (元)", "estimatedCost", "1200000"], ["建议报价 (元)", "suggestedPrice", "1680000"], ["预估工时", "estimatedHours", "220"], ["预估周期 (天)", "estimatedDuration", "45"]].map(([label, field, ph]) => (
                      <div key={field} className="space-y-2"><p className="text-xs text-slate-400">{label}</p><Input type="number" placeholder={ph} value={pp.generatorForm[field]} onChange={(e) => pp.handleGenerateFieldChange(field, e.target.value)} /></div>
                    ))}
                  </div>
                  {pp.generationError && <Alert className="border-red-500/30 bg-red-500/10 text-red-100"><AlertTitle>生成失败</AlertTitle><AlertDescription>{pp.generationError}</AlertDescription></Alert>}
                  <div className="flex items-center gap-2">
                    <Button onClick={pp.handleGenerateProposal} disabled={pp.generating}><Sparkles className={`mr-2 h-4 w-4 ${pp.generating ? "animate-pulse" : ""}`} />{pp.generating ? "正在生成..." : "生成并保存方案"}</Button>
                    <Button variant="outline" onClick={() => pp.handleGenerateFieldChange("name", "") || pp.handleGenerateFieldChange("requirementSummary", "")}>清空输入</Button>
                  </div>
                </CardContent>
              </Card>
              <Card className="border-white/10 bg-slate-900/70">
                <CardHeader><CardTitle className="text-base">推荐生成模板</CardTitle><CardDescription>一键填入常用生成参数</CardDescription></CardHeader>
                <CardContent className="space-y-3">
                  {AI_TEMPLATE_SUGGESTIONS.map((t) => (
                    <button key={t.title} type="button" className="w-full rounded-lg border border-white/10 bg-white/5 p-3 text-left transition-colors hover:border-cyan-400/40 hover:bg-cyan-500/10" onClick={() => pp.applyTemplateSuggestion(t)}>
                      <p className="text-sm font-medium text-slate-100">{t.title}</p>
                      <p className="mt-1 text-xs text-slate-400">{t.description}</p>
                      <p className="mt-2 text-xs text-cyan-200">交付周期参考：{t.days}</p>
                    </button>
                  ))}
                </CardContent>
              </Card>
            </div>
            {pp.latestGenerated && (
              <Card className="border-cyan-400/30 bg-cyan-500/5">
                <CardHeader><CardTitle className="flex items-center gap-2 text-cyan-200"><CheckCircle2 className="h-5 w-5" />最近生成方案</CardTitle></CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-3">
                  <div><p className="text-xs text-slate-400">方案名称</p><p className="mt-1 text-sm text-slate-100">{pp.latestGenerated.name}</p></div>
                  <div><p className="text-xs text-slate-400">方案编号</p><p className="mt-1 text-sm text-slate-100">{pp.latestGenerated.solutionNo}</p></div>
                  <div><p className="text-xs text-slate-400">版本号</p><p className="mt-1 text-sm text-slate-100">{pp.latestGenerated.version}</p></div>
                  <div className="md:col-span-3"><Button variant="outline" onClick={() => navigate(`/solutions/${pp.latestGenerated.id}`)}>打开方案详情<ArrowRight className="ml-2 h-4 w-4" /></Button></div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* 方案评审 Tab */}
          <TabsContent value="review" className="space-y-4">
            {pp.reviewQueue.length === 0 ? (
              <div className="rounded-xl border border-dashed border-white/20 py-16 text-center text-slate-400">当前没有待评审方案</div>
            ) : pp.reviewQueue.map((solution) => {
              const completeness = calculateCompleteness(solution);
              const statusConfig = getStatusConfig(solution.status);
              return (
                <Card key={solution.id} className="border-white/10 bg-white/5 backdrop-blur">
                  <CardHeader>
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div><CardTitle className="text-base">{solution.name}</CardTitle><CardDescription className="mt-1 text-xs">{solution.solutionNo} · 版本 {solution.version}</CardDescription></div>
                      <Badge className={statusConfig.className}>{statusConfig.label}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-slate-300">{solution.requirementSummary}</p>
                    <div><div className="mb-1 flex items-center justify-between text-xs text-slate-400"><span>材料完整度</span><span>{completeness}%</span></div><Progress value={completeness} className="h-2" /></div>
                    <Textarea rows={3} placeholder="填写评审意见（可选）" value={pp.reviewComments[solution.id] || ""} onChange={(e) => pp.setReviewComments((prev) => ({ ...prev, [solution.id]: e.target.value }))} />
                    <div className="flex flex-wrap items-center gap-2">
                      <Button onClick={() => pp.handleReviewAction(solution.id, "APPROVED")} disabled={pp.reviewActionLoadingId === solution.id}><CheckCircle2 className="mr-2 h-4 w-4" />通过评审</Button>
                      <Button variant="outline" className="border-red-400/40 text-red-100 hover:bg-red-500/10" onClick={() => pp.handleReviewAction(solution.id, "REJECTED")} disabled={pp.reviewActionLoadingId === solution.id}><XCircle className="mr-2 h-4 w-4" />驳回修改</Button>
                      <Button variant="ghost" onClick={() => { pp.setSelectedSolutionId(String(solution.id)); pp.setActiveTab("versions"); }}><GitBranch className="mr-2 h-4 w-4" />查看版本轨迹</Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </TabsContent>

          {/* 版本管理 Tab */}
          <TabsContent value="versions" className="space-y-4">
            <Card className="border-white/10 bg-white/5 backdrop-blur">
              <CardContent className="pt-6">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div><p className="text-sm font-medium text-slate-100">选择方案查看版本链</p><p className="text-xs text-slate-400">支持查看历史版本和评审记录</p></div>
                  <Select value={pp.selectedSolutionId || ""} onValueChange={pp.setSelectedSolutionId}>
                    <SelectTrigger className="w-full md:w-[320px]"><SelectValue placeholder="请选择方案" /></SelectTrigger>
                    <SelectContent>{pp.solutions.map((s) => <SelectItem key={s.id} value={String(s.id)}>{s.name} ({s.version})</SelectItem>)}</SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {pp.versionsError && <Alert className="border-red-500/30 bg-red-500/10 text-red-100"><AlertTitle>版本加载失败</AlertTitle><AlertDescription>{pp.versionsError}</AlertDescription></Alert>}

            {pp.versionsLoading ? (
              <div className="rounded-xl border border-white/10 bg-white/5 py-12 text-center text-slate-300"><RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin" />正在加载版本记录...</div>
            ) : (
              <div className="grid gap-4 lg:grid-cols-3">
                <Card className="lg:col-span-1 border-white/10 bg-white/5">
                  <CardHeader><CardTitle className="text-base">版本时间线</CardTitle><CardDescription>共 {pp.versions.length} 个版本</CardDescription></CardHeader>
                  <CardContent className="space-y-2">
                    {pp.versions.length > 0 ? pp.versions.map((version) => {
                      const isActive = String(version.id) === String(pp.selectedVersionId);
                      const statusConfig = getStatusConfig(version.status);
                      return (
                        <button key={version.id} type="button" onClick={() => pp.setSelectedVersionId(String(version.id))} className={`w-full rounded-lg border p-3 text-left transition-colors ${isActive ? "border-cyan-400/60 bg-cyan-500/10" : "border-white/10 bg-white/5 hover:border-white/20"}`}>
                          <div className="mb-2 flex items-center justify-between gap-2"><p className="text-sm font-medium text-slate-100">{version.version}</p><Badge className={statusConfig.className}>{statusConfig.label}</Badge></div>
                          <p className="text-xs text-slate-400">{formatDate(version.updatedAt || version.createdAt)}</p>
                        </button>
                      );
                    }) : <p className="py-8 text-center text-sm text-slate-400">当前方案暂无版本记录</p>}
                  </CardContent>
                </Card>
                <Card className="lg:col-span-2 border-white/10 bg-white/5">
                  <CardHeader><CardTitle className="text-base">版本详情</CardTitle><CardDescription>查看方案内容、评审意见与估算信息</CardDescription></CardHeader>
                  <CardContent>
                    {pp.selectedVersion ? (
                      <div className="space-y-5">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div><p className="text-lg font-medium text-slate-100">{pp.selectedVersion.name}</p><p className="text-xs text-slate-400">{pp.selectedVersion.solutionNo} · {pp.selectedVersion.industry}</p></div>
                          <Badge className={getStatusConfig(pp.selectedVersion.status).className}>{getStatusConfig(pp.selectedVersion.status).label}</Badge>
                        </div>
                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3"><p className="text-xs text-slate-400">需求摘要</p><p className="mt-1 text-sm text-slate-200">{pp.selectedVersion.requirementSummary}</p></div>
                          <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3"><p className="text-xs text-slate-400">方案概述</p><p className="mt-1 text-sm text-slate-200">{pp.selectedVersion.solutionOverview}</p></div>
                          <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3 md:col-span-2"><p className="text-xs text-slate-400">技术规格</p><pre className="mt-1 whitespace-pre-wrap text-sm text-slate-200">{pp.selectedVersion.technicalSpec}</pre></div>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-3">
                          <div className="rounded-lg border border-white/10 bg-white/5 p-3"><p className="text-xs text-slate-400">预估成本</p><p className="mt-1 text-sm text-slate-100">{formatWan(pp.selectedVersion.estimatedCost)} 万</p></div>
                          <div className="rounded-lg border border-white/10 bg-white/5 p-3"><p className="text-xs text-slate-400">建议报价</p><p className="mt-1 text-sm text-cyan-200">{formatWan(pp.selectedVersion.suggestedPrice)} 万</p></div>
                          <div className="rounded-lg border border-white/10 bg-white/5 p-3"><p className="text-xs text-slate-400">更新时间</p><p className="mt-1 text-sm text-slate-100">{formatDate(pp.selectedVersion.updatedAt || pp.selectedVersion.createdAt)}</p></div>
                        </div>
                        {pp.selectedVersion.reviewComment && <Alert className="border-amber-400/30 bg-amber-500/10"><AlertTitle className="text-amber-100">评审意见</AlertTitle><AlertDescription className="text-amber-100/90">{pp.selectedVersion.reviewComment}</AlertDescription></Alert>}
                      </div>
                    ) : (
                      <div className="py-14 text-center text-slate-400">请选择左侧版本查看详情</div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
