/**
 * CreateEditOrderDialog - 采购订单创建/编辑对话框
 * 支持创建新订单和编辑现有订单
 */

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody } from
"../../ui/dialog";
import { Button } from "../../ui/button";
import { Input } from "../../ui/input";
import { Label } from "../../ui/label";
import { Textarea } from "../../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../ui/select";
import { Plus, Trash2 } from "lucide-react";
import {
  PAYMENT_TERMS,
  PAYMENT_TERMS_CONFIGS,
  SHIPPING_METHOD_CONFIGS,
  SHIPPING_METHODS,
} from "@/lib/constants/procurement";

export default function CreateEditOrderDialog({
  open,
  onOpenChange,
  mode = "create", // "create" | "edit"
  orderData,
  suppliers = [],
  projects = [],
  onChange,
  onSubmit
}) {
  const isEditing = mode === "edit";
  const title = isEditing ? "编辑采购订单" : "创建采购订单";
  const submitLabel = isEditing ? "保存修改" : "创建订单";
  const items = orderData?.items || [];

  const updateItem = (index, patch) => {
    const nextItems = items.map((item, itemIndex) =>
      itemIndex === index ? { ...item, ...patch } : item
    );
    onChange?.({ ...orderData, items: nextItems });
  };

  const addItem = () => {
    onChange?.({
      ...orderData,
      items: [
        ...items,
        {
          material_code: "",
          material_name: "",
          specification: "",
          unit: "件",
          quantity: "",
          unit_price: "",
          tax_rate: 13,
          required_date: orderData?.expected_date || orderData?.required_date || "",
        },
      ],
    });
  };

  const removeItem = (index) => {
    onChange?.({
      ...orderData,
      items: items.filter((_, itemIndex) => itemIndex !== index),
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] bg-slate-800/50 border border-slate-700/50">
        <DialogHeader>
          <DialogTitle className="text-white">{title}</DialogTitle>
          <DialogDescription className="text-slate-400">
            录入供应商、项目、预计到货日期和采购明细，用于生成采购订单。
          </DialogDescription>
        </DialogHeader>

        <DialogBody className="space-y-4">
          {/* 供应商和项目 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-400">供应商</Label>
              <Select
                value={orderData?.supplier_id ? String(orderData.supplier_id) : ""}
                onValueChange={(value) => onChange?.({ ...orderData, supplier_id: value })}>

                <SelectTrigger className="bg-slate-900 border-slate-700 text-white">
                  <SelectValue placeholder="选择供应商" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  {(suppliers || []).map((supplier) =>
                  <SelectItem key={supplier.id} value={String(supplier.id)}>
                      {supplier.supplier_name || supplier.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-slate-400">项目</Label>
              <Select
                value={orderData?.project_id ? String(orderData.project_id) : ""}
                onValueChange={(value) => onChange?.({ ...orderData, project_id: value })}>

                <SelectTrigger className="bg-slate-900 border-slate-700 text-white">
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  {(projects || []).map((project) =>
                  <SelectItem key={project.id} value={String(project.id)}>
                      {project.project_name || project.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label className="text-slate-400">预计到货日期</Label>
            <Input
              type="date"
              value={orderData?.expected_date || orderData?.required_date || ""}
              onChange={(e) =>
                onChange?.({
                  ...orderData,
                  expected_date: e.target.value,
                  required_date: e.target.value,
                  items: items.map((item) => ({
                    ...item,
                    required_date: item.required_date || e.target.value,
                  })),
                })
              }
              className="bg-slate-900 border-slate-700 text-white"
            />
          </div>

          {/* 支付条款和运输方式 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-400">支付条款</Label>
              <Select
                value={orderData?.payment_terms || PAYMENT_TERMS.NET30}
                onValueChange={(value) => onChange?.({ ...orderData, payment_terms: value })}>

                <SelectTrigger className="bg-slate-900 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  {Object.entries(PAYMENT_TERMS_CONFIGS).map(([key, config]) =>
                  <SelectItem key={key} value={key}>
                      {config.label}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-slate-400">运输方式</Label>
              <Select
                value={orderData?.shipping_method || SHIPPING_METHODS.STANDARD}
                onValueChange={(value) => onChange?.({ ...orderData, shipping_method: value })}>

                <SelectTrigger className="bg-slate-900 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  {Object.entries(SHIPPING_METHOD_CONFIGS).map(([key, config]) =>
                  <SelectItem key={key} value={key || SHIPPING_METHODS.STANDARD}>
                      {config.label}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 紧急程度（仅编辑模式显示） */}
          {isEditing &&
          <div>
              <Label className="text-slate-400">紧急程度</Label>
              <Select
              value={orderData?.urgency || "normal"}
              onValueChange={(value) => onChange?.({ ...orderData, urgency: value })}>

                <SelectTrigger className="bg-slate-900 border-slate-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  <SelectItem value="normal">普通</SelectItem>
                  <SelectItem value="urgent">紧急</SelectItem>
                  <SelectItem value="critical">非常紧急</SelectItem>
                </SelectContent>
              </Select>
          </div>
          }

          {/* 备注 */}
          <div>
            <Label className="text-slate-400">备注</Label>
            <Textarea
              value={orderData?.notes || ""}
              onChange={(e) => onChange?.({ ...orderData, notes: e.target.value })}
              placeholder="订单备注信息..."
              className="bg-slate-900 border-slate-700 text-white placeholder-slate-400"
              rows={3} />

          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-slate-400">采购明细</Label>
              <Button type="button" variant="secondary" size="sm" onClick={addItem}>
                <Plus className="w-4 h-4 mr-1" />
                添加明细
              </Button>
            </div>

            {items.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-700 p-4 text-sm text-slate-500">
                暂无采购明细，请添加至少一条物料。
              </div>
            ) : (
              <div className="space-y-3">
                {items.map((item, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-slate-700/70 bg-slate-900/40 p-3"
                  >
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs text-slate-400">物料编码</Label>
                        <Input
                          value={item.material_code || ""}
                          onChange={(e) => updateItem(index, { material_code: e.target.value })}
                          placeholder="如 MAT-QA-001"
                          className="bg-slate-950 border-slate-700 text-white"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-slate-400">物料名称</Label>
                        <Input
                          value={item.material_name || ""}
                          onChange={(e) => updateItem(index, { material_name: e.target.value })}
                          placeholder="请输入物料名称"
                          className="bg-slate-950 border-slate-700 text-white"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-slate-400">规格型号</Label>
                        <Input
                          value={item.specification || ""}
                          onChange={(e) => updateItem(index, { specification: e.target.value })}
                          placeholder="规格型号"
                          className="bg-slate-950 border-slate-700 text-white"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-slate-400">单位</Label>
                        <Input
                          value={item.unit || ""}
                          onChange={(e) => updateItem(index, { unit: e.target.value })}
                          placeholder="件"
                          className="bg-slate-950 border-slate-700 text-white"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-slate-400">数量</Label>
                        <Input
                          type="number"
                          min="0"
                          step="0.0001"
                          value={item.quantity ?? item.qty ?? ""}
                          onChange={(e) =>
                            updateItem(index, { quantity: e.target.value, qty: e.target.value })
                          }
                          placeholder="0"
                          className="bg-slate-950 border-slate-700 text-white"
                        />
                      </div>
                      <div>
                        <Label className="text-xs text-slate-400">单价</Label>
                        <Input
                          type="number"
                          min="0"
                          step="0.0001"
                          value={item.unit_price ?? item.price ?? ""}
                          onChange={(e) =>
                            updateItem(index, { unit_price: e.target.value, price: e.target.value })
                          }
                          placeholder="0.00"
                          className="bg-slate-950 border-slate-700 text-white"
                        />
                      </div>
                    </div>
                    <div className="mt-3 flex justify-end">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeItem(index)}
                        className="text-red-300 hover:text-red-200"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        删除明细
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogBody>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            className="bg-slate-700 border-slate-600 text-white">

            取消
          </Button>
          <Button
            onClick={onSubmit}
            className="bg-blue-500 hover:bg-blue-600 text-white">

            {submitLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}
