/**
 * CreateEditOrderDialog - 采购订单创建/编辑对话框
 * 支持创建新订单和编辑现有订单
 */

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody } from
"../../ui/dialog";
import { Button } from "../../ui/button";
import { Label } from "../../ui/label";
import { Textarea } from "../../ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../ui/select";
import { PAYMENT_TERMS, PAYMENT_TERMS_CONFIGS, SHIPPING_METHODS } from "@/lib/constants/procurement";

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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] bg-slate-800/50 border border-slate-700/50">
        <DialogHeader>
          <DialogTitle className="text-white">{title}</DialogTitle>
        </DialogHeader>

        <DialogBody className="space-y-4">
          {/* 供应商和项目 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-slate-400">供应商</Label>
              <Select
                value={orderData?.supplier_id || ""}
                onValueChange={(value) => onChange?.({ ...orderData, supplier_id: value })}>

                <SelectTrigger className="bg-slate-900 border-slate-700 text-white">
                  <SelectValue placeholder="选择供应商" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  {suppliers.map((supplier) =>
                  <SelectItem key={supplier.id} value={supplier.id}>
                      {supplier.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className="text-slate-400">项目</Label>
              <Select
                value={orderData?.project_id || ""}
                onValueChange={(value) => onChange?.({ ...orderData, project_id: value })}>

                <SelectTrigger className="bg-slate-900 border-slate-700 text-white">
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  {projects.map((project) =>
                  <SelectItem key={project.id} value={project.id}>
                      {project.name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
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
                  {Object.entries(SHIPPING_METHODS).map(([key, config]) =>
                  <SelectItem key={key} value={key}>
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