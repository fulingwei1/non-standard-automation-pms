/**
 * DeliveryForm — create / edit form for a delivery order
 */

import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Alert,
  toast,
} from "../../components/ui";
import { businessSupportApi } from "../../services/api";
import { getItemsCompat, getResponseData } from "../../utils/apiResponse";
import { notifyDelivery } from "./notify";

const EMPTY_FORM = {
  order_id: "",
  order_label: "",
  delivery_date: "",
  delivery_type: "",
  logistics_company: "",
  tracking_no: "",
  receiver_name: "",
  receiver_phone: "",
  receiver_address: "",
  delivery_amount: "",
  remark: "",
};

const getFirstParam = (searchParams, names) => {
  for (const name of names) {
    const value = searchParams.get(name);
    if (value) return value;
  }
  return "";
};

const DeliveryForm = ({ id, onBack }) => {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [salesOrdersLoading, setSalesOrdersLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [salesOrders, setSalesOrders] = useState([]);

  const isEdit = Boolean(id);
  const projectId = getFirstParam(searchParams, ["project_id", "projectId"]);
  const orderId = getFirstParam(searchParams, ["order_id", "orderId"]);
  const hasCreateContext = Boolean(projectId || orderId);
  const notify = (options) => notifyDelivery(toast, options);

  useEffect(() => {
    if (isEdit || !hasCreateContext) return;

    setSalesOrdersLoading(true);
    const params = { page: 1, page_size: 100 };
    if (projectId) {
      params.project_id = projectId;
    }

    businessSupportApi.salesOrders
      .list(params)
      .then(async (res) => {
        let items = getItemsCompat(res);
        items = Array.isArray(items) ? items : [];
        let selectedOrder = orderId
          ? items.find((order) => String(order.id) === String(orderId))
          : null;

        if (!selectedOrder && orderId && businessSupportApi.salesOrders.get) {
          const detailRes = await businessSupportApi.salesOrders.get(orderId);
          selectedOrder = getResponseData(detailRes);
          if (selectedOrder?.id) {
            items = [
              selectedOrder,
              ...items.filter((order) => String(order.id) !== String(selectedOrder.id)),
            ];
          }
        }

        if (!selectedOrder && items.length === 1) {
          selectedOrder = items[0];
        }

        setSalesOrders(items);
        if (selectedOrder?.id) {
          setFormData((prev) => ({
            ...prev,
            order_id: String(selectedOrder.id),
            order_label: selectedOrder.order_no || String(selectedOrder.id),
            delivery_amount: prev.delivery_amount || selectedOrder.order_amount || "",
          }));
        }
      })
      .catch(() =>
        notify({
          title: "提示",
          description: "销售订单列表加载失败，可稍后刷新重试",
        })
      )
      .finally(() => setSalesOrdersLoading(false));
  }, [hasCreateContext, isEdit, orderId, projectId]);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    businessSupportApi.deliveryOrders
      .get(id)
      .then((res) => {
        const data = getResponseData(res) || {};
        setFormData({
          order_id: data.order_id ? String(data.order_id) : "",
          order_label: data.order_no || (data.order_id ? String(data.order_id) : ""),
          delivery_date: data.delivery_date || "",
          delivery_type: data.delivery_type || "",
          logistics_company: data.logistics_company || "",
          tracking_no: data.tracking_no || "",
          receiver_name: data.receiver_name || "",
          receiver_phone: data.receiver_phone || "",
          receiver_address: data.receiver_address || "",
          delivery_amount: data.delivery_amount || "",
          remark: data.remark || "",
        });
      })
      .catch(() =>
        notify({
          title: "错误",
          description: "加载发货单数据失败",
          variant: "destructive",
        })
      )
      .finally(() => setLoading(false));
  }, [id]);

  const updateField = (field, value) =>
    setFormData((prev) => ({ ...prev, [field]: value }));

  const getErrorMessage = (error) => {
    const detail = error?.response?.data?.detail || error?.response?.data?.message;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg || JSON.stringify(item)).join("；");
    }
    if (typeof detail === "string") return detail;
    return isEdit ? "更新失败" : "创建失败";
  };

  const validateForm = () => {
    if (!formData.order_id) {
      notify({
        title: "警告",
        description: "请选择项目销售订单",
        variant: "destructive",
      });
      return false;
    }
    if (!formData.delivery_date) {
      notify({
        title: "警告",
        description: "请选择计划发货日期",
        variant: "destructive",
      });
      return false;
    }
    if (!formData.delivery_type) {
      notify({
        title: "警告",
        description: "请选择发货类型",
        variant: "destructive",
      });
      return false;
    }
    const amount = Number(formData.delivery_amount);
    if (!Number.isFinite(amount) || amount <= 0) {
      notify({
        title: "警告",
        description: "请填写有效的发货金额",
        variant: "destructive",
      });
      return false;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        order_id: Number(formData.order_id),
        delivery_amount: Number(formData.delivery_amount),
      };
      if (isEdit) {
        const { order_id: _orderId, order_label: _orderLabel, ...updatePayload } = payload;
        await businessSupportApi.deliveryOrders.update(id, updatePayload);
        notify({ title: "成功", description: "更新成功" });
      } else {
        await businessSupportApi.deliveryOrders.create(payload);
        notify({ title: "成功", description: "生成成功" });
      }
      onBack();
    } catch (err) {
      notify({
        title: "错误",
        description: getErrorMessage(err),
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
      </div>
    );
  }

  if (!isEdit && !hasCreateContext) {
    return (
      <Card className="bg-surface-100/50">
        <CardHeader className="border-b border-white/10">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white">生成发货计划</CardTitle>
            <Button variant="outline" onClick={onBack}>
              返回列表
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-6">
          <Alert variant="warning">请从项目交付页发起发货计划</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-surface-100/50">
      <CardHeader className="border-b border-white/10">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">
            {isEdit ? "编辑发货计划" : "生成发货计划"}
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onBack}>
              取消
            </Button>
            <Button onClick={handleSubmit} disabled={submitting}>
              保存
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <label className="text-sm text-slate-400">项目销售订单 *</label>
            {isEdit ? (
              <Input
                value={formData.order_label || formData.order_id}
                readOnly
                className="bg-surface-100 border-white/10"
              />
            ) : (
              <>
                <Select
                  value={formData.order_id ? String(formData.order_id) : ""}
                  onValueChange={(v) => updateField("order_id", v)}
                  disabled={salesOrdersLoading || Boolean(orderId)}
                >
                  <SelectTrigger className="bg-surface-100 border-white/10">
                    <SelectValue
                      placeholder={salesOrdersLoading ? "加载销售订单..." : "选择项目销售订单"}
                    />
                  </SelectTrigger>
                  <SelectContent>
                    {salesOrders.map((order) => (
                      <SelectItem key={order.id} value={String(order.id)}>
                        {order.order_no} - {order.customer_name || "未命名客户"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {salesOrders.length === 0 && !salesOrdersLoading && (
                  <p className="text-xs text-amber-400">
                    当前项目暂无可生成发货计划的销售订单
                  </p>
                )}
              </>
            )}
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">计划发货日期</label>
            <Input
              type="date"
              value={formData.delivery_date}
              onChange={(e) => updateField("delivery_date", e.target.value)}
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">发货类型</label>
            <Select
              value={formData.delivery_type}
              onValueChange={(v) => updateField("delivery_type", v)}
            >
              <SelectTrigger className="bg-surface-100 border-white/10">
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="standard">标准发货</SelectItem>
                <SelectItem value="express">加急发货</SelectItem>
                <SelectItem value="freight">物流发货</SelectItem>
                <SelectItem value="self_pickup">自提</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">物流公司</label>
            <Input
              value={formData.logistics_company}
              onChange={(e) => updateField("logistics_company", e.target.value)}
              placeholder="物流公司名称"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">物流单号</label>
            <Input
              value={formData.tracking_no}
              onChange={(e) => updateField("tracking_no", e.target.value)}
              placeholder="物流单号"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">发货金额</label>
            <Input
              type="number"
              value={formData.delivery_amount}
              onChange={(e) => updateField("delivery_amount", e.target.value)}
              placeholder="金额"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">收货人</label>
            <Input
              value={formData.receiver_name}
              onChange={(e) => updateField("receiver_name", e.target.value)}
              placeholder="收货人姓名"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">联系电话</label>
            <Input
              value={formData.receiver_phone}
              onChange={(e) => updateField("receiver_phone", e.target.value)}
              placeholder="联系电话"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="md:col-span-3 space-y-2">
            <label className="text-sm text-slate-400">收货地址</label>
            <Input
              value={formData.receiver_address}
              onChange={(e) => updateField("receiver_address", e.target.value)}
              placeholder="收货地址"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="md:col-span-3 space-y-2">
            <label className="text-sm text-slate-400">备注</label>
            <textarea
              rows={3}
              value={formData.remark}
              onChange={(e) => updateField("remark", e.target.value)}
              placeholder="备注信息"
              className="w-full px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DeliveryForm;
