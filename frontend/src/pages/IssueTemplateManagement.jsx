/**
 * Issue Template Management Page - 问题模板管理页面
 * Features: 问题模板列表、创建、编辑、删除、从模板创建问题
 */
import { useState, useEffect, useMemo } from "react";
import { Plus } from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import { formatDate } from "../lib/utils";
import {
  issueTemplateApi,
  projectApi,
  machineApi,
} from "../services/api";
import {
  IssueTemplateFilters,
  IssueTemplateList,
  TemplateFormDialog,
  TemplateDetailDialog,
  DeleteTemplateDialog,
  CreateIssueFromTemplateDialog,
  categoryConfigs,
  issueTypeConfigs,
  severityConfigs,
  priorityConfigs,
} from "../components/issue-template-management";

export default function IssueTemplateManagement() {
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [projects, setProjects] = useState([]);
  const [machines, setMachines] = useState([]);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterActive, setFilterActive] = useState("all");

  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showCreateIssueDialog, setShowCreateIssueDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // Form state
  const [templateForm, setTemplateForm] = useState({
    template_name: "",
    template_code: "",
    category: "PROJECT",
    issue_type: "DEFECT",
    default_severity: "MINOR",
    default_priority: "MEDIUM",
    default_impact_level: "",
    title_template: "",
    description_template: "",
    solution_template: "",
    default_tags: [],
    default_impact_scope: "",
    default_is_blocking: false,
    is_active: true,
    remark: "",
  });

  const [createIssueForm, setCreateIssueForm] = useState({
    project_id: "",
    machine_id: "",
    task_id: "",
    assignee_id: "",
    due_date: "",
    severity: "",
    priority: "",
    title: "",
    description: "",
  });

  const [tagInput, setTagInput] = useState("");

  useEffect(() => {
    loadTemplates();
    loadProjects();
  }, []);

  useEffect(() => {
    if (createIssueForm.project_id) {
      loadMachines(createIssueForm.project_id);
    }
  }, [createIssueForm.project_id]);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const params = { page: 1, page_size: 100 };
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      if (filterCategory !== "all") {
        params.category = filterCategory;
      }
      if (filterActive !== "all") {
        params.is_active = filterActive === "active";
      }

      const res = await issueTemplateApi.list(params);
      const items = res.data?.items || res.data?.data?.items || res.data?.items || res.data || [];
      setTemplates(items);
    } catch (error) {
      console.error("Failed to load templates:", error);
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      const items = res.data?.items || res.data?.data?.items || res.data?.items || res.data || [];
      setProjects(items);
    } catch (error) {
      console.error("Failed to load projects:", error);
    }
  };

  const loadMachines = async (projectId) => {
    try {
      const res = await machineApi.list(projectId, {
        page_size: 1000,
      });
      const items = res.data?.items || res.data?.data?.items || res.data?.items || res.data || [];
      setMachines(items);
    } catch (error) {
      console.error("Failed to load machines:", error);
      setMachines([]);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, [searchKeyword, filterCategory, filterActive]);

  const handleCreate = () => {
    setTemplateForm({
      template_name: "",
      template_code: "",
      category: "PROJECT",
      issue_type: "DEFECT",
      default_severity: "MINOR",
      default_priority: "MEDIUM",
      default_impact_level: "",
      title_template: "",
      description_template: "",
      solution_template: "",
      default_tags: [],
      default_impact_scope: "",
      default_is_blocking: false,
      is_active: true,
      remark: "",
    });
    setTagInput("");
    setShowCreateDialog(true);
  };

  const handleEdit = (template) => {
    setSelectedTemplate(template);
    setTemplateForm({
      template_name: template.template_name || "",
      template_code: template.template_code || "",
      category: template.category || "PROJECT",
      issue_type: template.issue_type || "DEFECT",
      default_severity: template.default_severity || "MINOR",
      default_priority: template.default_priority || "MEDIUM",
      default_impact_level: template.default_impact_level || "",
      title_template: template.title_template || "",
      description_template: template.description_template || "",
      solution_template: template.solution_template || "",
      default_tags: Array.isArray(template.default_tags)
        ? template.default_tags
        : template.default_tags
        ? JSON.parse(template.default_tags)
        : [],
      default_impact_scope: template.default_impact_scope || "",
      default_is_blocking: template.default_is_blocking || false,
      is_active: template.is_active !== false,
      remark: template.remark || "",
    });
    setTagInput(
      template.default_tags
        ? Array.isArray(template.default_tags)
          ? template.default_tags.join(",")
          : JSON.parse(template.default_tags).join(",")
        : ""
    );
    setShowEditDialog(true);
  };

  const handleViewDetail = async (templateId) => {
    try {
      const res = await issueTemplateApi.get(templateId);
      setSelectedTemplate(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch template detail:", error);
    }
  };

  const handleDelete = (template) => {
    setSelectedTemplate(template);
    setShowDeleteDialog(true);
  };

  const handleCreateIssue = (template) => {
    setSelectedTemplate(template);
    setCreateIssueForm({
      project_id: "",
      machine_id: "",
      task_id: "",
      assignee_id: "",
      due_date: "",
      severity: "",
      priority: "",
      title: "",
      description: "",
    });
    setShowCreateIssueDialog(true);
  };

  const handleSaveTemplate = async () => {
    if (!templateForm.template_name || !templateForm.template_code) {
      alert("请填写模板名称和模板编码");
      return;
    }

    try {
      setLoading(true);
      // 处理标签
      const tags = tagInput
        ? tagInput
            .split(",")
            .map((t) => t.trim())
            .filter((t) => t)
        : [];

      const formData = {
        ...templateForm,
        default_tags: tags,
      };

      if (selectedTemplate) {
        await issueTemplateApi.update(selectedTemplate.id, formData);
      } else {
        await issueTemplateApi.create(formData);
      }

      setShowCreateDialog(false);
      setShowEditDialog(false);
      setSelectedTemplate(null);
      await loadTemplates();
    } catch (error) {
      console.error("Failed to save template:", error);
      alert("保存模板失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDelete = async () => {
    try {
      setLoading(true);
      await issueTemplateApi.delete(selectedTemplate.id);
      setShowDeleteDialog(false);
      setSelectedTemplate(null);
      await loadTemplates();
    } catch (error) {
      console.error("Failed to delete template:", error);
      alert("删除模板失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmCreateIssue = async () => {
    if (!selectedTemplate) {
      return;
    }

    try {
      setLoading(true);
      const formData = {
        ...createIssueForm,
        project_id: createIssueForm.project_id
          ? parseInt(createIssueForm.project_id)
          : null,
        machine_id: createIssueForm.machine_id
          ? parseInt(createIssueForm.machine_id)
          : null,
        task_id: createIssueForm.task_id
          ? parseInt(createIssueForm.task_id)
          : null,
        assignee_id: createIssueForm.assignee_id
          ? parseInt(createIssueForm.assignee_id)
          : null,
        severity: createIssueForm.severity || null,
        priority: createIssueForm.priority || null,
        title: createIssueForm.title || null,
        description: createIssueForm.description || null,
      };

      await issueTemplateApi.createIssue(selectedTemplate.id, formData);
      setShowCreateIssueDialog(false);
      setSelectedTemplate(null);
      alert("问题创建成功");
    } catch (error) {
      console.error("Failed to create issue from template:", error);
      alert("创建问题失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const filteredTemplates = useMemo(() => {
    return templates.filter((template) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          template.template_name?.toLowerCase().includes(keyword) ||
          template.template_code?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [templates, searchKeyword]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <PageHeader
        title="问题模板管理"
        description="管理问题模板，快速创建常见问题类型"
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        <IssueTemplateFilters
          searchKeyword={searchKeyword}
          setSearchKeyword={setSearchKeyword}
          filterCategory={filterCategory}
          setFilterCategory={setFilterCategory}
          filterActive={filterActive}
          setFilterActive={setFilterActive}
          categoryConfigs={categoryConfigs}
        />

        {/* Action Bar */}
        <div className="flex justify-end">
          <Button
            onClick={handleCreate}
            className="bg-primary hover:bg-primary/90"
          >
            <Plus className="w-4 h-4 mr-2" />
            新建模板
          </Button>
        </div>

        <IssueTemplateList
          loading={loading}
          templates={filteredTemplates}
          categoryConfigs={categoryConfigs}
          issueTypeConfigs={issueTypeConfigs}
          priorityConfigs={priorityConfigs}
          onViewDetail={handleViewDetail}
          onEdit={handleEdit}
          onCreateIssue={handleCreateIssue}
          onDelete={handleDelete}
          formatDate={formatDate}
        />
      </div>

      <TemplateFormDialog
        open={showCreateDialog || showEditDialog}
        onOpenChange={(open) => {
          if (!open) {
            setShowCreateDialog(false);
            setShowEditDialog(false);
            setSelectedTemplate(null);
          }
        }}
        form={templateForm}
        setForm={setTemplateForm}
        tagInput={tagInput}
        setTagInput={setTagInput}
        onSubmit={handleSaveTemplate}
        isEdit={!!selectedTemplate}
        categoryConfigs={categoryConfigs}
        issueTypeConfigs={issueTypeConfigs}
        severityConfigs={severityConfigs}
        priorityConfigs={priorityConfigs}
      />

      <TemplateDetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        template={selectedTemplate}
        categoryConfigs={categoryConfigs}
        issueTypeConfigs={issueTypeConfigs}
        formatDate={formatDate}
      />

      <DeleteTemplateDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        template={selectedTemplate}
        onConfirm={handleConfirmDelete}
      />

      <CreateIssueFromTemplateDialog
        open={showCreateIssueDialog}
        onOpenChange={setShowCreateIssueDialog}
        template={selectedTemplate}
        form={createIssueForm}
        setForm={setCreateIssueForm}
        projects={projects}
        machines={machines}
        onConfirm={handleConfirmCreateIssue}
      />
    </div>
  );
}
