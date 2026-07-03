import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../services/api";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";

// AI 经营简报：主动扫描需关注的异常 + 今日重点（数据主动找人）
const SEV = { high: "text-red-500 border-red-500/30 bg-red-500/5", medium: "text-amber-600 border-amber-500/30 bg-amber-500/5" };

export default function SalesBriefing() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const nav = useNavigate();

    useEffect(() => {
        (async () => {
            try {
                const { data: d } = await api.get("/sales/ai-briefing");
                setData(d?.data || d);
            } catch (e) { /* ignore */ } finally { setLoading(false); }
        })();
    }, []);

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">✨ AI 经营简报</CardTitle>
            </CardHeader>
            <CardContent>
                {loading && <div className="text-sm text-muted-foreground">AI 扫描中…</div>}
                {!loading && data?.summary && (
                    <div className="mb-3 rounded bg-primary/5 border border-primary/20 p-2 text-sm">
                        今日重点：{data.summary}
                    </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {(data?.alerts || []).map((a, i) => (
                        <div key={i} className={`rounded border p-3 ${SEV[a.severity] || ""}`}>
                            <div className="flex items-center justify-between">
                                <span className="font-medium">{a.type}</span>
                                <span className="text-lg font-bold">{a.count}</span>
                            </div>
                            <div className="text-xs text-muted-foreground mb-1">建议：{a.action}</div>
                            <div className="space-y-0.5">
                                {(a.items || []).slice(0, 3).map((it, j) => (
                                    <div key={j}
                                        className="text-xs truncate cursor-pointer hover:underline"
                                        onClick={() => it.opportunity_id && nav(`/sales/opportunities/${it.opportunity_id}`)}>
                                        · {it.name || it.opportunity_id || it.quote_id}
                                        {it.gross_margin != null && ` (毛利${it.gross_margin}%)`}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                    {!loading && (data?.alerts || []).length === 0 && (
                        <div className="text-sm text-muted-foreground">暂无需关注的异常 👍</div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
