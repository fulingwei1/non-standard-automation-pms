import React, { useState, useEffect, useCallback } from "react";
import { AlertTriangle, Search, RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent } from "../../components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { warehouseApi } from "../../services/api";

export default function StockAlerts() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({ items: [], total: 0 });
  const [summary, setSummary] = useState({ low_stock_count: 0, overstock_count: 0, total_alerts: 0 });
  const [keyword, setKeyword] = useState("");
  const [alertType, setAlertType] = useState("all");
  const [page, setPage] = useState(1);

  useEffect(() => { warehouseApi.alerts.summary().then((r) => setSummary(r.data || r)).catch(() => {}); }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 20 };
      if (alertType && alertType !== "all") params.alert_type = alertType;
      if (keyword) params.keyword = keyword;
      const res = await warehouseApi.alerts.list(params);
      setData(res.data || res);
    } catch (_e) { console.error(_e); } finally { setLoading(false); }
  }, [page, alertType, keyword]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="库存预警" subtitle={`共 ${summary.total_alerts} 条预警`} icon={<AlertTriangle className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card><CardContent className="pt-6 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-red-400/10"><TrendingDown className="h-6 w-6 text-red-400" /></div>
            <div><p className="text-2xl font-bold">{summary.low_stock_count}</p><p className="text-sm text-text-muted">低库存预警</p></div>
          </CardContent></Card>
          <Card><CardContent className="pt-6 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-yellow-400/10"><TrendingUp className="h-6 w-6 text-yellow-400" /></div>
            <div><p className="text-2xl font-bold">{summary.overstock_count}</p><p className="text-sm text-text-muted">超储预警</p></div>
          </CardContent></Card>
          <Card><CardContent className="pt-6 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-orange-400/10"><AlertTriangle className="h-6 w-6 text-orange-400" /></div>
            <div><p className="text-2xl font-bold">{summary.total_alerts}</p><p className="text-sm text-text-muted">总预警数</p></div>
          </CardContent></Card>
        </div>
        <div className="flex gap-3 items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input placeholder="搜索物料..." value={keyword} onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchData()} className="pl-9" />
          </div>
          <Select value={alertType} onValueChange={(v) => { setAlertType(v); setPage(1); }}>
            <SelectTrigger className="w-36"><SelectValue placeholder="全部类型" /></SelectTrigger>
            <SelectContent><SelectItem value="all">全部</SelectItem><SelectItem value="LOW">低库存</SelectItem><SelectItem value="OVERSTOCK">超储</SelectItem></SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={fetchData}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /></Button>
        </div>
        <div className="bg-surface-200 rounded-xl border border-white/5 overflow-hidden">
          <Table><TableHeader><TableRow>
            <TableHead>类型</TableHead><TableHead>物料编码</TableHead><TableHead>物料名称</TableHead><TableHead>规格</TableHead>
            <TableHead className="text-right">当前库存</TableHead><TableHead className="text-right">可用</TableHead>
            <TableHead className="text-right">安全库存</TableHead><TableHead className="text-right">缺口/超储</TableHead>
          </TableRow></TableHeader><TableBody>
            {loading ? <TableRow><TableCell colSpan={8} className="text-center py-8 text-text-muted">加载中...</TableCell></TableRow>
            : data.items?.length === 0 ? <TableRow><TableCell colSpan={8} className="text-center py-8 text-text-muted">暂无预警 🎉</TableCell></TableRow>
            : (data.items || []).map((row, idx) => (
              <TableRow key={idx}>
                <TableCell><Badge variant="outline" className={row.alert_type === "LOW" ? "text-red-400 bg-red-400/10" : "text-yellow-400 bg-yellow-400/10"}>{row.alert_type === "LOW" ? "低库存" : "超储"}</Badge></TableCell>
                <TableCell className="font-mono text-sm">{row.material_code}</TableCell>
                <TableCell>{row.material_name || "-"}</TableCell>
                <TableCell className="text-text-muted text-sm">{row.specification || "-"}</TableCell>
                <TableCell className="text-right">{row.quantity}</TableCell>
                <TableCell className="text-right">{row.available_quantity}</TableCell>
                <TableCell className="text-right text-text-muted">{row.min_stock}</TableCell>
                <TableCell className={`text-right font-medium ${row.alert_type === "LOW" ? "text-red-400" : "text-yellow-400"}`}>{row.shortage}</TableCell>
              </TableRow>
            ))}
          </TableBody></Table>
        </div>
      </main>
    </div>
  );
}
