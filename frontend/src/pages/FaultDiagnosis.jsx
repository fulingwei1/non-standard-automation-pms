import { useState } from "react";
import api from "../services/api";
import { Button } from "../components/ui/button";

// B4 售后 AI 故障诊断
const EQUIP = ["视觉检测", "ICT测试", "FCT测试", "上下料", "运动控制", "其他"];

export default function FaultDiagnosis() {
    const [symptom, setSymptom] = useState("");
    const [equip, setEquip] = useState("视觉检测");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const submit = async () => {
        if (symptom.trim().length < 2) return;
        setLoading(true); setResult(null);
        try {
            const { data } = await api.post("/ai-eng/fault-diagnosis", { symptom, equipment_type: equip });
            setResult(data?.data || data);
        } catch (e) { alert(e?.response?.data?.detail || "诊断失败"); } finally { setLoading(false); }
    };
    return (
        <div className="p-6 max-w-4xl mx-auto space-y-4">
            <div>
                <h1 className="text-2xl font-bold">AI 故障诊断</h1>
                <p className="text-sm text-muted-foreground">描述现场故障现象，AI 给出可能原因与排查步骤（把老师傅经验变成可问的助手）</p>
            </div>
            <div className="rounded-lg border p-4 space-y-3">
                <select value={equip} onChange={(e) => setEquip(e.target.value)} className="border rounded px-3 py-1.5 text-sm bg-background">
                    {EQUIP.map((x) => <option key={x} value={x}>{x}</option>)}
                </select>
                <textarea value={symptom} onChange={(e) => setSymptom(e.target.value)}
                    className="w-full h-24 border rounded p-3 text-sm bg-background"
                    placeholder="例：视觉检测经常误判，合格品被判NG / 设备频繁报通讯超时 / 上料机构卡料…" />
                <Button onClick={submit} disabled={loading || symptom.trim().length < 2}>{loading ? "AI 诊断中…" : "AI 诊断"}</Button>
            </div>
            {result && (
                <div className="rounded-lg border p-4 space-y-3 text-sm">
                    {result.degraded && (
                        <div className="rounded border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                            AI 诊断暂不可用，当前展示规则降级建议。
                        </div>
                    )}
                    {result.context_sources && (
                        <div className="text-xs text-muted-foreground">
                            已参考历史工单 {result.context_sources.service_tickets || 0} 条，服务知识库 {result.context_sources.knowledge_base || 0} 条
                        </div>
                    )}
                    <div>
                        <div className="font-medium mb-1">可能原因</div>
                        {(result.possible_causes || []).map((c, i) => (
                            <div key={i} className="text-xs mb-1">
                                <span className={c.likelihood === "高" ? "text-red-500 font-medium" : "text-amber-600"}>[{c.likelihood}]</span> {c.cause}
                                <div className="text-muted-foreground">排查：{c.check}</div>
                            </div>
                        ))}
                    </div>
                    <div>
                        <div className="font-medium mb-1">处理步骤</div>
                        <ol className="list-decimal list-inside text-xs text-muted-foreground">
                            {(result.steps || []).map((s, i) => <li key={i}>{s}</li>)}
                        </ol>
                    </div>
                    {result.safety && <div className="text-xs text-red-500">⚠️ 安全：{result.safety}</div>}
                </div>
            )}
        </div>
    );
}
