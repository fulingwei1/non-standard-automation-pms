/**
 * 售前 AI 工作台：需求分析 → 确认回填商机 → 方案/三档报价。
 *
 * 北极星链路的前端闭环：需求只录一次，分析结果（requirement_analysis_id）
 * 直通方案生成与三档报价；确认动作把结构化需求增量回填商机（不覆盖人工值）。
 * 重 AI 生成走后台任务（提交即返回，页面轮询进度）。
 */
import { useEffect, useRef, useState } from "react";

import { presaleAIService } from "../services/presaleAIService";

const POLL_INTERVAL_MS = 3000;

function JobResultCard({ title, job, renderResult }) {
  if (!job) return null;
  return (
    <div className="rounded-lg border p-3 text-sm">
      <div className="font-medium mb-1">{title}</div>
      {job.status === "SUCCESS" ? (
        renderResult(job.result || {})
      ) : job.status === "FAILED" ? (
        <div className="text-xs text-red-500">失败：{job.error || "未知原因"}</div>
      ) : (
        <div className="text-xs text-muted-foreground">
          生成中…（{job.status}，进度 {job.progress ?? 0}%）
        </div>
      )}
    </div>
  );
}

export default function PresaleAIWorkbench() {
  const [ticketId, setTicketId] = useState("");
  const [rawRequirement, setRawRequirement] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [confirmResult, setConfirmResult] = useState(null);
  const [solutionJob, setSolutionJob] = useState(null);
  const [quoteJob, setQuoteJob] = useState(null);
  const timers = useRef([]);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const poll = (jobId, setJob) => {
    const tick = async () => {
      try {
        const job = await presaleAIService.getJob(jobId);
        setJob(job);
        if (job?.status !== "SUCCESS" && job?.status !== "FAILED") {
          timers.current.push(setTimeout(tick, POLL_INTERVAL_MS));
        }
      } catch (e) {
        setJob({ status: "FAILED", error: "轮询失败" });
      }
    };
    tick();
  };

  const handleAnalyze = async () => {
    if (!ticketId || rawRequirement.trim().length < 10) {
      alert("请填写售前工单ID和至少10字的需求描述");
      return;
    }
    setAnalyzing(true);
    setAnalysis(null);
    setConfirmResult(null);
    setSolutionJob(null);
    setQuoteJob(null);
    try {
      const result = await presaleAIService.analyzeRequirement({
        presale_ticket_id: Number(ticketId),
        raw_requirement: rawRequirement.trim(),
      });
      setAnalysis(result);
    } catch (e) {
      alert(e?.response?.data?.detail || "需求分析失败");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConfirm = async () => {
    try {
      const result = await presaleAIService.confirmAnalysis(analysis.id);
      setConfirmResult(result);
    } catch (e) {
      alert(e?.response?.data?.detail || "确认失败");
    }
  };

  const handleGenerateSolution = async () => {
    setSolutionJob({ status: "PENDING", progress: 0 });
    try {
      const { job_id } = await presaleAIService.submitGenerateSolution({
        presale_ticket_id: Number(ticketId),
        requirement_analysis_id: analysis.id,
        generate_architecture: false,
        generate_bom: false,
      });
      poll(job_id, setSolutionJob);
    } catch (e) {
      setSolutionJob(null);
      alert(e?.response?.data?.detail || "提交方案生成失败");
    }
  };

  const handleThreeTier = async () => {
    setQuoteJob({ status: "PENDING", progress: 0 });
    try {
      const { job_id } = await presaleAIService.submitThreeTierQuotation({
        presale_ticket_id: Number(ticketId),
        requirement_analysis_id: analysis.id,
      });
      poll(job_id, setQuoteJob);
    } catch (e) {
      setQuoteJob(null);
      alert(e?.response?.data?.detail || "提交三档报价失败");
    }
  };

  const structured = analysis?.structured_requirement || {};
  const money = (v) => (v == null ? "—" : `¥${Number(v).toLocaleString()}`);

  return (
    <div className="p-6 space-y-4 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold">售前 AI 工作台</h1>
        <p className="text-sm text-muted-foreground">
          需求只录一次：AI 分析 → 人工确认回填商机 → 方案与三档报价自动带出分析结果。
        </p>
      </div>

      <div className="rounded-lg border p-4 space-y-3">
        <div>
          <label htmlFor="ticket-id" className="block text-sm font-medium mb-1">售前工单ID</label>
          <input
            id="ticket-id"
            type="number"
            value={ticketId}
            onChange={(e) => setTicketId(e.target.value)}
            className="w-40 rounded border px-2 py-1 text-sm bg-transparent"
          />
        </div>
        <div>
          <label htmlFor="raw-req" className="block text-sm font-medium mb-1">原始需求</label>
          <textarea
            id="raw-req"
            rows={4}
            value={rawRequirement}
            onChange={(e) => setRawRequirement(e.target.value)}
            placeholder="粘贴客户需求描述/纪要要点（至少10字）"
            className="w-full rounded border px-2 py-1 text-sm bg-transparent"
          />
        </div>
        <button
          type="button"
          disabled={analyzing}
          onClick={handleAnalyze}
          className="rounded bg-primary text-primary-foreground px-3 py-1.5 text-sm disabled:opacity-50"
        >
          {analyzing ? "分析中…" : "🧠 AI 需求分析"}
        </button>
      </div>

      {analysis && (
        <div className="rounded-lg border border-sky-500/30 bg-sky-500/5 p-4 text-sm space-y-2">
          <div className="font-medium">
            分析结果 #{analysis.id} · 置信度 {Math.round((analysis.confidence_score || 0) * 100)}%
          </div>
          <div className="text-xs space-y-1">
            {structured.project_type && <div><b>项目类型：</b>{structured.project_type}</div>}
            {structured.industry && <div><b>行业：</b>{structured.industry}</div>}
            {(structured.core_objectives || []).length > 0 && (
              <div><b>核心目标：</b>{structured.core_objectives.join("；")}</div>
            )}
            {(structured.functional_requirements || []).length > 0 && (
              <div><b>功能需求：</b>{structured.functional_requirements.join("；")}</div>
            )}
            {(structured.constraints || []).length > 0 && (
              <div><b>约束：</b>{structured.constraints.join("；")}</div>
            )}
            {(analysis.clarification_questions || []).length > 0 && (
              <div className="text-amber-600">
                <b>待澄清：</b>
                {analysis.clarification_questions.map((q) => q.question || q).join("；")}
              </div>
            )}
          </div>
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={handleConfirm}
              className="text-xs rounded border border-emerald-500/40 text-emerald-600 px-2 py-1 hover:bg-emerald-500/10"
            >
              ✅ 确认并回填商机
            </button>
            <button
              type="button"
              onClick={handleGenerateSolution}
              className="text-xs rounded border border-purple-500/40 text-purple-600 px-2 py-1 hover:bg-purple-500/10"
            >
              📐 生成方案
            </button>
            <button
              type="button"
              onClick={handleThreeTier}
              className="text-xs rounded border border-amber-500/40 text-amber-600 px-2 py-1 hover:bg-amber-500/10"
            >
              💰 三档报价
            </button>
          </div>
          {confirmResult && (
            <div className="text-xs text-emerald-600">
              ✅ 已回填商机{confirmResult.opportunity_id ? ` #${confirmResult.opportunity_id}` : ""}
              {(confirmResult.filled_fields || []).length > 0 &&
                `（补齐：${confirmResult.filled_fields.join("、")}）`}
              {confirmResult.backfilled === false && "（工单未挂商机，仅确认分析）"}
            </div>
          )}
        </div>
      )}

      <JobResultCard
        title="📐 AI 方案"
        job={solutionJob}
        renderResult={(r) => (
          <div className="text-xs space-y-1">
            <div>方案ID：{r.solution_id} · 置信度 {Math.round((r.confidence_score || 0) * 100)}%</div>
            {r.solution?.description && <div>{r.solution.description}</div>}
          </div>
        )}
      />

      <JobResultCard
        title="💰 三档报价"
        job={quoteJob}
        renderResult={(r) => (
          <div className="grid grid-cols-3 gap-2 text-xs">
            {["basic", "standard", "premium"].map((tier) => (
              <div key={tier} className="rounded border p-2 text-center">
                <div className="text-muted-foreground">
                  {{ basic: "基础档", standard: "标准档", premium: "高级档" }[tier]}
                </div>
                <div className="font-bold">{money(r[tier]?.total)}</div>
                <div className="text-muted-foreground">{r[tier]?.quotation_number}</div>
              </div>
            ))}
          </div>
        )}
      />
    </div>
  );
}
