import React, { useState, useEffect, useCallback } from "react";
import { Package, Search, RefreshCw, AlertTriangle } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { warehouseApi } from "../../services/api";

export default function InventoryList() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({ items: [], total: 0 });
  const [keyword, setKeyword] = useState("");
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [warehouses, setWarehouses] = useState([]);
  const [warehouseId, setWarehouseId] = useState("all");
  const [page, setPage] = useState(1);

  useEffect(() => { warehouseApi.warehouses().then((r) => setWarehouses(r.data?.items || r.data || [])).catch(() => {}); }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 20 };
      if (warehouseId && warehouseId !== "all") params.warehouse_id = parseInt(warehouseId);
      if (keyword) params.keyword = keyword;
      if (lowStockOnly) params.low_stock = true;
      const res = await warehouseApi.inventory.list(params);
      setData(res.data || res);
    } catch (_e) { console.error(_e); } finally { setLoading(false); }
  }, [page, warehouseId, keyword, lowStockOnly]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const getStatus = (r) => {
    if (r.min_stock > 0 && r.available_quantity <= r.min_stock) return { label: "低库存", color: "text-red-400 bg-red-400/10" };
    if (r.max_stock > 0 && r.quantity > r.max_stock) return { label: "超储", color: "text-yellow-400 bg-yellow-400/10" };
    return { label: "正常", color: "text-green-400 bg-green-400/10" };
  };

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="库存管理" subtitle={`共 ${data.total} 种物料`} icon={<Package className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6 space-y-4">
        <div className="flex gap-3 items-center flex-wrap">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input placeholder="搜索物料编码/名称..." value={keyword} onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchData()} className="pl-9" />
          </div>
          <Select value={warehouseId} onValueChange={(v) => { setWarehouseId(v); setPage(1); }}>
            <SelectTrigger className="w-40"><SelectValue placeholder="全部仓库" /></SelectTrigger>
            <SelectContent><SelectItem value="all">全部仓库</SelectItem>
              {warehouses.map((w) => <SelectItem key={w.id} value={w.id.toString()}>{w.warehouse_name}</SelectItem>)}</SelectContent>
          </Select>
          <Button variant={lowStockOnly ? "default" : "outline"} size="sm" onClick={() => { setLowStockOnly(!lowStockOnly); setPage(1); }} className="gap-1">
            <AlertTriangle className="h-4 w-4" /> 仅低库存
          </Button>
          <Button variant="outline" size="icon" onClick={fetchData}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /></Button>
        </div>
        <div className="bg-surface-200 rounded-xl border border-white/5 overflow-hidden">
          <Table><TableHeader><TableRow>
            <TableHead>物料编码</TableHead><TableHead>物料名称</TableHead><TableHead>规格</TableHead><TableHead>单位</TableHead>
            <TableHead className="text-right">库存</TableHead><TableHead className="text-right">预留</TableHead>
            <TableHead className="text-right">可用</TableHead><TableHead className="text-right">安全库存</TableHead>
            <TableHead>状态</TableHead><TableHead>批次号</TableHead>
          </TableRow></TableHeader><TableBody>
            {loading ? <TableRow><TableCell colSpan={10} className="text-center py-8 text-text-muted">加载中...</TableCell></TableRow>
            : data.items.length === 0 ? <TableRow><TableCell colSpan={10} className="text-center py-8 text-text-muted">暂无数据</TableCell></TableRow>
            : data.items.map((row) => {
              const s = getStatus(row);
              return (<TableRow key={row.id}>
                <TableCell className="font-mono text-sm">{row.material_code}</TableCell>
                <TableCell>{row.material_name || "-"}</TableCell>
                <TableCell className="text-text-muted text-sm">{row.specification || "-"}</TableCell>
                <TableCell>{row.unit}</TableCell>
                <TableCell className="text-right font-medium">{row.quantity}</TableCell>
                <TableCell className="text-right">{row.reserved_quantity}</TableCell>
                <TableCell className="text-right font-medium">{row.available_quantity}</TableCell>
                <TableCell className="text-right text-text-muted">{row.min_stock}</TableCell>
                <TableCell><Badge variant="outline" className={`${s.color} text-xs`}>{s.label}</Badge></TableCell>
                <TableCell className="text-text-muted text-sm">{row.batch_no || "-"}</TableCell>
              </TableRow>);
            })}
          </TableBody></Table>
        </div>
        {data.total > 20 && <div className="flex justify-between items-center text-sm text-text-muted">
          <span>共 {data.total} 条</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>上一页</Button>
            <Button variant="outline" size="sm" disabled={page * 20 >= data.total} onClick={() => setPage(page + 1)}>下一页</Button>
          </div>
        </div>}
      </main>
    </div>
  );
}
