import { useEffect, useRef, useState } from "react";
import api from "../../services/api";
import { Button, Input } from "../ui";

/**
 * 把 AI 返回的字段合并进现有表单：
 * - 只合并表单里已存在的键，忽略 AI 多给的键
 * - 用户已填的值不覆盖，只填空位
 * - 嵌套对象（如 requirement）递归合并一层
 * - 数字转字符串以适配受控 Input
 */
export function mergeAutofill(prev, fields) {
  const next = { ...prev };
  Object.entries(fields || {}).forEach(([key, value]) => {
    if (!(key in next)) return;
    const cur = next[key];
    if (cur && typeof cur === "object" && value && typeof value === "object") {
      next[key] = mergeAutofill(cur, value);
      return;
    }
    const empty = cur === "" || cur === null || cur === undefined;
    const usable = value !== "" && value !== null && value !== undefined && value !== 0;
    if (empty && usable && typeof value !== "object") {
      next[key] = typeof value === "number" ? String(value) : value;
    }
  });
  return next;
}

/**
 * AI 智能表单填充条：输入一句话线索 → 调 /ai-copilot/autofill → 回填表单。
 * 线索中没提到的字段后端会留空，onFill 只应合并非空字段，避免覆盖用户已填内容。
 */
export default function AutofillBar({ formType, onFill, placeholder, defaultHint }) {
  const [hint, setHint] = useState(defaultHint || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const autoRanRef = useRef(false);

  const run = async (text) => {
    const value = (text ?? hint).trim();
    if (value.length < 2 || loading) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/ai-copilot/autofill", {
        form_type: formType,
        hint: value,
      });
      const fields = data?.data?.fields || data?.fields;
      if (fields && typeof fields === "object") {
        onFill(fields);
      } else {
        setError("AI 未返回可用字段");
      }
    } catch (e) {
      setError("AI 填充失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  // 从命令栏等入口带线索进来时自动执行填充（同一线索只跑一次）
  useEffect(() => {
    if (defaultHint && defaultHint.trim().length >= 2 && autoRanRef.current !== defaultHint) {
      autoRanRef.current = defaultHint;
      setHint(defaultHint);
      run(defaultHint);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultHint]);

  return (
    <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/5 p-3 space-y-1">
      <div className="flex items-center gap-2">
        <span aria-hidden="true">✨</span>
        <Input
          value={hint}
          onChange={(e) => setHint(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder={placeholder || "一句话描述，AI 帮你预填表单…"}
          className="flex-1"
        />
        <Button size="sm" onClick={() => run()} disabled={loading || hint.trim().length < 2}>
          {loading ? "填充中…" : "AI 填充"}
        </Button>
      </div>
      {error ? <p className="text-xs text-red-400">{error}</p> : null}
      <p className="text-xs text-slate-500">
        线索里没提到的字段会留空，已填写的内容不会被覆盖。
      </p>
    </div>
  );
}
