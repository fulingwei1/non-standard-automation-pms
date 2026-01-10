/**
 * BOM Assembly Attributes Management Page - BOM装配属性维护页面
 * Features: 物料装配阶段配置、阻塞性设置、批量分配、模板套用
 */
import { useState, useEffect } from "react";
import {
  Package,
  Settings,
  Save,
  RefreshCw,
  Wand2,
  FileDown,
  Filter,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Wrench,
  Zap,
  Cable,
  Bug,
  Palette,
  Search,
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
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Switch } from "../components/ui/switch";
import { cn } from "../lib/utils";
import { assemblyKitApi, bomApi, projectApi } from "../services/api";

// 装配阶段配置
const stageOptions = [
  { value: "FRAME", label: "框架装配", icon: Wrench, color: "bg-slate-500" },
  { value: "MECH", label: "机械模组", icon: Package, color: "bg-blue-500" },
  { value: "ELECTRIC", label: "电气安装", icon: Zap, color: "bg-yellow-500" },
  { value: "WIRING", label: "线路整理", icon: Cable, color: "bg-green-500" },
  { value: "DEBUG", label: "调试准备", icon: Bug, color: "bg-purple-500" },
  { value: "COSMETIC", label: "外观完善", icon: Palette, color: "bg-pink-500" },
];

// 重要程度配置
const importanceOptions = [
  { value: "CRITICAL", label: "关键", color: "bg-red-500" },
  { value: "HIGH", label: "高", color: "bg-orange-500" },
  { value: "NORMAL", label: "普通", color: "bg-blue-500" },
  { value: "LOW", label: "低", color: "bg-slate-500" },
];

export default function BomAssemblyAttrs() {
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [boms, setBoms] = useState([]);
  const [stages, setStages] = useState([]);
  const [templates, setTemplates] = useState([]);

  const [selectedProject, setSelectedProject] = useState("");
  const [selectedBom, setSelectedBom] = useState("");
  const [filterStage, setFilterStage] = useState("all");
  const [filterBlocking, setFilterBlocking] = useState("all");
  const [searchText, setSearchText] = useState("");

  const [bomItems, setBomItems] = useState([]);
  const [assemblyAttrs, setAssemblyAttrs] = useState([]);
  const [editedAttrs, setEditedAttrs] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  const [autoAssignDialogOpen, setAutoAssignDialogOpen] = useState(false);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [overwrite, setOverwrite] = useState(false);

  useEffect(() => {
    fetchProjects();
    fetchStages();
    fetchTemplates();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      fetchBoms();
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedBom) {
      fetchBomAssemblyAttrs();
    }
  }, [selectedBom]);

  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };

  const fetchBoms = async () => {
    try {
      const res = await bomApi.list({
        project_id: selectedProject,
        page_size: 100,
      });
      setBoms(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch BOMs:", error);
      setBoms([]);
    }
  };

  const fetchStages = async () => {
    try {
      const res = await assemblyKitApi.getStages();
      setStages(res.data || res || []);
    } catch (error) {
      console.error("Failed to fetch stages:", error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const res = await assemblyKitApi.getTemplates();
      setTemplates(res.data || res || []);
    } catch (error) {
      console.error("Failed to fetch templates:", error);
    }
  };

  const fetchBomAssemblyAttrs = async () => {
    try {
      setLoading(true);
      const res = await assemblyKitApi.getBomAssemblyAttrs(selectedBom);
      const attrs = res.data || res || [];
      setAssemblyAttrs(attrs);

      // 初始化编辑状态
      const initialEdits = {};
      attrs.forEach((attr) => {
        initialEdits[attr.bom_item_id] = { ...attr };
      });
      setEditedAttrs(initialEdits);
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to fetch assembly attrs:", error);
      setAssemblyAttrs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAttrChange = (bomItemId, field, value) => {
    setEditedAttrs((prev) => ({
      ...prev,
      [bomItemId]: {
        ...prev[bomItemId],
        bom_item_id: bomItemId,
        bom_id: parseInt(selectedBom),
        [field]: value,
      },
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const items = Object.values(editedAttrs).filter(
        (attr) => attr.assembly_stage,
      );

      if (items.length === 0) {
        console.error("没有需要保存的配置");
        return;
      }

      await assemblyKitApi.batchSetAssemblyAttrs(selectedBom, { items });
      console.log("保存成功");
      setHasChanges(false);
      fetchBomAssemblyAttrs();
    } catch (error) {
      console.error("保存失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoAssign = async () => {
    try {
      setLoading(true);
      const res = await assemblyKitApi.autoAssignAttrs(selectedBom, {
        bom_id: parseInt(selectedBom),
        overwrite,
      });
      console.log(res.message || "自动分配完成");
      setAutoAssignDialogOpen(false);
      fetchBomAssemblyAttrs();
    } catch (error) {
      console.error("自动分配失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSmartRecommend = async () => {
    try {
      setLoading(true);
      // 先获取推荐结果预览
      const previewRes = await assemblyKitApi.getRecommendations(selectedBom);
      console.log("推荐结果预览:", previewRes.data);

      // 询问用户是否应用推荐
      if (
        window.confirm(
          `智能推荐完成，共推荐 ${previewRes.data?.total || 0} 项。是否应用推荐结果？`,
        )
      ) {
        const res = await assemblyKitApi.smartRecommend(selectedBom, {
          bom_id: parseInt(selectedBom),
          overwrite,
        });
        console.log(res.message || "智能推荐完成");
        if (res.data?.recommendation_stats) {
          const stats = res.data.recommendation_stats;
          const statsText = Object.entries(stats)
            .filter(([_, count]) => count > 0)
            .map(([source, count]) => {
              const sourceNames = {
                HISTORY: "历史数据",
                CATEGORY: "分类匹配",
                KEYWORD: "关键词",
                SUPPLIER: "供应商类型",
                DEFAULT: "默认",
              };
              return `${sourceNames[source] || source}: ${count}项`;
            })
            .join(", ");
          alert(`推荐完成！\n${statsText}`);
        }
        setAutoAssignDialogOpen(false);
        fetchBomAssemblyAttrs();
      }
    } catch (error) {
      console.error("智能推荐失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyTemplate = async () => {
    if (!selectedTemplate) {
      console.error("请选择模板");
      return;
    }
    try {
      setLoading(true);
      const res = await assemblyKitApi.applyTemplate(selectedBom, {
        bom_id: parseInt(selectedBom),
        template_id: parseInt(selectedTemplate),
        overwrite,
      });
      console.log(res.message || "模板套用完成");
      setTemplateDialogOpen(false);
      fetchBomAssemblyAttrs();
    } catch (error) {
      console.error("模板套用失败:", error);
    } finally {
      setLoading(false);
    }
  };

  // 过滤显示的数据
  const filteredAttrs = assemblyAttrs.filter((attr) => {
    if (filterStage !== "all" && attr.assembly_stage !== filterStage)
      return false;
    if (filterBlocking === "blocking" && !attr.is_blocking) return false;
    if (filterBlocking === "postpone" && attr.is_blocking) return false;
    if (searchText) {
      const search = searchText.toLowerCase();
      if (
        !attr.material_code?.toLowerCase().includes(search) &&
        !attr.material_name?.toLowerCase().includes(search)
      ) {
        return false;
      }
    }
    return true;
  });

  // 按阶段分组统计
  const stageStats = stageOptions.map((stage) => {
    const items = assemblyAttrs.filter((a) => a.assembly_stage === stage.value);
    return {
      ...stage,
      total: items.length,
      blocking: items.filter((i) => i.is_blocking).length,
    };
  });

  const getStageOption = (code) =>
    stageOptions.find((s) => s.value === code) || stageOptions[1];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <PageHeader
          title="BOM装配属性配置"
          description="配置物料的装配阶段、阻塞性和重要程度，用于齐套分析"
        />
        <div className="flex items-center gap-2">
          {hasChanges && (
            <Badge
              variant="outline"
              className="bg-yellow-50 text-yellow-700 border-yellow-300"
            >
              有未保存的更改
            </Badge>
          )}
          <Button
            variant="outline"
            disabled={!selectedBom || loading}
            onClick={() => setAutoAssignDialogOpen(true)}
          >
            <Wand2 className="w-4 h-4 mr-2" />
            自动分配
          </Button>
          <Button
            variant="outline"
            disabled={!selectedBom || loading}
            onClick={handleSmartRecommend}
            className="bg-blue-50 hover:bg-blue-100 border-blue-300"
          >
            <Wand2 className="w-4 h-4 mr-2" />
            智能推荐
          </Button>
          <Button
            variant="outline"
            disabled={!selectedBom || loading}
            onClick={() => setTemplateDialogOpen(true)}
          >
            <FileDown className="w-4 h-4 mr-2" />
            套用模板
          </Button>
          <Button disabled={!hasChanges || loading} onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            保存配置
          </Button>
        </div>
      </div>

      {/* Selectors */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label className="mb-2 block">选择项目</Label>
              <Select
                value={selectedProject}
                onValueChange={(v) => {
                  setSelectedProject(v);
                  setSelectedBom("");
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  {projects.map((proj) => (
                    <SelectItem key={proj.id} value={proj.id.toString()}>
                      {proj.name || proj.project_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="mb-2 block">选择BOM</Label>
              <Select
                value={selectedBom}
                onValueChange={setSelectedBom}
                disabled={!selectedProject}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择BOM" />
                </SelectTrigger>
                <SelectContent>
                  {boms.map((bom) => (
                    <SelectItem key={bom.id} value={bom.id.toString()}>
                      {bom.bom_no} - {bom.name || bom.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="mb-2 block">筛选阶段</Label>
              <Select value={filterStage} onValueChange={setFilterStage}>
                <SelectTrigger>
                  <SelectValue placeholder="全部阶段" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部阶段</SelectItem>
                  {stageOptions.map((stage) => (
                    <SelectItem key={stage.value} value={stage.value}>
                      {stage.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="mb-2 block">筛选类型</Label>
              <Select value={filterBlocking} onValueChange={setFilterBlocking}>
                <SelectTrigger>
                  <SelectValue placeholder="全部类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部类型</SelectItem>
                  <SelectItem value="blocking">仅阻塞性</SelectItem>
                  <SelectItem value="postpone">仅可后补</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Search */}
          <div className="mt-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="搜索物料编码或名称..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stage Statistics */}
      {selectedBom && assemblyAttrs.length > 0 && (
        <div className="grid grid-cols-6 gap-4">
          {stageStats.map((stage) => {
            const Icon = stage.icon;
            return (
              <Card
                key={stage.value}
                className={cn(
                  "cursor-pointer transition-all hover:shadow-md",
                  filterStage === stage.value && "ring-2 ring-blue-500",
                )}
                onClick={() =>
                  setFilterStage(
                    filterStage === stage.value ? "all" : stage.value,
                  )
                }
              >
                <CardContent className="pt-4 pb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center",
                        stage.color,
                      )}
                    >
                      <Icon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-medium">{stage.label}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">共 {stage.total} 项</span>
                    <span className="text-red-600">{stage.blocking} 阻塞</span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Main Table */}
      {selectedBom ? (
        <Card>
          <CardHeader>
            <CardTitle>物料装配属性配置</CardTitle>
            <CardDescription>
              共 {filteredAttrs.length} 条记录
              {searchText && ` (搜索: ${searchText})`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : filteredAttrs.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[120px]">物料编码</TableHead>
                    <TableHead>物料名称</TableHead>
                    <TableHead className="w-[80px]">需求数量</TableHead>
                    <TableHead className="w-[150px]">装配阶段</TableHead>
                    <TableHead className="w-[120px]">重要程度</TableHead>
                    <TableHead className="w-[80px]">阻塞性</TableHead>
                    <TableHead className="w-[80px]">可后补</TableHead>
                    <TableHead className="w-[80px]">有替代</TableHead>
                    <TableHead className="w-[80px]">安装顺序</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAttrs.map((attr) => {
                    const edited = editedAttrs[attr.bom_item_id] || attr;
                    const stageOpt = getStageOption(edited.assembly_stage);
                    const StageIcon = stageOpt.icon;

                    return (
                      <TableRow key={attr.id || attr.bom_item_id}>
                        <TableCell className="font-mono text-sm">
                          {attr.material_code}
                        </TableCell>
                        <TableCell>{attr.material_name}</TableCell>
                        <TableCell>{attr.required_qty}</TableCell>
                        <TableCell>
                          <Select
                            value={edited.assembly_stage || "MECH"}
                            onValueChange={(v) =>
                              handleAttrChange(
                                attr.bom_item_id,
                                "assembly_stage",
                                v,
                              )
                            }
                          >
                            <SelectTrigger className="h-8">
                              <SelectValue>
                                <div className="flex items-center gap-1">
                                  <div
                                    className={cn(
                                      "w-3 h-3 rounded-full",
                                      stageOpt.color,
                                    )}
                                  />
                                  <span className="text-sm">
                                    {stageOpt.label}
                                  </span>
                                </div>
                              </SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                              {stageOptions.map((stage) => {
                                const Icon = stage.icon;
                                return (
                                  <SelectItem
                                    key={stage.value}
                                    value={stage.value}
                                  >
                                    <div className="flex items-center gap-2">
                                      <div
                                        className={cn(
                                          "w-3 h-3 rounded-full",
                                          stage.color,
                                        )}
                                      />
                                      {stage.label}
                                    </div>
                                  </SelectItem>
                                );
                              })}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <Select
                            value={edited.importance_level || "NORMAL"}
                            onValueChange={(v) =>
                              handleAttrChange(
                                attr.bom_item_id,
                                "importance_level",
                                v,
                              )
                            }
                          >
                            <SelectTrigger className="h-8">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {importanceOptions.map((imp) => (
                                <SelectItem key={imp.value} value={imp.value}>
                                  <Badge className={imp.color}>
                                    {imp.label}
                                  </Badge>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={edited.is_blocking ?? true}
                            onCheckedChange={(v) =>
                              handleAttrChange(
                                attr.bom_item_id,
                                "is_blocking",
                                v,
                              )
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={edited.can_postpone ?? false}
                            onCheckedChange={(v) =>
                              handleAttrChange(
                                attr.bom_item_id,
                                "can_postpone",
                                v,
                              )
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <Switch
                            checked={edited.has_substitute ?? false}
                            onCheckedChange={(v) =>
                              handleAttrChange(
                                attr.bom_item_id,
                                "has_substitute",
                                v,
                              )
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            className="h-8 w-16"
                            value={edited.stage_order || 0}
                            onChange={(e) =>
                              handleAttrChange(
                                attr.bom_item_id,
                                "stage_order",
                                parseInt(e.target.value) || 0,
                              )
                            }
                            min={0}
                          />
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8 text-slate-400">
                {assemblyAttrs.length === 0
                  ? '暂无装配属性配置，请使用"自动分配"或"套用模板"初始化'
                  : "没有匹配的记录"}
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-slate-400">
              <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>请先选择项目和BOM</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Auto Assign Dialog */}
      <Dialog
        open={autoAssignDialogOpen}
        onOpenChange={setAutoAssignDialogOpen}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>自动分配装配属性</DialogTitle>
            <DialogDescription>
              根据物料分类自动分配装配阶段和阻塞性设置
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>覆盖已有配置</Label>
                <p className="text-sm text-slate-500">
                  是否覆盖已经配置过的物料
                </p>
              </div>
              <Switch checked={overwrite} onCheckedChange={setOverwrite} />
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5" />
                <div className="text-sm text-amber-700">
                  <p className="font-medium">提示</p>
                  <p>
                    自动分配会根据物料分类映射配置来设置装配阶段。请确保已配置好物料分类映射。
                  </p>
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setAutoAssignDialogOpen(false)}
            >
              取消
            </Button>
            <Button onClick={handleAutoAssign} disabled={loading}>
              <Wand2 className="w-4 h-4 mr-2" />
              开始分配
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Template Dialog */}
      <Dialog open={templateDialogOpen} onOpenChange={setTemplateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>套用装配模板</DialogTitle>
            <DialogDescription>
              选择一个预设的装配模板应用到当前BOM
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="mb-2 block">选择模板</Label>
              <Select
                value={selectedTemplate}
                onValueChange={setSelectedTemplate}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择模板" />
                </SelectTrigger>
                <SelectContent>
                  {templates.map((tpl) => (
                    <SelectItem key={tpl.id} value={tpl.id.toString()}>
                      <div>
                        <span className="font-medium">{tpl.template_name}</span>
                        {tpl.equipment_type && (
                          <span className="text-slate-500 ml-2">
                            ({tpl.equipment_type})
                          </span>
                        )}
                        {tpl.is_default && (
                          <Badge variant="outline" className="ml-2">
                            默认
                          </Badge>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label>覆盖已有配置</Label>
                <p className="text-sm text-slate-500">
                  是否覆盖已经配置过的物料
                </p>
              </div>
              <Switch checked={overwrite} onCheckedChange={setOverwrite} />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setTemplateDialogOpen(false)}
            >
              取消
            </Button>
            <Button
              onClick={handleApplyTemplate}
              disabled={loading || !selectedTemplate}
            >
              <FileDown className="w-4 h-4 mr-2" />
              应用模板
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
