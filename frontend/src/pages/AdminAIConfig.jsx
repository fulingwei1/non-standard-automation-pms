import { useState, useEffect } from "react";
import api from "../services/api";
import { Button } from "../components/ui/button";

// 管理员：可视化配置 AI 接入 + 一键测试
export default function AdminAIConfig() {
    const [fields, setFields] = useState([]);
    const [values, setValues] = useState({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState(null);
    const [msg, setMsg] = useState("");

    const load = async () => {
        try {
            const { data } = await api.get("/admin/ai-config");
            setFields((data?.data || data)?.fields || []);
        } catch (e) {
            setMsg(e?.response?.status === 403 ? "仅管理员可访问本页" : "加载失败");
        } finally { setLoading(false); }
    };
    useEffect(() => { load(); }, []);

    const save = async () => {
        setSaving(true); setMsg("");
        try {
            const { data } = await api.put("/admin/ai-config", { values });
            setMsg(data?.message || "已保存");
            setValues({});
            await load();
        } catch (e) { setMsg(e?.response?.data?.detail || "保存失败"); } finally { setSaving(false); }
    };
    // 日报/周报推送排程
    const [sched, setSched] = useState(null);
    const loadSched = async () => { try { const { data } = await api.get("/admin/ai-config/report-schedule"); setSched(data?.data || data); } catch (e) { /* */ } };
    useEffect(() => { loadSched(); }, []);
    const saveSched = async (kind, patch) => {
        const cur = sched[kind];
        const body = { kind, enabled: patch.enabled ?? cur.enabled, hour: patch.hour ?? cur.cron.hour ?? 18, minute: patch.minute ?? cur.cron.minute ?? 30 };
        if (kind === "weekly") body.day_of_week = cur.cron.day_of_week || "fri";
        try { await api.put("/admin/ai-config/report-schedule", body); await loadSched(); setMsg("排程已更新"); }
        catch (e) { setMsg(e?.response?.data?.detail || "更新失败"); }
    };
    const pushNow = async (period) => {
        try { const { data } = await api.post(`/admin/ai-config/push-reports?period=${period}`); setMsg(data?.message || "已触发"); }
        catch (e) { setMsg("触发失败"); }
    };

    const [testModel, setTestModel] = useState("");
    const test = async () => {
        setTesting(true); setTestResult(null);
        try {
            const { data } = await api.post("/admin/ai-config/test", testModel ? { model: testModel } : {});
            setTestResult(data?.data || data);
        } catch (e) { setTestResult({ ok: false, sample: e?.response?.data?.detail || "连接失败" }); } finally { setTesting(false); }
    };

    if (loading) return <div className="p-6 text-sm text-muted-foreground">加载中…</div>;

    const MODEL_PRESETS = ["qwen3.7-plus", "qwen3-coder-plus", "glm-5", "gpt-4o", "kimi"];
    const groups = [];
    fields.forEach((f) => {
        const name = f.group || "通用";
        let g = groups.find((x) => x.name === name);
        if (!g) { g = { name, fields: [] }; groups.push(g); }
        g.fields.push(f);
    });

    return (
        <div className="p-6 max-w-2xl mx-auto space-y-4">
            <div>
                <h1 className="text-2xl font-bold">AI 接入配置</h1>
                <p className="text-sm text-muted-foreground">支持多厂商：默认模型的前缀决定路由（qwen*→阿里百炼 / glm*→智谱 / gpt*→OpenAI / kimi*→月之暗面）。留空的敏感字段表示不修改，保存后即时生效。</p>
            </div>
            {groups.map((g) => (
                <div key={g.name} className="rounded-lg border">
                    <div className="px-3 py-2 text-xs font-medium text-muted-foreground border-b bg-muted/30">{g.name}</div>
                    <div className="divide-y">
                        {g.fields.map((f) => (
                            <div key={f.key} className="p-3 flex items-center gap-3">
                                <div className="w-36 text-sm shrink-0">
                                    <div>{f.label}</div>
                                    <div className="text-[10px] text-muted-foreground">{f.source}</div>
                                </div>
                                <div className="flex-1">
                                    <input
                                        type={f.secret ? "password" : "text"}
                                        list={f.key === "AI_DEFAULT_MODEL" ? "ai-model-presets" : undefined}
                                        placeholder={f.secret && f.configured ? `已配置（${f.value}），留空不改` : f.placeholder}
                                        value={values[f.key] ?? (f.secret ? "" : (f.value || ""))}
                                        onChange={(e) => setValues({ ...values, [f.key]: e.target.value })}
                                        className="w-full border rounded px-3 py-1.5 text-sm bg-background"
                                    />
                                    {f.key === "AI_DEFAULT_MODEL" && (
                                        <div className="flex gap-1 mt-1 flex-wrap">
                                            {MODEL_PRESETS.map((m) => (
                                                <button key={m} type="button"
                                                    onClick={() => setValues({ ...values, AI_DEFAULT_MODEL: m })}
                                                    className="text-[10px] border rounded px-1.5 py-0.5 hover:bg-muted">
                                                    {m}
                                                </button>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
            <datalist id="ai-model-presets">
                {MODEL_PRESETS.map((m) => <option key={m} value={m} />)}
            </datalist>
            <div className="flex items-center gap-3 flex-wrap">
                <Button onClick={save} disabled={saving || Object.keys(values).length === 0}>{saving ? "保存中…" : "保存配置"}</Button>
                <select value={testModel} onChange={(e) => setTestModel(e.target.value)}
                    className="border rounded px-2 py-1.5 text-sm bg-background">
                    <option value="">测试当前默认模型</option>
                    {MODEL_PRESETS.map((m) => <option key={m} value={m}>测试 {m}</option>)}
                </select>
                <Button variant="outline" onClick={test} disabled={testing}>{testing ? "测试中…" : "🔌 测试连接"}</Button>
                {msg && <span className="text-sm text-emerald-600">{msg}</span>}
            </div>
            {testResult && (
                <div className={`rounded-lg border p-3 text-sm ${testResult.ok ? "border-emerald-500/40 bg-emerald-500/5" : "border-red-500/40 bg-red-500/5"}`}>
                    <div className="font-medium">{testResult.ok ? "✅ 连接正常" : "❌ 连接异常"}</div>
                    {testResult.model && <div className="text-xs">模型：{testResult.model} · 耗时 {testResult.latency_s}s</div>}
                    {testResult.sample && <div className="text-xs text-muted-foreground mt-1">返回：{testResult.sample}</div>}
                </div>
            )}

            {/* 日报/周报推送排程 */}
            {sched && (
                <div className="rounded-lg border p-4 space-y-3">
                    <div className="font-medium">📋 日报 / 周报自动推送</div>
                    {["daily", "weekly"].map((k) => {
                        const s = sched[k]; if (!s) return null;
                        return (
                            <div key={k} className="flex items-center gap-3 flex-wrap text-sm">
                                <label className="flex items-center gap-1 w-28">
                                    <input type="checkbox" checked={s.enabled} onChange={(e) => saveSched(k, { enabled: e.target.checked })} />
                                    {k === "daily" ? "日报(每天)" : "周报(每周五)"}
                                </label>
                                <span>时间</span>
                                <input type="number" min="0" max="23" value={s.cron.hour ?? 18}
                                    onChange={(e) => saveSched(k, { hour: Number(e.target.value) })}
                                    className="w-16 border rounded px-2 py-1 bg-background" /> 时
                                <input type="number" min="0" max="59" value={s.cron.minute ?? 30}
                                    onChange={(e) => saveSched(k, { minute: Number(e.target.value) })}
                                    className="w-16 border rounded px-2 py-1 bg-background" /> 分
                                <Button size="sm" variant="outline" onClick={() => pushNow(k === "daily" ? "day" : "week")}>立即推送</Button>
                            </div>
                        );
                    })}
                    <div className="text-xs text-muted-foreground">修改时间/开关即时保存并热生效（数据源：销售活动 + 任务进展，覆盖销售/PM/工程师；通道：系统站内+邮件+企微）。</div>
                </div>
            )}
        </div>
    );
}
