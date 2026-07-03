import { useState, useEffect } from "react";
import api from "../../services/api";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";

// B3 交付风险预警
export default function DeliveryRiskCard() {
    const [d, setD] = useState(null);
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        (async () => {
            try { const { data } = await api.get("/ai-delivery/risk"); setD(data?.data || data); }
            catch (e) { /* ignore */ } finally { setLoading(false); }
        })();
    }, []);
    return (
        <Card>
            <CardHeader><CardTitle>⚠️ AI 交付风险预警</CardTitle></CardHeader>
            <CardContent>
                {loading && <div className="text-sm text-muted-foreground">AI 扫描中…</div>}
                {!loading && (
                    <>
                        {d?.summary && <div className="mb-2 rounded bg-red-500/5 border border-red-500/20 p-2 text-sm">{d.summary}</div>}
                        <div className="text-xs text-muted-foreground mb-2">共 {d?.total || 0} 个风险项目，高风险 {d?.high_risk || 0} 个</div>
                        <div className="space-y-1">
                            {(d?.risks || []).slice(0, 8).map((r, i) => (
                                <div key={i} className="text-xs flex justify-between border-l-2 border-red-500/40 pl-2">
                                    <span className="truncate">{r.name}（进度{r.progress}%）</span>
                                    <span className="text-red-500 shrink-0">{(r.reasons || []).join("/")}</span>
                                </div>
                            ))}
                            {(d?.risks || []).length === 0 && <div className="text-xs text-muted-foreground">暂无交付风险 👍</div>}
                        </div>
                    </>
                )}
            </CardContent>
        </Card>
    );
}
