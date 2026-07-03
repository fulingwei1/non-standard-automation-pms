import { useState, useEffect } from "react";
import api from "../../services/api";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";

// 回款风险 + 催收
export default function ReceivableRiskCard() {
    const [d, setD] = useState(null);
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        (async () => {
            try { const { data } = await api.get("/ai-more/receivable-risk"); setD(data?.data || data); }
            catch (e) { /* ignore */ } finally { setLoading(false); }
        })();
    }, []);
    const wan = (n) => (n / 10000).toFixed(0);
    return (
        <Card>
            <CardHeader><CardTitle>💰 回款风险预警</CardTitle></CardHeader>
            <CardContent>
                {loading && <div className="text-sm text-muted-foreground">加载中…</div>}
                {!loading && (
                    <>
                        <div className="text-sm mb-2">未回款合同 <b>{d?.count || 0}</b> 个，合计 <b className="text-red-500">¥{wan(d?.total_unreceived || 0)}万</b></div>
                        {d?.strategy && <div className="text-xs text-muted-foreground mb-2">{d.strategy}</div>}
                        <div className="space-y-1">
                            {(d?.items || []).slice(0, 6).map((x, i) => (
                                <div key={i} className="text-xs flex justify-between border-l-2 border-red-500/40 pl-2">
                                    <span className="truncate">{x.customer}</span>
                                    <span className="shrink-0">未回¥{wan(x.unreceived)}万（已回{x.collection_rate}%）</span>
                                </div>
                            ))}
                        </div>
                    </>
                )}
            </CardContent>
        </Card>
    );
}
