/**
 * Material Arrival New - 新建到货跟踪
 * 创建到货跟踪记录，可以从采购订单或缺料上报创建
 */

import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Truck, Save, X, Search, Calendar } from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Input,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea } from
"../components/ui";
import { fadeIn } from "../lib/animations";
import {
  shortageApi,
  materialApi,
  purchaseApi as _purchaseApi,
  supplierApi } from
"../services/api";

export default function ArrivalNew() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [materials, setMaterials] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [formData, setFormData] = useState({
    shortage_report_id: location.state?.shortage_report_id || "",
    purchase_order_id: location.state?.purchase_order_id || "",
    purchase_order_item_id: location.state?.purchase_order_item_id || "",
    material_id: location.state?.material_id || "",
    expected_qty: "",
    supplier_id: "",
    supplier_name: "",
    expected_date: "",
    remark: ""
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    loadMaterials();
    loadSuppliers();
    // 如果有传入的物料ID，设置默认值
    if (location.state?.material_id) {
      const material = materials.find(
        (m) => m.id === location.state.material_id
      );
      if (material) {
        setFormData((prev) => ({
          ...prev,
          material_id: String(material.id)
        }));
      }
    }
  }, []);

  const loadMaterials = async () => {
    try {
      const res = await materialApi.list({
        page: 1,
        page_size: 100,
        is_active: true
      });
      setMaterials(res.data.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("加载物料列表失败", error);
    }
  };

  const loadSuppliers = async () => {
    try {
      const res = await supplierApi.list({ page: 1, page_size: 100 });
      setSuppliers(res.data.items || res.data?.items || res.data || []);
    } catch (error) {
      console.error("加载供应商列表失败", error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // 验证
    const newErrors = {};
    if (!formData.material_id) {newErrors.material_id = "请选择物料";}
    if (!formData.expected_qty || parseFloat(formData.expected_qty) <= 0) {
      newErrors.expected_qty = "请输入有效的预期数量";
    }
    if (!formData.expected_date) {newErrors.expected_date = "请选择预期到货日期";}

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      const submitData = {
        ...formData,
        shortage_report_id: formData.shortage_report_id ?
        parseInt(formData.shortage_report_id) :
        null,
        purchase_order_id: formData.purchase_order_id ?
        parseInt(formData.purchase_order_id) :
        null,
        purchase_order_item_id: formData.purchase_order_item_id ?
        parseInt(formData.purchase_order_item_id) :
        null,
        material_id: parseInt(formData.material_id),
        expected_qty: parseFloat(formData.expected_qty),
        supplier_id: formData.supplier_id ?
        parseInt(formData.supplier_id) :
        null,
        expected_date: formData.expected_date
      };

      const res = await shortageApi.arrivals.create(submitData);
      alert("到货跟踪创建成功！");
      navigate(`/shortage/arrivals/${res.data.id}`);
    } catch (error) {
      console.error("创建到货跟踪失败", error);
      alert("创建失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: null }));
    }

    // 如果选择了供应商，自动填充供应商名称
    if (field === "supplier_id" && value) {
      const supplier = suppliers.find((s) => s.id === parseInt(value));
      if (supplier) {
        setFormData((prev) => ({
          ...prev,
          supplier_name: supplier.supplier_name || ""
        }));
      }
    }
  };

  const filteredMaterials = materials.filter(
    (m) =>
    !searchKeyword ||
    m.material_code?.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    m.material_name?.toLowerCase().includes(searchKeyword.toLowerCase())
  );

  // 设置默认日期为7天后
  useEffect(() => {
    if (!formData.expected_date) {
      const defaultDate = new Date();
      defaultDate.setDate(defaultDate.getDate() + 7);
      setFormData((prev) => ({
        ...prev,
        expected_date: defaultDate.toISOString().split("T")[0]
      }));
    }
  }, []);

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate("/shortage")}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          返回
        </Button>
        <PageHeader title="新建到货跟踪" description="创建物料到货跟踪记录" />
      </div>

      <motion.form
        variants={fadeIn}
        initial="hidden"
        animate="visible"
        onSubmit={handleSubmit}
        className="max-w-4xl">

        <Card>
          <CardHeader>
            <CardTitle>关联信息</CardTitle>
            <CardDescription>关联缺料上报或采购订单（可选）</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="shortage_report_id">关联缺料上报（可选）</Label>
                <Input
                  id="shortage_report_id"
                  type="number"
                  placeholder="缺料上报ID"
                  value={formData.shortage_report_id}
                  onChange={(e) =>
                  handleChange("shortage_report_id", e.target.value)
                  } />

              </div>

              <div>
                <Label htmlFor="purchase_order_id">关联采购订单（可选）</Label>
                <Input
                  id="purchase_order_id"
                  type="number"
                  placeholder="采购订单ID"
                  value={formData.purchase_order_id}
                  onChange={(e) =>
                  handleChange("purchase_order_id", e.target.value)
                  } />

              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>物料信息</CardTitle>
            <CardDescription>选择物料和供应商</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="material_id" className="required">
                物料 <span className="text-red-400">*</span>
              </Label>
              <div className="space-y-2">
                <Input
                  placeholder="搜索物料编码或名称..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="mb-2" />

                <Select
                  value={formData.material_id}
                  onValueChange={(value) => handleChange("material_id", value)}>

                  <SelectTrigger
                    id="material_id"
                    className={errors.material_id ? "border-red-400" : ""}>

                    <SelectValue placeholder="请选择物料" />
                  </SelectTrigger>
                  <SelectContent>
                    {filteredMaterials.map((material) =>
                    <SelectItem key={material.id} value={String(material.id)}>
                        {material.material_code} - {material.material_name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {errors.material_id &&
                <div className="text-sm text-red-400 mt-1">
                    {errors.material_id}
                </div>
                }
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="expected_qty" className="required">
                  预期数量 <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="expected_qty"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0.00"
                  value={formData.expected_qty}
                  onChange={(e) => handleChange("expected_qty", e.target.value)}
                  className={errors.expected_qty ? "border-red-400" : ""} />

                {errors.expected_qty &&
                <div className="text-sm text-red-400 mt-1">
                    {errors.expected_qty}
                </div>
                }
              </div>

              <div>
                <Label htmlFor="expected_date" className="required">
                  预期到货日期 <span className="text-red-400">*</span>
                </Label>
                <Input
                  id="expected_date"
                  type="date"
                  value={formData.expected_date}
                  onChange={(e) =>
                  handleChange("expected_date", e.target.value)
                  }
                  className={errors.expected_date ? "border-red-400" : ""} />

                {errors.expected_date &&
                <div className="text-sm text-red-400 mt-1">
                    {errors.expected_date}
                </div>
                }
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="supplier_id">供应商（可选）</Label>
                <Select
                  value={formData.supplier_id}
                  onValueChange={(value) => handleChange("supplier_id", value)}>

                  <SelectTrigger id="supplier_id">
                    <SelectValue placeholder="请选择供应商" />
                  </SelectTrigger>
                  <SelectContent>
                    {suppliers.map((supplier) =>
                    <SelectItem key={supplier.id} value={String(supplier.id)}>
                        {supplier.supplier_name} ({supplier.supplier_code})
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="supplier_name">供应商名称</Label>
                <Input
                  id="supplier_name"
                  placeholder="或手动输入供应商名称"
                  value={formData.supplier_name}
                  onChange={(e) =>
                  handleChange("supplier_name", e.target.value)
                  } />

              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>备注</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="其他需要说明的信息..."
              value={formData.remark}
              onChange={(e) => handleChange("remark", e.target.value)}
              rows={3} />

          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/shortage")}
            disabled={loading}>

            <X className="h-4 w-4 mr-2" />
            取消
          </Button>
          <Button type="submit" disabled={loading}>
            <Save className="h-4 w-4 mr-2" />
            {loading ? "提交中..." : "创建跟踪"}
          </Button>
        </div>
      </motion.form>
    </div>);

}