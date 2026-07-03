/**
 * AI 方案评审卡片：风险清单 + HIGH 风险处置入口。
 * 人机分工：AI 出风险清单（初判），人处置留痕（关键判断+责任）；
 * 未处置的 HIGH 风险会被 G2 闸门拦截，本卡片是解除拦截的操作入口。
 */
import { useState } from "react";

import api from "../../services/api";

const LEVEL_COLOR = {
  HIGH: "text-red-500",
  MEDIUM: "text-amber-600",
  LOW: "text-slate-400",
};

export default function SolutionReviewCard({ opportunityId, reviews }) {
  const [resolution, setResolution] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (!reviews) return null;
  const highCount = reviews.filter(
    (r) => String(r.risk_level).toUpperCase() === "HIGH"
  ).length;

  const resolve = async (action, promptText) => {
    const note = window.prompt(promptText);
    if (note === null || !note.trim()) return;
    setSubmitting(true);
    try {
      const { data } = await api.post(
        `/sales/opportunities/${opportunityId}/solution-review/resolution`,
        { action, note: note.trim() }
      );
      setResolution((data?.data || data)?.resolution || { action });
    } catch (e) {
      alert(e?.response?.data?.detail || "处置提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mb-4 rounded-lg border border-purple-500/30 bg-purple-500/5 p-3 text-sm">
      <div className="font-medium mb-2">🔍 AI 方案评审（定稿前抓返工点）</div>
      <div className="space-y-1.5">
        {reviews.map((r, i) => {
          const lv = String(r.risk_level).toUpperCase();
          return (
            <div key={i} className="text-xs">
              <span className={`font-medium ${LEVEL_COLOR[lv] || "text-slate-400"}`}>
                [{lv}] {r.aspect}
              </span>
              ：{r.finding}
              <div className="text-muted-foreground">→ {r.suggestion}</div>
            </div>
          );
        })}
      </div>
      {highCount > 0 && !resolution && (
        <div className="mt-3 rounded border border-red-500/30 bg-red-500/5 p-2">
          <div className="text-xs text-red-500 font-medium mb-1.5">
            ⚠️ {highCount} 项高风险未处置将被 G2 闸门拦截，请处置后再提交阶段门
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={submitting}
              onClick={() => resolve("RESOLVED", "说明风险如何消除（如已调整方案/客户已确认）：")}
              className="text-xs rounded border border-emerald-500/40 text-emerald-600 px-2 py-0.5 hover:bg-emerald-500/10 disabled:opacity-50"
            >
              ✅ 已消除风险
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={() => resolve("ACCEPT_RISK", "说明为何带险推进（决策理由将留痕）：")}
              className="text-xs rounded border border-amber-500/40 text-amber-600 px-2 py-0.5 hover:bg-amber-500/10 disabled:opacity-50"
            >
              ⚠️ 带险推进
            </button>
          </div>
        </div>
      )}
      {resolution && (
        <div className="mt-3 text-xs text-emerald-600">
          ✅ 已处置（{resolution.action === "ACCEPT_RISK" ? "带险推进" : "风险已消除"}），G2 闸门解除拦截
        </div>
      )}
    </div>
  );
}
