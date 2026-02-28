import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowDownToLine, Plus, Trash2, ArrowLeft, Save } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { warehouseApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

const ORDER_TYPES = [
  { value: "PURCHASE", label: "采购入库" }, { value: "RETURN", label: "退货入库" },
  { value: "TRANSFER", label: "调拨入库" }, { value: "OTHER", label: "其他入库" },
];
const emptyItem = { material_code: "", material_name: "", specification: "", unit: "件", planned_quantity: 0, remark: "" };

export default function InboundNew() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [warehouses, setWarehouses] = useState([]);
  const [form, setForm] = useState({ order_type: "PURCHASE", warehouse_id: null, source_no: "", supplier_name: "", planned_date: "", remark: "" });
  const [items, setItems] = useState([{ ...emptyItem }]);

  useEffect(() => { warehouseApi.warehouses().then((r) => setWarehouses(r.data?.items || r.data || [])).catch(() => {}); }, []);

  const updateItem = (idx, field, value) => { const n = [...items]; n[idx] = { ...n[idx], [field]: value }; setItems(n); };

  const handleSubmit = async () => {
    const valid = (items || []).filter((i) => i.material_code && i.planned_quantity > 0);
    if (!valid.length) { alert("请至少添加一个物料明细"); return; }
    setSubmitting(true);
    try {
      await warehouseApi.inbound.create({
        ...form, warehouse_id: form.warehouse_id ? parseInt(form.warehouse_id) : null,
        planned_date: form.planned_date || null,
        items: (valid || []).map((i) => ({ ...i, planned_quantity: parseFloat(i.planned_quantity) })),
      });
      toast?.success?.("入库单创建成功"); navigate("/warehouse/inbound");
    } catch (_e) { toast?.error?.("创建失败"); } finally { setSubmitting(false); }
  };

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="新建入库单" subtitle="创建新的入库单" icon={<ArrowDownToLine className="h-6 w-6" />}
        actions={<Button variant="outline" onClick={() => navigate(-1)} className="gap-2"><ArrowLeft className="h-4 w-4" /> 返回</Button>} />
      <main className="container mx-auto px-4 py-6 space-y-6">
        <Card><CardHeader><CardTitle>基本信息</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2"><Label>入库类型</Label>
              <Select value={form.order_type} onValueChange={(v) => setForm({ ...form, order_type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{ORDER_TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
              </Select></div>
            <div className="space-y-2"><Label>目标仓库</Label>
              <Select value={form.warehouse_id?.toString() || ""} onValueChange={(v) => setForm({ ...form, warehouse_id: v })}>
                <SelectTrigger><SelectValue placeholder="选择仓库" /></SelectTrigger>
                <SelectContent>{(warehouses || []).map((w) => <SelectItem key={w.id} value={w.id.toString()}>{w.warehouse_name}</SelectItem>)}</SelectContent>
              </Select></div>
            <div className="space-y-2"><Label>计划入库日期</Label><Input type="date" value={form.planned_date} onChange={(e) => setForm({ ...form, planned_date: e.target.value })} /></div>
            <div className="space-y-2"><Label>来源单号</Label><Input value={form.source_no} onChange={(e) => setForm({ ...form, source_no: e.target.value })} placeholder="采购单号等" /></div>
            <div className="space-y-2"><Label>供应商</Label><Input value={form.supplier_name} onChange={(e) => setForm({ ...form, supplier_name: e.target.value })} /></div>
            <div className="space-y-2"><Label>备注</Label><Input value={form.remark} onChange={(e) => setForm({ ...form, remark: e.target.value })} /></div>
          </CardContent></Card>
        <Card><CardHeader className="flex flex-row items-center justify-between"><CardTitle>物料明细</CardTitle>
            <Button variant="outline" size="sm" onClick={() => setItems([...items, { ...emptyItem }])} className="gap-1"><Plus className="h-4 w-4" /> 添加行</Button></CardHeader>
          <CardContent><div className="space-y-3">
            <div className="grid grid-cols-12 gap-2 text-xs text-text-muted font-medium px-1">
              <div className="col-span-2">物料编码*</div><div className="col-span-3">物料名称</div><div className="col-span-2">规格型号</div>
              <div className="col-span-1">单位</div><div className="col-span-2">计划数量*</div><div className="col-span-1">备注</div><div className="col-span-1"></div>
            </div>
            {(items || []).map((item, idx) => (
              <div key={idx} className="grid grid-cols-12 gap-2 items-center">
                <Input className="col-span-2" value={item.material_code} onChange={(e) => updateItem(idx, "material_code", e.target.value)} placeholder="编码" />
                <Input className="col-span-3" value={item.material_name} onChange={(e) => updateItem(idx, "material_name", e.target.value)} placeholder="名称" />
                <Input className="col-span-2" value={item.specification} onChange={(e) => updateItem(idx, "specification", e.target.value)} placeholder="规格" />
                <Input className="col-span-1" value={item.unit} onChange={(e) => updateItem(idx, "unit", e.target.value)} />
                <Input className="col-span-2" type="number" value={item.planned_quantity} onChange={(e) => updateItem(idx, "planned_quantity", e.target.value)} />
                <Input className="col-span-1" value={item.remark} onChange={(e) => updateItem(idx, "remark", e.target.value)} />
                <div className="col-span-1 flex justify-center">
                  <Button variant="ghost" size="icon" onClick={() => setItems((items || []).filter((_, i) => i !== idx))} disabled={items?.length <= 1}><Trash2 className="h-4 w-4 text-red-400" /></Button>
                </div>
              </div>
            ))}
          </div></CardContent></Card>
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={() => navigate(-1)}>取消</Button>
          <Button onClick={handleSubmit} disabled={submitting} className="gap-2"><Save className="h-4 w-4" /> {submitting ? "提交中..." : "创建入库单"}</Button>
        </div>
      </main>
    </div>
  );
}
