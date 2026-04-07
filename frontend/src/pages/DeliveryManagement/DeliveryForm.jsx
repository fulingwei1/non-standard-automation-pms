/**
 * DeliveryForm — create / edit form for a delivery order
 */

import { useState, useEffect } from "react";

import {
  toast,
} from "../../components/ui";
import { businessSupportApi } from "../../services/api";

const EMPTY_FORM = {
  order_id: "",
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

const DeliveryForm = ({ id, onBack }) => {
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState(EMPTY_FORM);

  const isEdit = Boolean(id);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    businessSupportApi.deliveryOrders
      .get(id)
      .then((res) => {
        const data = res?.data?.data || res?.data || {};
        setFormData({
          order_id: data.order_id || "",
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
        toast({
          title: "错误",
          description: "加载发货单数据失败",
          variant: "destructive",
        })
      )
      .finally(() => setLoading(false));
  }, [id]);

  const updateField = (field, value) =>
    setFormData((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async () => {
    if (!formData.order_id) {
      toast({
        title: "警告",
        description: "请填写销售订单 ID",
        variant: "destructive",
      });
      return;
    }
    setSubmitting(true);
    try {
      if (isEdit) {
        await businessSupportApi.deliveryOrders.update(id, formData);
        toast({ title: "成功", description: "更新成功" });
      } else {
        await businessSupportApi.deliveryOrders.create(formData);
        toast({ title: "成功", description: "创建成功" });
      }
      onBack();
    } catch (_err) {
      toast({
        title: "错误",
        description: isEdit ? "更新失败" : "创建失败",
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

  return (
    <Card className="bg-surface-100/50">
      <CardHeader className="border-b border-white/10">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white">
            {isEdit ? "编辑发货单" : "新建发货单"}
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
            <label className="text-sm text-slate-400">销售订单 ID *</label>
            <Input
              value={formData.order_id}
              onChange={(e) => updateField("order_id", e.target.value)}
              placeholder="输入销售订单 ID"
              className="bg-surface-100 border-white/10"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm text-slate-400">发货日期</label>
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
