import { useState, useEffect } from "react";
import api from "../services/api";
import { Button } from "../components/ui/button";

// M2 标准模块库：AI 从历史 BOM 挖出的可复用模块
export default function ModuleLibrary() {
    const [mods, setMods] = useState([]);
    const [loading, setLoading] = useState(true);
    const [mining, setMining] = useState(false);
    const load = async () => {
        try { const { data } = await api.get("/ai-modules"); setMods((data?.data || data)?.modules || []); }
        catch (e) { /* ignore */ } finally { setLoading(false); }
    };
    useEffect(() => { load(); }, []);
    const mine = async () => {
        setMining(true);
        try { const { data } = await api.post("/ai-modules/extract"); alert((data?.data ? `AI 挖出 ${data.message || ""}` : "完成")); await load(); }
        catch (e) { alert("挖掘失败"); } finally { setMining(false); }
    };
    return (
        <div className="p-6 max-w-6xl mx-auto space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">标准模块库</h1>
                    <p className="text-sm text-muted-foreground">AI 从历史 BOM 挖出的可复用模块，支撑配置式设计与模块级报价</p>
                </div>
                <Button size="sm" onClick={mine} disabled={mining}>{mining ? "AI 挖掘中…" : "✨ AI 从BOM挖模块"}</Button>
            </div>
            {loading && <div className="text-sm text-muted-foreground">加载中…</div>}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {mods.map((m) => (
                    <div key={m.id} className="rounded-lg border p-3">
                        <div className="flex items-center justify-between">
                            <span className="font-medium">{m.module_name}</span>
                            <span className="text-xs rounded bg-muted px-2 py-0.5">{m.category}</span>
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">{m.description}</div>
                        <div className="text-sm mt-2">参考成本 <b className="text-emerald-600">¥{m.ref_cost}</b> · {m.components?.length || 0} 组件 · 出现{m.source_count}次</div>
                    </div>
                ))}
                {!loading && mods.length === 0 && (
                    <div className="text-sm text-muted-foreground">模块库为空，点右上角「AI 从BOM挖模块」生成。</div>
                )}
            </div>
        </div>
    );
}
