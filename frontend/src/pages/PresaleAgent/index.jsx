// 售前智能体工作台（v2）
// 改进：①输入引导 ②结论摘要 ③进度感知 ④结果导出
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Sparkles, Loader2, Send, RotateCcw, AlertCircle, Download, FileText,
  Lightbulb, Boxes, DollarSign, ShieldAlert, FileSearch,
  CheckCircle2, Clock, Flag, Wrench, TrendingUp, Pencil, History, X, Save, CheckCheck,
  MessageSquare, Bot, User, Map, ExternalLink, GitBranch,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Alert, AlertDescription, AlertTitle, Badge, Button, Card,
  CardContent, CardHeader, CardTitle, Progress, Textarea,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import {
  submitPresaleAgent, pollPresaleAgentJob,
  submitRevision, listRevisions, revisionStats, clarifyRequirement,
} from "../../services/api/presaleAgent";
import {
  createProposal, reviseProposal, submitProposal, listProposals,
} from "../../services/api/presaleProposals";

// 步骤定义（含中文说明 + 预计耗时秒）
const STEPS = [
  { key: "understand_requirement", label: "需求理解", icon: FileSearch, eta: 3 },
  { key: "retrieve_ammo", label: "弹药检索", icon: Boxes, eta: 1 },
  { key: "generate_solution", label: "方案生成", icon: Lightbulb, eta: 8 },
  { key: "recommend_bom", label: "BOM模板", icon: Wrench, eta: 1 },
  { key: "quote_range", label: "报价区间", icon: DollarSign, eta: 1 },
  { key: "risk_warnings", label: "风险提示", icon: ShieldAlert, eta: 8 },
];

// 快速需求模板（销售点一下就填好，不用自己想怎么描述）
const TEMPLATES = [
  {
    label: "BMS测试",
    industry: "新能源汽车",
    text: "BMS电池管理系统测试设备，支持多串电芯模拟（48-96串），绝缘检测，CAN/CANFD通讯，节拍60秒",
  },
  {
    label: "800V电驱",
    industry: "新能源汽车",
    text: "800V高压电驱总成下线测试系统，测电机控制器+减速器，1000A大电流电子负载，支持高压绝缘监测",
  },
  {
    label: "ICT测试",
    industry: "电子制造",
    text: "ICT在线测试设备，PCBA电路板测试，支持多板兼容，节拍15秒，含针床和测试软件",
  },
  {
    label: "老化测试",
    industry: "消费电子",
    text: "整机老化测试设备，多工位并行老化，温控精度±2℃，支持数据追溯和SPC分析",
  },
  {
    label: "视觉检测",
    industry: "电子制造",
    text: "SMT视觉检测设备（AOI），高精度外观检测，0.01mm精度，支持多板兼容和自动判别",
  },
  {
    label: "SiC功率器件",
    industry: "新能源汽车",
    text: "SiC碳化硅功率器件动态测试系统，双脉冲测试，1200V，高频开关特性测试",
  },
];

export default function PresaleAgent() {
  const [requirementText, setRequirementText] = useState("");
  const [industryHint, setIndustryHint] = useState("");
  const [equipmentHint, setEquipmentHint] = useState("");
  const [deepRisk, setDeepRisk] = useState(false);
  // 澄清对话状态
  const [clarifyMode, setClarifyMode] = useState(false); // 是否开启澄清模式
  const [chatMessages, setChatMessages] = useState([]); // [{role, content}]
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [clarifyDone, setClarifyDone] = useState(false); // 澄清完成（需求够完整）
  const chatEndRef = useRef(null);
  const [deepSolution, setDeepSolution] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [jobId, setJobId] = useState(null);
  const abortRef = useRef(null);

  // 澄清对话：发送一条消息
  const handleClarifySend = useCallback(async () => {
    const text = chatInput.trim();
    if (!text || chatLoading) return;

    // 用户消息入列
    const userMsg = { role: "user", content: text };
    const newMessages = [...chatMessages, userMsg];
    setChatMessages(newMessages);
    setChatInput("");
    setChatLoading(true);

    try {
      // 调澄清引擎（history 传除本轮外的历史）
      const historyForApi = chatMessages.map((m) => ({ role: m.role, content: m.content }));
      const res = await clarifyRequirement(text, historyForApi);

      const botMsg = { role: "assistant", content: res.reply_to_user || "（无回复）" };
      setChatMessages((prev) => [...prev, botMsg]);

      if (res.is_complete) {
        setClarifyDone(true);
        // 把整合后的需求填回输入框
        const understood = res.understood || {};
        const parts = [];
        if (understood.test_object) parts.push(understood.test_object);
        if (understood.industry) parts.push(understood.industry);
        if (understood.key_specs?.length) parts.push(understood.key_specs.join("、"));
        if (understood.scale) parts.push(understood.scale);
        if (understood.special_reqs?.length) parts.push(understood.special_reqs.join("、"));
        if (parts.length) setRequirementText(parts.join("，"));
      }
    } catch (e) {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ 澄清服务暂时不可用：" + (e.message || "未知错误") },
      ]);
    } finally {
      setChatLoading(false);
      // 滚动到底部
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  }, [chatInput, chatMessages, chatLoading]);

  // 开始澄清（用输入框里的初始需求）
  const startClarify = useCallback(() => {
    if (!requirementText.trim()) {
      setError("请先输入客户需求，再开始澄清");
      return;
    }
    setClarifyMode(true);
    setChatMessages([
      { role: "user", content: requirementText.trim() },
    ]);
    setChatInput("");
    setClarifyDone(false);
    // 自动触发第一轮澄清
    setTimeout(async () => {
      setChatLoading(true);
      try {
        const res = await clarifyRequirement(requirementText.trim(), []);
        setChatMessages((prev) => [
          ...prev,
          { role: "assistant", content: res.reply_to_user || "请补充更多信息" },
        ]);
        if (res.is_complete) setClarifyDone(true);
      } catch (e) {
        setChatMessages((prev) => [
          ...prev,
          { role: "assistant", content: "⚠️ 澄清服务暂时不可用" },
        ]);
      } finally {
        setChatLoading(false);
      }
    }, 100);
  }, [requirementText]);

  const exitClarify = () => {
    setClarifyMode(false);
    setChatMessages([]);
    setClarifyDone(false);
    setChatInput("");
  };

  const handleRun = useCallback(async () => {
    if (!requirementText.trim()) {
      setError("请输入客户需求");
      return;
    }
    setError("");
    setResult(null);
    setProgress(5);
    setLoading(true);
    abortRef.current = new AbortController();
    try {
      const submit = await submitPresaleAgent({
        requirement_text: requirementText.trim(),
        industry_hint: industryHint.trim() || null,
        equipment_hint: equipmentHint.trim() || null,
        enable_deep_risk: deepRisk,
        enable_deep_solution: deepSolution,
      });
      setJobId(submit.job_id);
      const res = await pollPresaleAgentJob(
        submit.job_id,
        (job) => setProgress(job.progress || 0),
        { signal: abortRef.current.signal }
      );
      setResult(res);
      setProgress(100);
    } catch (e) {
      if (e.message !== "已取消") {
        setError(e?.response?.data?.detail || e.message || "分析失败");
      }
    } finally {
      setLoading(false);
    }
  }, [requirementText, industryHint, equipmentHint, deepRisk, deepSolution]);

  const handleReset = () => {
    abortRef.current?.abort();
    setLoading(false);
    setResult(null);
    setError("");
    setProgress(0);
    setJobId(null);
  };

  const applyTemplate = (tpl) => {
    setRequirementText(tpl.text);
    setIndustryHint(tpl.industry);
    setError("");
  };

  // 进度对应步骤索引
  const currentStepIdx = Math.min(
    Math.floor((progress / 100) * STEPS.length),
    STEPS.length - 1
  );
  // 预计剩余耗时（基于各步 ETA）
  const remainingEta = STEPS.slice(currentStepIdx).reduce((s, st) => s + st.eta, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="售前智能体"
          description="输入客户需求，AI 自动完成需求理解、案例检索、方案生成、报价区间、风险提示"
        />

        {error && (
          <Alert className="mb-4 border-red-500/30 bg-red-500/10 text-red-100">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>分析失败</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* 输入区 */}
        <Card className="mb-6 border-white/10 bg-slate-950/40">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Sparkles className="h-5 w-5 text-cyan-400" />
              客户需求
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 快速模板 */}
            <div>
              <p className="mb-2 text-xs text-slate-400">
                💡 不知道怎么描述？点一个快速模板填充：
              </p>
              <div className="flex flex-wrap gap-2">
                {TEMPLATES.map((tpl) => (
                  <button
                    key={tpl.label}
                    type="button"
                    onClick={() => applyTemplate(tpl)}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-xs transition",
                      requirementText === tpl.text
                        ? "border-cyan-500/50 bg-cyan-500/15 text-cyan-300"
                        : "border-white/10 bg-white/5 text-slate-400 hover:border-cyan-500/30 hover:text-cyan-300"
                    )}
                  >
                    {tpl.label}
                  </button>
                ))}
              </div>
            </div>

            <Textarea
              value={requirementText}
              onChange={(e) => setRequirementText(e.target.value)}
              placeholder="描述客户要做的测试系统，建议包含：①测试对象（如BMS/电驱/PCBA）②关键指标（电压/电流/节拍/精度）③行业 ④特殊要求（通讯/安全/追溯）"
              rows={4}
              className="resize-none border-white/10 bg-slate-900/60 text-slate-100 placeholder:text-slate-500"
            />
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <input
                value={industryHint}
                onChange={(e) => setIndustryHint(e.target.value)}
                placeholder="行业（可选，如：新能源汽车）"
                className="rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none"
              />
              <input
                value={equipmentHint}
                onChange={(e) => setEquipmentHint(e.target.value)}
                placeholder="设备类型（可选，如：电驱测试）"
                className="rounded-md border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none"
              />
            </div>

            {/* 深度模式开关 */}
            <div className="rounded-lg border border-white/10 bg-slate-900/40 p-3">
              <div className="mb-2 flex items-center gap-2">
                <Sparkles className="h-3.5 w-3.5 text-violet-400" />
                <span className="text-xs font-medium text-slate-300">
                  分析深度（可选，深度模式更完整但耗时更长）
                </span>
              </div>
              <div className="flex flex-wrap gap-4">
                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={deepRisk}
                    onChange={(e) => setDeepRisk(e.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-slate-800 accent-cyan-500"
                  />
                  <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                  深度风险分析
                  <span className="text-xs text-slate-500">(+约15s)</span>
                </label>
                <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={deepSolution}
                    onChange={(e) => setDeepSolution(e.target.checked)}
                    className="h-4 w-4 rounded border-white/20 bg-slate-800 accent-violet-500"
                  />
                  <Lightbulb className="h-3.5 w-3.5 text-violet-400" />
                  深度方案生成
                  <span className="text-xs text-slate-500">(+约55s，含完整方案/档位/周期)</span>
                </label>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <Button
                onClick={handleRun}
                disabled={loading || !requirementText.trim()}
                className="bg-cyan-600 hover:bg-cyan-500"
              >
                {loading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Send className="mr-2 h-4 w-4" />
                )}
                {loading ? "分析中..." : deepSolution ? "启动深度方案分析" : deepRisk ? "启动深度分析" : "启动智能体分析"}
              </Button>
              {!clarifyMode && !result && (
                <Button
                  variant="outline"
                  onClick={startClarify}
                  disabled={loading || !requirementText.trim()}
                  className="border-violet-500/30 text-violet-300 hover:bg-violet-500/10"
                >
                  <MessageSquare className="mr-2 h-4 w-4" />
                  先澄清需求
                </Button>
              )}
              {(loading || result) && (
                <Button variant="outline" onClick={handleReset} className="border-white/20 text-slate-300">
                  <RotateCcw className="mr-2 h-4 w-4" />
                  重置
                </Button>
              )}
              {jobId && <span className="text-xs text-slate-500">任务 #{jobId}</span>}
            </div>

            {/* 澄清对话面板（clarifyMode 时显示） */}
            {clarifyMode && (
              <ClarifyChatPanel
                messages={chatMessages}
                input={chatInput}
                setInput={setChatInput}
                onSend={handleClarifySend}
                loading={chatLoading}
                done={clarifyDone}
                onExit={exitClarify}
                onGenerate={handleRun}
                generating={loading}
                chatEndRef={chatEndRef}
              />
            )}
          </CardContent>
        </Card>

        {/* 进度区（改进：每步说明 + 预计剩余） */}
        {loading && (
          <Card className="mb-6 border-cyan-500/20 bg-cyan-500/5">
            <CardContent className="pt-5">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-sm text-cyan-200">
                  正在：{STEPS[currentStepIdx]?.label}...
                </span>
                <span className="text-sm font-medium text-cyan-300">
                  {progress}% · 预计还需 {remainingEta}s
                </span>
              </div>
              <Progress value={progress} color="primary" className="mb-4" />
              <ol className="flex flex-wrap items-center gap-2">
                {STEPS.map((s, i) => {
                  const done = i < currentStepIdx;
                  const active = i === currentStepIdx;
                  const Icon = done ? CheckCircle2 : active ? Loader2 : Flag;
                  return (
                    <li key={s.key} className="flex items-center gap-2">
                      <div
                        className={cn(
                          "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs",
                          done && "border border-emerald-500/30 bg-emerald-500/15 text-emerald-300",
                          active && "border border-cyan-500/30 bg-cyan-500/15 text-cyan-300",
                          !done && !active && "border border-white/10 bg-white/5 text-slate-500"
                        )}
                      >
                        <Icon className={cn("h-3.5 w-3.5", active && "animate-spin")} />
                        {s.label}
                      </div>
                      {i < STEPS.length - 1 && (
                        <div className={cn("h-px w-4", done ? "bg-emerald-500/40" : "bg-white/10")} />
                      )}
                    </li>
                  );
                })}
              </ol>
            </CardContent>
          </Card>
        )}

        {/* 结果区 */}
        {result && <AgentResult result={result} requirement={requirementText} deep={deepRisk || deepSolution} />}
      </div>
    </div>
  );
}

// ============= 结果展示（改进：结论摘要 + 分主次 + 导出） =============

function AgentResult({ result, requirement, deep }) {
  const { steps, summary, timings, total_time } = result;
  const [showEditor, setShowEditor] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [revisedResult, setRevisedResult] = useState(null); // 修订后的结果（用于展示对比）

  // ===== 方案协作状态 =====
  const [proposalId, setProposalId] = useState(null); // 已保存为 proposal 的 id
  const [proposalStatus, setProposalStatus] = useState(null); // draft/pending_review/approved/rejected
  const [iterationMsgs, setIterationMsgs] = useState([]); // 迭代对话 [{role, content}]
  const [iterInput, setIterInput] = useState("");
  const [iterLoading, setIterLoading] = useState(false);
  const [currentSolution, setCurrentSolution] = useState(result); // 当前方案（迭代后会更新）
  const iterEndRef = useRef(null);

  // 保存为方案（创建 proposal）
  const handleSaveAsProposal = async () => {
    try {
      const r = await createProposal({
        title: requirement.slice(0, 40),
        requirement_text: requirement,
        solution: currentSolution,
      });
      setProposalId(r.id);
      setProposalStatus("draft");
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "保存失败");
    }
  };

  // 迭代修改：提建议→agent改
  const handleIterate = async () => {
    const text = iterInput.trim();
    if (!text || iterLoading || !proposalId) return;
    setIterationMsgs((prev) => [...prev, { role: "user", content: text }]);
    setIterInput("");
    setIterLoading(true);
    try {
      const r = await reviseProposal(proposalId, text);
      setIterationMsgs((prev) => [...prev, { role: "assistant", content: r.changes_summary || "已修改" }]);
      if (r.solution) setCurrentSolution(r.solution); // 更新展示的方案
      setProposalStatus("draft");
    } catch (e) {
      setIterationMsgs((prev) => [...prev, { role: "assistant", content: "⚠️ 修改失败：" + (e.message || "未知错误") }]);
    } finally {
      setIterLoading(false);
      setTimeout(() => iterEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  // 提交审核
  const handleSubmitReview = async () => {
    try {
      const r = await submitProposal(proposalId);
      setProposalStatus(r.status);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    }
  };

  const handleExportMarkdown = () => {
    const md = buildExportMarkdown(revisedResult || result, requirement);
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `售前方案_${requirement.slice(0, 12)}_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* ① 结论摘要卡（顶部，一眼看到重点） */}
      <ConclusionSummary
        result={result}
        deep={deep}
        onExport={handleExportMarkdown}
        onRevise={() => setShowEditor(true)}
        onHistory={() => setShowHistory(true)}
        revised={!!revisedResult}
      />

      {/* 修订提示 */}
      {revisedResult && (
        <Alert className="border-emerald-500/30 bg-emerald-500/10 text-emerald-100">
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>
            ✅ 已保存工程师修订。修改已记录，将用于持续优化 AI 产出质量。
          </AlertDescription>
        </Alert>
      )}

      {/* ===== 方案协作面板（保存→迭代→提交→审核） ===== */}
      <ProposalCollaborationPanel
        proposalId={proposalId}
        proposalStatus={proposalStatus}
        iterationMsgs={iterationMsgs}
        iterInput={iterInput}
        setIterInput={setIterInput}
        onIterate={handleIterate}
        iterLoading={iterLoading}
        onSave={handleSaveAsProposal}
        onSubmit={handleSubmitReview}
        iterEndRef={iterEndRef}
      />

      <StepCard stepKey="quote_range" title="报价区间（基于历史数据）" timing={timings} steps={steps} icon={DollarSign}>
        <QuoteRangeView data={steps.quote_range} />
      </StepCard>

      {/* 可视化方案包（整线项目，4 个 HTML） */}
      {steps.layout_html?.ok && (
        <VisualPackageCard layoutData={steps.layout_html} requirement={requirement} timing={timings?.layout_html} />
      )}

      {/* ③ 风险（主结论） */}
      {steps.deep_risk_analysis?.ok ? (
        <StepCard stepKey="deep_risk_analysis" title="深度风险分析（自主多轮）" timing={timings} steps={steps} icon={ShieldAlert}>
          <DeepRiskView data={steps.deep_risk_analysis} />
        </StepCard>
      ) : (
        <StepCard stepKey="risk_warnings" title="关键风险与验收难点" timing={timings} steps={steps} icon={ShieldAlert}>
          <RiskView data={steps.risk_warnings} />
        </StepCard>
      )}

      {/* ④ 参考信息（案例/BOM/需求解析）在后 */}
      <details className="group rounded-lg border border-white/10 bg-slate-950/40">
        <summary className="flex cursor-pointer items-center gap-2 p-4 text-sm text-slate-300 hover:text-slate-100">
          <Boxes className="h-4 w-4 text-cyan-400" />
          参考信息（相似案例 / BOM / 需求解析）
          <span className="text-xs text-slate-500 group-open:hidden">[展开]</span>
          <span className="hidden text-xs text-slate-500 group-open:inline">[收起]</span>
        </summary>
        <div className="space-y-4 p-4 pt-0">
          <StepCard stepKey="retrieve_ammo" title="相似历史案例" timing={timings} steps={steps} icon={Boxes} embedded>
            <CasesList cases={steps.retrieve_ammo?.similar_cases} summary={steps.retrieve_ammo?.ammo_summary} />
          </StepCard>
          <StepCard stepKey="recommend_bom" title="BOM 模板推荐" timing={timings} steps={steps} icon={Wrench} embedded>
            <BomModules modules={steps.recommend_bom?.modules} note={steps.recommend_bom?.note} />
          </StepCard>
          <StepCard stepKey="understand_requirement" title="需求理解" timing={timings} steps={steps} icon={FileSearch} embedded>
            <ParsedRequirement parsed={steps.understand_requirement?.parsed} />
          </StepCard>
        </div>
      </details>

      {/* 修订编辑器弹层 */}
      {showEditor && (
        <RevisionEditor
          result={result}
          requirement={requirement}
          onClose={() => setShowEditor(false)}
          onSaved={(rev) => {
            setRevisedResult(rev);
            setShowEditor(false);
          }}
        />
      )}

      {/* 修订历史抽屉 */}
      {showHistory && (
        <RevisionHistory onClose={() => setShowHistory(false)} />
      )}
    </div>
  );
}

// ============= 结论摘要（改进：加修订/历史按钮） =============

function ConclusionSummary({ result, deep, onExport, onRevise, onHistory, revised }) {
  const { steps, total_time } = result;
  const parsed = steps.understand_requirement?.parsed || {};

  // 提取关键数字
  const qr = steps.quote_range || {};
  const price = qr.price || {};
  const hasQuote = qr.sample_count > 0;
  const risks = (steps.deep_risk_analysis?.deep_risks || steps.risk_warnings?.risks || []);
  const highRisks = risks.filter(r => r.severity === "high");
  const tiers = steps.deep_solution?.tiers || [];

  return (
    <Card className="border-cyan-400/30 bg-gradient-to-br from-cyan-500/10 to-violet-500/5">
      <CardContent className="pt-5">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            <span className="text-sm font-medium text-emerald-200">
              {deep ? "深度分析完成" : "分析完成"}
            </span>
            <Badge variant="secondary" className="border-white/10 text-slate-400">
              <Clock className="mr-1 h-3 w-3" /> {total_time}s
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onExport} className="border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10">
              <Download className="mr-1.5 h-3.5 w-3.5" />
              导出
            </Button>
            <Button variant="outline" size="sm" onClick={onHistory} className="border-white/20 text-slate-300 hover:bg-white/5">
              <History className="mr-1.5 h-3.5 w-3.5" />
              修订历史
            </Button>
            <Button size="sm" onClick={onRevise} className={revised ? "bg-emerald-600 hover:bg-emerald-500" : "bg-violet-600 hover:bg-violet-500"}>
              <Pencil className="mr-1.5 h-3.5 w-3.5" />
              {revised ? "已修订（再改）" : "修订并确认"}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {/* 报价中位 */}
          <SummaryStat
            label="历史报价中位"
            value={hasQuote ? fmtWan(price.median) : "暂无数据"}
            sub={hasQuote ? `${fmtWan(price.min)}~${fmtWan(price.max)}` : ""}
            icon={DollarSign}
            color="emerald"
          />
          {/* 主要风险数 */}
          <SummaryStat
            label="关键风险"
            value={`${risks.length} 项`}
            sub={`${highRisks.length} 项高危`}
            icon={ShieldAlert}
            color={highRisks.length > 0 ? "red" : "amber"}
          />
          {/* 相似案例数 */}
          <SummaryStat
            label="相似案例"
            value={`${steps.retrieve_ammo?.similar_cases?.length || 0} 个`}
            sub={parsed.equipment_type || ""}
            icon={Boxes}
            color="cyan"
          />
          {/* 推荐档位（深度）或设备类型 */}
          {tiers.length > 0 ? (
            <SummaryStat
              label="推荐档位"
              value={tiers[1]?.price || tiers[0]?.price || ""}
              sub={tiers[1]?.tier || "标准型"}
              icon={TrendingUp}
              color="violet"
            />
          ) : (
            <SummaryStat
              label="设备/行业"
              value={parsed.equipment_type || ""}
              sub={parsed.industry || ""}
              icon={FileSearch}
              color="violet"
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function SummaryStat({ label, value, sub, icon: Icon, color }) {
  const colors = {
    emerald: "border-emerald-500/20 bg-emerald-500/5 text-emerald-300",
    red: "border-red-500/20 bg-red-500/5 text-red-300",
    amber: "border-amber-500/20 bg-amber-500/5 text-amber-300",
    cyan: "border-cyan-500/20 bg-cyan-500/5 text-cyan-300",
    violet: "border-violet-500/20 bg-violet-500/5 text-violet-300",
  };
  return (
    <div className={cn("rounded-lg border p-3", colors[color] || colors.cyan)}>
      <div className="flex items-center gap-1 text-[10px] opacity-70">
        <Icon className="h-3 w-3" />
        {label}
      </div>
      <div className="mt-1 truncate text-base font-semibold">{value || "-"}</div>
      {sub && <div className="truncate text-[10px] opacity-60">{sub}</div>}
    </div>
  );
}

// ============= 导出 Markdown =============

function buildExportMarkdown(result, requirement) {
  const { steps, total_time } = result;
  const parsed = steps.understand_requirement?.parsed || {};
  const lines = [`# 售前方案分析：${requirement.slice(0, 40)}`, ""];
  lines.push(`> 生成时间：${new Date().toLocaleString("zh-CN")} ｜ 用时 ${total_time}s ｜ 售前智能体`);
  lines.push("");

  if (parsed.equipment_type || parsed.industry) {
    lines.push(`## 需求识别`);
    lines.push(`- 设备类型：${parsed.equipment_type || "-"}`);
    lines.push(`- 行业：${parsed.industry || "-"}`);
    if (parsed.key_specs?.length) lines.push(`- 关键指标：${parsed.key_specs.join("、")}`);
    lines.push("");
  }

  const ds = steps.deep_solution;
  if (ds?.ok) {
    lines.push(`## 完整技术方案`);
    if (ds.system_architecture) lines.push(`\n**架构**：${ds.system_architecture}`);
    if (ds.subsystems?.length) {
      lines.push(`\n**子系统**：`);
      ds.subsystems.forEach(s => lines.push(`- ${s.name}（${s.ref_cost || ""}）：${s.function || ""}`));
    }
    if (ds.equipment_selection?.length) {
      lines.push(`\n**设备选型**：`);
      ds.equipment_selection.forEach(e => lines.push(`- ${e.item}：${e.brand_suggestion || ""}`));
    }
    if (ds.tiers?.length) {
      lines.push(`\n**方案档位**：`);
      ds.tiers.forEach(t => lines.push(`- ${t.tier}：${t.price}（${t.diff || ""}）`));
    }
    lines.push("");
  } else if (steps.generate_solution?.solution) {
    const s = steps.generate_solution.solution;
    lines.push(`## 初步方案`);
    if (s.architecture) lines.push(`- 架构：${s.architecture}`);
    if (s.key_modules?.length) lines.push(`- 关键模块：${s.key_modules.join("、")}`);
    lines.push("");
  }

  const qr = steps.quote_range;
  if (qr?.sample_count) {
    const p = qr.price || {};
    lines.push(`## 报价区间（${qr.sample_count} 条历史数据）`);
    lines.push(`- 价格：${fmtWan(p.min)} ~ ${fmtWan(p.max)}（中位 ${fmtWan(p.median)}）`);
    if (qr.margin_pct?.median != null) lines.push(`- 毛利中位：${qr.margin_pct.median}%`);
    if (qr.lead_time_days?.median != null) lines.push(`- 交期中位：${qr.lead_time_days.median} 天`);
    lines.push("");
  }

  const risks = steps.deep_risk_analysis?.deep_risks || steps.risk_warnings?.risks || [];
  if (risks.length) {
    lines.push(`## 关键风险`);
    risks.forEach(r => lines.push(`- [${r.severity || ""}] ${r.description}${r.mitigation ? ` → ${r.mitigation}` : ""}`));
    lines.push("");
  }

  const cases = steps.retrieve_ammo?.similar_cases || [];
  if (cases.length) {
    lines.push(`## 相似历史案例`);
    cases.forEach(c => lines.push(`- ${c.case_name}（${c.equipment_type || ""}）${c.technical_highlights ? "：" + c.technical_highlights : ""}`));
  }

  return lines.join("\n");
}

function fmtWan(v) {
  if (v == null) return "-";
  try { return `${(Number(v) / 10000).toFixed(1)}万`; } catch { return String(v); }
}

// ============= 原有展示组件（保留） =============

function StepCard({ stepKey, title, timing, steps, icon: Icon, children, embedded }) {
  const stepData = steps?.[stepKey];
  const ok = stepData?.ok;
  return (
    <Card className={cn("border-white/10", embedded ? "bg-transparent shadow-none" : "bg-slate-950/40")}>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base text-slate-100">
          <Icon className="h-4 w-4 text-cyan-400" />
          {title}
          {timing?.[stepKey] != null && (
            <span className="ml-2 text-xs font-normal text-slate-500">{timing[stepKey]}s</span>
          )}
        </CardTitle>
        {ok === false && <Badge variant="danger">失败</Badge>}
        {ok === true && <Badge variant="success">完成</Badge>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ParsedRequirement({ parsed }) {
  if (!parsed) return <Muted>无</Muted>;
  return (
    <div className="space-y-2 text-sm">
      <div className="flex flex-wrap gap-2">
        {parsed.industry && <Tag label="行业" value={parsed.industry} color="violet" />}
        {parsed.equipment_type && <Tag label="设备" value={parsed.equipment_type} color="cyan" />}
        {parsed.scale && <Tag label="规模" value={parsed.scale} color="amber" />}
      </div>
      {parsed.key_specs?.length > 0 && <Field label="关键指标" value={parsed.key_specs.join("、")} />}
      {parsed.special_requirements?.length > 0 && <Field label="特殊要求" value={parsed.special_requirements.join("、")} />}
      {parsed.acceptance_focus?.length > 0 && <Field label="验收关注" value={parsed.acceptance_focus.join("、")} />}
    </div>
  );
}

function CasesList({ cases, summary }) {
  if (!cases?.length) return <Muted>{summary || "无相似历史案例（真实项目数据补充后会改善）"}</Muted>;
  return (
    <div className="space-y-2">
      {summary && <p className="text-xs text-slate-400">{summary}</p>}
      {cases.map((c) => (
        <div key={c.id} className="rounded-lg border border-white/10 bg-slate-900/40 p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-slate-100">{c.case_name}</span>
            <div className="flex gap-1">
              {c.equipment_type && <Badge variant="info">{c.equipment_type}</Badge>}
              {c.industry && <Badge variant="secondary">{c.industry}</Badge>}
            </div>
          </div>
          {c.technical_highlights && (
            <p className="mt-1.5 text-xs text-slate-400"><span className="text-cyan-300">技术亮点：</span>{c.technical_highlights}</p>
          )}
          {c.lessons_learned && (
            <p className="mt-1 text-xs text-slate-400"><span className="text-amber-300">教训：</span>{c.lessons_learned}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function SolutionView({ solution }) {
  if (!solution?.architecture) return <Muted>方案生成失败或无内容</Muted>;
  return (
    <div className="space-y-3 text-sm">
      <Field label="系统架构" value={solution.architecture} multiline />
      {solution.key_modules?.length > 0 && <TagList label="关键模块" items={solution.key_modules} color="cyan" />}
      {solution.key_equipment?.length > 0 && <TagList label="关键设备选型" items={solution.key_equipment} color="violet" />}
    </div>
  );
}

function BomModules({ modules, note }) {
  if (!modules?.length) return <Muted>{note || "无匹配标准模块"}</Muted>;
  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-400">{note}</p>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        {modules.map((m) => (
          <div key={m.module_name} className="rounded-lg border border-white/10 bg-slate-900/40 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-100">{m.module_name}</span>
              {m.ref_cost != null && <span className="text-xs text-emerald-300">¥{Number(m.ref_cost).toLocaleString()}</span>}
            </div>
            <p className="mt-1 text-xs text-slate-500">{m.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function QuoteRangeView({ data }) {
  if (!data?.sample_count) return <Muted>无匹配的历史报价数据（真实项目数据补充后会改善）</Muted>;
  const { price, margin_pct, lead_time_days, sample_count } = data;
  return (
    <div className="space-y-3 text-sm">
      <p className="text-xs text-slate-400">基于 <span className="text-cyan-300">{sample_count}</span> 条历史报价统计</p>
      {price && (
        <div className="grid grid-cols-5 gap-2">
          {[["最低", price.min], ["25分位", price.p25], ["中位", price.median], ["75分位", price.p75], ["最高", price.max]].map(([label, v]) => (
            <div key={label} className="rounded-lg border border-white/10 bg-slate-900/40 p-2 text-center">
              <div className="text-[10px] text-slate-500">{label}</div>
              <div className="mt-0.5 text-sm font-medium text-emerald-300">{v != null ? `¥${(v / 10000).toFixed(1)}万` : "-"}</div>
            </div>
          ))}
        </div>
      )}
      <div className="flex flex-wrap gap-3 text-xs">
        {margin_pct?.median != null && <span className="text-slate-400">毛利中位 <span className="text-emerald-300">{margin_pct.median}%</span></span>}
        {lead_time_days?.median != null && <span className="text-slate-400">交期中位 <span className="text-cyan-300">{lead_time_days.median}天</span></span>}
      </div>
    </div>
  );
}

function RiskView({ data }) {
  const risks = data?.risks || [];
  return (
    <div className="space-y-3 text-sm">
      {risks.length === 0 && <Muted>无风险数据</Muted>}
      {risks.map((r, i) => {
        const sev = r.severity || "medium";
        const color = sev === "high" ? "border-red-500/30 bg-red-500/10 text-red-200" : sev === "medium" ? "border-amber-500/30 bg-amber-500/10 text-amber-200" : "border-slate-500/30 bg-slate-500/10 text-slate-200";
        return (
          <div key={i} className={cn("rounded-lg border p-3", color)}>
            <div className="flex items-center gap-2">
              <Badge variant={sev === "high" ? "danger" : sev === "medium" ? "warning" : "secondary"}>{sev.toUpperCase()}</Badge>
              <span className="text-xs opacity-70">{r.category}</span>
            </div>
            <p className="mt-1.5">{r.description}</p>
            {r.mitigation && <p className="mt-1 text-xs opacity-80">→ {r.mitigation}</p>}
          </div>
        );
      })}
      {data?.must_confirm?.length > 0 && (
        <div>
          <p className="mb-1 text-xs text-amber-300">报价前必须确认：</p>
          <ul className="ml-4 list-disc space-y-0.5 text-xs text-slate-300">
            {data.must_confirm.map((m, i) => <li key={i}>{m}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

// ============= 深度方案/风险展示（保留原有） =============

function DeepRiskView({ data }) {
  if (!data?.ok) return <Muted>深度风险分析失败：{data?.error || "未知错误"}</Muted>;
  const { deep_risks = [], supply_chain_warnings = [], cost_risks = [], tool_calls = [], rounds = 0 } = data;
  return (
    <div className="space-y-3 text-sm">
      <div className="mb-2 flex items-center gap-2 rounded-md border border-violet-500/20 bg-violet-500/5 px-3 py-1.5 text-xs text-violet-200">
        <Sparkles className="h-3 w-3" />
        模型自主调用了 {tool_calls.length} 次工具（{rounds} 轮），以下结论均有数据依据
      </div>
      {deep_risks.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs text-slate-400">深度识别的风险：</p>
          <div className="space-y-2">
            {deep_risks.map((r, i) => {
              const sev = r.severity || "medium";
              const color = sev === "high" ? "border-red-500/30 bg-red-500/10 text-red-200" : sev === "medium" ? "border-amber-500/30 bg-amber-500/10 text-amber-200" : "border-slate-500/30 bg-slate-500/10 text-slate-200";
              return (
                <div key={i} className={cn("rounded-lg border p-3", color)}>
                  <div className="flex items-center gap-2">
                    <Badge variant={sev === "high" ? "danger" : sev === "medium" ? "warning" : "secondary"}>{sev.toUpperCase()}</Badge>
                    <span className="text-xs opacity-70">{r.category}</span>
                  </div>
                  <p className="mt-1.5">{r.description}</p>
                  {r.mitigation && <p className="mt-1 text-xs opacity-80">→ {r.mitigation}</p>}
                  {r.evidence && <p className="mt-1 text-xs opacity-60">依据：{r.evidence}</p>}
                </div>
              );
            })}
          </div>
        </div>
      )}
      {supply_chain_warnings.length > 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
          <p className="mb-1 text-xs text-amber-300">⚠ 供应链警告</p>
          <ul className="ml-4 list-disc space-y-0.5 text-xs text-slate-300">
            {supply_chain_warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
      {cost_risks.length > 0 && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
          <p className="mb-1 text-xs text-red-300">¥ 成本风险</p>
          <ul className="ml-4 list-disc space-y-0.5 text-xs text-slate-300">
            {cost_risks.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

function DeepSolutionView({ data }) {
  if (!data?.ok) return <Muted>深度方案生成失败：{data?.error || "未知错误"}</Muted>;
  const { solution_overview, system_architecture, subsystems = [], equipment_selection = [], test_strategy, software_design, cost_breakdown = [], tiers = [], implementation_phases = [], evidence = [], differentiation, assumptions = [], tool_calls = [], rounds = 0 } = data;
  return (
    <div className="space-y-4 text-sm">
      <div className="mb-1 flex items-center gap-2 rounded-md border border-violet-500/20 bg-violet-500/5 px-3 py-1.5 text-xs text-violet-200">
        <Sparkles className="h-3 w-3" />
        模型自主调用了 {tool_calls.length} 次工具（{rounds} 轮）查全资料后综合生成
      </div>
      {solution_overview && (
        <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3">
          <p className="mb-1 text-xs font-medium text-cyan-300">方案总述</p>
          <p className="text-slate-200">{solution_overview}</p>
        </div>
      )}
      {system_architecture && <Field label="系统架构" value={system_architecture} multiline />}
      {subsystems.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-slate-300">子系统拆解（{subsystems.length}个）</p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {subsystems.map((ss, i) => (
              <div key={i} className="rounded-lg border border-white/10 bg-slate-900/40 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-slate-100">{ss.name}</span>
                  {ss.ref_cost && <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs text-emerald-300">{ss.ref_cost}</span>}
                </div>
                <p className="mt-1 text-xs text-slate-400">{ss.function}</p>
                {ss.key_components?.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {ss.key_components.map((c, j) => (
                      <span key={j} className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] text-slate-400">{c}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      {equipment_selection.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-slate-300">关键设备选型（{equipment_selection.length}项）</p>
          <div className="overflow-hidden rounded-lg border border-white/10">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/5 text-slate-400">
                <tr>
                  <th className="px-2 py-1.5 font-medium">设备</th>
                  <th className="px-2 py-1.5 font-medium">规格</th>
                  <th className="px-2 py-1.5 font-medium">品牌建议</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {equipment_selection.map((eq, i) => (
                  <tr key={i} className="text-slate-300">
                    <td className="px-2 py-1.5 font-medium text-slate-100">{eq.item}</td>
                    <td className="px-2 py-1.5 text-slate-400">{eq.spec}</td>
                    <td className="px-2 py-1.5 text-violet-300">{eq.brand_suggestion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {cost_breakdown.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-slate-300">成本分解</p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-5 md:gap-3">
            {cost_breakdown.map((cb, i) => (
              <div key={i} className="rounded-lg border border-white/10 bg-slate-900/40 p-2 text-center">
                <div className="text-[10px] text-slate-500">{cb.category}</div>
                <div className="mt-0.5 text-sm font-medium text-emerald-300">{cb.amount}</div>
                {cb.ratio && <div className="text-[10px] text-slate-500">占比 {cb.ratio}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
      {tiers.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-slate-300">方案档位（3档可选）</p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
            {tiers.map((t, i) => {
              const colors = ["border-emerald-500/30 bg-emerald-500/10", "border-cyan-500/30 bg-cyan-500/10", "border-violet-500/30 bg-violet-500/10"];
              return (
                <div key={i} className={cn("rounded-lg border p-3", colors[i] || colors[0])}>
                  <div className="text-xs font-medium text-slate-100">{t.tier}</div>
                  <div className="mt-1 text-lg font-semibold text-white">{t.price}</div>
                  <p className="mt-1 text-[11px] text-slate-400">{t.diff}</p>
                  {t.suitable && <p className="mt-0.5 text-[11px] text-slate-500">适合：{t.suitable}</p>}
                </div>
              );
            })}
          </div>
        </div>
      )}
      {implementation_phases.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-slate-300">实施阶段</p>
          <div className="flex flex-wrap items-center gap-1">
            {implementation_phases.map((ph, i) => (
              <div key={i} className="flex items-center gap-1">
                <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs">
                  <span className="text-slate-300">{ph.phase}</span>
                  <span className="ml-1.5 text-cyan-300">{ph.duration}</span>
                </div>
                {i < implementation_phases.length - 1 && <span className="text-slate-600">→</span>}
              </div>
            ))}
          </div>
        </div>
      )}
      {(evidence.length > 0 || differentiation || assumptions.length > 0) && (
        <div className="rounded-lg border border-white/10 bg-slate-900/40 p-3">
          {evidence.length > 0 && (
            <>
              <p className="mb-1 text-xs text-emerald-300">本方案依据</p>
              <ul className="ml-4 list-disc space-y-0.5 text-[11px] text-slate-400">
                {evidence.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </>
          )}
          {differentiation && <p className="mt-2 text-xs text-slate-400"><span className="text-cyan-300">差异化：</span>{differentiation}</p>}
          {assumptions.length > 0 && (
            <>
              <p className="mt-2 mb-1 text-xs text-amber-300">需客户确认的前提假设</p>
              <ul className="ml-4 list-disc space-y-0.5 text-[11px] text-slate-400">
                {assumptions.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ============= 小工具 =============

function Tag({ label, value, color }) {
  const colors = {
    violet: "border-violet-500/30 bg-violet-500/10 text-violet-200",
    cyan: "border-cyan-500/30 bg-cyan-500/10 text-cyan-200",
    amber: "border-amber-500/30 bg-amber-500/10 text-amber-200",
    emerald: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
  };
  return (
    <span className={cn("rounded-full border px-2.5 py-0.5 text-xs", colors[color] || colors.cyan)}>
      <span className="opacity-60">{label}</span> {value}
    </span>
  );
}

function TagList({ label, items, color }) {
  return (
    <div>
      <span className="text-xs text-slate-500">{label}：</span>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {items.map((it, i) => <Tag key={i} value={it} color={color} />)}
      </div>
    </div>
  );
}

function Field({ label, value, multiline }) {
  if (!value) return null;
  return (
    <div>
      <span className="text-xs text-slate-500">{label}：</span>
      <span className={cn("text-slate-200", multiline && "block py-1")}>{value}</span>
    </div>
  );
}

function Muted({ children }) {
  return <p className="text-sm text-slate-500">{children}</p>;
}

// ============= 方案协作面板（保存→迭代→提交→审核） =============

const STATUS_CONFIG = {
  draft: { label: "迭代中", color: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300", icon: Pencil },
  pending_review: { label: "待审核", color: "border-amber-500/30 bg-amber-500/10 text-amber-300", icon: Clock },
  approved: { label: "已通过", color: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300", icon: CheckCircle2 },
  rejected: { label: "已打回", color: "border-red-500/30 bg-red-500/10 text-red-300", icon: AlertCircle },
};

function ProposalCollaborationPanel({
  proposalId, proposalStatus, iterationMsgs, iterInput, setIterInput,
  onIterate, iterLoading, onSave, onSubmit, iterEndRef,
}) {
  // 还没保存为 proposal
  if (!proposalId) {
    return (
      <Card className="border-violet-500/20 bg-slate-950/40">
        <CardContent className="flex items-center justify-between pt-5">
          <div className="flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-violet-400" />
            <div>
              <p className="text-sm font-medium text-slate-200">方案协作</p>
              <p className="text-xs text-slate-500">保存方案后，可和 AI 多轮互动修改，再提交售前工程师审核</p>
            </div>
          </div>
          <Button onClick={onSave} className="bg-violet-600 hover:bg-violet-500">
            <Save className="mr-2 h-4 w-4" />
            保存为方案
          </Button>
        </CardContent>
      </Card>
    );
  }

  const statusCfg = STATUS_CONFIG[proposalStatus] || STATUS_CONFIG.draft;
  const StatusIcon = statusCfg.icon;
  const canEdit = proposalStatus === "draft" || proposalStatus === "rejected";

  return (
    <Card className="border-violet-500/20 bg-slate-950/40">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base text-slate-100">
          <GitBranch className="h-4 w-4 text-violet-400" />
          方案协作
          <span className={cn("ml-1 rounded-full border px-2 py-0.5 text-[10px]", statusCfg.color)}>
            <StatusIcon className="mr-1 inline h-3 w-3" />
            {statusCfg.label}
          </span>
          {proposalId && <span className="text-[10px] text-slate-500">方案 #{proposalId}</span>}
        </CardTitle>
        {canEdit && (
          <Button onClick={onSubmit} size="sm" className="bg-amber-600 hover:bg-amber-500">
            <CheckCheck className="mr-1.5 h-3.5 w-3.5" />
            提交审核
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 迭代对话区 */}
        {canEdit && (
          <>
            <div className="max-h-[240px] min-h-[100px] space-y-2 overflow-y-auto rounded-lg border border-white/10 bg-slate-900/40 p-3">
              {iterationMsgs.length === 0 ? (
                <p className="py-4 text-center text-xs text-slate-500">
                  提修改建议，AI 会自动改方案。例如："报价调低10%""加个老化工位""PLC换成西门子"
                </p>
              ) : (
                iterationMsgs.map((m, i) => (
                  <div key={i} className={cn("flex gap-2", m.role === "user" ? "justify-end" : "justify-start")}>
                    {m.role === "assistant" && (
                      <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-violet-500/20">
                        <Bot className="h-3.5 w-3.5 text-violet-300" />
                      </div>
                    )}
                    <div className={cn(
                      "max-w-[80%] rounded-lg px-3 py-1.5 text-xs",
                      m.role === "user" ? "bg-cyan-600/30 text-cyan-100" : "bg-white/5 text-slate-200"
                    )}>
                      {m.content}
                    </div>
                    {m.role === "user" && (
                      <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500/20">
                        <User className="h-3.5 w-3.5 text-cyan-300" />
                      </div>
                    )}
                  </div>
                ))
              )}
              {iterLoading && (
                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Loader2 className="h-3 w-3 animate-spin" /> AI 正在修改方案...
                </div>
              )}
              <div ref={iterEndRef} />
            </div>
            <div className="flex gap-2">
              <input
                value={iterInput}
                onChange={(e) => setIterInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), onIterate())}
                placeholder="提修改建议...（如：标准型报价调低到600万）"
                disabled={iterLoading}
                className="flex-1 rounded-md border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-violet-500/50 focus:outline-none disabled:opacity-50"
              />
              <Button onClick={onIterate} disabled={iterLoading || !iterInput.trim()} className="bg-violet-600 hover:bg-violet-500">
                {iterLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
          </>
        )}

        {/* 状态提示 */}
        {proposalStatus === "pending_review" && (
          <Alert className="border-amber-500/30 bg-amber-500/10 text-amber-100">
            <Clock className="h-4 w-4" />
            <AlertDescription>已提交审核，等待售前工程师确认。审核通过后方案定稿。</AlertDescription>
          </Alert>
        )}
        {proposalStatus === "approved" && (
          <Alert className="border-emerald-500/30 bg-emerald-500/10 text-emerald-100">
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>✅ 方案已审核通过，定稿。</AlertDescription>
          </Alert>
        )}
        {proposalStatus === "rejected" && (
          <Alert className="border-red-500/30 bg-red-500/10 text-red-100">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>方案被打回，请根据意见继续修改后重新提交。</AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

// ============= 可视化方案包卡片（4 个 HTML，Tab 切换） =============

function VisualPackageCard({ layoutData, requirement, timing }) {
  const [activeTab, setActiveTab] = useState("layout");

  const tabs = [
    { key: "layout_html", label: "产线布局图", icon: Map, short: "layout" },
    { key: "spec_html", label: "技术规格书", icon: FileText, short: "spec" },
    { key: "gantt_html", label: "进度甘特图", icon: Clock, short: "gantt" },
    { key: "response_html", label: "技术响应表", icon: CheckCircle2, short: "response" },
  ].filter((t) => layoutData[t.key]); // 只显示有内容的

  if (tabs.length === 0) return null;
  const activeHtml = layoutData[tabs.find((t) => t.short === activeTab)?.key] || "";

  const handleDownload = () => {
    const blob = new Blob([activeHtml], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const tabLabel = tabs.find((t) => t.short === activeTab)?.label || "可视化";
    a.download = `${tabLabel}_${requirement.slice(0, 12)}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleOpenNew = () => {
    const blob = new Blob([activeHtml], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank");
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  };

  return (
    <Card className="border-cyan-500/20 bg-slate-950/40">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base text-slate-100">
          <Map className="h-4 w-4 text-cyan-400" />
          可视化方案包
          {timing != null && <span className="ml-1 text-xs font-normal text-slate-500">{timing}s</span>}
          <Badge variant="info" className="ml-1">{tabs.length}个</Badge>
        </CardTitle>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleOpenNew} className="border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10">
            <ExternalLink className="mr-1.5 h-3.5 w-3.5" />新窗口
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownload} className="border-white/20 text-slate-300">
            <Download className="mr-1.5 h-3.5 w-3.5" />下载
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Tab 切换 */}
        <div className="mb-3 flex flex-wrap gap-1.5">
          {tabs.map((t) => (
            <button
              key={t.short}
              onClick={() => setActiveTab(t.short)}
              className={cn(
                "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs transition",
                activeTab === t.short
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                  : "bg-white/5 text-slate-400 border border-white/10 hover:text-slate-200"
              )}
            >
              <t.icon className="h-3.5 w-3.5" />
              {t.label}
            </button>
          ))}
        </div>
        {/* HTML 预览（iframe） */}
        <iframe
          srcDoc={activeHtml}
          className="h-[450px] w-full rounded border border-white/10 bg-white"
          title={tabs.find((t) => t.short === activeTab)?.label}
        />
      </CardContent>
    </Card>
  );
}

// ============= 需求澄清对话面板 =============

function ClarifyChatPanel({
  messages, input, setInput, onSend, loading, done, onExit, onGenerate, generating, chatEndRef,
}) {
  return (
    <div className="mt-4 rounded-lg border border-violet-500/30 bg-slate-900/60">
      {/* 头部 */}
      <div className="flex items-center justify-between border-b border-violet-500/20 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-violet-400" />
          <span className="text-sm font-medium text-violet-200">需求澄清对话</span>
          {done && (
            <Badge variant="success" className="ml-1">
              <CheckCircle2 className="mr-1 h-3 w-3" /> 需求已完整
            </Badge>
          )}
        </div>
        <button onClick={onExit} className="text-slate-500 hover:text-slate-300">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* 对话区 */}
      <div className="max-h-[320px] min-h-[160px] space-y-3 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn("flex gap-2", m.role === "user" ? "justify-end" : "justify-start")}
          >
            {m.role === "assistant" && (
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-violet-500/20">
                <Bot className="h-4 w-4 text-violet-300" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[80%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm",
                m.role === "user"
                  ? "bg-cyan-600/30 text-cyan-100"
                  : "bg-white/5 text-slate-200"
              )}
            >
              {m.content}
            </div>
            {m.role === "user" && (
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-cyan-500/20">
                <User className="h-4 w-4 text-cyan-300" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Loader2 className="h-3 w-3 animate-spin" />
            售前顾问思考中...
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* 输入区 */}
      <div className="border-t border-white/10 p-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), onSend())}
            placeholder="回答问题，或补充更多需求细节..."
            disabled={loading || done}
            className="flex-1 rounded-md border border-white/10 bg-slate-950/60 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-violet-500/50 focus:outline-none disabled:opacity-50"
          />
          {done ? (
            <Button onClick={onGenerate} disabled={generating} className="bg-cyan-600 hover:bg-cyan-500">
              {generating ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Send className="mr-1.5 h-4 w-4" />}
              生成方案
            </Button>
          ) : (
            <Button onClick={onSend} disabled={loading || !input.trim()} className="bg-violet-600 hover:bg-violet-500">
              <Send className="mr-1.5 h-4 w-4" />
              回复
            </Button>
          )}
        </div>
        <p className="mt-1.5 text-[10px] text-slate-500">
          {done
            ? "✓ 需求已澄清完整，点击「生成方案」启动智能体分析"
            : "💡 回答问题帮助 AI 理解需求。也可以直接说'差不多了/你看着办'提前结束"}
        </p>
      </div>
    </div>
  );
}

// ============= 修订编辑器（左 AI 原稿 / 右 工程师定稿） =============

function RevisionEditor({ result, requirement, onClose, onSaved }) {
  // 工程师编辑的是 AI 结果的 JSON 文本。提交时解析回 JSON。
  const [editText, setEditText] = useState(JSON.stringify(result, null, 2));
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSave = async () => {
    setError("");
    let revised;
    try {
      revised = JSON.parse(editText);
    } catch (e) {
      setError("JSON 格式错误：" + e.message);
      return;
    }
    setSaving(true);
    try {
      const res = await submitRevision({
        requirement_text: requirement,
        ai_output: result,
        revised_output: revised,
        revision_note: note || null,
      });
      onSaved(revised);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleCopyAiToEdit = () => {
    setEditText(JSON.stringify(result, null, 2));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="flex max-h-[90vh] w-full max-w-7xl flex-col rounded-lg border border-white/10 bg-slate-950">
        {/* 头部 */}
        <div className="flex items-center justify-between border-b border-white/10 p-4">
          <div className="flex items-center gap-2">
            <Pencil className="h-5 w-5 text-violet-400" />
            <h2 className="text-lg font-semibold text-white">修订并确认</h2>
            <span className="text-xs text-slate-500">修改后会自动记录 diff，用于持续优化 AI</span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* 左右对比 */}
        <div className="grid flex-1 grid-cols-2 gap-2 overflow-hidden p-2">
          {/* 左：AI 原稿（只读） */}
          <div className="flex flex-col overflow-hidden rounded border border-white/10">
            <div className="border-b border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-400">
              📄 AI 原稿（只读参考）
            </div>
            <pre className="flex-1 overflow-auto bg-slate-900/60 p-3 text-[11px] leading-relaxed text-slate-400">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
          {/* 右：工程师编辑（可改） */}
          <div className="flex flex-col overflow-hidden rounded border border-violet-500/30">
            <div className="flex items-center justify-between border-b border-violet-500/20 bg-violet-500/5 px-3 py-1.5">
              <span className="text-xs text-violet-300">✏️ 工程师定稿（在此修改）</span>
              <button
                onClick={handleCopyAiToEdit}
                className="text-[10px] text-slate-500 hover:text-violet-300"
              >
                重置为AI原稿
              </button>
            </div>
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="flex-1 resize-none bg-slate-900/60 p-3 font-mono text-[11px] leading-relaxed text-slate-200 focus:outline-none"
              spellCheck={false}
            />
          </div>
        </div>

        {/* 修订说明 + 提交 */}
        <div className="space-y-2 border-t border-white/10 p-3">
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="修订说明（可选）：为什么改？补充了什么？— 这会帮助改进 AI"
            className="w-full rounded border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:border-violet-500/50 focus:outline-none"
          />
          {error && <p className="text-xs text-red-400">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose} className="border-white/20 text-slate-300">
              取消
            </Button>
            <Button onClick={handleSave} disabled={saving} className="bg-violet-600 hover:bg-violet-500">
              {saving ? <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> : <Save className="mr-1.5 h-4 w-4" />}
              保存修订
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============= 修订历史抽屉（查看过往修改 + 高频统计 + 改进建议） =============

function RevisionHistory({ onClose }) {
  const [items, setItems] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [majorOnly, setMajorOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [list, st] = await Promise.all([
        listRevisions(20, majorOnly),
        revisionStats(30),
      ]);
      setItems(list?.items || []);
      setStats(st);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [majorOnly]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40" onClick={onClose}>
      <div
        className="flex h-full w-full max-w-2xl flex-col overflow-y-auto border-l border-white/10 bg-slate-950"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="sticky top-0 flex items-center justify-between border-b border-white/10 bg-slate-950 p-4">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-cyan-400" />
            <h2 className="text-lg font-semibold text-white">修订历史</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* 高频统计（AI 改进方向） */}
        {stats && stats.total_revisions > 0 && (
          <div className="m-4 rounded-lg border border-violet-500/20 bg-violet-500/5 p-4">
            <p className="mb-2 text-sm font-medium text-violet-200">
              📊 AI 改进方向（近30天，{stats.total_revisions} 次修订）
            </p>
            {stats.suggestion && (
              <p className="mb-3 text-xs text-slate-400">{stats.suggestion}</p>
            )}
            <div className="space-y-1">
              <p className="text-[11px] text-slate-500">高频被改字段 TOP5：</p>
              {(stats.top_changed_fields || []).slice(0, 5).map((f, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">{f.field}</span>
                  <div className="h-1.5 flex-1 rounded-full bg-white/5">
                    <div
                      className="h-full rounded-full bg-violet-500/60"
                      style={{ width: `${Math.min(100, f.count * 20)}%` }}
                    />
                  </div>
                  <span className="text-slate-500">{f.count}次</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 筛选 */}
        <div className="flex items-center gap-2 px-4 pb-2">
          <label className="flex cursor-pointer items-center gap-1.5 text-xs text-slate-400">
            <input
              type="checkbox"
              checked={majorOnly}
              onChange={(e) => setMajorOnly(e.target.checked)}
              className="h-3.5 w-3.5 accent-violet-500"
            />
            只看大改（≥3字段）
          </label>
        </div>

        {/* 历史列表 */}
        <div className="flex-1 space-y-3 p-4 pt-0">
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-slate-500" />
            </div>
          ) : items.length === 0 ? (
            <div className="py-8 text-center text-sm text-slate-500">
              暂无修订记录
              <p className="mt-1 text-xs">工程师修订 AI 结果后，会在这里展示，并自动统计高频修改字段</p>
            </div>
          ) : (
            items.map((r) => (
              <div key={r.id} className="rounded-lg border border-white/10 bg-slate-900/40 p-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {r.is_major_revision ? (
                      <Badge variant="danger">大改</Badge>
                    ) : (
                      <Badge variant="secondary">小改</Badge>
                    )}
                    <span className="text-xs text-slate-400">
                      {r.changed_field_count} 处修改 · {r.revised_by_name}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-600">
                    {r.created_at?.slice(0, 16).replace("T", " ")}
                  </span>
                </div>
                <p className="mt-1.5 text-xs text-slate-300">
                  <span className="text-slate-500">需求：</span>
                  {r.requirement_text}
                </p>
                {/* diff 摘要 */}
                <div className="mt-2 space-y-0.5">
                  {(r.fields_diff || []).slice(0, 4).map((d, i) => (
                    <div key={i} className="flex items-start gap-1 text-[10px]">
                      <span className="text-violet-400">•</span>
                      <span className="text-slate-500">{d.section}.{d.field}:</span>
                      <span className="flex-1 truncate text-slate-400">
                        {String(d.old_value || "").slice(0, 30)} → {String(d.new_value || "").slice(0, 30)}
                      </span>
                    </div>
                  ))}
                </div>
                {r.revision_note && (
                  <p className="mt-1.5 text-[10px] text-slate-500">📝 {r.revision_note}</p>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
