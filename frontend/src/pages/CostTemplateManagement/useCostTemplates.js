/**
 * Custom hook for cost template state management
 */

import { useState, useEffect, useMemo } from "react";
import { salesTemplateApi } from "../../services/api";
import { INITIAL_FORM_DATA, INITIAL_COST_ITEM } from "./constants";

export function useCostTemplates() {
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [filteredTemplates, setFilteredTemplates] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [equipmentFilter, setEquipmentFilter] = useState("all");

  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // Form state
  const [formData, setFormData] = useState({ ...INITIAL_FORM_DATA });

  useEffect(() => {
    loadTemplates();
  }, []);

  useEffect(() => {
    filterTemplates();
  }, [templates, searchTerm, typeFilter, equipmentFilter]);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const res = await salesTemplateApi.listCostTemplates({
        page: 1,
        page_size: 1000,
      });
      const items = res.data?.data?.items || res.data?.items || [];
      setTemplates(items);
    } catch (error) {
      console.error("加载模板列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const filterTemplates = () => {
    let filtered = [...templates];

    if (searchTerm) {
      filtered = (filtered || []).filter(
        (t) =>
          t.template_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          t.template_code?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (typeFilter !== "all") {
      filtered = (filtered || []).filter((t) => t.template_type === typeFilter);
    }

    if (equipmentFilter !== "all") {
      filtered = (filtered || []).filter(
        (t) => t.equipment_type === equipmentFilter
      );
    }

    setFilteredTemplates(filtered);
  };

  const handleCreate = () => {
    setFormData({ ...INITIAL_FORM_DATA, cost_structure: { categories: [] } });
    setShowCreateDialog(true);
  };

  const handleEdit = (template) => {
    setSelectedTemplate(template);
    setFormData({
      template_code: template.template_code || "",
      template_name: template.template_name || "",
      template_type: template.template_type || "STANDARD",
      equipment_type: template.equipment_type || "",
      industry: template.industry || "",
      description: template.description || "",
      cost_structure: template.cost_structure || { categories: [] },
      is_active: template.is_active !== false,
    });
    setShowEditDialog(true);
  };

  const handlePreview = (template) => {
    setSelectedTemplate(template);
    setShowPreviewDialog(true);
  };

  const handleDelete = (template) => {
    setSelectedTemplate(template);
    setShowDeleteDialog(true);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      if (selectedTemplate) {
        await salesTemplateApi.updateCostTemplate(
          selectedTemplate.id,
          formData
        );
      } else {
        await salesTemplateApi.createCostTemplate(formData);
      }
      await loadTemplates();
      setShowCreateDialog(false);
      setShowEditDialog(false);
      setSelectedTemplate(null);
    } catch (error) {
      console.error("保存模板失败:", error);
      alert("保存模板失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDelete = async () => {
    try {
      setLoading(true);
      await salesTemplateApi.deleteCostTemplate(selectedTemplate.id);
      await loadTemplates();
      setShowDeleteDialog(false);
      setSelectedTemplate(null);
    } catch (error) {
      console.error("删除模板失败:", error);
      alert("删除模板失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const closeFormDialog = () => {
    setShowCreateDialog(false);
    setShowEditDialog(false);
    setSelectedTemplate(null);
  };

  // Cost structure mutations
  const addCategory = () => {
    setFormData({
      ...formData,
      cost_structure: {
        categories: [
          ...(formData.cost_structure?.categories || []),
          { category: "", items: [] },
        ],
      },
    });
  };

  const addItem = (categoryIndex) => {
    const categories = [...(formData.cost_structure?.categories || [])];
    categories[categoryIndex].items = [
      ...(categories[categoryIndex].items || []),
      { ...INITIAL_COST_ITEM },
    ];
    setFormData({ ...formData, cost_structure: { categories } });
  };

  const updateCategory = (index, field, value) => {
    const categories = [...(formData.cost_structure?.categories || [])];
    categories[index][field] = value;
    setFormData({ ...formData, cost_structure: { categories } });
  };

  const updateItem = (categoryIndex, itemIndex, field, value) => {
    const categories = [...(formData.cost_structure?.categories || [])];
    categories[categoryIndex].items[itemIndex][field] = value;
    setFormData({ ...formData, cost_structure: { categories } });
  };

  const removeCategory = (index) => {
    const categories = [...(formData.cost_structure?.categories || [])];
    categories.splice(index, 1);
    setFormData({ ...formData, cost_structure: { categories } });
  };

  const removeItem = (categoryIndex, itemIndex) => {
    const categories = [...(formData.cost_structure?.categories || [])];
    categories[categoryIndex].items.splice(itemIndex, 1);
    setFormData({ ...formData, cost_structure: { categories } });
  };

  const equipmentTypes = useMemo(() => {
    const types = new Set();
    (templates || []).forEach((t) => {
      if (t.equipment_type) types.add(t.equipment_type);
    });
    return Array.from(types);
  }, [templates]);

  return {
    loading,
    filteredTemplates,
    searchTerm,
    setSearchTerm,
    typeFilter,
    setTypeFilter,
    equipmentFilter,
    setEquipmentFilter,
    equipmentTypes,
    showCreateDialog,
    showEditDialog,
    showPreviewDialog,
    setShowPreviewDialog,
    showDeleteDialog,
    setShowDeleteDialog,
    selectedTemplate,
    formData,
    setFormData,
    handleCreate,
    handleEdit,
    handlePreview,
    handleDelete,
    handleSave,
    handleConfirmDelete,
    closeFormDialog,
    addCategory,
    addItem,
    updateCategory,
    updateItem,
    removeCategory,
    removeItem,
  };
}
