import { useState, useEffect } from "react";
import api from "../services/api";
import { Button } from "../components/ui/button";

// AI 助手：我的一天 · 图纸理解 · 数字员工问答 · 文本助手 · 日报周报
export default function AIAssistant() {
    // 我的一天
    const [myDay, setMyDay] = useState(null);
    useEffect(() => { api.get("/ai-copilot/my-day").then(({ data }) => setMyDay(data?.data || data)).catch(() => {}); }, []);

    // 图纸理解
    const [imgResult, setImgResult] = useState(null);
    const [imgLoading, setImgLoading] = useState(false);
    const onFile = async (e) => {
        const f = e.target.files?.[0]; if (!f) return;
        setImgLoading(true); setImgResult(null);
        const fd = new FormData(); fd.append("file", f);
        try { const { data } = await api.post("/ai-advanced/analyze-drawing", fd, { headers: { "Content-Type": "multipart/form-data" } }); setImgResult(data?.data || data); }
        catch (err) { alert(err?.response?.data?.detail || "图纸分析失败"); } finally { setImgLoading(false); }
    };

    // 数字员工问答
    const [q, setQ] = useState(""); const [ans, setAns] = useState(null); const [asking, setAsking] = useState(false);
    const ask = async () => {
        if (q.trim().length < 2) return; setAsking(true); setAns(null);
        try { const { data } = await api.post("/ai-advanced/ask", { question: q }); setAns(data?.data || data); }
        catch (e) { alert("问答失败"); } finally { setAsking(false); }
    };

    // 文本助手（摘要/翻译/润色/邮件）
    const [txt, setTxt] = useState(""); const [out, setOut] = useState(""); const [busy, setBusy] = useState("");
    const tool = async (kind) => {
        if (txt.trim().length < 2) return; setBusy(kind); setOut("");
        try {
            let d;
            if (kind === "摘要") d = (await api.post("/ai-copilot/summarize", { text: txt })).data?.data;
            else if (kind === "翻译") d = (await api.post("/ai-copilot/translate", { text: txt, target: "en" })).data?.data;
            else if (kind === "润色") d = (await api.post("/ai-copilot/polish", { text: txt })).data?.data;
            else if (kind === "邮件") d = (await api.post("/ai-copilot/draft", { purpose: txt })).data?.data;
            setOut(d?.summary ? `${d.summary}\n\n要点：${(d.key_points || []).join("；")}` : (d?.translation || d?.polished || d?.draft || JSON.stringify(d)));
        } catch (e) { setOut("处理失败"); } finally { setBusy(""); }
    };

    // 日报
    const [report, setReport] = useState(""); const [rBusy, setRBusy] = useState(false);
    const [history, setHistory] = useState([]);
    const loadHistory = async () => { try { const { data } = await api.get("/ai-copilot/my-reports"); setHistory((data?.data || data)?.reports || []); } catch (e) { /* */ } };
    useEffect(() => { loadHistory(); }, []);
    const genReport = async (period) => {
        setRBusy(true); setReport("");
        try { const { data } = await api.get(`/ai-copilot/report?period=${period}`); setReport((data?.data || data)?.report || ""); loadHistory(); }
        catch (e) { setReport("生成失败"); } finally { setRBusy(false); }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto space-y-5">
            <div><h1 className="text-2xl font-bold">AI 助手</h1><p className="text-sm text-muted-foreground">我的一天 · 图纸理解 · 数字员工问答 · 文本助手 · 日报周报（也可按 Cmd/Ctrl+K 唤起全局命令栏）</p></div>

            {/* 我的一天 */}
            {myDay && (
                <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
                    <div className="font-medium mb-1">🌤 我的一天</div>
                    <div className="text-xs text-muted-foreground mb-2">在跟商机 {myDay.my_opportunities} · 停滞 {myDay.stale} · 缺售前评估 {myDay.unassessed}</div>
                    <div className="text-sm whitespace-pre-wrap">{myDay.today_focus}</div>
                </div>
            )}

            {/* 图纸理解 */}
            <div className="rounded-lg border p-4 space-y-2">
                <div className="font-medium">📐 图纸 / 现场照片 AI 理解</div>
                <input type="file" accept="image/*" onChange={onFile} className="text-sm" />
                {imgLoading && <div className="text-sm text-muted-foreground">AI 视觉分析中…</div>}
                {imgResult && (imgResult.raw ? <div className="text-xs whitespace-pre-wrap">{imgResult.raw}</div> : (
                    <div className="text-sm space-y-1">
                        <div><b>类型：</b>{imgResult.image_type} · <b>识别：</b>{imgResult.identified}</div>
                        <div><b>参数：</b>{(imgResult.parameters || []).map((p) => `${p.name}=${p.value}`).join("；")}</div>
                        <div className="text-emerald-600"><b>可行性：</b>{imgResult.feasibility}</div>
                        {(imgResult.questions || []).length > 0 && <div className="text-amber-600"><b>待确认：</b>{(imgResult.questions || []).join("；")}</div>}
                    </div>
                ))}
            </div>

            {/* 数字员工问答 */}
            <div className="rounded-lg border p-4 space-y-2">
                <div className="font-medium">🤖 数字员工（内部知识问答）</div>
                <div className="flex gap-2">
                    <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask()} className="flex-1 border rounded px-3 py-2 text-sm bg-background" placeholder="例：视觉检测模组参考成本？我们做过哪些锂电项目？" />
                    <Button onClick={ask} disabled={asking}>{asking ? "…" : "问"}</Button>
                </div>
                {ans && <div className="text-sm whitespace-pre-wrap">{ans.answer}{ans.matched > 0 && <span className="text-xs text-muted-foreground"> （依据{ans.matched}条内部记录）</span>}</div>}
            </div>

            {/* 文本助手 */}
            <div className="rounded-lg border p-4 space-y-2">
                <div className="font-medium">📝 文本助手（摘要 / 翻译 / 润色 / 邮件代写）</div>
                <textarea value={txt} onChange={(e) => setTxt(e.target.value)} className="w-full h-20 border rounded p-2 text-sm bg-background" placeholder="粘贴文本，或输入邮件目的（如：催促客户支付尾款）…" />
                <div className="flex gap-2">
                    {["摘要", "翻译", "润色", "邮件"].map((k) => <Button key={k} size="sm" variant="outline" onClick={() => tool(k)} disabled={!!busy}>{busy === k ? "…" : k}</Button>)}
                </div>
                {out && <div className="text-sm whitespace-pre-wrap rounded bg-muted p-2">{out}</div>}
            </div>

            {/* 日报周报 */}
            <div className="rounded-lg border p-4 space-y-2">
                <div className="font-medium">🗒 日报 / 周报（每天18:30自动推送到通知中心，也可手动生成）</div>
                <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => genReport("day")} disabled={rBusy}>生成日报</Button>
                    <Button size="sm" variant="outline" onClick={() => genReport("week")} disabled={rBusy}>生成周报</Button>
                </div>
                {rBusy && <div className="text-sm text-muted-foreground">AI 整理中…</div>}
                {report && <div className="text-sm whitespace-pre-wrap rounded bg-muted p-2">{report}</div>}
                {history.length > 0 && (
                    <div className="pt-1">
                        <div className="text-xs text-muted-foreground mb-1">历史推送（{history.length}）</div>
                        <div className="space-y-1">
                            {history.map((h, i) => (
                                <details key={i} className="text-xs border rounded p-2">
                                    <summary className="cursor-pointer">{h.period === "week" ? "周报" : "日报"} · {String(h.created_at).slice(0, 16)}</summary>
                                    <div className="whitespace-pre-wrap mt-1 text-muted-foreground">{h.content}</div>
                                </details>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
