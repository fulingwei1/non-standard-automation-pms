import { useState, useEffect, useCallback } from "react";
import { alertApi } from "../../services/api";
import { toast } from "../../components/ui/toast";
import { initialFormData } from "./constants";

export function useAlertRules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState("ALL");
  const [selectedTarget, setSelectedTarget] = useState("ALL");
  const [showEnabled, setShowEnabled] = useState(null);
  const [showDialog, setShowDialog] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState(initialFormData);

  const loadRules = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchQuery) {
        params.keyword = searchQuery;
      }
      if (selectedType !== "ALL") {
        params.rule_type = selectedType;
      }
      if (selectedTarget !== "ALL") {
        params.target_type = selectedTarget;
      }
      if (showEnabled !== null) {
        params.is_enabled = showEnabled;
      }
      const response = await alertApi.rules.list(params);
      const data = response.data?.data || response.data || response;
      if (data && typeof data === "object" && "items" in data) {
        setRules(data.items || []);
        setTotal(data.total || 0);
      } else if (Array.isArray(data)) {
        setRules(data);
        setTotal(data.length);
      } else {
        setRules([]);
        setTotal(0);
      }
    } catch (err) {
      console.error("Failed to load rules:", err);
      setError(err.response?.data?.detail || err.message || "加载规则列表失败");
      setRules([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchQuery, selectedType, selectedTarget, showEnabled]);

  const loadTemplates = useCallback(async () => {
    try {
      const response = await alertApi.templates();
      const data = response.data || response;
      setTemplates(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load templates:", err);
    }
  }, []);

  useEffect(() => {
    loadRules();
  }, [loadRules]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const handleCreate = () => {
    setEditingRule(null);
    setFormData(initialFormData);
    setSelectedTemplate(null);
    setShowDialog(true);
  };

  const handleEdit = (rule) => {
    setEditingRule(rule);
    setFormData({
      rule_code: rule.rule_code,
      rule_name: rule.rule_name,
      rule_type: rule.rule_type,
      target_type: rule.target_type,
      target_field: rule.target_field || "",
      condition_type: rule.condition_type,
      condition_operator: rule.condition_operator || "GT",
      threshold_value: rule.threshold_value || "",
      threshold_min: rule.threshold_min || "",
      threshold_max: rule.threshold_max || "",
      condition_expr: rule.condition_expr || "",
      alert_level: rule.alert_level,
      advance_days: rule.advance_days || 0,
      notify_channels: rule.notify_channels || ["SYSTEM"],
      notify_roles: rule.notify_roles || [],
      notify_users: rule.notify_users || [],
      check_frequency: rule.check_frequency || "DAILY",
      is_enabled: rule.is_enabled !== false,
      description: rule.description || "",
      solution_guide: rule.solution_guide || "",
    });
    setShowDialog(true);
  };

  const handleDelete = async (rule) => {
    if (!confirm(`确定要删除规则 "${rule.rule_name}" 吗？`)) {
      return;
    }
    try {
      await alertApi.rules.delete(rule.id);
      toast.success("规则已删除");
      loadRules();
    } catch (err) {
      toast.error(err.response?.data?.detail || "删除失败");
    }
  };

  const handleToggle = async (rule) => {
    try {
      await alertApi.rules.toggle(rule.id);
      toast.success(rule.is_enabled ? "规则已禁用" : "规则已启用");
      loadRules();
    } catch (err) {
      toast.error(err.response?.data?.detail || "操作失败");
    }
  };

  const handleSave = async () => {
    try {
      if (!formData.rule_code.trim()) {
        toast.error("请输入规则编码");
        return;
      }
      if (!formData.rule_name.trim()) {
        toast.error("请输入规则名称");
        return;
      }
      if (!formData.rule_type) {
        toast.error("请选择规则类型");
        return;
      }
      if (!formData.target_type) {
        toast.error("请选择监控对象类型");
        return;
      }
      if (
        formData.condition_type === "THRESHOLD" &&
        !formData.threshold_value &&
        formData.condition_operator !== "BETWEEN"
      ) {
        toast.error("请输入阈值");
        return;
      }
      if (
        formData.condition_operator === "BETWEEN" &&
        (!formData.threshold_min || !formData.threshold_max)
      ) {
        toast.error("请输入阈值范围");
        return;
      }

      if (editingRule) {
        await alertApi.rules.update(editingRule.id, formData);
        toast.success("规则已更新");
      } else {
        await alertApi.rules.create(formData);
        toast.success("规则已创建");
      }
      setShowDialog(false);
      loadRules();
    } catch (err) {
      toast.error(err.response?.data?.detail || "保存失败");
    }
  };

  const handleTemplateSelect = (templateId) => {
    const template = templates.find((t) => t.id === templateId);
    if (template && template.rule_config) {
      setSelectedTemplate(template);
      const config = template.rule_config;
      setFormData((prev) => ({
        ...prev,
        rule_type: config.rule_type || prev.rule_type,
        target_type: config.target_type || prev.target_type,
        condition_type: config.condition_type || prev.condition_type,
        alert_level: config.alert_level || prev.alert_level,
        check_frequency: config.check_frequency || prev.check_frequency,
        notify_channels: config.notify_channels || prev.notify_channels,
        description: template.description || prev.description,
      }));
    }
  };

  const handleChannelToggle = (channel) => {
    setFormData((prev) => {
      const channels = prev.notify_channels || [];
      if (channels.includes(channel)) {
        return {
          ...prev,
          notify_channels: channels.filter((c) => c !== channel),
        };
      } else {
        return { ...prev, notify_channels: [...channels, channel] };
      }
    });
  };

  return {
    rules,
    loading,
    error,
    page,
    setPage,
    total,
    pageSize,
    searchQuery,
    setSearchQuery,
    selectedType,
    setSelectedType,
    selectedTarget,
    setSelectedTarget,
    showEnabled,
    setShowEnabled,
    showDialog,
    setShowDialog,
    editingRule,
    templates,
    selectedTemplate,
    formData,
    setFormData,
    loadRules,
    handleCreate,
    handleEdit,
    handleDelete,
    handleToggle,
    handleSave,
    handleTemplateSelect,
    handleChannelToggle,
  };
}
