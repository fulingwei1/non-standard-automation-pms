import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";

// 全局 AI 命令栏（Cmd/Ctrl+K）：自然语言导航 / 搜索 / 问答
export default function CommandBar() {
    const [open, setOpen] = useState(false);
    const [q, setQ] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const inputRef = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        const onKey = (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
                e.preventDefault();
                setOpen((v) => !v);
            }
            if (e.key === "Escape") setOpen(false);
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, []);

    useEffect(() => {
        if (open) setTimeout(() => inputRef.current?.focus(), 50);
        else { setQ(""); setResult(null); }
    }, [open]);

    const go = (path) => { if (path) { navigate(path); setOpen(false); } };

    const run = useCallback(async () => {
        if (q.trim().length < 1) return;
        setLoading(true); setResult(null);
        try {
            const { data } = await api.post("/ai-copilot/command", { input: q });
            const d = data?.data || data;
            setResult(d);
            if (d.intent === "navigate" && d.path) go(d.path);
            // 执行动作：跳到目标页并带上线索，由页面打开预填好的新建对话框
            if (d.intent === "action" && d.path && d.hint) {
                go(`${d.path}?ai_hint=${encodeURIComponent(d.hint)}`);
            }
        } catch (e) { setResult({ error: "AI 处理失败" }); } finally { setLoading(false); }
    }, [q]);

    if (!open) return null;
    return (
        <div className="fixed inset-0 z-[9999] flex items-start justify-center pt-[15vh] bg-black/40" onClick={() => setOpen(false)}>
            <div className="w-full max-w-xl bg-background rounded-xl border shadow-2xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center gap-2 px-4 py-3 border-b">
                    <span className="text-muted-foreground">✨</span>
                    <input
                        ref={inputRef}
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && run()}
                        placeholder="输入指令或问题…（如：打开商机列表 / 新建商机 给宁德时代做视觉检测 / 本月赢单率）"
                        className="flex-1 bg-transparent outline-none text-sm"
                    />
                    <kbd className="text-[10px] text-muted-foreground border rounded px-1">Esc</kbd>
                </div>
                <div className="max-h-80 overflow-y-auto p-2">
                    {loading && <div className="p-3 text-sm text-muted-foreground">AI 处理中…</div>}
                    {result?.answer && (
                        <div className="p-3 text-sm rounded bg-primary/5 mb-1">{result.answer}</div>
                    )}
                    {result?.error && <div className="p-3 text-sm text-red-500">{result.error}</div>}
                    {(result?.hits || []).map((h, i) => (
                        <div key={i} onClick={() => go(h.path)}
                            className="px-3 py-2 rounded hover:bg-muted cursor-pointer flex items-center justify-between text-sm">
                            <span><span className="text-[10px] rounded bg-muted px-1.5 py-0.5 mr-2">{h.type}</span>{h.title}</span>
                            <span className="text-xs text-muted-foreground">{h.sub}</span>
                        </div>
                    ))}
                    {!loading && !result && (
                        <div className="p-3 text-xs text-muted-foreground">回车执行 · 支持自然语言导航、全局搜索、问答与动作（新建客户/商机自动预填）</div>
                    )}
                </div>
            </div>
        </div>
    );
}
