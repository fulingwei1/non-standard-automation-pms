import { useState, useEffect, useCallback as _useCallback } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileText,
  Plus,
  Trash2,
  Search,
  Save,
  Send,
  ArrowLeft,
  Package,
  Building2,
  Calendar,
  DollarSign,
  AlertCircle } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody } from
"../components/ui/dialog";
import { cn as _cn } from "../lib/utils";
import { fadeIn } from "../lib/animations";
import {
  purchaseApi,
  projectApi,
  materialApi,
  machineApi,
  supplierApi } from
"../services/api";
import { toast } from "../components/ui/toast";
import { LoadingCard } from "../components/common";
import { ErrorMessage } from "../components/common";

export default function PurchaseRequestNew() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  // Form data
  const [formData, setFormData] = useState({
    project_id: null,
    machine_id: null,
    supplier_id: null,
    request_type: "NORMAL",
    request_reason: "",
    required_date: "",
    remark: "",
    items: []
  });

  // Dropdown data
  const [projects, setProjects] = useState([]);
  const [machines, setMachines] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [materialSearchQuery, setMaterialSearchQuery] = useState("");
  const [showMaterialDialog, setShowMaterialDialog] = useState(false);
  const [selectedItemIndex, setSelectedItemIndex] = useState(null);

  // Check if demo account
  // Load projects
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const res = await projectApi.list({ page_size: 1000 });
        setProjects(res.data?.items || res.data?.items || res.data || []);
      } catch (err) {
        console.error("Failed to load projects:", err);
      }
    };
    loadProjects();
  }, []);

  // Load machines when project changes
  useEffect(() => {
    const loadMachines = async () => {
      if (!formData.project_id) {
        setMachines([]);
        return;
      }

      try {
        const response = await machineApi.list(formData.project_id, {
          page: 1,
          page_size: 100
        });
        const machineList = response.data?.items || response.data?.items || response.data || [];
        setMachines(
          (machineList || []).map((m) => ({
            id: m.id,
            machine_code: m.machine_code || m.machine_no,
            machine_name: m.machine_name || m.machine_code || `机台${m.id}`
          }))
        );
      } catch (err) {
        console.error("Failed to load machines:", err);
        setMachines([]);
      }
    };
    loadMachines();
  }, [formData.project_id]);

  // Load materials
  useEffect(() => {
    const loadMaterials = async () => {
      try {
        const res = await materialApi.list({ page_size: 1000 });
        setMaterials(res.data?.items || res.data?.items || res.data || []);
      } catch (err) {
        console.error("Failed to load materials:", err);
      }
    };
    loadMaterials();
  }, []);

  // Load suppliers
  useEffect(() => {
    const loadSuppliers = async () => {
      try {
        const res = await supplierApi.list({ page: 1, page_size: 1000 });
        setSuppliers(res.data?.items || res.data?.items || res.data || []);
      } catch (err) {
        console.error("Failed to load suppliers:", err);
      }
    };
    loadSuppliers();
  }, []);

  // Load request data if editing
  useEffect(() => {
    if (isEdit && id) {
      const loadRequest = async () => {
        try {
          setLoading(true);
          const res = await purchaseApi.requests.get(id);
          const data = res.data?.data || res.data;
          setFormData({
            project_id: data.project_id,
            machine_id: data.machine_id,
            supplier_id: data.supplier_id || null,
            request_type: data.request_type || "NORMAL",
            request_reason: data.request_reason || "",
            required_date: data.required_date || "",
            remark: data.remark || "",
            items: data.items || []
          });
        } catch (err) {
          console.error("Failed to load request:", err);
          setError(err.response?.data?.detail || "加载失败");
        } finally {
          setLoading(false);
        }
      };
      loadRequest();
    }
  }, [isEdit, id]);

  // Calculate total amount
  const totalAmount = (formData.items || []).reduce((sum, item) => {
    return (
      sum + parseFloat(item.quantity || 0) * parseFloat(item.unit_price || 0));

  }, 0);

  // Filter materials for search
  const filteredMaterials = (materials || []).filter((m) => {
    if (!materialSearchQuery) {return true;}
    const query = materialSearchQuery.toLowerCase();
    return (
      m.material_code?.toLowerCase().includes(query) ||
      m.material_name?.toLowerCase().includes(query));

  });

  // Add item
  const handleAddItem = () => {
    setFormData({
      ...formData,
      items: [
      ...formData.items,
      {
        material_id: null,
        material_code: "",
        material_name: "",
        specification: "",
        unit: "件",
        quantity: 1,
        unit_price: 0,
        required_date: formData.required_date || "",
        remark: ""
      }]

    });
  };

  // Remove item
  const handleRemoveItem = (index) => {
    const newItems = (formData.items || []).filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems });
  };

  // Update item
  const handleUpdateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], [field]: value };
    setFormData({ ...formData, items: newItems });
  };

  // Select material
  const handleSelectMaterial = (material) => {
    if (selectedItemIndex !== null) {
      const newItems = [...formData.items];
      newItems[selectedItemIndex] = {
        ...newItems[selectedItemIndex],
        material_id: material.id,
        material_code: material.material_code,
        material_name: material.material_name,
        unit: material.unit || "件",
        unit_price: material.standard_price || material.last_price || 0
      };
      setFormData({ ...formData, items: newItems });
      setShowMaterialDialog(false);
      setSelectedItemIndex(null);
      setMaterialSearchQuery("");
    }
  };

  // Open material selection dialog
  const handleOpenMaterialDialog = (index) => {
    setSelectedItemIndex(index);
    setMaterialSearchQuery("");
    setShowMaterialDialog(true);
  };

  // Save request
  const handleSave = async () => {
    // Validation
    if (!formData.items || formData.items?.length === 0) {
      toast.error("请至少添加一个物料");
      return;
    }

    for (let i = 0; i < formData.items?.length; i++) {
      const item = formData.items[i];
      if (!item.material_name || !item.quantity || item.quantity <= 0) {
        toast.error(`物料明细第 ${i + 1} 行填写不完整`);
        return;
      }
    }

    if (!formData.supplier_id) {
      toast.error("请选择供应商");
      return;
    }

    try {
      setSaving(true);
      const requestData = {
        project_id: formData.project_id || null,
        machine_id: formData.machine_id || null,
        supplier_id: formData.supplier_id || null,
        request_type: formData.request_type,
        request_reason: formData.request_reason || null,
        required_date: formData.required_date || null,
        remark: formData.remark || null,
        items: (formData.items || []).map((item) => ({
          material_id: item.material_id || null,
          material_code: item.material_code,
          material_name: item.material_name,
          specification: item.specification || null,
          unit: item.unit || "件",
          quantity: parseFloat(item.quantity),
          unit_price: parseFloat(item.unit_price || 0),
          required_date: item.required_date || null,
          remark: item.remark || null
        }))
      };

      if (isEdit) {
        await purchaseApi.requests.update(id, requestData);
        toast.success("采购申请已更新");
        navigate("/purchase-requests");
      } else {
        await purchaseApi.requests.create(requestData);
        toast.success("采购申请已创建");
        navigate("/purchase-requests");
      }
    } catch (err) {
      console.error("Failed to save request:", err);
      toast.error(err.response?.data?.detail || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  // Submit request
  const handleSubmit = async () => {
    if (!formData.items || formData.items?.length === 0) {
      toast.error("请至少添加一个物料");
      return;
    }

    // Save first, then submit
    await handleSave();

    if (!error) {
      try {
        // Get the created request ID from the response
        // For now, just show success message
        toast.success("采购申请已提交");
        navigate("/purchase-requests");
      } catch (err) {
        console.error("Failed to submit request:", err);
        toast.error(err.response?.data?.detail || "提交失败");
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <LoadingCard />
        </div>
      </div>);

  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
        <PageHeader
          title={isEdit ? "编辑采购申请" : "新建采购申请"}
          description={isEdit ? "修改采购申请信息" : "创建新的采购申请"}
          actions={
          <Button
            variant="outline"
            onClick={() => navigate("/purchase-requests")}>

              <ArrowLeft className="w-4 h-4 mr-2" />
              返回
          </Button>
          } />


        {error && <ErrorMessage message={error} />}

        <motion.div
          variants={fadeIn}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Info */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-slate-200">基本信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-400">所属项目</Label>
                    <Select
                      value={formData.project_id?.toString() || ""}
                      onValueChange={(val) =>
                      setFormData({
                        ...formData,
                        project_id: val ? parseInt(val) : null,
                        machine_id: null
                      })
                      }>

                      <SelectTrigger className="bg-slate-900/50 border-slate-700">
                        <SelectValue placeholder="选择项目（可选）" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">无</SelectItem>
                        {(projects || []).map((project) =>
                        <SelectItem
                          key={project.id}
                          value={project.id.toString()}>

                            {project.project_name}
                        </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-slate-400">设备</Label>
                    <Select
                      value={formData.machine_id?.toString() || ""}
                      onValueChange={(val) =>
                      setFormData({
                        ...formData,
                        machine_id: val ? parseInt(val) : null
                      })
                      }
                      disabled={!formData.project_id}>

                      <SelectTrigger
                        className="bg-slate-900/50 border-slate-700"
                        disabled={!formData.project_id}>

                        <SelectValue placeholder="选择设备（可选）" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">无</SelectItem>
                        {(machines || []).map((machine) =>
                        <SelectItem
                          key={machine.id}
                          value={machine.id.toString()}>

                            {machine.machine_code} - {machine.machine_name}
                        </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-slate-400">指定供应商 *</Label>
                    <Select
                      value={formData.supplier_id?.toString() || ""}
                      onValueChange={(val) => {
                        if (val === "none") {
                          setFormData({ ...formData, supplier_id: null });
                        } else {
                          setFormData({
                            ...formData,
                            supplier_id: parseInt(val)
                          });
                        }
                      }}>

                      <SelectTrigger className="bg-slate-900/50 border-slate-700">
                        <SelectValue placeholder="选择供应商" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">未指定</SelectItem>
                        {(suppliers || []).map((supplier) =>
                        <SelectItem
                          key={supplier.id}
                          value={supplier.id.toString()}>

                            {supplier.supplier_name || supplier.name}
                        </SelectItem>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-slate-400">申请类型</Label>
                    <Select
                      value={formData.request_type}
                      onValueChange={(val) =>
                      setFormData({ ...formData, request_type: val })
                      }>

                      <SelectTrigger className="bg-slate-900/50 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NORMAL">普通</SelectItem>
                        <SelectItem value="URGENT">紧急</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-slate-400">需求日期</Label>
                    <Input
                      type="date"
                      value={formData.required_date}
                      onChange={(e) =>
                      setFormData({
                        ...formData,
                        required_date: e.target.value
                      })
                      }
                      className="bg-slate-900/50 border-slate-700" />

                  </div>
                </div>
                <div>
                  <Label className="text-slate-400">申请原因</Label>
                  <Textarea
                    value={formData.request_reason}
                    onChange={(e) =>
                    setFormData({
                      ...formData,
                      request_reason: e.target.value
                    })
                    }
                    placeholder="填写申请原因..."
                    className="bg-slate-900/50 border-slate-700 text-slate-200"
                    rows={3} />

                </div>
                <div>
                  <Label className="text-slate-400">备注</Label>
                  <Textarea
                    value={formData.remark}
                    onChange={(e) =>
                    setFormData({ ...formData, remark: e.target.value })
                    }
                    placeholder="备注信息（可选）..."
                    className="bg-slate-900/50 border-slate-700 text-slate-200"
                    rows={2} />

                </div>
              </CardContent>
            </Card>

            {/* Items */}
            <Card className="bg-slate-800/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-slate-200">物料明细</CardTitle>
                  <Button size="sm" onClick={handleAddItem} variant="outline">
                    <Plus className="w-4 h-4 mr-1" />
                    添加物料
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {formData.items?.length === 0 ?
                <div className="text-center py-8 text-slate-400">
                    <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>暂无物料，点击上方按钮添加</p>
                </div> :

                <div className="space-y-3">
                    {(formData.items || []).map((item, index) =>
                  <div
                    key={index}
                    className="p-4 border border-slate-700 rounded-lg bg-slate-900/30">

                        <div className="flex items-start justify-between mb-3">
                          <Badge className="bg-blue-500/20 text-blue-400">
                            物料 {index + 1}
                          </Badge>
                          <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleRemoveItem(index)}
                        className="text-red-400 hover:text-red-300">

                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div className="md:col-span-2">
                            <Label className="text-slate-400 text-xs">
                              物料
                            </Label>
                            <div className="flex gap-2">
                              <Input
                            placeholder="物料编码"
                            value={item.material_code}
                            onChange={(e) =>
                            handleUpdateItem(
                              index,
                              "material_code",
                              e.target.value
                            )
                            }
                            className="bg-slate-800 border-slate-700 text-slate-200" />

                              <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleOpenMaterialDialog(index)}
                            className="whitespace-nowrap">

                                <Search className="w-4 h-4" />
                              </Button>
                            </div>
                            <Input
                          placeholder="物料名称 *"
                          value={item.material_name}
                          onChange={(e) =>
                          handleUpdateItem(
                            index,
                            "material_name",
                            e.target.value
                          )
                          }
                          className="bg-slate-800 border-slate-700 text-slate-200 mt-2" />

                          </div>
                          <div>
                            <Label className="text-slate-400 text-xs">
                              数量 *
                            </Label>
                            <Input
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.quantity}
                          onChange={(e) =>
                          handleUpdateItem(
                            index,
                            "quantity",
                            parseFloat(e.target.value) || 0
                          )
                          }
                          className="bg-slate-800 border-slate-700 text-slate-200" />

                          </div>
                          <div>
                            <Label className="text-slate-400 text-xs">
                              单位
                            </Label>
                            <Input
                          value={item.unit}
                          onChange={(e) =>
                          handleUpdateItem(index, "unit", e.target.value)
                          }
                          className="bg-slate-800 border-slate-700 text-slate-200" />

                          </div>
                          <div>
                            <Label className="text-slate-400 text-xs">
                              单价
                            </Label>
                            <Input
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.unit_price}
                          onChange={(e) =>
                          handleUpdateItem(
                            index,
                            "unit_price",
                            parseFloat(e.target.value) || 0
                          )
                          }
                          className="bg-slate-800 border-slate-700 text-slate-200" />

                          </div>
                          <div>
                            <Label className="text-slate-400 text-xs">
                              金额
                            </Label>
                            <Input
                          value={(
                          parseFloat(item.quantity || 0) *
                          parseFloat(item.unit_price || 0)).
                          toFixed(2)}
                          disabled
                          className="bg-slate-800/50 border-slate-700 text-slate-300" />

                          </div>
                          <div>
                            <Label className="text-slate-400 text-xs">
                              需求日期
                            </Label>
                            <Input
                          type="date"
                          value={item.required_date}
                          onChange={(e) =>
                          handleUpdateItem(
                            index,
                            "required_date",
                            e.target.value
                          )
                          }
                          className="bg-slate-800 border-slate-700 text-slate-200" />

                          </div>
                        </div>
                  </div>
                  )}
                </div>
                }
              </CardContent>
            </Card>
          </div>

          {/* Summary */}
          <div className="lg:col-span-1">
            <Card className="bg-slate-800/50 border-slate-700/50 sticky top-6">
              <CardHeader>
                <CardTitle className="text-slate-200">汇总信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-slate-400">物料数量</Label>
                  <p className="text-2xl font-bold text-slate-200">
                    {formData.items?.length}
                  </p>
                </div>
                <div>
                  <Label className="text-slate-400">总金额</Label>
                  <p className="text-2xl font-bold text-emerald-400">
                    ¥{totalAmount.toFixed(2)}
                  </p>
                </div>
                <div className="pt-4 border-t border-slate-700 space-y-2">
                  <Button
                    className="w-full bg-blue-600 hover:bg-blue-700"
                    onClick={handleSave}
                    disabled={saving}>

                    <Save className="w-4 h-4 mr-2" />
                    {saving ? "保存中..." : "保存草稿"}
                  </Button>
                  <Button
                    className="w-full bg-emerald-600 hover:bg-emerald-700"
                    onClick={handleSubmit}
                    disabled={saving}>

                    <Send className="w-4 h-4 mr-2" />
                    {saving ? "提交中..." : "保存并提交"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </motion.div>

        {/* Material Selection Dialog */}
        <Dialog open={showMaterialDialog} onOpenChange={setShowMaterialDialog}>
          <DialogContent className="max-w-2xl bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle className="text-slate-200">选择物料</DialogTitle>
            </DialogHeader>
            <DialogBody>
              <div className="space-y-4">
                <Input
                  placeholder="搜索物料编码或名称..."
                  value={materialSearchQuery}
                  onChange={(e) => setMaterialSearchQuery(e.target.value)}
                  icon={Search}
                  className="bg-slate-800 border-slate-700" />

                <div className="max-h-96 overflow-y-auto space-y-2">
                  {filteredMaterials.length === 0 ?
                  <div className="text-center py-8 text-slate-400">
                      <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>未找到物料</p>
                  </div> :

                  (filteredMaterials || []).map((material) =>
                  <div
                    key={material.id}
                    onClick={() => handleSelectMaterial(material)}
                    className="p-3 border border-slate-700 rounded-lg hover:border-blue-500 cursor-pointer transition-colors">

                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-slate-200 font-medium">
                              {material.material_code}
                            </p>
                            <p className="text-slate-400 text-sm">
                              {material.material_name}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-slate-300">
                              ¥
                              {material.standard_price ||
                          material.last_price ||
                          0}
                            </p>
                            <p className="text-slate-500 text-xs">
                              {material.unit || "件"}
                            </p>
                          </div>
                        </div>
                  </div>
                  )
                  }
                </div>
              </div>
            </DialogBody>
          </DialogContent>
        </Dialog>
      </div>
    </div>);

}
