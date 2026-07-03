import { useState, useEffect } from "react";
import api from "../../services/api";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";

// B7 AI 经营分析（管理层）：内部数据市场自我诊断
export default function BusinessAnalysisCard() {
    const [d, setD] = useState(null);
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        (async () => {
            try { const { data } = await api.get("/sales/ai-business-analysis"); setD(data?.data || data); }
            catch (e) { /* ignore */ } finally { setLoading(false); }
        })();
    }, []);
    const m = d?.metrics || {}, a = d?.analysis || {};
    return (
        <Card>
            <CardHeader><CardTitle>✨ AI 经营分析</CardTitle></CardHeader>
            <CardContent>
                {loading && <div className="text-sm text-muted-foreground">AI 分析中…</div>}
                {!loading && (
                    <>
                        {a.headline && <div className="mb-2 rounded bg-primary/5 border border-primary/20 p-2 text-sm">{a.headline}</div>}
                        <div className="grid grid-cols-3 gap-2 mb-3 text-center text-xs">
                            <div className="rounded border p-2"><div className="text-lg font-bold">{m.win_rate}%</div>赢单率</div>
                            <div className="rounded border p-2"><div className="text-lg font-bold">{m.avg_gross_margin}%</div>平均毛利</div>
                            <div className="rounded border p-2"><div className="text-lg font-bold text-amber-600">{m.low_margin_quotes}</div>低毛利报价</div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            <div><div className="font-medium text-emerald-600 mb-1">优势</div>
                                <ul className="list-disc list-inside text-muted-foreground">{(a.strengths || []).map((x, i) => <li key={i}>{x}</li>)}</ul></div>
                            <div><div className="font-medium text-red-500 mb-1">风险</div>
                                <ul className="list-disc list-inside text-muted-foreground">{(a.risks || []).map((x, i) => <li key={i}>{x}</li>)}</ul></div>
                        </div>
                        {(a.suggestions || []).length > 0 && (
                            <div className="mt-2 text-xs"><span className="font-medium">建议：</span>{(a.suggestions || []).join("；")}</div>
                        )}
                    </>
                )}
            </CardContent>
        </Card>
    );
}
