/**
 * WBS Template Management Page - WBS模板管理页面
 * Features: WBS模板CRUD、任务配置、从模板初始化项目WBS
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  Plus,
  Search,
  Edit,
  Trash2,
  Eye,
  Copy,
  ChevronRight,
  ChevronDown,
  CheckCircle2,
  Circle,
  Settings,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { cn, formatDate } from "../lib/utils";
import { progressApi, projectApi } from "../services/api";
export default function WBSTemplateManagement() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateTasks, setTemplateTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("");
  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showInitDialog, setShowInitDialog] = useState(false);
  const [expandedTasks, setExpandedTasks] = useState(new Set());
  // Form states
  const [newTemplate, setNewTemplate] = useState({
    template_name: "",
    template_type: "SINGLE_MACHINE", // SINGLE_MACHINE or LINE
    description: "",
  });
  const [selectedProject, setSelectedProject] = useState("");
  useEffect(() => {
    fetchTemplates();
    fetchProjects();
  }, [filterType, searchKeyword]);
  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const params = {
        page: 1,
        page_size: 100,
      };
      if (filterType) params.project_type = filterType;
      if (searchKeyword) params.keyword = searchKeyword;
      const res = await progressApi.wbsTemplates.list(params);
      setTemplates(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch templates:", error);
      setTemplates([]); // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false);
    }
  };
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };
  const fetchTemplateTasks = async (templateId) => {
    try {
      const res = await progressApi.wbsTemplates.getTasks(templateId);
      setTemplateTasks(res.data || []);
    } catch (error) {
      console.error("Failed to fetch template tasks:", error);
      setTemplateTasks([]); // 不再使用mock数据，显示空列表
    }
  };
  const handleViewDetail = async (template) => {
    setSelectedTemplate(template);
    await fetchTemplateTasks(template.id);
    setShowDetailDialog(true);
  };
  const handleCreateTemplate = async () => {
    if (!newTemplate.template_name) {
      alert("请填写模板名称");
      return;
    }
    try {
      await progressApi.wbsTemplates.create(newTemplate);
      setShowCreateDialog(false);
      setNewTemplate({
        template_name: "",
        template_type: "SINGLE_MACHINE",
        description: "",
      });
      fetchTemplates();
    } catch (error) {
      console.error("Failed to create template:", error);
      alert("创建模板失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const handleInitProjectWBS = async () => {
    if (!selectedProject || !selectedTemplate) {
      alert("请选择项目和模板");
      return;
    }
    try {
      await progressApi.projects.initWBS(selectedProject, {
        template_id: selectedTemplate.id,
      });
      setShowInitDialog(false);
      setSelectedProject("");
      alert("WBS初始化成功");
      navigate(`/projects/${selectedProject}`);
    } catch (error) {
      console.error("Failed to init WBS:", error);
      alert(
        "初始化WBS失败: " + (error.response?.data?.detail || error.message),
      );
    }
  };
  const toggleTaskExpand = (taskId) => {
    const newExpanded = new Set(expandedTasks);
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId);
    } else {
      newExpanded.add(taskId);
    }
    setExpandedTasks(newExpanded);
  };
  const typeConfigs = {
    SINGLE_MACHINE: { label: "单机类", color: "bg-blue-500" },
    LINE: { label: "线体类", color: "bg-purple-500" },
  };
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="WBS模板管理"
        description="工作分解结构模板管理，支持从模板快速初始化项目WBS"
      />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索模板名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(typeConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              新建模板
            </Button>
          </div>
        </CardContent>
      </Card>
      {/* Template List */}
      <Card>
        <CardHeader>
          <CardTitle>模板列表</CardTitle>
          <CardDescription>共 {templates.length} 个模板</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : templates.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无模板数据</div>
          ) : (
            <div className="space-y-3">
              {templates.map((template) => (
                <Card
                  key={template.id}
                  className="hover:bg-slate-50 transition-colors"
                >
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-medium">
                            {template.template_name}
                          </h3>
                          <Badge
                            className={
                              typeConfigs[template.template_type]?.color
                            }
                          >
                            {typeConfigs[template.template_type]?.label}
                          </Badge>
                        </div>
                        {template.description && (
                          <p className="text-sm text-slate-500 mb-2">
                            {template.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-sm text-slate-500">
                          <span>任务数: {template.task_count || 0}</span>
                          <span>
                            创建时间: {formatDate(template.created_at)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(template)}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          查看
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedTemplate(template);
                            setShowInitDialog(true);
                          }}
                        >
                          <Copy className="w-4 h-4 mr-2" />
                          应用到项目
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      {/* Template Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedTemplate?.template_name}</DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedTemplate && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">模板类型</div>
                    <Badge
                      className={
                        typeConfigs[selectedTemplate.template_type]?.color
                      }
                    >
                      {typeConfigs[selectedTemplate.template_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">任务数量</div>
                    <div>{selectedTemplate.task_count || 0}</div>
                  </div>
                </div>
                {selectedTemplate.description && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">描述</div>
                    <div>{selectedTemplate.description}</div>
                  </div>
                )}
                <div>
                  <div className="text-sm font-medium mb-3">模板任务列表</div>
                  {templateTasks.length === 0 ? (
                    <div className="text-center py-4 text-slate-400">
                      暂无任务
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {templateTasks.map((task) => (
                        <div
                          key={task.id}
                          className="border rounded-lg p-3 hover:bg-slate-50"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              {task.children && task.children.length > 0 ? (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => toggleTaskExpand(task.id)}
                                >
                                  {expandedTasks.has(task.id) ? (
                                    <ChevronDown className="w-4 h-4" />
                                  ) : (
                                    <ChevronRight className="w-4 h-4" />
                                  )}
                                </Button>
                              ) : (
                                <div className="w-8" />
                              )}
                              <div>
                                <div className="font-medium">
                                  {task.task_name}
                                </div>
                                {task.description && (
                                  <div className="text-sm text-slate-500">
                                    {task.description}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              {task.planned_duration && (
                                <Badge variant="outline">
                                  {task.planned_duration} 天
                                </Badge>
                              )}
                            </div>
                          </div>
                          {expandedTasks.has(task.id) && task.children && (
                            <div className="ml-8 mt-2 space-y-2">
                              {task.children.map((child) => (
                                <div
                                  key={child.id}
                                  className="border-l-2 pl-3 py-2 text-sm"
                                >
                                  <div className="font-medium">
                                    {child.task_name}
                                  </div>
                                  {child.description && (
                                    <div className="text-slate-500">
                                      {child.description}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}
            >
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Create Template Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建WBS模板</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  模板名称 *
                </label>
                <Input
                  value={newTemplate.template_name}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      template_name: e.target.value,
                    })
                  }
                  placeholder="请输入模板名称"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  模板类型 *
                </label>
                <Select
                  value={newTemplate.template_type}
                  onValueChange={(val) =>
                    setNewTemplate({ ...newTemplate, template_type: val })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(typeConfigs).map(([key, config]) => (
                      <SelectItem key={key} value={key}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <Input
                  value={newTemplate.description}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      description: e.target.value,
                    })
                  }
                  placeholder="模板描述"
                />
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleCreateTemplate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Init Project WBS Dialog */}
      <Dialog open={showInitDialog} onOpenChange={setShowInitDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>从模板初始化项目WBS</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  选择项目 *
                </label>
                <Select
                  value={selectedProject}
                  onValueChange={setSelectedProject}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择项目" />
                  </SelectTrigger>
                  <SelectContent>
                    {projects.map((proj) => (
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                        {proj.project_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {selectedTemplate && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">模板信息</div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <div className="font-medium">
                      {selectedTemplate.template_name}
                    </div>
                    <div className="text-sm text-slate-500">
                      {typeConfigs[selectedTemplate.template_type]?.label} ·{" "}
                      {selectedTemplate.task_count || 0} 个任务
                    </div>
                  </div>
                </div>
              )}
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInitDialog(false)}>
              取消
            </Button>
            <Button onClick={handleInitProjectWBS} disabled={!selectedProject}>
              初始化
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
