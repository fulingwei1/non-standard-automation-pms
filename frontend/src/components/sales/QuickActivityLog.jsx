import { useState, useEffect, useCallback } from "react";
import api from "../../services/api";
import { Button } from "../ui/button";

// 快速记录销售活动 + 活动时间线（自动按 ID 挂客户/商机）
const TYPES = [
    { v: "CALL", l: "电话" }, { v: "VISIT", l: "拜访" }, { v: "MEETING", l: "会议" },
    { v: "EMAIL", l: "邮件" }, { v: "WECHAT", l: "微信" }, { v: "OTHER", l: "其他" },
];
const TYPE_LABEL = Object.fromEntries(TYPES.map(t => [t.v, t.l]));

export default function QuickActivityLog({ customerId, opportunityId, leadId, projectId }) {
    const [type, setType] = useState("VISIT");
    const [content, setContent] = useState("");
    const [followUp, setFollowUp] = useState("");
    const [saving, setSaving] = useState(false);
    const [items, setItems] = useState([]);
    const [err, setErr] = useState("");
    // AI 智能记录
    const [aiNote, setAiNote] = useState("");
    const [aiSaving, setAiSaving] = useState(false);
    const [showManual, setShowManual] = useState(false);

    const load = useCallback(async () => {
        try {
            let url = null;
            if (opportunityId) url = `/sales/activities/by-opportunity/${opportunityId}`;
            else if (customerId) url = `/sales/activities/by-customer/${customerId}`;
            if (!url) return;
            const { data } = await api.get(url);
            setItems((data?.data || data)?.activities || []);
        } catch (e) { /* ignore */ }
    }, [opportunityId, customerId]);

    useEffect(() => { load(); }, [load]);

    const submit = async () => {
        if (content.trim().length < 1) return;
        setSaving(true); setErr("");
        try {
            await api.post("/sales/activities/quick", {
                activity_type: type, content, follow_up_task: followUp || null,
                customer_id: customerId || null, opportunity_id: opportunityId || null,
                lead_id: leadId || null, project_id: projectId || null,
            });
            setContent(""); setFollowUp("");
            await load();
        } catch (e) {
            setErr(e?.response?.data?.detail || "记录失败");
        } finally { setSaving(false); }
    };

    const submitAI = async () => {
        if (aiNote.trim().length < 1) return;
        setAiSaving(true); setErr("");
        try {
            await api.post("/sales/activities/quick-ai", {
                raw_text: aiNote,
                customer_id: customerId || null, opportunity_id: opportunityId || null,
                lead_id: leadId || null, project_id: projectId || null,
            });
            setAiNote("");
            await load();
        } catch (e) {
            setErr(e?.response?.data?.detail || "AI记录失败");
        } finally { setAiSaving(false); }
    };

    return (
        <div className="space-y-4">
            {/* AI 智能记录（主）：写一句话，AI自动判类型/主题/跟进+挂客户商机 */}
            <div className="rounded-lg border p-3 space-y-2 bg-primary/5">
                <div className="flex items-center gap-2 text-sm font-medium">
                    ✨ AI 智能记录 <span className="text-xs text-muted-foreground font-normal">随手写一句，AI 帮你整理归档（客户/商机自动带）</span>
                </div>
                <textarea value={aiNote} onChange={e => setAiNote(e.target.value)}
                    className="w-full h-16 border rounded p-2 text-sm bg-background"
                    placeholder="例：刚跟客户王工电话，确认下周三现场演示，要带FCT测试样机…" />
                <div className="flex items-center gap-2">
                    <Button size="sm" onClick={submitAI} disabled={aiSaving || aiNote.trim().length < 1}>
                        {aiSaving ? "AI 整理中…" : "AI 记录"}
                    </Button>
                    <button className="text-xs text-muted-foreground underline" onClick={() => setShowManual(v => !v)}>
                        {showManual ? "收起手动录入" : "手动录入"}
                    </button>
                    {err && <span className="text-xs text-red-500">{err}</span>}
                </div>
            </div>

            {/* 手动录入（备选） */}
            {showManual && (
            <div className="rounded-lg border p-3 space-y-2">
                <div className="flex items-center gap-2">
                    <select value={type} onChange={e => setType(e.target.value)}
                        className="border rounded px-2 py-1.5 text-sm bg-background">
                        {TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
                    </select>
                    <span className="text-xs text-muted-foreground">手动记一条</span>
                </div>
                <textarea value={content} onChange={e => setContent(e.target.value)}
                    className="w-full h-16 border rounded p-2 text-sm bg-background"
                    placeholder="活动内容（客户说了什么、进展、结论…）" />
                <input value={followUp} onChange={e => setFollowUp(e.target.value)}
                    className="w-full border rounded px-2 py-1.5 text-sm bg-background"
                    placeholder="跟进任务（可选）" />
                <Button size="sm" variant="outline" onClick={submit} disabled={saving || content.trim().length < 1}>
                    {saving ? "记录中…" : "记录"}
                </Button>
            </div>
            )}

            {/* 时间线 */}
            <div>
                <div className="text-sm font-medium mb-2">活动时间线（{items.length}）</div>
                <div className="space-y-2">
                    {items.map(a => (
                        <div key={a.id} className="border-l-2 border-primary/40 pl-3 py-1">
                            <div className="text-xs text-muted-foreground">
                                {a.date} · {TYPE_LABEL[a.type] || a.type} · {a.topic}
                            </div>
                            <div className="text-sm">{a.summary}</div>
                            {a.follow_up && <div className="text-xs text-amber-600">跟进：{a.follow_up}</div>}
                        </div>
                    ))}
                    {items.length === 0 && <div className="text-xs text-muted-foreground">暂无活动记录</div>}
                </div>
            </div>
        </div>
    );
}
