import { useState, useCallback, useEffect, useMemo } from "react";
import { acceptanceApi } from "../../../services/api";
import { DEFAULT_TEMPLATE_FORM, DEFAULT_NEW_ITEM } from "../constants";

export function useAcceptanceTemplateManagement() {
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [error, setError] = useState(null);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("");

  // Dialog visibility
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showItemsDialog, setShowItemsDialog] = useState(false);

  // Selected data
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateItems, setTemplateItems] = useState([]);

  // Form state
  const [templateForm, setTemplateForm] = useState(DEFAULT_TEMPLATE_FORM);
  const [newItem, setNewItem] = useState(DEFAULT_NEW_ITEM);

  // ── Data fetching ────────────────────────────────────────────────────────────

  const fetchTemplates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = { page: 1, page_size: 100 };
      if (filterType) params.template_type = filterType;
      if (searchKeyword) params.search = searchKeyword;
      const res = await acceptanceApi.templates.list(params);
      setTemplates(res.data?.items || res.data || []);
    } catch (err) {
      console.error("Failed to fetch templates:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filterType, searchKeyword]);

  const fetchTemplateItems = useCallback(async (templateId) => {
    try {
      const res = await acceptanceApi.templates.getItems(templateId);
      setTemplateItems(res.data || res || []);
    } catch (err) {
      console.error("Failed to fetch template items:", err);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  // ── Derived state ────────────────────────────────────────────────────────────

  const filteredTemplates = useMemo(() => {
    if (!searchKeyword) return templates || [];
    const keyword = searchKeyword.toLowerCase();
    return (templates || []).filter(
      (t) =>
        t.template_name?.toLowerCase().includes(keyword) ||
        t.category?.toLowerCase().includes(keyword)
    );
  }, [templates, searchKeyword]);

  // ── Actions ──────────────────────────────────────────────────────────────────

  const resetForm = useCallback(() => {
    setTemplateForm(DEFAULT_TEMPLATE_FORM);
    setSelectedTemplate(null);
  }, []);

  const handleCreate = useCallback(async () => {
    if (!templateForm.template_name) {
      alert("请填写模板名称");
      return;
    }
    try {
      await acceptanceApi.templates.create(templateForm);
      setShowCreateDialog(false);
      resetForm();
      fetchTemplates();
    } catch (err) {
      console.error("Failed to create template:", err);
      alert("创建模板失败: " + (err.response?.data?.detail || err.message));
    }
  }, [templateForm, resetForm, fetchTemplates]);

  const handleViewDetail = useCallback(
    async (templateId) => {
      try {
        const res = await acceptanceApi.templates.get(templateId);
        setSelectedTemplate(res.data || res);
        await fetchTemplateItems(templateId);
        setShowDetailDialog(true);
      } catch (err) {
        console.error("Failed to fetch template detail:", err);
      }
    },
    [fetchTemplateItems]
  );

  const handleViewItems = useCallback(
    async (templateId) => {
      const res = await acceptanceApi.templates.get(templateId);
      setSelectedTemplate(res.data || res);
      await fetchTemplateItems(templateId);
      setShowItemsDialog(true);
    },
    [fetchTemplateItems]
  );

  const handleAddItem = useCallback(async () => {
    if (!selectedTemplate || !newItem.item_name) {
      alert("请填写检查项名称");
      return;
    }
    try {
      await acceptanceApi.templates.addItems(selectedTemplate.id, {
        category_id: null,
        items: [newItem],
      });
      setNewItem(DEFAULT_NEW_ITEM);
      await fetchTemplateItems(selectedTemplate.id);
    } catch (err) {
      console.error("Failed to add item:", err);
      alert("添加检查项失败: " + (err.response?.data?.detail || err.message));
    }
  }, [selectedTemplate, newItem, fetchTemplateItems]);

  return {
    // State
    loading,
    error,
    templates,
    filteredTemplates,
    selectedTemplate,
    templateItems,
    templateForm,
    newItem,
    // Filters
    searchKeyword,
    setSearchKeyword,
    filterType,
    setFilterType,
    // Dialog flags
    showCreateDialog,
    setShowCreateDialog,
    showDetailDialog,
    setShowDetailDialog,
    showItemsDialog,
    setShowItemsDialog,
    // Form setters
    setTemplateForm,
    setNewItem,
    // Handlers
    handleCreate,
    handleViewDetail,
    handleViewItems,
    handleAddItem,
    resetForm,
    fetchTemplates,
  };
}
