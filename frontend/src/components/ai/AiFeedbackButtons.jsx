/**
 * AI 产出反馈按钮：采纳/驳回，打到统一反馈端点 /ai-feedback。
 * 任何 AI 建议卡片挂上即接入反馈闭环；驳回必须写原因（校准的原料）。
 */
import { useState } from "react";

import api from "../../services/api";

export default function AiFeedbackButtons({ featureKey, refType = null, refId = null, className = "" }) {
  const [state, setState] = useState(null); // null | "submitting" | "ADOPTED" | "REJECTED"

  const submit = async (verdict, reason) => {
    setState("submitting");
    try {
      await api.post("/ai-feedback", {
        feature_key: featureKey,
        verdict,
        ref_type: refType,
        ref_id: refId,
        reason: reason ?? null,
      });
      setState(verdict);
    } catch (e) {
      setState(null);
      alert(e?.response?.data?.detail || "反馈提交失败");
    }
  };

  const handleReject = () => {
    const reason = window.prompt("驳回原因（帮助我们校准 AI 建议）：");
    if (reason === null || !reason.trim()) return;
    submit("REJECTED", reason.trim());
  };

  if (state === "ADOPTED" || state === "REJECTED") {
    return (
      <span className={`text-xs text-muted-foreground ${className}`}>
        已记录反馈（{state === "ADOPTED" ? "采纳" : "驳回"}）
      </span>
    );
  }

  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <button
        type="button"
        disabled={state === "submitting"}
        onClick={() => submit("ADOPTED")}
        className="text-xs rounded border border-emerald-500/40 text-emerald-600 px-2 py-0.5 hover:bg-emerald-500/10 disabled:opacity-50"
      >
        👍 采纳
      </button>
      <button
        type="button"
        disabled={state === "submitting"}
        onClick={handleReject}
        className="text-xs rounded border border-red-500/40 text-red-500 px-2 py-0.5 hover:bg-red-500/10 disabled:opacity-50"
      >
        👎 驳回
      </button>
    </span>
  );
}
