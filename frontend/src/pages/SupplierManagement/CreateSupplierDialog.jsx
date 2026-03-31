import { useState } from "react";
import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  Label,
  Textarea,
} from "../../components/ui";
import { supplierApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

function CreateSupplierDialog({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    supplier_code: "",
    supplier_name: "",
    supplier_short_name: "",
    supplier_type: "",
    contact_person: "",
    contact_phone: "",
    contact_email: "",
    address: "",
    business_license: "",
    bank_name: "",
    bank_account: "",
    tax_number: "",
    payment_terms: "",
    remark: "",
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    // Validation
    const newErrors = {};
    if (!formData.supplier_code.trim()) {
      newErrors.supplier_code = "请输入供应商编码";
    }
    if (!formData.supplier_name.trim()) {
      newErrors.supplier_name = "请输入供应商名称";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setLoading(true);
      await supplierApi.create(formData);
      onSuccess();
    } catch (error) {
      console.error("Failed to create supplier:", error);
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
          <DialogTitle>新建供应商</DialogTitle>
        </DialogHeader>
        <DialogBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="required">
                供应商编码 <span className="text-red-400">*</span>
              </Label>
              <Input
                value={formData.supplier_code}
                onChange={(e) =>
                setFormData({ ...formData, supplier_code: e.target.value })
                }
                placeholder="请输入供应商编码"
                className={errors.supplier_code ? "border-red-400" : ""} />

              {errors.supplier_code &&
              <div className="text-sm text-red-400 mt-1">
                  {errors.supplier_code}
              </div>
              }
            </div>
            <div>
              <Label className="required">
                供应商名称 <span className="text-red-400">*</span>
              </Label>
              <Input
                value={formData.supplier_name}
                onChange={(e) =>
                setFormData({ ...formData, supplier_name: e.target.value })
                }
                placeholder="请输入供应商名称"
                className={errors.supplier_name ? "border-red-400" : ""} />

              {errors.supplier_name &&
              <div className="text-sm text-red-400 mt-1">
                  {errors.supplier_name}
              </div>
              }
            </div>
            <div>
              <Label>供应商简称</Label>
              <Input
                value={formData.supplier_short_name}
                onChange={(e) =>
                setFormData({
                  ...formData,
                  supplier_short_name: e.target.value,
                })
                }
                placeholder="请输入供应商简称" />

            </div>
            <div>
              <Label>供应商类型</Label>
              <Input
                value={formData.supplier_type}
                onChange={(e) =>
                setFormData({ ...formData, supplier_type: e.target.value })
                }
                placeholder="如：电子元器件、机械件等" />

            </div>
            <div>
              <Label>联系人</Label>
              <Input
                value={formData.contact_person}
                onChange={(e) =>
                setFormData({ ...formData, contact_person: e.target.value })
                }
                placeholder="请输入联系人姓名" />

            </div>
            <div>
              <Label>联系电话</Label>
              <Input
                value={formData.contact_phone}
                onChange={(e) =>
                setFormData({ ...formData, contact_phone: e.target.value })
                }
                placeholder="请输入联系电话" />

            </div>
            <div>
              <Label>联系邮箱</Label>
              <Input
                type="email"
                value={formData.contact_email}
                onChange={(e) =>
                setFormData({ ...formData, contact_email: e.target.value })
                }
                placeholder="请输入联系邮箱" />

            </div>
            <div>
              <Label>地址</Label>
              <Input
                value={formData.address}
                onChange={(e) =>
                setFormData({ ...formData, address: e.target.value })
                }
                placeholder="请输入供应商地址" />

            </div>
            <div>
              <Label>营业执照号</Label>
              <Input
                value={formData.business_license}
                onChange={(e) =>
                setFormData({ ...formData, business_license: e.target.value })
                }
                placeholder="请输入营业执照号" />

            </div>
            <div>
              <Label>开户银行</Label>
              <Input
                value={formData.bank_name}
                onChange={(e) =>
                setFormData({ ...formData, bank_name: e.target.value })
                }
                placeholder="请输入开户银行" />

            </div>
            <div>
              <Label>银行账号</Label>
              <Input
                value={formData.bank_account}
                onChange={(e) =>
                setFormData({ ...formData, bank_account: e.target.value })
                }
                placeholder="请输入银行账号" />

            </div>
            <div>
              <Label>税号</Label>
              <Input
                value={formData.tax_number}
                onChange={(e) =>
                setFormData({ ...formData, tax_number: e.target.value })
                }
                placeholder="请输入税号" />

            </div>
            <div>
              <Label>付款条件</Label>
              <Input
                value={formData.payment_terms}
                onChange={(e) =>
                setFormData({ ...formData, payment_terms: e.target.value })
                }
                placeholder="如：2/10 N30" />

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
            {loading ? "创建中..." : "创建供应商"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>);

}

export default CreateSupplierDialog;
