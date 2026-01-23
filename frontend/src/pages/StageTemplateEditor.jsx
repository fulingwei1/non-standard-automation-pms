import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  Plus,
  Edit3,
  Trash2,
  GripVertical,
  ChevronDown,
  ChevronRight,
  Settings,
  Save,
  RotateCcw,
} from "lucide-react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Switch } from "../components/ui/switch";
import { cn } from "../lib/utils";
import { fadeIn } from "../lib/animations";
import { stageTemplateApi } from "../services/api";

// 节点类型枚举
const NODE_TYPES = {
  TASK: { label: "任务节点", color: "bg-blue-500/20 text-blue-400" },
  APPROVAL: { label: "审批节点", color: "bg-amber-500/20 text-amber-400" },
  DELIVERABLE: { label: "交付物节点", color: "bg-emerald-500/20 text-emerald-400" },
};

// 完成方式枚举
const COMPLETION_METHODS = {
  MANUAL: "手动完成",
  APPROVAL: "需要审批",
  UPLOAD: "上传附件",
  AUTO: "自动完成",
};

export default function StageTemplateEditor() {
  const { templateId } = useParams();
  const navigate = useNavigate();

  const [template, setTemplate] = useState(null);
  const [stages, setStages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedStages, setExpandedStages] = useState(new Set());
  const [saving, setSaving] = useState(false);

  // Stage Dialog states
  const [showStageDialog, setShowStageDialog] = useState(false);
  const [stageDialogMode, setStageDialogMode] = useState("create"); // create | edit
  const [selectedStage, setSelectedStage] = useState(null);
  const [stageFormData, setStageFormData] = useState({
    stage_code: "",
    stage_name: "",
    sequence: 1,
    estimated_days: 5,
    description: "",
    is_required: true,
  });

  // Node Dialog states
  const [showNodeDialog, setShowNodeDialog] = useState(false);
  const [nodeDialogMode, setNodeDialogMode] = useState("create"); // create | edit
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedStageForNode, setSelectedStageForNode] = useState(null);
  const [nodeFormData, setNodeFormData] = useState({
    node_code: "",
    node_name: "",
    node_type: "TASK",
    sequence: 1,
    estimated_days: 1,
    completion_method: "MANUAL",
    is_required: true,
    required_attachments: false,
    description: "",
    approval_role_ids: [],
    auto_condition: "",
    dependency_node_ids: [],
  });

  // 加载模板详情
  const loadTemplate = useCallback(async () => {
    setLoading(true);
    try {
      const response = await stageTemplateApi.get(templateId);
      setTemplate(response.data);
      setStages(response.data.stage_definitions || []);
      // 默认展开所有阶段
      setExpandedStages(new Set((response.data.stage_definitions || []).map((s) => s.id)));
    } catch (error) {
      console.error("加载模板详情失败:", error);
      // Mock data
      setTemplate({
        id: parseInt(templateId),
        template_code: "STD_9_STAGE",
        template_name: "标准九阶段流程",
        description: "适用于大多数非标自动化项目的标准九阶段流程模板",
        project_type: "STANDARD",
        is_default: true,
        is_active: true,
      });
      setStages([
        {
          id: 1,
          stage_code: "S1",
          stage_name: "需求进入",
          sequence: 1,
          estimated_days: 3,
          description: "项目需求收集和初步评估",
          is_required: true,
          node_definitions: [
            {
              id: 1,
              node_code: "S1_N1",
              node_name: "需求调研",
              node_type: "TASK",
              sequence: 1,
              estimated_days: 2,
              completion_method: "MANUAL",
              is_required: true,
            },
            {
              id: 2,
              node_code: "S1_N2",
              node_name: "需求评审",
              node_type: "APPROVAL",
              sequence: 2,
              estimated_days: 1,
              completion_method: "APPROVAL",
              is_required: true,
            },
          ],
        },
        {
          id: 2,
          stage_code: "S2",
          stage_name: "方案设计",
          sequence: 2,
          estimated_days: 7,
          description: "技术方案设计和评审",
          is_required: true,
          node_definitions: [
            {
              id: 3,
              node_code: "S2_N1",
              node_name: "方案设计",
              node_type: "TASK",
              sequence: 1,
              estimated_days: 5,
              completion_method: "MANUAL",
              is_required: true,
            },
            {
              id: 4,
              node_code: "S2_N2",
              node_name: "方案评审",
              node_type: "APPROVAL",
              sequence: 2,
              estimated_days: 2,
              completion_method: "APPROVAL",
              is_required: true,
            },
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [templateId]);

  useEffect(() => {
    loadTemplate();
  }, [loadTemplate]);

  const toggleStageExpanded = (stageId) => {
    setExpandedStages((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(stageId)) {
        newSet.delete(stageId);
      } else {
        newSet.add(stageId);
      }
      return newSet;
    });
  };

  // Stage handlers
  const handleAddStage = () => {
    setStageDialogMode("create");
    setStageFormData({
      stage_code: "",
      stage_name: "",
      sequence: stages.length + 1,
      estimated_days: 5,
      description: "",
      is_required: true,
    });
    setShowStageDialog(true);
  };

  const handleEditStage = (stage) => {
    setStageDialogMode("edit");
    setSelectedStage(stage);
    setStageFormData({
      stage_code: stage.stage_code,
      stage_name: stage.stage_name,
      sequence: stage.sequence,
      estimated_days: stage.estimated_days,
      description: stage.description || "",
      is_required: stage.is_required,
    });
    setShowStageDialog(true);
  };

  const handleDeleteStage = async (stage) => {
    if (!confirm(`确定要删除阶段 "${stage.stage_name}" 吗？`)) return;
    try {
      await stageTemplateApi.stages.delete(stage.id);
      loadTemplate();
    } catch (error) {
      console.error("删除阶段失败:", error);
      // Optimistic update for demo
      setStages((prev) => prev.filter((s) => s.id !== stage.id));
    }
  };

  const handleSaveStage = async () => {
    try {
      if (stageDialogMode === "create") {
        await stageTemplateApi.stages.add(template.id, {
          ...stageFormData,
          template_id: parseInt(templateId),
        });
      } else {
        await stageTemplateApi.stages.update(selectedStage.id, stageFormData);
      }
      setShowStageDialog(false);
      loadTemplate();
    } catch (error) {
      console.error("保存阶段失败:", error);
      alert("保存失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // Node handlers
  const handleAddNode = (stage) => {
    setNodeDialogMode("create");
    setSelectedStageForNode(stage);
    const existingNodes = stage.node_definitions || [];
    setNodeFormData({
      node_code: "",
      node_name: "",
      node_type: "TASK",
      sequence: existingNodes.length + 1,
      estimated_days: 1,
      completion_method: "MANUAL",
      is_required: true,
      required_attachments: false,
      description: "",
      approval_role_ids: [],
      auto_condition: "",
      dependency_node_ids: [],
    });
    setShowNodeDialog(true);
  };

  const handleEditNode = (stage, node) => {
    setNodeDialogMode("edit");
    setSelectedStageForNode(stage);
    setSelectedNode(node);
    setNodeFormData({
      node_code: node.node_code,
      node_name: node.node_name,
      node_type: node.node_type,
      sequence: node.sequence,
      estimated_days: node.estimated_days,
      completion_method: node.completion_method,
      is_required: node.is_required,
      required_attachments: node.required_attachments || false,
      description: node.description || "",
      approval_role_ids: node.approval_role_ids || [],
      auto_condition: node.auto_condition || "",
      dependency_node_ids: node.dependency_node_ids || [],
    });
    setShowNodeDialog(true);
  };

  const handleDeleteNode = async (stage, node) => {
    if (!confirm(`确定要删除节点 "${node.node_name}" 吗？`)) return;
    try {
      await stageTemplateApi.nodes.delete(node.id);
      loadTemplate();
    } catch (error) {
      console.error("删除节点失败:", error);
      // Optimistic update for demo
      setStages((prev) =>
        prev.map((s) => {
          if (s.id === stage.id) {
            return {
              ...s,
              node_definitions: s.node_definitions.filter((n) => n.id !== node.id),
            };
          }
          return s;
        })
      );
    }
  };

  const handleSaveNode = async () => {
    try {
      const stageId = selectedStageForNode.id;
      if (nodeDialogMode === "create") {
        await stageTemplateApi.nodes.add(stageId, {
          ...nodeFormData,
          stage_definition_id: stageId,
        });
      } else {
        await stageTemplateApi.nodes.update(selectedNode.id, nodeFormData);
      }
      setShowNodeDialog(false);
      loadTemplate();
    } catch (error) {
      console.error("保存节点失败:", error);
      alert("保存失败: " + (error.response?.data?.detail || error.message));
    }
  };

  if (loading && !template) {
    return (
      <div className="min-h-screen bg-surface-50 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-violet-500" />
          <span>加载中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title={
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => navigate("/system/stage-templates")}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <div className="flex items-center gap-2">
                <span>{template?.template_name}</span>
                <Badge variant="outline" className="text-xs">
                  {template?.template_code}
                </Badge>
              </div>
              <p className="text-sm text-slate-400 font-normal mt-0.5">
                {template?.description}
              </p>
            </div>
          </div>
        }
        subtitle="配置项目的阶段流程和节点定义"
        icon={Settings}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate("/system/stage-templates")}>
              取消
            </Button>
            <Button onClick={() => navigate("/system/stage-templates")}>
              <Save className="h-4 w-4 mr-2" />
              保存
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-4">
        {/* 阶段列表 */}
        <AnimatePresence>
          {stages.map((stage, stageIndex) => (
            <motion.div
              key={stage.id}
              variants={fadeIn}
              initial="hidden"
              animate="show"
              exit="hidden"
              transition={{ delay: stageIndex * 0.05 }}
            >
              <Card className="bg-surface-100 border-white/5 overflow-hidden">
                {/* 阶段标题 */}
                <CardHeader
                  className={cn(
                    "border-b border-white/5 cursor-pointer hover:bg-white/[0.02] transition-colors",
                    expandedStages.has(stage.id) ? "bg-white/[0.02]" : ""
                  )}
                  onClick={() => toggleStageExpanded(stage.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {expandedStages.has(stage.id) ? (
                        <ChevronDown className="h-4 w-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      )}
                      <GripVertical className="h-4 w-4 text-slate-600 cursor-grab" />
                      <Badge variant="outline" className="bg-violet-500/20 text-violet-400 border-violet-500/30">
                        {stage.stage_code}
                      </Badge>
                      <span className="text-white font-medium">{stage.stage_name}</span>
                      <span className="text-sm text-slate-400">
                        {stage.estimated_days} 天
                      </span>
                      {stage.is_required && (
                        <Badge variant="secondary" className="text-xs">
                          必需
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddNode(stage);
                        }}
                      >
                        <Plus className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditStage(stage);
                        }}
                      >
                        <Edit3 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteStage(stage);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  {stage.description && (
                    <p className="text-sm text-slate-400 mt-2 ml-9">{stage.description}</p>
                  )}
                </CardHeader>

                {/* 节点列表 */}
                {expandedStages.has(stage.id) && (
                  <CardContent className="p-4">
                    <div className="space-y-2">
                      {(stage.node_definitions || []).map((node, nodeIndex) => (
                        <motion.div
                          key={node.id}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: nodeIndex * 0.03 }}
                          className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/5 hover:border-white/10 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <GripVertical className="h-4 w-4 text-slate-600 cursor-grab" />
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-xs",
                                NODE_TYPES[node.node_type]?.color || NODE_TYPES.TASK.color
                              )}
                            >
                              {NODE_TYPES[node.node_type]?.label || "任务"}
                            </Badge>
                            <code className="text-xs font-mono text-slate-400 bg-white/5 px-2 py-0.5 rounded">
                              {node.node_code}
                            </code>
                            <span className="text-white">{node.node_name}</span>
                            <span className="text-xs text-slate-500">
                              {COMPLETION_METHODS[node.completion_method] || "手动完成"}
                            </span>
                            <span className="text-xs text-slate-500">
                              {node.estimated_days} 天
                            </span>
                            {node.is_required && (
                              <Badge variant="secondary" className="text-xs">
                                必需
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => handleEditNode(stage, node)}
                            >
                              <Edit3 className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                              onClick={() => handleDeleteNode(stage, node)}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </div>
                        </motion.div>
                      ))}
                      {(stage.node_definitions || []).length === 0 && (
                        <div className="text-center py-6 text-slate-500">
                          暂无节点，点击上方 "+" 添加节点
                        </div>
                      )}
                    </div>
                  </CardContent>
                )}
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* 添加阶段按钮 */}
        <motion.div variants={fadeIn} initial="hidden" animate="show">
          <Button
            variant="outline"
            className="w-full border-dashed border-white/20 hover:border-violet-500/50 hover:bg-violet-500/5"
            onClick={handleAddStage}
          >
            <Plus className="h-4 w-4 mr-2" />
            添加阶段
          </Button>
        </motion.div>

        {stages.length === 0 && !loading && (
          <Card className="bg-surface-100 border-white/5">
            <CardContent className="p-12 text-center">
              <Settings className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">暂无阶段定义</p>
              <p className="text-sm text-slate-500 mt-2">点击上方按钮添加第一个阶段</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* 阶段对话框 */}
      <Dialog open={showStageDialog} onOpenChange={setShowStageDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {stageDialogMode === "create" ? (
                <>
                  <Plus className="h-5 w-5 text-violet-400" />
                  添加阶段
                </>
              ) : (
                <>
                  <Edit3 className="h-5 w-5 text-violet-400" />
                  编辑阶段
                </>
              )}
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>阶段编码 *</Label>
                <Input
                  placeholder="如 S1"
                  value={stageFormData.stage_code}
                  onChange={(e) =>
                    setStageFormData((prev) => ({ ...prev, stage_code: e.target.value.toUpperCase() }))
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div className="space-y-2">
                <Label>排序顺序</Label>
                <Input
                  type="number"
                  value={stageFormData.sequence}
                  onChange={(e) =>
                    setStageFormData((prev) => ({ ...prev, sequence: parseInt(e.target.value) || 1 }))
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>阶段名称 *</Label>
              <Input
                placeholder="如 需求进入"
                value={stageFormData.stage_name}
                onChange={(e) =>
                  setStageFormData((prev) => ({ ...prev, stage_name: e.target.value }))
                }
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>预估天数</Label>
              <Input
                type="number"
                value={stageFormData.estimated_days}
                onChange={(e) =>
                  setStageFormData((prev) => ({ ...prev, estimated_days: parseInt(e.target.value) || 1 }))
                }
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="space-y-2">
              <Label>阶段描述</Label>
              <Textarea
                placeholder="描述该阶段的主要工作内容..."
                value={stageFormData.description}
                onChange={(e) =>
                  setStageFormData((prev) => ({ ...prev, description: e.target.value }))
                }
                className="bg-white/5 border-white/10 min-h-[80px]"
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="stage_required"
                checked={stageFormData.is_required}
                onCheckedChange={(v) => setStageFormData((prev) => ({ ...prev, is_required: v }))}
              />
              <Label htmlFor="stage_required" className="cursor-pointer">
                必需阶段
              </Label>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowStageDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSaveStage}>
              {stageDialogMode === "create" ? "添加" : "保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 节点对话框 */}
      <Dialog open={showNodeDialog} onOpenChange={setShowNodeDialog}>
        <DialogContent className="max-w-md max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {nodeDialogMode === "create" ? (
                <>
                  <Plus className="h-5 w-5 text-violet-400" />
                  添加节点
                </>
              ) : (
                <>
                  <Edit3 className="h-5 w-5 text-violet-400" />
                  编辑节点
                </>
              )}
              <Badge variant="outline" className="bg-violet-500/20 text-violet-400 border-violet-500/30">
                {selectedStageForNode?.stage_code}
              </Badge>
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>节点编码 *</Label>
                <Input
                  placeholder="如 S1_N1"
                  value={nodeFormData.node_code}
                  onChange={(e) =>
                    setNodeFormData((prev) => ({ ...prev, node_code: e.target.value.toUpperCase() }))
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div className="space-y-2">
                <Label>排序顺序</Label>
                <Input
                  type="number"
                  value={nodeFormData.sequence}
                  onChange={(e) =>
                    setNodeFormData((prev) => ({ ...prev, sequence: parseInt(e.target.value) || 1 }))
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>节点名称 *</Label>
              <Input
                placeholder="如 需求调研"
                value={nodeFormData.node_name}
                onChange={(e) =>
                  setNodeFormData((prev) => ({ ...prev, node_name: e.target.value }))
                }
                className="bg-white/5 border-white/10"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>节点类型</Label>
                <Select
                  value={nodeFormData.node_type}
                  onValueChange={(v) => setNodeFormData((prev) => ({ ...prev, node_type: v }))}
                >
                  <SelectTrigger className="bg-white/5 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="TASK">任务节点</SelectItem>
                    <SelectItem value="APPROVAL">审批节点</SelectItem>
                    <SelectItem value="DELIVERABLE">交付物节点</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>预估天数</Label>
                <Input
                  type="number"
                  value={nodeFormData.estimated_days}
                  onChange={(e) =>
                    setNodeFormData((prev) => ({ ...prev, estimated_days: parseInt(e.target.value) || 1 }))
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>完成方式</Label>
              <Select
                value={nodeFormData.completion_method}
                onValueChange={(v) => setNodeFormData((prev) => ({ ...prev, completion_method: v }))}
              >
                <SelectTrigger className="bg-white/5 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MANUAL">手动完成</SelectItem>
                  <SelectItem value="APPROVAL">需要审批</SelectItem>
                  <SelectItem value="UPLOAD">上传附件</SelectItem>
                  <SelectItem value="AUTO">自动完成</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>节点描述</Label>
              <Textarea
                placeholder="描述该节点的工作内容..."
                value={nodeFormData.description}
                onChange={(e) =>
                  setNodeFormData((prev) => ({ ...prev, description: e.target.value }))
                }
                className="bg-white/5 border-white/10 min-h-[60px]"
              />
            </div>
            {nodeFormData.completion_method === "AUTO" && (
              <div className="space-y-2">
                <Label>自动完成条件 (JSON)</Label>
                <Textarea
                  placeholder='{"field": "value"}'
                  value={nodeFormData.auto_condition}
                  onChange={(e) =>
                    setNodeFormData((prev) => ({ ...prev, auto_condition: e.target.value }))
                  }
                  className="bg-white/5 border-white/10 min-h-[60px] font-mono text-sm"
                />
              </div>
            )}
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <Switch
                  id="node_required"
                  checked={nodeFormData.is_required}
                  onCheckedChange={(v) => setNodeFormData((prev) => ({ ...prev, is_required: v }))}
                />
                <Label htmlFor="node_required" className="cursor-pointer">
                  必需节点
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  id="node_attachments"
                  checked={nodeFormData.required_attachments}
                  onCheckedChange={(v) =>
                    setNodeFormData((prev) => ({ ...prev, required_attachments: v }))
                  }
                />
                <Label htmlFor="node_attachments" className="cursor-pointer">
                  需要上传附件
                </Label>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" onClick={() => setShowNodeDialog(false)}>
              取消
            </Button>
            <Button onClick={handleSaveNode}>
              {nodeDialogMode === "create" ? "添加" : "保存"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
