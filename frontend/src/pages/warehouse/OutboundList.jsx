import React, { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowUpFromLine, Plus, Search, Eye, RefreshCw, AlertTriangle } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Badge } from "../../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { warehouseApi } from "../../services/api";
import { formatDate } from "../../lib/utils";

const STATUS_MAP = {
  DRAFT: { label: "草稿", color: "bg-gray-500" }, PENDING: { label: "待出库", color: "bg-yellow-500" },
  PICKING: { label: "拣货中", color: "bg-blue-500" }, COMPLETED: { label: "已完成", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-red-500" },
};
const TYPE_MAP = { PRODUCTION: "生产领料", SALES: "销售出库", TRANSFER: "调拨出库", SCRAP: "报废出库", OTHER: "其他出库" };

export default function OutboundList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({ items: [], total: 0 });
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState(searchParams.get("status") || "all");
  const [page, setPage] = useState(1);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 20 };
      if (statusFilter && statusFilter !== "all") params.status = statusFilter;
      if (keyword) params.keyword = keyword;
      const res = await warehouseApi.outbound.list(params);
      setData(res.data || res);
    } catch (_e) { console.error(_e); } finally { setLoading(false); }
  }, [page, statusFilter, keyword]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="出库管理" subtitle={`共 ${data.total} 条`} icon={<ArrowUpFromLine className="h-6 w-6" />}
        actions={<Button onClick={() => navigate("/warehouse/outbound/new")} className="gap-2"><Plus className="h-4 w-4" /> 新建出库单</Button>} />
      <main className="container mx-auto px-4 py-6 space-y-4">
        <div className="flex gap-3 items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input placeholder="搜索单号/目标单号/部门..." value={keyword} onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchData()} className="pl-9" />
          </div>
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-36"><SelectValue placeholder="全部状态" /></SelectTrigger>
            <SelectContent><SelectItem value="all">全部状态</SelectItem>
              {Object.entries(STATUS_MAP).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}</SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={fetchData}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /></Button>
        </div>
        <div className="bg-surface-200 rounded-xl border border-white/5 overflow-hidden">
          <Table><TableHeader><TableRow>
            <TableHead>出库单号</TableHead><TableHead>类型</TableHead><TableHead>部门</TableHead>
            <TableHead>目标单号</TableHead><TableHead>计划日期</TableHead><TableHead>数量</TableHead>
            <TableHead>状态</TableHead><TableHead className="text-right">操作</TableHead>
          </TableRow></TableHeader><TableBody>
            {loading ? <TableRow><TableCell colSpan={8} className="text-center py-8 text-text-muted">加载中...</TableCell></TableRow>
            : data.items?.length === 0 ? <TableRow><TableCell colSpan={8} className="text-center py-8 text-text-muted">暂无数据</TableCell></TableRow>
            : (data.items || []).map((row) => (
              <TableRow key={row.id} className="cursor-pointer hover:bg-surface-300/50" onClick={() => navigate(`/warehouse/outbound/${row.id}`)}>
                <TableCell className="font-mono text-sm">{row.order_no}{row.is_urgent && <AlertTriangle className="inline ml-1 h-3 w-3 text-red-400" />}</TableCell>
                <TableCell>{TYPE_MAP[row.order_type] || row.order_type}</TableCell>
                <TableCell>{row.department || "-"}</TableCell><TableCell>{row.target_no || "-"}</TableCell>
                <TableCell>{row.planned_date ? formatDate(row.planned_date) : "-"}</TableCell>
                <TableCell>{row.picked_quantity}/{row.total_quantity}</TableCell>
                <TableCell><Badge variant="outline" className={`${STATUS_MAP[row.status]?.color || ""} text-white text-xs`}>{STATUS_MAP[row.status]?.label || row.status}</Badge></TableCell>
                <TableCell className="text-right"><Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); navigate(`/warehouse/outbound/${row.id}`); }}><Eye className="h-4 w-4" /></Button></TableCell>
              </TableRow>
            ))}
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
