import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowUpFromLine, ArrowLeft, XCircle, Play, AlertTriangle } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  Card, CardContent, CardHeader, CardTitle,
} from "../../components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../../components/ui/table";
import { warehouseApi } from "../../services/api";
import { formatDate } from "../../lib/utils";
import { toast } from "../../components/ui/toast";

const STATUS_MAP = {
  DRAFT: { label: "草稿", color: "bg-gray-500", next: "PENDING", nextLabel: "提交" },
  PENDING: { label: "待出库", color: "bg-yellow-500", next: "PICKING", nextLabel: "开始拣货" },
  PICKING: { label: "拣货中", color: "bg-blue-500", next: "COMPLETED", nextLabel: "完成出库" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-red-500" },
};

export default function OutboundDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState(null);

  const fetchOrder = async () => {
    try {
      setLoading(true);
      const res = await warehouseApi.outbound.get(id);
      setOrder(res.data || res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOrder(); }, [id]);

  const handleStatusChange = async (newStatus) => {
    try {
      await warehouseApi.outbound.updateStatus(id, newStatus);
      toast?.success?.("状态更新成功");
      fetchOrder();
    } catch (e) {
      toast?.error?.("状态更新失败");
    }
  };

  if (loading) return <div className="p-8 text-center text-text-muted">加载中...</div>;
  if (!order) return <div className="p-8 text-center text-text-muted">出库单不存在</div>;

  const statusInfo = STATUS_MAP[order.status] || {};

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title={`出库单 ${order.order_no}`}
        subtitle={<>{statusInfo.label} {order.is_urgent && <AlertTriangle className="inline h-4 w-4 text-red-400 ml-1" />}</>}
        icon={<ArrowUpFromLine className="h-6 w-6" />}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate(-1)} className="gap-2">
              <ArrowLeft className="h-4 w-4" /> 返回
            </Button>
            {statusInfo.next && (
              <Button onClick={() => handleStatusChange(statusInfo.next)} className="gap-2">
                <Play className="h-4 w-4" /> {statusInfo.nextLabel}
              </Button>
            )}
            {order.status === "DRAFT" && (
              <Button variant="destructive" onClick={() => handleStatusChange("CANCELLED")} className="gap-2">
                <XCircle className="h-4 w-4" /> 取消
              </Button>
            )}
          </div>
        }
      />
      <main className="container mx-auto px-4 py-6 space-y-6">
        <Card>
          <CardHeader><CardTitle>基本信息</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><span className="text-text-muted">单号:</span> <span className="font-mono">{order.order_no}</span></div>
            <div><span className="text-text-muted">类型:</span> {order.order_type}</div>
            <div><span className="text-text-muted">领料部门:</span> {order.department || "-"}</div>
            <div><span className="text-text-muted">目标单号:</span> {order.target_no || "-"}</div>
            <div><span className="text-text-muted">计划日期:</span> {order.planned_date ? formatDate(order.planned_date) : "-"}</div>
            <div><span className="text-text-muted">实际日期:</span> {order.actual_date ? formatDate(order.actual_date) : "-"}</div>
            <div><span className="text-text-muted">总数量:</span> {order.total_quantity}</div>
            <div><span className="text-text-muted">已拣数量:</span> {order.picked_quantity}</div>
            {order.remark && <div className="col-span-full"><span className="text-text-muted">备注:</span> {order.remark}</div>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>物料明细 ({order.items?.length || 0})</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>物料编码</TableHead>
                  <TableHead>物料名称</TableHead>
                  <TableHead>规格型号</TableHead>
                  <TableHead>单位</TableHead>
                  <TableHead>计划数量</TableHead>
                  <TableHead>实拣数量</TableHead>
                  <TableHead>备注</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(order.items || []).map((item, idx) => (
                  <TableRow key={item.id}>
                    <TableCell>{idx + 1}</TableCell>
                    <TableCell className="font-mono text-sm">{item.material_code}</TableCell>
                    <TableCell>{item.material_name || "-"}</TableCell>
                    <TableCell>{item.specification || "-"}</TableCell>
                    <TableCell>{item.unit}</TableCell>
                    <TableCell>{item.planned_quantity}</TableCell>
                    <TableCell>{item.picked_quantity}</TableCell>
                    <TableCell>{item.remark || "-"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
