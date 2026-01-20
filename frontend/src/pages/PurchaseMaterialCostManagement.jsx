/**
 * Purchase Material Cost Management Page - 采购物料成本清单管理页面
 * Features: List, create, edit, delete purchase material costs (采购部维护标准件成本)
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  Search,
  Filter,
  Edit,
  Trash2,
  Eye,
  Upload,
  Download,
  CheckCircle2,
  XCircle,
  DollarSign,
  Package,
  Calendar,
  Building2,
  Bell,
  AlertTriangle,
  Clock,
  Settings } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Input,
  Label,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui";
import { cn as _cn, formatCurrency, formatDate } from "../lib/utils";
import { fadeIn as _fadeIn, staggerContainer } from "../lib/animations";
import { salesTemplateApi, supplierApi } from "../services/api";

export default function PurchaseMaterialCostManagement() {
  const [loading, setLoading] = useState(false);
  const [costs, setCosts] = useState([]);
  const [filteredCosts, setFilteredCosts] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [standardFilter, setStandardFilter] = useState("all");
  const [activeFilter, setActiveFilter] = useState("all");

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedCost, setSelectedCost] = useState(null);

  // Suppliers
  const [suppliers, setSuppliers] = useState([]);

  // Reminder
  const [reminder, setReminder] = useState(null);
  const [showReminderDialog, setShowReminderDialog] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    material_code: "",
    material_name: "",
    specification: "",
    brand: "",
    unit: "件",
    material_type: "",
    is_standard_part: true,
    unit_cost: "",
    currency: "CNY",
    supplier_id: "",
    supplier_name: "",
    purchase_date: "",
    purchase_order_no: "",
    purchase_quantity: "",
    lead_time_days: "",
    is_active: true,
    match_priority: 0,
    match_keywords: "",
    remark: ""
  });

  useEffect(() => {
    loadCosts();
    loadSuppliers();
    loadReminder();
  }, []);

  const loadReminder = async () => {
    try {
      const res = await salesTemplateApi.getCostUpdateReminder();
      const reminderData = res.data?.data || res.data;
      setReminder(reminderData);

      // 如果提醒到期，自动显示提醒对话框
      if (reminderData?.is_due) {
        setShowReminderDialog(true);
      }
    } catch (error) {
      console.error("加载提醒信息失败:", error);
    }
  };

  const handleAcknowledgeReminder = async () => {
    try {
      await salesTemplateApi.acknowledgeCostUpdateReminder();
      await loadReminder();
      setShowReminderDialog(false);
    } catch (error) {
      console.error("确认提醒失败:", error);
      alert("确认提醒失败: " + (error.response?.data?.detail || error.message));
    }
  };

  useEffect(() => {
    filterCosts();
  }, [costs, searchTerm, typeFilter, standardFilter, activeFilter]);

  const loadCosts = async () => {
    setLoading(true);
    try {
      const res = await salesTemplateApi.listPurchaseMaterialCosts({
        page: 1,
        page_size: 1000
      });
      const items = res.data?.data?.items || res.data?.items || [];
      setCosts(items);
    } catch (error) {
      console.error("加载成本清单失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadSuppliers = async () => {
    try {
      const res = await supplierApi.list({ page: 1, page_size: 1000 });
      const items = res.data?.data?.items || res.data?.items || [];
      setSuppliers(items);
    } catch (error) {
      console.error("加载供应商列表失败:", error);
    }
  };

  const filterCosts = () => {
    let filtered = [...costs];

    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
        c.material_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.material_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.specification?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (typeFilter !== "all") {
      filtered = filtered.filter((c) => c.material_type === typeFilter);
    }

    if (standardFilter !== "all") {
      filtered = filtered.filter(
        (c) => c.is_standard_part === (standardFilter === "standard")
      );
    }

    if (activeFilter !== "all") {
      filtered = filtered.filter(
        (c) => c.is_active === (activeFilter === "active")
      );
    }

    setFilteredCosts(filtered);
  };

  const handleCreate = () => {
    setFormData({
      material_code: "",
      material_name: "",
      specification: "",
      brand: "",
      unit: "件",
      material_type: "",
      is_standard_part: true,
      unit_cost: "",
      currency: "CNY",
      supplier_id: "",
      supplier_name: "",
      purchase_date: "",
      purchase_order_no: "",
      purchase_quantity: "",
      lead_time_days: "",
      is_active: true,
      match_priority: 0,
      match_keywords: "",
      remark: ""
    });
    setShowCreateDialog(true);
  };

  const handleEdit = (cost) => {
    setSelectedCost(cost);
    setFormData({
      material_code: cost.material_code || "",
      material_name: cost.material_name || "",
      specification: cost.specification || "",
      brand: cost.brand || "",
      unit: cost.unit || "件",
      material_type: cost.material_type || "",
      is_standard_part: cost.is_standard_part !== false,
      unit_cost: cost.unit_cost || "",
      currency: cost.currency || "CNY",
      supplier_id: cost.supplier_id || "",
      supplier_name: cost.supplier_name || "",
      purchase_date: cost.purchase_date || "",
      purchase_order_no: cost.purchase_order_no || "",
      purchase_quantity: cost.purchase_quantity || "",
      lead_time_days: cost.lead_time_days || "",
      is_active: cost.is_active !== false,
      match_priority: cost.match_priority || 0,
      match_keywords: cost.match_keywords || "",
      remark: cost.remark || ""
    });
    setShowEditDialog(true);
  };

  const handleDelete = (cost) => {
    setSelectedCost(cost);
    setShowDeleteDialog(true);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const submitData = {
        ...formData,
        unit_cost: parseFloat(formData.unit_cost) || 0,
        purchase_quantity: formData.purchase_quantity ?
        parseFloat(formData.purchase_quantity) :
        null,
        lead_time_days: formData.lead_time_days ?
        parseInt(formData.lead_time_days) :
        null,
        match_priority: parseInt(formData.match_priority) || 0,
        supplier_id: formData.supplier_id ?
        parseInt(formData.supplier_id) :
        null
      };

      if (selectedCost) {
        await salesTemplateApi.updatePurchaseMaterialCost(
          selectedCost.id,
          submitData
        );
      } else {
        await salesTemplateApi.createPurchaseMaterialCost(submitData);
      }
      await loadCosts();
      setShowCreateDialog(false);
      setShowEditDialog(false);
      setSelectedCost(null);
    } catch (error) {
      console.error("保存失败:", error);
      alert("保存失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDelete = async () => {
    try {
      setLoading(true);
      await salesTemplateApi.deletePurchaseMaterialCost(selectedCost.id);
      await loadCosts();
      setShowDeleteDialog(false);
      setSelectedCost(null);
    } catch (error) {
      console.error("删除失败:", error);
      alert("删除失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // Get unique material types
  const materialTypes = useMemo(() => {
    const types = new Set();
    costs.forEach((c) => {
      if (c.material_type) {types.add(c.material_type);}
    });
    return Array.from(types);
  }, [costs]);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6">

      <PageHeader
        title="采购物料成本清单管理"
        description="采购部维护标准件等常用物料的历史采购成本，用于报价成本自动匹配"
        actions={
        <div className="flex gap-2">
            {reminder &&
          <Button
            variant={reminder.is_due ? "default" : "outline"}
            className={
            reminder.is_due ? "bg-amber-500 hover:bg-amber-600" : ""
            }
            onClick={() => setShowReminderDialog(true)}>

                <Bell className="h-4 w-4 mr-2" />
                {reminder.is_due ? "更新提醒" : "提醒设置"}
                {reminder.is_due &&
            <Badge className="ml-2 bg-red-500">到期</Badge>
            }
          </Button>
          }
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              导出
            </Button>
            <Button variant="outline">
              <Upload className="h-4 w-4 mr-2" />
              导入
            </Button>
            <Button onClick={handleCreate}>
              <Plus className="h-4 w-4 mr-2" />
              新增成本
            </Button>
        </div>
        } />


      {/* Update Reminder Alert */}
      {reminder && reminder.is_due &&
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-amber-900/20 border border-amber-500/50 rounded-lg p-4 mb-6">

          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <div className="font-medium text-amber-400 mb-1">
                物料成本更新提醒
              </div>
              <div className="text-sm text-slate-300 mb-3">
                距离上次更新已超过 {reminder.reminder_interval_days}{" "}
                天，请及时更新物料成本信息，确保报价成本准确性。
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={handleAcknowledgeReminder}>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  我已更新，确认提醒
                </Button>
                <Button
                size="sm"
                variant="outline"
                onClick={() => setShowReminderDialog(true)}>

                  <Settings className="h-4 w-4 mr-2" />
                  设置提醒
                </Button>
              </div>
            </div>
          </div>
      </motion.div>
      }

      {/* Reminder Info Card (when not due) */}
      {reminder && !reminder.is_due && reminder.days_until_next !== null &&
      <Card className="mb-6 border-blue-500/30 bg-blue-900/10">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Bell className="h-5 w-5 text-blue-400" />
                <div>
                  <div className="font-medium text-blue-400">下次更新提醒</div>
                  <div className="text-sm text-slate-400">
                    距离下次提醒还有{" "}
                    <strong className="text-blue-300">
                      {reminder.days_until_next}
                    </strong>{" "}
                    天
                    {reminder.next_reminder_date &&
                  ` (${formatDate(reminder.next_reminder_date)})`}
                  </div>
                </div>
              </div>
              <Button
              variant="outline"
              size="sm"
              onClick={() => setShowReminderDialog(true)}>

                <Settings className="h-4 w-4 mr-2" />
                设置
              </Button>
            </div>
          </CardContent>
      </Card>
      }

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="搜索物料名称、编码或规格..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10" />

              </div>
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="物料类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {materialTypes.map((type) =>
                <SelectItem key={type} value={type}>
                    {type}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={standardFilter} onValueChange={setStandardFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="标准件" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="standard">标准件</SelectItem>
                <SelectItem value="non-standard">非标准件</SelectItem>
              </SelectContent>
            </Select>
            <Select value={activeFilter} onValueChange={setActiveFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="启用状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="active">启用</SelectItem>
                <SelectItem value="inactive">禁用</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Cost List */}
      <Card>
        <CardHeader>
          <CardTitle>成本清单</CardTitle>
          <CardDescription>共 {filteredCosts.length} 条记录</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>物料名称</TableHead>
                <TableHead>规格型号</TableHead>
                <TableHead>物料类型</TableHead>
                <TableHead>单位成本</TableHead>
                <TableHead>供应商</TableHead>
                <TableHead>采购日期</TableHead>
                <TableHead>优先级</TableHead>
                <TableHead>使用次数</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCosts.map((cost) =>
              <TableRow key={cost.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{cost.material_name}</div>
                      {cost.material_code &&
                    <div className="text-xs text-slate-400">
                          {cost.material_code}
                    </div>
                    }
                    </div>
                  </TableCell>
                  <TableCell>{cost.specification || "-"}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{cost.material_type || "-"}</Badge>
                  </TableCell>
                  <TableCell className="font-medium">
                    {formatCurrency(cost.unit_cost || 0)}
                  </TableCell>
                  <TableCell>{cost.supplier_name || "-"}</TableCell>
                  <TableCell>
                    {cost.purchase_date ? formatDate(cost.purchase_date) : "-"}
                  </TableCell>
                  <TableCell>
                    <Badge
                    className={
                    cost.match_priority > 0 ? "bg-blue-500" : "bg-slate-500"
                    }>

                      {cost.match_priority}
                    </Badge>
                  </TableCell>
                  <TableCell>{cost.usage_count || 0}</TableCell>
                  <TableCell>
                    <Badge
                    className={
                    cost.is_active ? "bg-green-500" : "bg-slate-500"
                    }>

                      {cost.is_active ? "启用" : "禁用"}
                    </Badge>
                    {cost.is_standard_part &&
                  <Badge className="ml-2 bg-purple-500">标准件</Badge>
                  }
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(cost)}>

                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(cost)}
                      className="text-red-400">

                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
              </TableRow>
              )}
            </TableBody>
          </Table>

          {filteredCosts.length === 0 && !loading &&
          <div className="text-center py-12 text-slate-400">
              暂无成本记录，点击"新增成本"添加第一条记录
          </div>
          }
        </CardContent>
      </Card>

      {/* Create/Edit Dialog */}
      <Dialog
        open={showCreateDialog || showEditDialog}
        onOpenChange={(open) => {
          if (!open) {
            setShowCreateDialog(false);
            setShowEditDialog(false);
            setSelectedCost(null);
          }
        }}>

        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedCost ? "编辑成本" : "新增成本"}</DialogTitle>
            <DialogDescription>
              采购部提交历史采购物料成本信息
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>物料编码</Label>
                <Input
                  value={formData.material_code}
                  onChange={(e) =>
                  setFormData({ ...formData, material_code: e.target.value })
                  }
                  placeholder="MAT-001" />

              </div>
              <div>
                <Label>物料名称 *</Label>
                <Input
                  value={formData.material_name}
                  onChange={(e) =>
                  setFormData({ ...formData, material_name: e.target.value })
                  }
                  placeholder="工控机"
                  required />

              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>规格型号</Label>
                <Input
                  value={formData.specification}
                  onChange={(e) =>
                  setFormData({ ...formData, specification: e.target.value })
                  }
                  placeholder="研华IPC-610H" />

              </div>
              <div>
                <Label>品牌</Label>
                <Input
                  value={formData.brand}
                  onChange={(e) =>
                  setFormData({ ...formData, brand: e.target.value })
                  }
                  placeholder="研华" />

              </div>
            </div>

            <div className="grid grid-cols-4 gap-4">
              <div>
                <Label>单位</Label>
                <Input
                  value={formData.unit}
                  onChange={(e) =>
                  setFormData({ ...formData, unit: e.target.value })
                  }
                  placeholder="件" />

              </div>
              <div>
                <Label>物料类型</Label>
                <Input
                  value={formData.material_type}
                  onChange={(e) =>
                  setFormData({ ...formData, material_type: e.target.value })
                  }
                  placeholder="标准件/电气件" />

              </div>
              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  checked={formData.is_standard_part}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    is_standard_part: e.target.checked
                  })
                  }
                  className="rounded" />

                <Label>标准件</Label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                  }
                  className="rounded" />

                <Label>启用匹配</Label>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>单位成本 *</Label>
                <Input
                  type="number"
                  value={formData.unit_cost}
                  onChange={(e) =>
                  setFormData({ ...formData, unit_cost: e.target.value })
                  }
                  placeholder="0.00"
                  required />

              </div>
              <div>
                <Label>币种</Label>
                <Select
                  value={formData.currency}
                  onValueChange={(value) =>
                  setFormData({ ...formData, currency: value })
                  }>

                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="CNY">CNY</SelectItem>
                    <SelectItem value="USD">USD</SelectItem>
                    <SelectItem value="EUR">EUR</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>匹配优先级</Label>
                <Input
                  type="number"
                  value={formData.match_priority}
                  onChange={(e) =>
                  setFormData({ ...formData, match_priority: e.target.value })
                  }
                  placeholder="0" />

              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>供应商</Label>
                <Select
                  value={formData.supplier_id?.toString()}
                  onValueChange={(value) => {
                    const supplier = suppliers.find(
                      (s) => s.id.toString() === value
                    );
                    setFormData({
                      ...formData,
                      supplier_id: value,
                      supplier_name: supplier?.supplier_name || ""
                    });
                  }}>

                  <SelectTrigger>
                    <SelectValue placeholder="选择供应商" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无</SelectItem>
                    {suppliers.map((s) =>
                    <SelectItem key={s.id} value={s.id.toString()}>
                        {s.supplier_name}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>供应商名称（手动输入）</Label>
                <Input
                  value={formData.supplier_name}
                  onChange={(e) =>
                  setFormData({ ...formData, supplier_name: e.target.value })
                  }
                  placeholder="供应商名称" />

              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>采购日期</Label>
                <Input
                  type="date"
                  value={formData.purchase_date}
                  onChange={(e) =>
                  setFormData({ ...formData, purchase_date: e.target.value })
                  } />

              </div>
              <div>
                <Label>采购订单号</Label>
                <Input
                  value={formData.purchase_order_no}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    purchase_order_no: e.target.value
                  })
                  }
                  placeholder="PO-20250101-001" />

              </div>
              <div>
                <Label>采购数量</Label>
                <Input
                  type="number"
                  value={formData.purchase_quantity}
                  onChange={(e) =>
                  setFormData({
                    ...formData,
                    purchase_quantity: e.target.value
                  })
                  }
                  placeholder="0" />

              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>交期(天)</Label>
                <Input
                  type="number"
                  value={formData.lead_time_days}
                  onChange={(e) =>
                  setFormData({ ...formData, lead_time_days: e.target.value })
                  }
                  placeholder="7" />

              </div>
              <div>
                <Label>匹配关键词</Label>
                <Input
                  value={formData.match_keywords}
                  onChange={(e) =>
                  setFormData({ ...formData, match_keywords: e.target.value })
                  }
                  placeholder="关键词1,关键词2（逗号分隔）" />

              </div>
            </div>

            <div>
              <Label>备注</Label>
              <Textarea
                value={formData.remark}
                onChange={(e) =>
                setFormData({ ...formData, remark: e.target.value })
                }
                placeholder="备注信息..."
                rows={3} />

            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCreateDialog(false);
                setShowEditDialog(false);
                setSelectedCost(null);
              }}>

              取消
            </Button>
            <Button
              onClick={handleSave}
              disabled={!formData.material_name || !formData.unit_cost}>

              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除物料成本 "{selectedCost?.material_name}"
              吗？此操作不可恢复。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}>

              取消
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reminder Settings Dialog */}
      <Dialog open={showReminderDialog} onOpenChange={setShowReminderDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>物料成本更新提醒设置</DialogTitle>
            <DialogDescription>
              配置定期更新提醒，系统将自动提醒您更新物料成本信息
            </DialogDescription>
          </DialogHeader>

          {reminder &&
          <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>提醒间隔（天）</Label>
                  <Input
                  type="number"
                  value={reminder.reminder_interval_days || 30}
                  disabled
                  className="bg-slate-800" />

                  <div className="text-xs text-slate-400 mt-1">
                    当前设置为每 {reminder.reminder_interval_days || 30}{" "}
                    天提醒一次
                  </div>
                </div>
                <div>
                  <Label>下次提醒日期</Label>
                  <Input
                  value={
                  reminder.next_reminder_date ?
                  formatDate(reminder.next_reminder_date) :
                  "-"
                  }
                  disabled
                  className="bg-slate-800" />

                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                type="checkbox"
                checked={reminder.is_enabled}
                disabled
                className="rounded" />

                <Label>启用提醒</Label>
              </div>

              {reminder.is_due &&
            <div className="bg-amber-900/20 border border-amber-500/50 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-5 w-5 text-amber-400 mt-0.5" />
                    <div>
                      <div className="font-medium text-amber-400 mb-1">
                        提醒已到期
                      </div>
                      <div className="text-sm text-slate-300">
                        请及时更新物料成本信息，更新后点击"确认提醒"按钮。
                      </div>
                    </div>
                  </div>
            </div>
            }
          </div>
          }

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowReminderDialog(false)}>

              关闭
            </Button>
            {reminder?.is_due &&
            <Button onClick={handleAcknowledgeReminder}>
                <CheckCircle2 className="h-4 w-4 mr-2" />
                我已更新，确认提醒
            </Button>
            }
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}