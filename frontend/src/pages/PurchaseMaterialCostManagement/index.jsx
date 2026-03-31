/**
 * Purchase Material Cost Management Page - 采购物料成本清单管理页面
 * Features: List, create, edit, delete purchase material costs (采购部维护标准件成本)
 */

import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  Download,
  Upload,
  Bell,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import DeleteConfirmDialog from "../../components/common/DeleteConfirmDialog";
import { Button, Badge } from "../../components/ui";
import { staggerContainer } from "../../lib/animations";
import { salesTemplateApi, supplierApi } from "../../services/api";

import { INITIAL_FORM_DATA } from "./constants";
import CostFormDialog from "./CostFormDialog";
import ReminderDialog from "./ReminderDialog";
import CostTable from "./CostTable";
import { ReminderDueAlert, ReminderInfoCard } from "./ReminderAlerts";
import FilterBar from "./FilterBar";

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
  const [formData, setFormData] = useState({ ...INITIAL_FORM_DATA });

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
        page_size: 1000,
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
      filtered = (filtered || []).filter(
        (c) =>
          c.material_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.material_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.specification?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (typeFilter !== "all") {
      filtered = (filtered || []).filter((c) => c.material_type === typeFilter);
    }

    if (standardFilter !== "all") {
      filtered = (filtered || []).filter(
        (c) => c.is_standard_part === (standardFilter === "standard")
      );
    }

    if (activeFilter !== "all") {
      filtered = (filtered || []).filter(
        (c) => c.is_active === (activeFilter === "active")
      );
    }

    setFilteredCosts(filtered);
  };

  const handleCreate = () => {
    setFormData({ ...INITIAL_FORM_DATA });
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
      remark: cost.remark || "",
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
        purchase_quantity: formData.purchase_quantity
          ? parseFloat(formData.purchase_quantity)
          : null,
        lead_time_days: formData.lead_time_days
          ? parseInt(formData.lead_time_days)
          : null,
        match_priority: parseInt(formData.match_priority) || 0,
        supplier_id: formData.supplier_id
          ? parseInt(formData.supplier_id)
          : null,
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
    (costs || []).forEach((c) => {
      if (c.material_type) {
        types.add(c.material_type);
      }
    });
    return Array.from(types);
  }, [costs]);

  const handleFormDialogOpenChange = (open) => {
    if (!open) {
      setShowCreateDialog(false);
      setShowEditDialog(false);
      setSelectedCost(null);
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6"
    >
      <PageHeader
        title="采购物料成本清单管理"
        description="采购部维护标准件等常用物料的历史采购成本，用于报价成本自动匹配"
        actions={
          <div className="flex gap-2">
            {reminder && (
              <Button
                variant={reminder.is_due ? "default" : "outline"}
                className={
                  reminder.is_due ? "bg-amber-500 hover:bg-amber-600" : ""
                }
                onClick={() => setShowReminderDialog(true)}
              >
                <Bell className="h-4 w-4 mr-2" />
                {reminder.is_due ? "更新提醒" : "提醒设置"}
                {reminder.is_due && (
                  <Badge className="ml-2 bg-red-500">到期</Badge>
                )}
              </Button>
            )}
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
        }
      />

      {/* Update Reminder Alert */}
      <ReminderDueAlert
        reminder={reminder}
        onAcknowledge={handleAcknowledgeReminder}
        onOpenSettings={() => setShowReminderDialog(true)}
      />

      {/* Reminder Info Card (when not due) */}
      <ReminderInfoCard
        reminder={reminder}
        onOpenSettings={() => setShowReminderDialog(true)}
      />

      {/* Filters */}
      <FilterBar
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        typeFilter={typeFilter}
        setTypeFilter={setTypeFilter}
        standardFilter={standardFilter}
        setStandardFilter={setStandardFilter}
        activeFilter={activeFilter}
        setActiveFilter={setActiveFilter}
        materialTypes={materialTypes}
      />

      {/* Cost List */}
      <CostTable
        filteredCosts={filteredCosts}
        loading={loading}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {/* Create/Edit Dialog */}
      <CostFormDialog
        open={showCreateDialog || showEditDialog}
        onOpenChange={handleFormDialogOpenChange}
        formData={formData}
        setFormData={setFormData}
        suppliers={suppliers}
        selectedCost={selectedCost}
        onSave={handleSave}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="确认删除"
        description={`确定要删除物料成本 "${selectedCost?.material_name}" 吗？此操作不可恢复。`}
        confirmText="删除"
        onConfirm={handleConfirmDelete}
      />

      {/* Reminder Settings Dialog */}
      <ReminderDialog
        open={showReminderDialog}
        onOpenChange={setShowReminderDialog}
        reminder={reminder}
        onAcknowledge={handleAcknowledgeReminder}
      />
    </motion.div>
  );
}
