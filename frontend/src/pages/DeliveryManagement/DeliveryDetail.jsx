/**
 * DeliveryDetail — read-only detail view for a single delivery order
 */

import { useState, useEffect } from "react";

import {
  toast,
} from "../../components/ui";
import { businessSupportApi } from "../../services/api";

const getStatusColor = (status) => {
  if (status === "approved")
    return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  if (status === "rejected")
    return "bg-red-500/20 text-red-400 border-red-500/30";
  return "bg-amber-500/20 text-amber-400 border-amber-500/30";
};

const getDeliveryStatusColor = (status) => {
  if (status === "shipped")
    return "bg-blue-500/20 text-blue-400 border-blue-500/30";
  if (status === "received")
    return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
  return "bg-slate-500/20 text-slate-400 border-slate-500/30";
};

const DeliveryDetail = ({ id, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    businessSupportApi.deliveryOrders
      .get(id)
      .then((res) => {
        const data = res?.data?.data || res?.data || {};
        setDetail(data);
      })
      .catch(() =>
        toast({
          title: "错误",
          description: "加载发货单详情失败",
          variant: "destructive",
        })
      )
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  if (!detail) {
    return (
      <Card className="bg-surface-100/50">
        <CardContent className="p-6">
          <div className="flex items-center gap-2 text-amber-400">
            <span>发货单不存在</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-surface-100/50">
      <CardHeader className="border-b border-white/10">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">
            发货单详情 - {detail.delivery_no || ""}
          </CardTitle>
          <Button variant="outline" onClick={onBack}>
            返回列表
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货单号</p>
            <p className="text-white font-medium">{detail.delivery_no}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">订单号</p>
            <p className="text-white font-medium">{detail.order_no}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">客户名称</p>
            <p className="text-white font-medium">{detail.customer_name}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货日期</p>
            <p className="text-white">{detail.delivery_date || "-"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货类型</p>
            <p className="text-white">{detail.delivery_type || "-"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">物流公司</p>
            <p className="text-white">{detail.logistics_company || "-"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">物流单号</p>
            <p className="text-white">{detail.tracking_no || "-"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">收货人</p>
            <p className="text-white">{detail.receiver_name || "-"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">联系电话</p>
            <p className="text-white">{detail.receiver_phone || "-"}</p>
          </div>
          <div className="md:col-span-3 space-y-1">
            <p className="text-sm text-slate-400">收货地址</p>
            <p className="text-white">{detail.receiver_address || "-"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货金额</p>
            <p className="text-white">{detail.delivery_amount ?? "-"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">审批状态</p>
            <Badge
              variant="outline"
              className={getStatusColor(detail.approval_status)}
            >
              {detail.approval_status || "-"}
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货状态</p>
            <Badge
              variant="outline"
              className={getDeliveryStatusColor(detail.delivery_status)}
            >
              {detail.delivery_status || "-"}
            </Badge>
          </div>
          <div className="md:col-span-3 space-y-1">
            <p className="text-sm text-slate-400">备注</p>
            <p className="text-white">{detail.remark || "-"}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DeliveryDetail;
