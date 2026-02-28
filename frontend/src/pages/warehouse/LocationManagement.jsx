import React, { useState, useEffect, useCallback } from "react";
import { MapPin, Plus, Search, Edit3, Trash2, RefreshCw } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Badge } from "../../components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import { warehouseApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

const LOC_TYPES = [{ value: "STORAGE", label: "存储区" }, { value: "PICKING", label: "拣货区" }, { value: "STAGING", label: "暂存区" }, { value: "RETURN", label: "退货区" }];
const emptyForm = { warehouse_id: null, location_code: "", location_name: "", zone: "", aisle: "", shelf: "", level: "", position: "", capacity: "", location_type: "STORAGE" };

export default function LocationManagement() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({ items: [], total: 0 });
  const [warehouses, setWarehouses] = useState([]);
  const [keyword, setKeyword] = useState("");
  const [whFilter, setWhFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [showDialog, setShowDialog] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({ ...emptyForm });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { warehouseApi.warehouses().then((r) => setWarehouses(r.data?.items || r.data || [])).catch(() => {}); }, []);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 50 };
      if (whFilter && whFilter !== "all") params.warehouse_id = parseInt(whFilter);
      if (keyword) params.keyword = keyword;
      const res = await warehouseApi.locations.list(params);
      setData(res.data || res);
    } catch (_e) { console.error(_e); } finally { setLoading(false); }
  }, [page, whFilter, keyword]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const openCreate = () => { setEditingId(null); setForm({ ...emptyForm }); setShowDialog(true); };
  const openEdit = (loc) => { setEditingId(loc.id); setForm({ warehouse_id: loc.warehouse_id?.toString(), location_code: loc.location_code, location_name: loc.location_name || "", zone: loc.zone || "", aisle: loc.aisle || "", shelf: loc.shelf || "", level: loc.level || "", position: loc.position || "", capacity: loc.capacity?.toString() || "", location_type: loc.location_type || "STORAGE" }); setShowDialog(true); };

  const handleSave = async () => {
    if (!form.location_code && !editingId) { alert("库位编码不能为空"); return; }
    setSubmitting(true);
    try {
      const p = { ...form, warehouse_id: form.warehouse_id ? parseInt(form.warehouse_id) : null, capacity: form.capacity ? parseFloat(form.capacity) : null };
      if (editingId) { const { warehouse_id: _warehouse_id, location_code: _location_code, ...u } = p; await warehouseApi.locations.update(editingId, u); }
      else { await warehouseApi.locations.create(p); }
      toast?.success?.(editingId ? "更新成功" : "创建成功"); setShowDialog(false); fetchData();
    } catch (_e) { toast?.error?.("操作失败"); } finally { setSubmitting(false); }
  };

  const handleDelete = async (id) => { if (!confirm("确定禁用该库位？")) return; try { await warehouseApi.locations.delete(id); toast?.success?.("已禁用"); fetchData(); } catch (_e) { toast?.error?.("失败"); } };

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="库位管理" subtitle={`共 ${data.total} 个库位`} icon={<MapPin className="h-6 w-6" />}
        actions={<Button onClick={openCreate} className="gap-2"><Plus className="h-4 w-4" /> 新建库位</Button>} />
      <main className="container mx-auto px-4 py-6 space-y-4">
        <div className="flex gap-3 items-center">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-muted" />
            <Input placeholder="搜索库位编码/名称..." value={keyword} onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchData()} className="pl-9" />
          </div>
          <Select value={whFilter} onValueChange={(v) => { setWhFilter(v); setPage(1); }}>
            <SelectTrigger className="w-40"><SelectValue placeholder="全部仓库" /></SelectTrigger>
            <SelectContent><SelectItem value="all">全部仓库</SelectItem>
              {(warehouses || []).map((w) => <SelectItem key={w.id} value={w.id.toString()}>{w.warehouse_name}</SelectItem>)}</SelectContent>
          </Select>
          <Button variant="outline" size="icon" onClick={fetchData}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /></Button>
        </div>
        <div className="bg-surface-200 rounded-xl border border-white/5 overflow-hidden">
          <Table><TableHeader><TableRow>
            <TableHead>库位编码</TableHead><TableHead>名称</TableHead><TableHead>仓库</TableHead><TableHead>区域</TableHead>
            <TableHead>通道/架/层/位</TableHead><TableHead>类型</TableHead><TableHead>容量</TableHead><TableHead>状态</TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow></TableHeader><TableBody>
            {loading ? <TableRow><TableCell colSpan={9} className="text-center py-8 text-text-muted">加载中...</TableCell></TableRow>
            : data.items?.length === 0 ? <TableRow><TableCell colSpan={9} className="text-center py-8 text-text-muted">暂无数据</TableCell></TableRow>
            : (data.items || []).map((loc) => (
              <TableRow key={loc.id}>
                <TableCell className="font-mono text-sm">{loc.location_code}</TableCell>
                <TableCell>{loc.location_name || "-"}</TableCell>
                <TableCell>{loc.warehouse_name || "-"}</TableCell>
                <TableCell>{loc.zone || "-"}</TableCell>
                <TableCell className="text-text-muted text-sm">{[loc.aisle, loc.shelf, loc.level, loc.position].filter(Boolean).join("-") || "-"}</TableCell>
                <TableCell><Badge variant="outline" className="text-xs">{LOC_TYPES.find((t) => t.value === loc.location_type)?.label || loc.location_type}</Badge></TableCell>
                <TableCell>{loc.capacity || "-"}</TableCell>
                <TableCell><Badge variant="outline" className={loc.is_active ? "text-green-400 bg-green-400/10" : "text-red-400 bg-red-400/10"}>{loc.is_active ? "启用" : "禁用"}</Badge></TableCell>
                <TableCell className="text-right space-x-1">
                  <Button variant="ghost" size="sm" onClick={() => openEdit(loc)}><Edit3 className="h-4 w-4" /></Button>
                  {loc.is_active && <Button variant="ghost" size="sm" onClick={() => handleDelete(loc.id)}><Trash2 className="h-4 w-4 text-red-400" /></Button>}
                </TableCell>
              </TableRow>
            ))}
          </TableBody></Table>
        </div>
      </main>

      <Dialog open={showDialog} onOpenChange={setShowDialog}><DialogContent>
        <DialogHeader><DialogTitle>{editingId ? "编辑库位" : "新建库位"}</DialogTitle></DialogHeader>
        <div className="grid grid-cols-2 gap-4">
          {!editingId && <div className="space-y-2"><Label>仓库</Label>
            <Select value={form.warehouse_id?.toString() || ""} onValueChange={(v) => setForm({ ...form, warehouse_id: v })}>
              <SelectTrigger><SelectValue placeholder="选择仓库" /></SelectTrigger>
              <SelectContent>{(warehouses || []).map((w) => <SelectItem key={w.id} value={w.id.toString()}>{w.warehouse_name}</SelectItem>)}</SelectContent>
            </Select></div>}
          {!editingId && <div className="space-y-2"><Label>库位编码*</Label><Input value={form.location_code} onChange={(e) => setForm({ ...form, location_code: e.target.value })} placeholder="A-01-01" /></div>}
          <div className="space-y-2"><Label>名称</Label><Input value={form.location_name} onChange={(e) => setForm({ ...form, location_name: e.target.value })} /></div>
          <div className="space-y-2"><Label>区域</Label><Input value={form.zone} onChange={(e) => setForm({ ...form, zone: e.target.value })} placeholder="A/B/C" /></div>
          <div className="space-y-2"><Label>通道</Label><Input value={form.aisle} onChange={(e) => setForm({ ...form, aisle: e.target.value })} /></div>
          <div className="space-y-2"><Label>货架</Label><Input value={form.shelf} onChange={(e) => setForm({ ...form, shelf: e.target.value })} /></div>
          <div className="space-y-2"><Label>层</Label><Input value={form.level} onChange={(e) => setForm({ ...form, level: e.target.value })} /></div>
          <div className="space-y-2"><Label>位</Label><Input value={form.position} onChange={(e) => setForm({ ...form, position: e.target.value })} /></div>
          <div className="space-y-2"><Label>类型</Label>
            <Select value={form.location_type} onValueChange={(v) => setForm({ ...form, location_type: v })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{LOC_TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
            </Select></div>
          <div className="space-y-2"><Label>容量</Label><Input type="number" value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} /></div>
        </div>
        <DialogFooter><Button variant="outline" onClick={() => setShowDialog(false)}>取消</Button><Button onClick={handleSave} disabled={submitting}>{submitting ? "保存中..." : "保存"}</Button></DialogFooter>
      </DialogContent></Dialog>
    </div>
  );
}
