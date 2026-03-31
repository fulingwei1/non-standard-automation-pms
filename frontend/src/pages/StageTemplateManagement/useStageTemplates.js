import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { stageTemplateApi } from "../../services/api";
import { INITIAL_FORM_DATA } from "./constants";

export default function useStageTemplates() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showCopyDialog, setShowCopyDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterActive, setFilterActive] = useState("all");
  const [formData, setFormData] = useState({ ...INITIAL_FORM_DATA });

  const resetForm = () => {
    setFormData({ ...INITIAL_FORM_DATA });
  };

  // 加载模板列表
  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        include_stages: true,
      };
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      if (filterType !== "all") {
        params.project_type = filterType;
      }
      if (filterActive !== "all") {
        params.is_active = filterActive === "active";
      }

      const response = await stageTemplateApi.list(params);
      const data = response.data;
      setTemplates(Array.isArray(data) ? data : (data.items || []));
    } catch (error) {
      console.error("加载模板列表失败:", error);
      // Mock data for demo
      setTemplates([
        {
          id: 1,
          template_code: "STD_9_STAGE",
          template_name: "标准九阶段流程",
          description: "适用于大多数非标自动化项目的标准九阶段流程模板",
          project_type: "STANDARD",
          is_default: true,
          is_active: true,
          stage_count: 9,
          node_count: 45,
          created_at: "2024-01-01T00:00:00",
        },
        {
          id: 2,
          template_code: "CUST_FAST_TRACK",
          template_name: "定制项目快速流程",
          description: "适用于紧急交付的定制项目，简化阶段和节点",
          project_type: "CUSTOM",
          is_default: false,
          is_active: true,
          stage_count: 5,
          node_count: 20,
          created_at: "2024-01-15T00:00:00",
        },
        {
          id: 3,
          template_code: "RD_PROTOTYPE",
          template_name: "研发原型流程",
          description: "适用于研发项目的原型开发流程",
          project_type: "R&D",
          is_default: false,
          is_active: true,
          stage_count: 6,
          node_count: 25,
          created_at: "2024-02-01T00:00:00",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [searchKeyword, filterType, filterActive]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const handleCreateClick = () => {
    resetForm();
    setShowCreateDialog(true);
  };

  const handleEditClick = (template) => {
    setSelectedTemplate(template);
    setFormData({
      template_code: template.template_code,
      template_name: template.template_name,
      description: template.description || "",
      project_type: template.project_type,
      is_default: template.is_default,
      is_active: template.is_active,
    });
    setShowEditDialog(true);
  };

  const handleCopyClick = (template) => {
    setSelectedTemplate(template);
    setFormData({
      template_code: `${template.template_code}_COPY`,
      template_name: `${template.template_name} (副本)`,
      description: template.description || "",
      project_type: template.project_type,
      is_default: false,
      is_active: true,
    });
    setShowCopyDialog(true);
  };

  const handleDeleteClick = (template) => {
    setSelectedTemplate(template);
    setShowDeleteDialog(true);
  };

  const handleViewClick = (template) => {
    navigate(`/system/stage-templates/${template.id}/edit`);
  };

  const handleFormChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleCreate = async () => {
    try {
      await stageTemplateApi.create(formData);
      setShowCreateDialog(false);
      resetForm();
      loadTemplates();
    } catch (error) {
      console.error("创建模板失败:", error);
      alert("创建失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdate = async () => {
    try {
      await stageTemplateApi.update(selectedTemplate.id, formData);
      setShowEditDialog(false);
      setSelectedTemplate(null);
      resetForm();
      loadTemplates();
    } catch (error) {
      console.error("更新模板失败:", error);
      alert("更新失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleCopy = async () => {
    try {
      await stageTemplateApi.copy(selectedTemplate.id, {
        new_code: formData.template_code,
        new_name: formData.template_name,
      });
      setShowCopyDialog(false);
      setSelectedTemplate(null);
      resetForm();
      loadTemplates();
    } catch (error) {
      console.error("复制模板失败:", error);
      alert("复制失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async () => {
    try {
      await stageTemplateApi.delete(selectedTemplate.id);
      setShowDeleteDialog(false);
      setSelectedTemplate(null);
      loadTemplates();
    } catch (error) {
      console.error("删除模板失败:", error);
      alert("删除失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleToggleActive = async (template) => {
    try {
      await stageTemplateApi.update(template.id, {
        is_active: !template.is_active,
      });
      loadTemplates();
    } catch (error) {
      console.error("切换状态失败:", error);
      // Update locally for demo
      setTemplates((prev) =>
        (prev || []).map((t) =>
          t.id === template.id ? { ...t, is_active: !t.is_active } : t
        )
      );
    }
  };

  const _handleSetDefault = async (template) => {
    try {
      await stageTemplateApi.setDefault(template.id);
      loadTemplates();
    } catch (error) {
      console.error("设置默认模板失败:", error);
      alert("设置失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const filteredTemplates = (templates || []).filter((t) => {
    if (searchKeyword && !t.template_name.includes(searchKeyword) && !t.template_code.includes(searchKeyword.toUpperCase())) {
      return false;
    }
    if (filterType !== "all" && t.project_type !== filterType) {
      return false;
    }
    if (filterActive !== "all") {
      const isActive = filterActive === "active";
      if (t.is_active !== isActive) return false;
    }
    return true;
  });

  // 统计数据
  const stats = {
    total: templates.length,
    active: (templates || []).filter((t) => t.is_active).length,
    default: (templates || []).filter((t) => t.is_default).length,
    totalStages: (templates || []).reduce((sum, t) => sum + (t.stage_count || 0), 0),
    totalNodes: (templates || []).reduce((sum, t) => sum + (t.node_count || 0), 0),
  };

  return {
    templates,
    loading,
    showCreateDialog,
    setShowCreateDialog,
    showEditDialog,
    setShowEditDialog,
    showCopyDialog,
    setShowCopyDialog,
    showDeleteDialog,
    setShowDeleteDialog,
    selectedTemplate,
    searchKeyword,
    setSearchKeyword,
    filterType,
    setFilterType,
    filterActive,
    setFilterActive,
    formData,
    filteredTemplates,
    stats,
    handleCreateClick,
    handleEditClick,
    handleCopyClick,
    handleDeleteClick,
    handleViewClick,
    handleFormChange,
    handleCreate,
    handleUpdate,
    handleCopy,
    handleDelete,
    handleToggleActive,
    _handleSetDefault,
  };
}
