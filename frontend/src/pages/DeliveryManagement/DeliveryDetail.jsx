/**
 * DeliveryDetail — read-only detail view for a single delivery order
 */

import { useState, useEffect } from "react";
import {
  CheckCircle2,
  Edit,
  PackageCheck,
  Printer,
  Send,
  XCircle,
} from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  toast,
} from "../../components/ui";
import { businessSupportApi } from "../../services/api";
import { getResponseData } from "../../utils/apiResponse";
import { notifyDelivery } from "./notify";

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

const approvalStatusLabels = {
  pending: "待审批",
  approved: "已通过",
  rejected: "已驳回",
};

const deliveryStatusLabels = {
  draft: "草稿",
  approved: "已审批",
  printed: "已打印",
  shipped: "已发货",
  received: "已签收",
  returned: "已退回",
};

const formatDateTime = (value) => {
  if (!value) return "-";
  return String(value).replace("T", " ").slice(0, 16);
};

const DeliveryDetail = ({ id, onBack, onEdit }) => {
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState("");
  const [detail, setDetail] = useState(null);
  const notify = (options) => notifyDelivery(toast, options);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    businessSupportApi.deliveryOrders
      .get(id)
      .then((res) => {
        const data = getResponseData(res) || {};
        setDetail(data);
      })
      .catch(() =>
        notify({
          title: "错误",
          description: "加载发货计划详情失败",
          variant: "destructive",
        })
      )
      .finally(() => setLoading(false));
  }, [id]);

  const getErrorMessage = (error, fallback) => {
    const detailText = error?.response?.data?.detail || error?.response?.data?.message;
    if (typeof detailText === "string") return detailText;
    return fallback;
  };

  const runAction = async (key, request, successMessage) => {
    setActionLoading(key);
    try {
      const res = await request();
      const data = getResponseData(res) || {};
      setDetail(data);
      notify({ title: "成功", description: successMessage });
    } catch (error) {
      notify({
        title: "错误",
        description: getErrorMessage(error, `${successMessage}失败`),
        variant: "destructive",
      });
    } finally {
      setActionLoading("");
    }
  };

  const handleApprove = (approved) =>
    runAction(
      approved ? "approve" : "reject",
      () =>
        businessSupportApi.deliveryOrders.approve(id, {
          approved,
          approval_comment: approved ? "发货审批通过" : "发货审批驳回",
        }),
      approved ? "审批通过" : "审批驳回"
    );

  const handlePrint = () =>
    runAction("print", () => businessSupportApi.deliveryOrders.print(id), "打印送货单");

  const handleShip = () =>
    runAction("ship", () => businessSupportApi.deliveryOrders.ship(id), "确认发货");

  const handleReceive = () =>
    runAction("receive", () => businessSupportApi.deliveryOrders.receive(id), "确认签收");

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

  const approvalStatus = (detail.approval_status || "").toLowerCase();
  const deliveryStatus = (detail.delivery_status || "").toLowerCase();
  const canApprove = approvalStatus === "pending";
  const canPrint = approvalStatus === "approved" && deliveryStatus === "approved";
  const canShip = approvalStatus === "approved" && ["approved", "printed"].includes(deliveryStatus);
  const canReceive = deliveryStatus === "shipped";

  return (
    <Card className="bg-surface-100/50">
      <CardHeader className="border-b border-white/10">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">
            发货计划详情 - {detail.delivery_no || ""}
          </CardTitle>
          <div className="flex flex-wrap justify-end gap-2">
            {canApprove && (
              <>
                <Button
                  variant="outline"
                  onClick={() => handleApprove(true)}
                  disabled={Boolean(actionLoading)}
                  className="gap-2"
                >
                  <CheckCircle2 size={16} />
                  审批通过
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleApprove(false)}
                  disabled={Boolean(actionLoading)}
                  className="gap-2"
                >
                  <XCircle size={16} />
                  审批驳回
                </Button>
              </>
            )}
            {canPrint && (
              <Button
                variant="outline"
                onClick={handlePrint}
                disabled={Boolean(actionLoading)}
                className="gap-2"
              >
                <Printer size={16} />
                打印送货单
              </Button>
            )}
            {canShip && (
              <Button
                variant="outline"
                onClick={handleShip}
                disabled={Boolean(actionLoading)}
                className="gap-2"
              >
                <Send size={16} />
                确认发货
              </Button>
            )}
            {canReceive && (
              <Button
                variant="outline"
                onClick={handleReceive}
                disabled={Boolean(actionLoading)}
                className="gap-2"
              >
                <PackageCheck size={16} />
                确认签收
              </Button>
            )}
            {onEdit && (
              <Button variant="outline" onClick={onEdit} className="gap-2">
                <Edit size={16} />
                编辑
              </Button>
            )}
            <Button variant="outline" onClick={onBack}>
              返回列表
            </Button>
          </div>
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
            <p className="text-sm text-slate-400">计划发货日期</p>
            <p className="text-white">{detail.delivery_date || "-"}</p>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">实际发货日期</p>
            <p className="text-white">{formatDateTime(detail.ship_date)}</p>
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
              {approvalStatusLabels[approvalStatus] || detail.approval_status || "-"}
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-slate-400">发货状态</p>
            <Badge
              variant="outline"
              className={getDeliveryStatusColor(detail.delivery_status)}
            >
              {deliveryStatusLabels[deliveryStatus] || detail.delivery_status || "-"}
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
