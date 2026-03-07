import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowDownToLine, ArrowLeft, XCircle, Play } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/table";
import { warehouseApi } from "../../services/api";
import { formatDate } from "../../lib/utils";
import { toast } from "../../components/ui/toast";

const STATUS_MAP = {
  DRAFT: { label: "草稿", next: "PENDING", nextLabel: "提交" },
  PENDING: { label: "待入库", next: "RECEIVING", nextLabel: "开始入库" },
  RECEIVING: { label: "入库中", next: "COMPLETED", nextLabel: "完成入库" },
  COMPLETED: { label: "已完成" }, CANCELLED: { label: "已取消" },
};

export default function InboundDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState(null);

  const fetch = async () => { try { setLoading(true); const r = await warehouseApi.inbound.get(id); setOrder(r.data || r); } catch (_e) { /* ignore */ } finally { setLoading(false); } };
  useEffect(() => { fetch(); }, [id]);

  const changeStatus = async (s) => { try { await warehouseApi.inbound.updateStatus(id, s); toast?.success?.("更新成功"); fetch(); } catch (_e) { toast?.error?.("失败"); } };

  if (loading) return <div className="p-8 text-center text-text-muted">加载中...</div>;
  if (!order) return <div className="p-8 text-center text-text-muted">入库单不存在</div>;
  const si = STATUS_MAP[order.status] || {};

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title={`入库单 ${order.order_no}`} subtitle={si.label} icon={<ArrowDownToLine className="h-6 w-6" />}
        actions={<div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate(-1)} className="gap-2"><ArrowLeft className="h-4 w-4" /> 返回</Button>
          {si.next && <Button onClick={() => changeStatus(si.next)} className="gap-2"><Play className="h-4 w-4" /> {si.nextLabel}</Button>}
          {order.status === "DRAFT" && <Button variant="destructive" onClick={() => changeStatus("CANCELLED")}><XCircle className="h-4 w-4" /> 取消</Button>}
        </div>} />
      <main className="container mx-auto px-4 py-6 space-y-6">
        <Card><CardHeader><CardTitle>基本信息</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><span className="text-text-muted">单号:</span> <span className="font-mono">{order.order_no}</span></div>
            <div><span className="text-text-muted">类型:</span> {order.order_type}</div>
            <div><span className="text-text-muted">供应商:</span> {order.supplier_name || "-"}</div>
            <div><span className="text-text-muted">来源单号:</span> {order.source_no || "-"}</div>
            <div><span className="text-text-muted">计划日期:</span> {order.planned_date ? formatDate(order.planned_date) : "-"}</div>
            <div><span className="text-text-muted">实际日期:</span> {order.actual_date ? formatDate(order.actual_date) : "-"}</div>
            <div><span className="text-text-muted">总数量:</span> {order.total_quantity}</div>
            <div><span className="text-text-muted">已收:</span> {order.received_quantity}</div>
            {order.remark && <div className="col-span-full"><span className="text-text-muted">备注:</span> {order.remark}</div>}
          </CardContent></Card>
        <Card><CardHeader><CardTitle>物料明细 ({order.items?.length || 0})</CardTitle></CardHeader>
          <CardContent><Table><TableHeader><TableRow>
            <TableHead>#</TableHead><TableHead>物料编码</TableHead><TableHead>物料名称</TableHead><TableHead>规格</TableHead>
            <TableHead>单位</TableHead><TableHead>计划数量</TableHead><TableHead>实收数量</TableHead><TableHead>备注</TableHead>
          </TableRow></TableHeader><TableBody>
            {(order.items || []).map((item, idx) => (
              <TableRow key={item.id}><TableCell>{idx + 1}</TableCell><TableCell className="font-mono text-sm">{item.material_code}</TableCell>
                <TableCell>{item.material_name || "-"}</TableCell><TableCell>{item.specification || "-"}</TableCell>
                <TableCell>{item.unit}</TableCell><TableCell>{item.planned_quantity}</TableCell>
                <TableCell>{item.received_quantity}</TableCell><TableCell>{item.remark || "-"}</TableCell></TableRow>
            ))}
          </TableBody></Table></CardContent></Card>
      </main>
    </div>
  );
}
