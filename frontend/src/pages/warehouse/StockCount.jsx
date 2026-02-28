import React, { useState, useEffect, useCallback } from "react";
import { ClipboardCheck, Plus, Eye, RefreshCw, Play } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Badge } from "../../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import { warehouseApi } from "../../services/api";
import { formatDate } from "../../lib/utils";
import { toast } from "../../components/ui/toast";

const STATUS_MAP = { DRAFT: { label: "草稿", color: "bg-gray-500" }, IN_PROGRESS: { label: "盘点中", color: "bg-blue-500" }, COMPLETED: { label: "已完成", color: "bg-green-500" }, CANCELLED: { label: "已取消", color: "bg-red-500" } };
const COUNT_TYPES = [{ value: "FULL", label: "全盘" }, { value: "PARTIAL", label: "抽盘" }, { value: "CYCLE", label: "循环盘点" }];

export default function StockCount() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({ items: [], total: 0 });
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [createForm, setCreateForm] = useState({ warehouse_id: null, count_type: "FULL", planned_date: "", remark: "" });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { warehouseApi.warehouses().then((r) => setWarehouses(r.data?.items || r.data || [])).catch(() => {}); }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 20 };
      if (statusFilter && statusFilter !== "all") params.status = statusFilter;
      const res = await warehouseApi.stockCount.list(params);
      setData(res.data || res);
    } catch (_e) { console.error(_e); } finally { setLoading(false); }
  }, [page, statusFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    setSubmitting(true);
    try {
      await warehouseApi.stockCount.create({ ...createForm, warehouse_id: createForm.warehouse_id ? parseInt(createForm.warehouse_id) : null, planned_date: createForm.planned_date || null });
      toast?.success?.("盘点单创建成功"); setShowCreate(false); fetchData();
    } catch (_e) { toast?.error?.("创建失败"); } finally { setSubmitting(false); }
  };

  const viewDetail = async (order) => {
    try { const r = await warehouseApi.stockCount.get(order.id); setSelectedOrder(r.data || r); setShowDetail(true); } catch (_e) { console.error(_e); }
  };

  const changeStatus = async (id, status) => {
    try { await warehouseApi.stockCount.updateStatus(id, status); toast?.success?.("更新成功"); fetchData();
      if (showDetail) { const r = await warehouseApi.stockCount.get(id); setSelectedOrder(r.data || r); }
    } catch (_e) { toast?.error?.("失败"); }
  };

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="盘点管理" subtitle={`共 ${data.total} 条`} icon={<ClipboardCheck className="h-6 w-6" />}
        actions={<Button onClick={() => setShowCreate(true)} className="gap-2"><Plus className="h-4 w-4" /> 新建盘点单</Button>} />
      <main className="container mx-auto px-4 py-6 space-y-4">
        <div className="flex gap-3 items-center">
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-36"><SelectValue placeholder="全部状态" /></SelectTrigger>
            <SelectContent><SelectItem value="all">全部状态</SelectItem>
              {Object.entries(STATUS_MAP).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}</SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={fetchData}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /></Button>
        </div>
        <div className="bg-surface-200 rounded-xl border border-white/5 overflow-hidden">
          <Table><TableHeader><TableRow>
            <TableHead>盘点单号</TableHead><TableHead>类型</TableHead><TableHead>计划日期</TableHead>
            <TableHead>项数</TableHead><TableHead>一致/差异</TableHead><TableHead>状态</TableHead><TableHead className="text-right">操作</TableHead>
          </TableRow></TableHeader><TableBody>
            {loading ? <TableRow><TableCell colSpan={7} className="text-center py-8 text-text-muted">加载中...</TableCell></TableRow>
            : data.items?.length === 0 ? <TableRow><TableCell colSpan={7} className="text-center py-8 text-text-muted">暂无数据</TableCell></TableRow>
            : (data.items || []).map((row) => (
              <TableRow key={row.id}>
                <TableCell className="font-mono text-sm">{row.count_no}</TableCell>
                <TableCell>{COUNT_TYPES.find((t) => t.value === row.count_type)?.label || row.count_type}</TableCell>
                <TableCell>{row.planned_date ? formatDate(row.planned_date) : "-"}</TableCell>
                <TableCell>{row.total_items}</TableCell>
                <TableCell><span className="text-green-400">{row.matched_items}</span> / <span className="text-red-400">{row.diff_items}</span></TableCell>
                <TableCell><Badge variant="outline" className={`${STATUS_MAP[row.status]?.color || ""} text-white text-xs`}>{STATUS_MAP[row.status]?.label || row.status}</Badge></TableCell>
                <TableCell className="text-right space-x-1">
                  <Button variant="ghost" size="sm" onClick={() => viewDetail(row)}><Eye className="h-4 w-4" /></Button>
                  {row.status === "DRAFT" && <Button variant="ghost" size="sm" onClick={() => changeStatus(row.id, "IN_PROGRESS")}><Play className="h-4 w-4" /></Button>}
                </TableCell>
              </TableRow>
            ))}
          </TableBody></Table>
        </div>
      </main>

      <Dialog open={showCreate} onOpenChange={setShowCreate}><DialogContent>
        <DialogHeader><DialogTitle>新建盘点单</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2"><Label>仓库</Label>
            <Select value={createForm.warehouse_id?.toString() || ""} onValueChange={(v) => setCreateForm({ ...createForm, warehouse_id: v })}>
              <SelectTrigger><SelectValue placeholder="选择仓库" /></SelectTrigger>
              <SelectContent>{(warehouses || []).map((w) => <SelectItem key={w.id} value={w.id.toString()}>{w.warehouse_name}</SelectItem>)}</SelectContent>
            </Select></div>
          <div className="space-y-2"><Label>盘点类型</Label>
            <Select value={createForm.count_type} onValueChange={(v) => setCreateForm({ ...createForm, count_type: v })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{COUNT_TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
            </Select></div>
          <div className="space-y-2"><Label>计划日期</Label><Input type="date" value={createForm.planned_date} onChange={(e) => setCreateForm({ ...createForm, planned_date: e.target.value })} /></div>
          <div className="space-y-2"><Label>备注</Label><Input value={createForm.remark} onChange={(e) => setCreateForm({ ...createForm, remark: e.target.value })} /></div>
        </div>
        <DialogFooter><Button variant="outline" onClick={() => setShowCreate(false)}>取消</Button><Button onClick={handleCreate} disabled={submitting}>{submitting ? "创建中..." : "创建"}</Button></DialogFooter>
      </DialogContent></Dialog>

      <Dialog open={showDetail} onOpenChange={setShowDetail}><DialogContent className="max-w-3xl">
        <DialogHeader><DialogTitle>盘点单 - {selectedOrder?.count_no}</DialogTitle></DialogHeader>
        {selectedOrder && <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div><span className="text-text-muted">类型:</span> {COUNT_TYPES.find((t) => t.value === selectedOrder.count_type)?.label}</div>
            <div><span className="text-text-muted">状态:</span> {STATUS_MAP[selectedOrder.status]?.label}</div>
            <div><span className="text-text-muted">项数:</span> {selectedOrder.total_items} (一致{selectedOrder.matched_items}/差异{selectedOrder.diff_items})</div>
          </div>
          {selectedOrder.items?.length > 0 && <Table><TableHeader><TableRow>
            <TableHead>物料编码</TableHead><TableHead>名称</TableHead><TableHead className="text-right">系统</TableHead>
            <TableHead className="text-right">实盘</TableHead><TableHead className="text-right">差异</TableHead><TableHead>原因</TableHead>
          </TableRow></TableHeader><TableBody>
            {(selectedOrder.items || []).map((item) => (
              <TableRow key={item.id}><TableCell className="font-mono text-sm">{item.material_code}</TableCell>
                <TableCell>{item.material_name || "-"}</TableCell>
                <TableCell className="text-right">{item.system_quantity}</TableCell>
                <TableCell className="text-right">{item.actual_quantity ?? "-"}</TableCell>
                <TableCell className={`text-right ${item.diff_quantity && item.diff_quantity !== 0 ? "text-red-400 font-medium" : ""}`}>{item.diff_quantity ?? "-"}</TableCell>
                <TableCell className="text-text-muted text-sm">{item.diff_reason || "-"}</TableCell></TableRow>
            ))}
          </TableBody></Table>}
        </div>}
        <DialogFooter>
          {selectedOrder?.status === "IN_PROGRESS" && <Button onClick={() => changeStatus(selectedOrder.id, "COMPLETED")}>完成盘点</Button>}
          <Button variant="outline" onClick={() => setShowDetail(false)}>关闭</Button>
        </DialogFooter>
      </DialogContent></Dialog>
    </div>
  );
}
