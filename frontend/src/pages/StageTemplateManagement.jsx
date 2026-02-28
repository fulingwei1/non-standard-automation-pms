import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  Edit3,
  Trash2,
  Copy,
  Layers,
  Settings,
  CheckCircle,
  Clock,
  FileText,
  Download,
  Upload,
  Star,
  Eye,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogBody,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import DeleteConfirmDialog from "../components/common/DeleteConfirmDialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Switch } from "../components/ui/switch";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { stageTemplateApi } from "../services/api";

// 项目类型常量
const PROJECT_TYPES = {
  STANDARD: { label: "标准项目", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  CUSTOM: { label: "定制项目", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
  RD: { label: "研发项目", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  MAINTENANCE: { label: "维保项目", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
};

export default function StageTemplateManagement() {
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

  const [formData, setFormData] = useState({
    template_code: "",
    template_name: "",
    description: "",
    project_type: "STANDARD",
    is_default: false,
    is_active: true,
  });

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

  const resetForm = () => {
    setFormData({
      template_code: "",
      template_name: "",
      description: "",
      project_type: "STANDARD",
      is_default: false,
      is_active: true,
    });
  };

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

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="阶段模板管理"
        subtitle="配置项目的阶段流程模板，定义阶段和节点的工作流程"
        icon={Layers}
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Upload className="h-4 w-4 mr-2" />
              导入模板
            </Button>
            <Button onClick={handleCreateClick}>
              <Plus className="h-4 w-4 mr-2" />
              新建模板
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* 统计卡片 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-5 gap-4"
        >
          {[
            { label: "模板总数", value: stats.total, icon: Layers, color: "text-violet-400" },
            { label: "已启用", value: stats.active, icon: CheckCircle, color: "text-emerald-400" },
            { label: "默认模板", value: stats.default, icon: Star, color: "text-amber-400" },
            { label: "阶段总数", value: stats.totalStages, icon: Settings, color: "text-blue-400" },
            { label: "节点总数", value: stats.totalNodes, icon: FileText, color: "text-purple-400" },
          ].map((stat) => (
            <motion.div key={stat.label} variants={fadeIn}>
              <Card className="bg-surface-100 border-white/5 hover:border-white/10 transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">{stat.label}</p>
                      <p className={cn("text-2xl font-bold mt-1", stat.color)}>
                        {stat.value}
                      </p>
                    </div>
                    <div className={cn("p-3 rounded-xl bg-white/5", stat.color)}>
                      <stat.icon className="h-5 w-5" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* 搜索和筛选 */}
        <Card className="bg-surface-100 border-white/5">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="搜索模板名称或编码..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 bg-white/5 border-white/10"
                />
              </div>
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[180px] bg-white/5 border-white/10">
                  <SelectValue placeholder="项目类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部类型</SelectItem>
                  <SelectItem value="STANDARD">标准项目</SelectItem>
                  <SelectItem value="CUSTOM">定制项目</SelectItem>
                  <SelectItem value="R&D">研发项目</SelectItem>
                  <SelectItem value="MAINTENANCE">维保项目</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterActive} onValueChange={setFilterActive}>
                <SelectTrigger className="w-[120px] bg-white/5 border-white/10">
                  <SelectValue placeholder="状态" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部状态</SelectItem>
                  <SelectItem value="active">已启用</SelectItem>
                  <SelectItem value="inactive">已禁用</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* 模板列表 */}
        <Card className="bg-surface-100 border-white/5">
          <CardHeader className="border-b border-white/5">
            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
              <Layers className="h-5 w-5 text-violet-400" />
              模板列表
              <Badge variant="secondary" className="ml-2">
                {filteredTemplates.length} 项
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-white/5 hover:bg-transparent">
                    <TableHead className="text-slate-400">模板编码</TableHead>
                    <TableHead className="text-slate-400">模板名称</TableHead>
                    <TableHead className="text-slate-400">项目类型</TableHead>
                    <TableHead className="text-slate-400">描述</TableHead>
                    <TableHead className="text-slate-400 text-center">阶段/节点</TableHead>
                    <TableHead className="text-slate-400 text-center">默认</TableHead>
                    <TableHead className="text-slate-400 text-center">状态</TableHead>
                    <TableHead className="text-slate-400 text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <AnimatePresence>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-10">
                          <div className="flex items-center justify-center gap-2 text-slate-400">
                            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-violet-500" />
                            加载中...
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : filteredTemplates.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-center py-10 text-slate-400">
                          暂无数据
                        </TableCell>
                      </TableRow>
                    ) : (
                      (filteredTemplates || []).map((template, index) => (
                        <motion.tr
                          key={template.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ delay: index * 0.03 }}
                          className="border-white/5 hover:bg-white/[0.02]"
                        >
                          <TableCell>
                            <code className="text-sm font-mono text-slate-300 bg-white/5 px-2 py-0.5 rounded">
                              {template.template_code}
                            </code>
                          </TableCell>
                          <TableCell>
                            <span className="text-white font-medium">{template.template_name}</span>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={cn(
                                "border",
                                PROJECT_TYPES[template.project_type]?.color ||
                                  PROJECT_TYPES.STANDARD.color
                              )}
                            >
                              {PROJECT_TYPES[template.project_type]?.label || "未知"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span className="text-slate-400 text-sm line-clamp-1 max-w-[250px]">
                              {template.description || "-"}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex items-center justify-center gap-3">
                              <span className="text-blue-400 font-medium">{template.stage_count || 0}</span>
                              <span className="text-slate-600">/</span>
                              <span className="text-purple-400 font-medium">{template.node_count || 0}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            {template.is_default ? (
                              <div className="flex items-center justify-center">
                                <Star className="h-4 w-4 text-amber-400 fill-amber-400" />
                              </div>
                            ) : (
                              <span className="text-slate-600">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            <Switch
                              checked={template.is_active}
                              onCheckedChange={() => handleToggleActive(template)}
                              className="data-[state=checked]:bg-emerald-500"
                            />
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleViewClick(template)}
                                title="查看详情"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleEditClick(template)}
                                title="编辑"
                              >
                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleCopyClick(template)}
                                title="复制"
                              >
                                <Copy className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleDeleteClick(template)}
                                className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                title="删除"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </motion.tr>
                      ))
                    )}
                  </AnimatePresence>
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 新增对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-violet-400" />
              新建阶段模板
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>模板编码 *</Label>
                <Input
                  placeholder="如 STD_9_STAGE"
                  value={formData.template_code}
                  onChange={(e) => handleFormChange("template_code", e.target.value.toUpperCase())}
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div className="space-y-2">
                <Label>项目类型</Label>
                <Select
                  value={formData.project_type}
                  onValueChange={(v) => handleFormChange("project_type", v)}
                >
                  <SelectTrigger className="bg-white/5 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="STANDARD">标准项目</SelectItem>
                    <SelectItem value="CUSTOM">定制项目</SelectItem>
                    <SelectItem value="R&D">研发项目</SelectItem>
                    <SelectItem value="MAINTENANCE">维保项目</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>模板名称 *</Label>
              <Input
                placeholder="如 标准九阶段流程"
                value={formData.template_name}
                onChange={(e) => handleFormChange("template_name", e.target.value)}
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>模板描述</Label>
              <Textarea
                placeholder="描述该模板的用途和适用场景..."
                value={formData.description}
                onChange={(e) => handleFormChange("description", e.target.value)}
                className="bg-white/5 border-white/10 min-h-[80px]"
              />
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  id="create_is_default"
                  checked={formData.is_default}
                  onCheckedChange={(v) => handleFormChange("is_default", v)}
                />
                <Label htmlFor="create_is_default" className="cursor-pointer">
                  设为默认
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  id="create_is_active"
                  checked={formData.is_active}
                  onCheckedChange={(v) => handleFormChange("is_active", v)}
                />
                <Label htmlFor="create_is_active" className="cursor-pointer">
                  启用
                </Label>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowCreateDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit3 className="h-5 w-5 text-violet-400" />
              编辑阶段模板
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="space-y-2">
              <Label>模板编码</Label>
              <Input
                value={formData.template_code}
                disabled
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>项目类型</Label>
              <Select
                value={formData.project_type}
                onValueChange={(v) => handleFormChange("project_type", v)}
              >
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="STANDARD">标准项目</SelectItem>
                  <SelectItem value="CUSTOM">定制项目</SelectItem>
                  <SelectItem value="R&D">研发项目</SelectItem>
                  <SelectItem value="MAINTENANCE">维保项目</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>模板名称 *</Label>
              <Input
                value={formData.template_name}
                onChange={(e) => handleFormChange("template_name", e.target.value)}
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>模板描述</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => handleFormChange("description", e.target.value)}
                className="bg-white/5 border-white/10 min-h-[80px]"
              />
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  id="edit_is_default"
                  checked={formData.is_default}
                  onCheckedChange={(v) => handleFormChange("is_default", v)}
                />
                <Label htmlFor="edit_is_default" className="cursor-pointer">
                  设为默认
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  id="edit_is_active"
                  checked={formData.is_active}
                  onCheckedChange={(v) => handleFormChange("is_active", v)}
                />
                <Label htmlFor="edit_is_active" className="cursor-pointer">
                  启用
                </Label>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowEditDialog(false)}>
              取消
            </Button>
            <Button onClick={handleUpdate}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 复制对话框 */}
      <Dialog open={showCopyDialog} onOpenChange={setShowCopyDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Copy className="h-5 w-5 text-violet-400" />
              复制模板
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <p className="text-sm text-slate-400">
              正在复制模板 <span className="text-white font-medium">{selectedTemplate?.template_name}</span>
            </p>
            <div className="space-y-2">
              <Label>新模板编码 *</Label>
              <Input
                value={formData.template_code}
                onChange={(e) => handleFormChange("template_code", e.target.value.toUpperCase())}
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>新模板名称 *</Label>
              <Input
                value={formData.template_name}
                onChange={(e) => handleFormChange("template_name", e.target.value)}
                className="bg-white/5 border-white/10"
              />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowCopyDialog(false)}>
              取消
            </Button>
            <Button onClick={handleCopy}>复制</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="确认删除"
        description={`确定要删除模板 "${selectedTemplate?.template_name}" 吗？`}
        confirmText="确认删除"
        onConfirm={handleDelete}
      >
        <p className="text-sm text-slate-500 mt-2">
          此操作不可撤销，所有相关的阶段和节点定义也将被删除。
        </p>
      </DeleteConfirmDialog>
    </div>
  );
}
