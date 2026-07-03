import { useState, useRef } from "react";
import api from "../services/api";
import { Button } from "../components/ui/button";

// 销售会议纪要 AI 解读：粘贴/上传纪要 → AI解读卡片 → 选择关联商机/项目 → 一键归档
export default function MeetingMinutesAI() {
    const [minutesText, setMinutesText] = useState("");
    const [customerId, setCustomerId] = useState("");
    const [parsing, setParsing] = useState(false);
    const [result, setResult] = useState(null); // job result
    const [selOpp, setSelOpp] = useState(null);
    const [selProj, setSelProj] = useState(null);
    const [jobId, setJobId] = useState(null);
    const [confirmRes, setConfirmRes] = useState(null);
    const [error, setError] = useState("");
    const fileRef = useRef(null);

    const poll = async (id) => {
        for (let i = 0; i < 40; i++) {
            await new Promise((r) => setTimeout(r, 2500));
            const { data } = await api.get(`/ai-jobs/${id}`);
            const d = data?.data || data;
            if (d.status === "SUCCESS") return d.result;
            if (d.status === "FAILED") throw new Error(d.error || "AI解读失败");
        }
        throw new Error("解读超时");
    };

    const start = async (submitFn) => {
        setError(""); setResult(null); setConfirmRes(null); setSelOpp(null); setSelProj(null);
        setParsing(true);
        try {
            const { data } = await submitFn();
            const id = (data?.data || data).job_id;
            setJobId(id);
            const res = await poll(id);
            setResult(res);
            // 默认选中首个候选
            const cand = res?.candidates || {};
            if (cand.opportunities?.[0]) setSelOpp(cand.opportunities[0].id);
            if (cand.projects?.[0]) setSelProj(cand.projects[0].id);
        } catch (e) {
            setError(e?.response?.data?.detail || e.message || "解读失败");
        } finally {
            setParsing(false);
        }
    };

    const handleParseText = () =>
        start(() =>
            api.post("/sales/activities/parse-minutes", {
                minutes_text: minutesText,
                customer_id: customerId ? Number(customerId) : null,
            })
        );

    const handleFile = (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const fd = new FormData();
        fd.append("file", file);
        if (customerId) fd.append("customer_id", customerId);
        start(() =>
            api.post("/sales/activities/parse-minutes-file", fd, {
                headers: { "Content-Type": "multipart/form-data" },
            })
        );
    };

    const handleConfirm = async () => {
        setError("");
        try {
            const { data } = await api.post("/sales/activities/confirm-minutes", {
                job_id: jobId,
                customer_id: customerId ? Number(customerId) : null,
                opportunity_id: selOpp,
                project_id: selProj,
            });
            setConfirmRes(data?.data || data);
        } catch (e) {
            setError(e?.response?.data?.detail || e.message || "归档失败");
        }
    };

    const s = result?.structured || {};
    const cl = s.next_meeting_checklist || {};
    const cand = result?.candidates || {};

    const Chip = ({ children }) => (
        <span className="inline-block rounded bg-muted px-2 py-0.5 text-xs mr-1 mb-1">{children}</span>
    );
    const List = ({ title, items, color }) => (
        <div className="mb-2">
            <div className={`text-sm font-medium ${color || ""}`}>{title}</div>
            <ul className="list-disc list-inside text-sm text-muted-foreground">
                {(items || []).map((x, i) => <li key={i}>{x}</li>)}
                {(!items || items.length === 0) && <li className="list-none text-xs">—</li>}
            </ul>
        </div>
    );

    return (
        <div className="p-6 max-w-5xl mx-auto space-y-4">
            <div>
                <h1 className="text-2xl font-bold">会议纪要 AI 解读</h1>
                <p className="text-sm text-muted-foreground">
                    粘贴或上传销售会议纪要，AI 自动抽取要点、生成下次会议信息清单，并关联商机/项目一键归档。
                </p>
            </div>

            {/* 输入区 */}
            <div className="rounded-lg border p-4 space-y-3">
                <div className="flex gap-3 items-center">
                    <input
                        className="border rounded px-3 py-1.5 text-sm w-48 bg-background"
                        placeholder="客户ID(可选)"
                        value={customerId}
                        onChange={(e) => setCustomerId(e.target.value)}
                    />
                    <input ref={fileRef} type="file" accept=".txt,.md,.docx" className="hidden" onChange={handleFile} />
                    <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()} disabled={parsing}>
                        上传文件(.txt/.docx)
                    </Button>
                </div>
                <textarea
                    className="w-full h-40 border rounded p-3 text-sm bg-background"
                    placeholder="在此粘贴会议纪要文本…"
                    value={minutesText}
                    onChange={(e) => setMinutesText(e.target.value)}
                />
                <Button onClick={handleParseText} disabled={parsing || minutesText.trim().length < 10}>
                    {parsing ? "AI 解读中…" : "AI 解读"}
                </Button>
                {error && <p className="text-sm text-red-500">{error}</p>}
            </div>

            {/* 解读结果卡片 */}
            {result && (
                <div className="rounded-lg border p-4 space-y-4">
                    <div>
                        <div className="text-lg font-semibold">{s.topic || "会议解读"}</div>
                        <p className="text-sm text-muted-foreground mt-1">{s.summary}</p>
                        <div className="mt-2">
                            {(s.participants || []).map((p, i) => <Chip key={i}>{p}</Chip>)}
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <List title="关键诉求" items={s.key_demands} />
                        <List title="竞品" items={s.competitors} color="text-orange-500" />
                        <List title="下一步行动" items={s.next_actions} />
                        <List title="我方承诺" items={s.commitments} />
                    </div>
                    <div className="text-sm"><b>预算：</b>{s.budget || "—"} &nbsp; <b>重要度：</b>{s.importance || "—"}</div>

                    {/* 下次会议信息清单(非标核心) */}
                    <div className="rounded bg-amber-500/5 border border-amber-500/20 p-3">
                        <div className="font-medium text-amber-600 mb-2">📋 下次会议信息清单（避免技术需求不清晰）</div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <List title="需获取" items={cl.to_obtain} color="text-blue-500" />
                            <List title="需确认" items={cl.to_confirm} color="text-green-600" />
                            <List title="技术需求盲点" items={cl.technical_gaps} color="text-red-500" />
                        </div>
                    </div>

                    {/* 关联选择 */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <div className="text-sm font-medium mb-1">关联商机</div>
                            {(cand.opportunities || []).map((o) => (
                                <label key={o.id} className="flex items-center gap-2 text-sm py-0.5">
                                    <input type="radio" name="opp" checked={selOpp === o.id} onChange={() => setSelOpp(o.id)} />
                                    {o.opp_name} <span className="text-xs text-muted-foreground">({o.stage})</span>
                                </label>
                            ))}
                            {(!cand.opportunities || cand.opportunities.length === 0) && <p className="text-xs text-muted-foreground">无候选商机</p>}
                        </div>
                        <div>
                            <div className="text-sm font-medium mb-1">关联项目</div>
                            {(cand.projects || []).map((p) => (
                                <label key={p.id} className="flex items-center gap-2 text-sm py-0.5">
                                    <input type="radio" name="proj" checked={selProj === p.id} onChange={() => setSelProj(p.id)} />
                                    {p.project_name} <span className="text-xs text-muted-foreground">{p.project_code}</span>
                                </label>
                            ))}
                            {(!cand.projects || cand.projects.length === 0) && <p className="text-xs text-muted-foreground">无候选项目</p>}
                        </div>
                    </div>

                    <Button onClick={handleConfirm} disabled={!!confirmRes}>一键归档并派生任务</Button>

                    {confirmRes && (
                        <div className="rounded bg-green-500/10 border border-green-500/20 p-3 text-sm">
                            ✅ {confirmRes.message}<br />
                            沟通记录：{confirmRes.communication_no}
                            {confirmRes.linked_project && <> · 已关联项目「{confirmRes.linked_project}」</>}
                            {confirmRes.derived && (
                                <> · 自动派生任务 {confirmRes.derived.created_tasks} 条
                                    {confirmRes.derived.backfilled_opportunity && "、已回填商机需求/预算/成熟度"}</>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
