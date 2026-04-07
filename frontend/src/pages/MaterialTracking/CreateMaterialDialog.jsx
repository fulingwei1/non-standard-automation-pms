/**
 * Material Tracking - Create Material Dialog
 * Form dialog for creating a new material entry
 */

import { useState } from "react";


import { materialApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

function CreateMaterialDialog({ categories, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    material_code: "",
    material_name: "",
    category_id: null,
    specification: "",
    brand: "",
    unit: "件",
    drawing_no: "",
    material_type: "",
    source_type: "PURCHASE",
    standard_price: 0,
    safety_stock: 0,
    lead_time_days: 0,
    min_order_qty: 1,
    default_supplier_id: null,
    is_key_material: false,
    remark: ""
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    // Validation
    const newErrors = {};
    if (!formData.material_code.trim()) {
      newErrors.material_code = "请输入物料编码";
    }
    if (!formData.material_name.trim()) {
      newErrors.material_name = "请输入物料名称";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setLoading(true);
      const submitData = {
        ...formData,
        category_id: formData.category_id || undefined,
        default_supplier_id: formData.default_supplier_id || undefined,
        standard_price: parseFloat(formData.standard_price) || 0,
        safety_stock: parseFloat(formData.safety_stock) || 0,
        min_order_qty: parseFloat(formData.min_order_qty) || 1
      };
      await materialApi.create(submitData);
      onSuccess();
    } catch (error) {
      console.error("Failed to create material:", error);
      toast.error(
        "创建失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-700">
        <DialogHeader>
          <DialogTitle>新建物料</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="required">
                物料编码 <span className="text-red-400">*</span>
              </Label>
              <Input
                value={formData.material_code}
                onChange={(e) =>
                setFormData({ ...formData, material_code: e.target.value })
                }
                placeholder="请输入物料编码"
                className={errors.material_code ? "border-red-400" : ""} />

              {errors.material_code &&
              <div className="text-sm text-red-400 mt-1">
                  {errors.material_code}
              </div>
              }
            </div>
            <div>
              <Label className="required">
                物料名称 <span className="text-red-400">*</span>
              </Label>
              <Input
                value={formData.material_name}
                onChange={(e) =>
                setFormData({ ...formData, material_name: e.target.value })
                }
                placeholder="请输入物料名称"
                className={errors.material_name ? "border-red-400" : ""} />

              {errors.material_name &&
              <div className="text-sm text-red-400 mt-1">
                  {errors.material_name}
              </div>
              }
            </div>
            <div>
              <Label>物料分类</Label>
              <Select
                value={formData.category_id?.toString() || ""}
                onValueChange={(value) =>
                setFormData({
                  ...formData,
                  category_id: value ? parseInt(value) : null
                })
                }>

                <SelectTrigger>
                  <SelectValue placeholder="请选择物料分类" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">无分类</SelectItem>
                  {(categories || []).map((cat) =>
                  <SelectItem key={cat.id} value={cat.id.toString()}>
                      {cat.category_name}
                  </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>规格型号</Label>
              <Input
                value={formData.specification}
                onChange={(e) =>
                setFormData({ ...formData, specification: e.target.value })
                }
                placeholder="请输入规格型号" />

            </div>
            <div>
              <Label>品牌</Label>
              <Input
                value={formData.brand}
                onChange={(e) =>
                setFormData({ ...formData, brand: e.target.value })
                }
                placeholder="请输入品牌" />

            </div>
            <div>
              <Label>单位</Label>
              <Input
                value={formData.unit}
                onChange={(e) =>
                setFormData({ ...formData, unit: e.target.value })
                }
                placeholder="如：件、个、根等" />

            </div>
            <div>
              <Label>图号</Label>
              <Input
                value={formData.drawing_no}
                onChange={(e) =>
                setFormData({ ...formData, drawing_no: e.target.value })
                }
                placeholder="请输入图号" />

            </div>
            <div>
              <Label>物料类型</Label>
              <Input
                value={formData.material_type}
                onChange={(e) =>
                setFormData({ ...formData, material_type: e.target.value })
                }
                placeholder="如：标准件、机械件、电气件等" />

            </div>
            <div>
              <Label>来源类型</Label>
              <Select
                value={formData.source_type}
                onValueChange={(value) =>
                setFormData({ ...formData, source_type: value })
                }>

                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PURCHASE">采购</SelectItem>
                  <SelectItem value="SELF_MADE">自制</SelectItem>
                  <SelectItem value="OUTSOURCING">外协</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>标准价格</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.standard_price}
                onChange={(e) =>
                setFormData({ ...formData, standard_price: e.target.value })
                }
                placeholder="0.00" />

            </div>
            <div>
              <Label>安全库存</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.safety_stock}
                onChange={(e) =>
                setFormData({ ...formData, safety_stock: e.target.value })
                }
                placeholder="0" />

            </div>
            <div>
              <Label>交期（天）</Label>
              <Input
                type="number"
                value={formData.lead_time_days}
                onChange={(e) =>
                setFormData({
                  ...formData,
                  lead_time_days: parseInt(e.target.value) || 0
                })
                }
                placeholder="0" />

            </div>
            <div>
              <Label>最小订购量</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.min_order_qty}
                onChange={(e) =>
                setFormData({ ...formData, min_order_qty: e.target.value })
                }
                placeholder="1" />

            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_key_material"
                checked={formData.is_key_material}
                onChange={(e) =>
                setFormData({
                  ...formData,
                  is_key_material: e.target.checked
                })
                }
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500" />

              <Label htmlFor="is_key_material" className="cursor-pointer">
                关键物料
              </Label>
            </div>
          </div>
          <div>
            <Label>备注</Label>
            <Textarea
              value={formData.remark}
              onChange={(e) =>
              setFormData({ ...formData, remark: e.target.value })
              }
              placeholder="请输入备注信息"
              rows={3}
              className="bg-slate-800/50 border-slate-700" />

          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>
            取消
          </Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? "创建中..." : "创建物料"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}

export default CreateMaterialDialog;
