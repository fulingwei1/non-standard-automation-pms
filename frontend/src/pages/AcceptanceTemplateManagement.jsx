/**
 * Acceptance Template Management Page - 验收模板管理页面
 * Features: 验收模板列表、创建、编辑、检查项管理
 */
import { useState, useEffect, useMemo } from "react";
import {
  FileText,
  Plus,
  Search,
  Eye,
  Edit,
  CheckSquare,
  Trash2 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { formatDate } from "../lib/utils";
import { acceptanceApi } from "../services/api";

const typeConfigs = {
  FAT: { label: "出厂验收", color: "bg-blue-500" },
  SAT: { label: "现场验收", color: "bg-purple-500" },
  FINAL: { label: "终验收", color: "bg-emerald-500" }
};

export default function AcceptanceTemplateManagement() {
  const [loading, setLoading] = useState(true);
  const [templates, setTemplates] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [_showEditDialog, _setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showItemsDialog, setShowItemsDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateItems, setTemplateItems] = useState([]);
  // Form state
  const [templateForm, setTemplateForm] = useState({
    template_name: "",
    template_type: "FAT",
    category: "",
    description: "",
    version: "1.0"
  });
  const [newItem, setNewItem] = useState({
    item_code: "",
    item_name: "",
    category_name: "",
    acceptance_criteria: "",
    standard_value: "",
    unit: "",
    is_required: true,
    is_key_item: false
  });

  useEffect(() => {
    fetchTemplates();
  }, [filterType, searchKeyword]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const params = { page: 1, page_size: 100 };
      if (filterType) params.template_type = filterType;
      if (searchKeyword) params.search = searchKeyword;
      const res = await acceptanceApi.templates.list(params);
      const templateList = res.data?.items || res.data || [];
      setTemplates(templateList);
    } catch (error) {
      console.error("Failed to fetch templates:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplateItems = async (templateId) => {
    try {
      const res = await acceptanceApi.templates.getItems(templateId);
      const items = res.data || res || [];
      setTemplateItems(items);
    } catch (error) {
      console.error("Failed to fetch template items:", error);
    }
  };

  const handleCreate = async () => {
    if (!templateForm.template_name) {
      alert("请填写模板名称");
      return;
    }
    try {
      await acceptanceApi.templates.create(templateForm);
      setShowCreateDialog(false);
      resetForm();
      fetchTemplates();
    } catch (error) {
      console.error("Failed to create template:", error);
      alert("创建模板失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (templateId) => {
    try {
      const res = await acceptanceApi.templates.get(templateId);
      setSelectedTemplate(res.data || res);
      await fetchTemplateItems(templateId);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch template detail:", error);
    }
  };

  const handleViewItems = async (templateId) => {
    await fetchTemplateItems(templateId);
    const res = await acceptanceApi.templates.get(templateId);
    setSelectedTemplate(res.data || res);
    setShowItemsDialog(true);
  };

  const handleAddItem = async () => {
    if (!selectedTemplate || !newItem.item_name) {
      alert("请填写检查项名称");
      return;
    }
    try {
      await acceptanceApi.templates.addItems(selectedTemplate.id, {
        category_id: null,
        items: [newItem]
      });
      setNewItem({
        item_code: "",
        item_name: "",
        category_name: "",
        acceptance_criteria: "",
        standard_value: "",
        unit: "",
        is_required: true,
        is_key_item: false
      });
      await fetchTemplateItems(selectedTemplate.id);
    } catch (error) {
      console.error("Failed to add item:", error);
      alert(
        "添加检查项失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const resetForm = () => {
    setTemplateForm({
      template_name: "",
      template_type: "FAT",
      category: "",
      description: "",
      version: "1.0"
    });
    setSelectedTemplate(null);
  };

  const filteredTemplates = useMemo(() => {
    return templates.filter((template) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          template.template_name?.toLowerCase().includes(keyword) ||
          template.category?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [templates, searchKeyword]);

  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="验收模板管理"
        description="验收模板列表、创建、编辑、检查项管理" />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索模板名称、分类..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10" />

            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(typeConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建模板
        </Button>
      </div>
      {/* Template List */}
      <Card>
        <CardHeader>
          <CardTitle>验收模板列表</CardTitle>
          <CardDescription>
            共 {filteredTemplates.length} 个模板
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          filteredTemplates.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无模板</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>模板名称</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>分类</TableHead>
                  <TableHead>版本</TableHead>
                  <TableHead>检查项数</TableHead>
                  <TableHead>创建时间</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTemplates.map((template) =>
              <TableRow key={template.id}>
                    <TableCell className="font-medium">
                      {template.template_name}
                    </TableCell>
                    <TableCell>
                      <Badge
                    className={
                    typeConfigs[template.template_type]?.color ||
                    "bg-slate-500"
                    }>

                        {typeConfigs[template.template_type]?.label ||
                    template.template_type}
                      </Badge>
                    </TableCell>
                    <TableCell>{template.category || "-"}</TableCell>
                    <TableCell>{template.version || "1.0"}</TableCell>
                    <TableCell>{template.item_count || 0}</TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {template.created_at ?
                  formatDate(template.created_at) :
                  "-"}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewDetail(template.id)}>

                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewItems(template.id)}>

                          <CheckSquare className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
              )}
              </TableBody>
            </Table>
          }
        </CardContent>
      </Card>
      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建验收模板</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  模板名称 *
                </label>
                <Input
                  value={templateForm.template_name}
                  onChange={(e) =>
                  setTemplateForm({
                    ...templateForm,
                    template_name: e.target.value
                  })
                  }
                  placeholder="请输入模板名称" />

              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    模板类型
                  </label>
                  <Select
                    value={templateForm.template_type}
                    onValueChange={(val) =>
                    setTemplateForm({ ...templateForm, template_type: val })
                    }>

                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(typeConfigs).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">版本</label>
                  <Input
                    value={templateForm.version}
                    onChange={(e) =>
                    setTemplateForm({
                      ...templateForm,
                      version: e.target.value
                    })
                    }
                    placeholder="1.0" />

                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">分类</label>
                <Input
                  value={templateForm.category}
                  onChange={(e) =>
                  setTemplateForm({
                    ...templateForm,
                    category: e.target.value
                  })
                  }
                  placeholder="模板分类" />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={templateForm.description}
                  onChange={(e) =>
                  setTemplateForm({
                    ...templateForm,
                    description: e.target.value
                  })
                  }
                  placeholder="模板描述..." />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreate}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedTemplate?.template_name} - 模板详情
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedTemplate &&
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">模板名称</div>
                    <div>{selectedTemplate.template_name}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">模板类型</div>
                    <Badge
                    className={
                    typeConfigs[selectedTemplate.template_type]?.color
                    }>

                      {typeConfigs[selectedTemplate.template_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">分类</div>
                    <div>{selectedTemplate.category || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">版本</div>
                    <div>{selectedTemplate.version || "1.0"}</div>
                  </div>
                </div>
                {selectedTemplate.description &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">描述</div>
                    <div>{selectedTemplate.description}</div>
                  </div>
              }
                <div>
                  <div className="text-sm text-slate-500 mb-2">检查项列表</div>
                  <div className="space-y-2">
                    {templateItems.length === 0 ?
                  <div className="text-center py-4 text-slate-400">
                        暂无检查项
                      </div> :

                  templateItems.map((item) =>
                  <div key={item.id} className="border rounded-lg p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="font-medium">
                                {item.item_name}
                              </div>
                              <div className="text-xs text-slate-500 mt-1">
                                {item.item_code}{" "}
                                {item.is_key_item &&
                          <Badge variant="destructive" className="ml-1">
                                    关键项
                                  </Badge>
                          }
                              </div>
                              {item.acceptance_criteria &&
                        <div className="text-xs text-slate-600 mt-1">
                                  验收标准: {item.acceptance_criteria}
                                </div>
                        }
                            </div>
                            {item.is_required &&
                      <Badge className="bg-blue-500">必检</Badge>
                      }
                          </div>
                        </div>
                  )
                  }
                  </div>
                </div>
              </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
            {selectedTemplate &&
            <Button
              onClick={() => {
                setShowDetailDialog(false);
                handleViewItems(selectedTemplate.id);
              }}>

                <CheckSquare className="w-4 h-4 mr-2" />
                管理检查项
              </Button>
            }
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Items Dialog */}
      <Dialog open={showItemsDialog} onOpenChange={setShowItemsDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedTemplate?.template_name} - 检查项管理
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium mb-2">添加检查项</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      检查项编码
                    </label>
                    <Input
                      value={newItem.item_code}
                      onChange={(e) =>
                      setNewItem({ ...newItem, item_code: e.target.value })
                      }
                      placeholder="检查项编码" />

                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      检查项名称 *
                    </label>
                    <Input
                      value={newItem.item_name}
                      onChange={(e) =>
                      setNewItem({ ...newItem, item_name: e.target.value })
                      }
                      placeholder="检查项名称" />

                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      分类
                    </label>
                    <Input
                      value={newItem.category_name}
                      onChange={(e) =>
                      setNewItem({
                        ...newItem,
                        category_name: e.target.value
                      })
                      }
                      placeholder="分类名称" />

                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      单位
                    </label>
                    <Input
                      value={newItem.unit}
                      onChange={(e) =>
                      setNewItem({ ...newItem, unit: e.target.value })
                      }
                      placeholder="单位" />

                  </div>
                </div>
                <div className="mt-4">
                  <label className="text-sm font-medium mb-2 block">
                    验收标准
                  </label>
                  <Input
                    value={newItem.acceptance_criteria}
                    onChange={(e) =>
                    setNewItem({
                      ...newItem,
                      acceptance_criteria: e.target.value
                    })
                    }
                    placeholder="验收标准" />

                </div>
                <div className="mt-4">
                  <label className="text-sm font-medium mb-2 block">
                    标准值
                  </label>
                  <Input
                    value={newItem.standard_value}
                    onChange={(e) =>
                    setNewItem({ ...newItem, standard_value: e.target.value })
                    }
                    placeholder="标准值" />

                </div>
                <div className="mt-4 flex items-center gap-4">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={newItem.is_required}
                      onChange={(e) =>
                      setNewItem({
                        ...newItem,
                        is_required: e.target.checked
                      })
                      } />

                    <span className="text-sm">必检项</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={newItem.is_key_item}
                      onChange={(e) =>
                      setNewItem({
                        ...newItem,
                        is_key_item: e.target.checked
                      })
                      } />

                    <span className="text-sm">关键项</span>
                  </label>
                </div>
                <Button onClick={handleAddItem} className="mt-4">
                  <Plus className="w-4 h-4 mr-2" />
                  添加检查项
                </Button>
              </div>
              <div className="border-t pt-4">
                <h3 className="text-sm font-medium mb-2">检查项列表</h3>
                <div className="space-y-2">
                  {templateItems.length === 0 ?
                  <div className="text-center py-4 text-slate-400">
                      暂无检查项
                    </div> :

                  templateItems.map((item) =>
                  <div key={item.id} className="border rounded-lg p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-medium">{item.item_name}</div>
                            <div className="text-xs text-slate-500 mt-1">
                              {item.item_code}{" "}
                              {item.category_name && `· ${item.category_name}`}
                            </div>
                            {item.acceptance_criteria &&
                        <div className="text-xs text-slate-600 mt-1">
                                验收标准: {item.acceptance_criteria}
                              </div>
                        }
                          </div>
                          <div className="flex items-center gap-2">
                            {item.is_required &&
                        <Badge className="bg-blue-500">必检</Badge>
                        }
                            {item.is_key_item &&
                        <Badge variant="destructive">关键项</Badge>
                        }
                          </div>
                        </div>
                      </div>
                  )
                  }
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowItemsDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}