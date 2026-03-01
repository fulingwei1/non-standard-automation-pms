/**
 * 模板配置可视化编辑器
 * 支持：
 * - 勾选启用/禁用阶段
 * - 勾选启用/禁用节点
 * - 拖拽调整顺序
 * - 保存为自定义配置
 */

import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, Reorder } from "framer-motion";
import {
  Save,
  Plus,
  Trash2,
  Edit2,
  ChevronDown,
  ChevronRight,
  GripVertical,
  CheckCircle,
  XCircle,
  Copy,
  Info,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { staggerContainer } from "../../lib/animations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Input,
  Label,
  Switch,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Textarea,
  Tooltip,
} from "../../components/ui";
import { templateConfigApi } from "../../services/api/templateConfig";

// 预置模板选项
const PRESET_TEMPLATES = [
  { code: "TPL_STANDARD", name: "标准全流程" },
  { code: "TPL_FULL_LIFECYCLE", name: "完整生命周期" },
  { code: "TPL_QUICK", name: "简易快速开发" },
  { code: "TPL_REPEAT", name: "重复生产" },
];

// 阶段介绍数据
const STAGE_DESCRIPTIONS = {
  S1: { name: "需求进入", desc: "接收客户需求，评估可行性", days: 7 },
  S2: { name: "方案设计", desc: "完成整体方案设计与技术评审", days: 14 },
  S3: { name: "采购备料", desc: "采购原材料和零部件", days: 10 },
  S4: { name: "生产制造", desc: "机械加工和装配", days: 20 },
  S5: { name: "厂内调试", desc: "设备组装和内部测试", days: 7 },
  S6: { name: "客户验收", desc: "客户现场验收", days: 5 },
  S7: { name: "发货交付", desc: "设备发货和现场安装", days: 5 },
  S8: { name: "售后支持", desc: "售后服务和技术支持", days: 30 },
  S9: { name: "项目结项", desc: "项目总结和归档", days: 3 },
};

// 节点类型说明
const NODE_TYPE_LABELS = {
  TASK: "任务",
  APPROVAL: "审批",
  DELIVERABLE: "交付物",
  MILESTONE: "里程碑",
};

function NodeItem({ node, onToggle, onReorder }) {
  return (
    <Reorder.Item
      value={node || "unknown"}
      id={node.id}
      onDragEnd={onReorder}
      className={`flex items-center justify-between p-3 rounded-lg border ${
        node.is_enabled
          ? "bg-emerald-500/5 border-emerald-500/20"
          : "bg-slate-800/50 border-slate-700"
      }`}
    >
      <div className="flex items-center gap-3">
        <GripVertical className="w-4 h-4 text-slate-600 cursor-grab" />
        <div>
          <div className="font-medium">
            {node.node_code} - {node.node_name}
          </div>
          <div className="text-xs text-slate-500 flex items-center gap-2">
            <span>类型：{NODE_TYPE_LABELS[node.node_type] || node.node_type}</span>
            <span>|</span>
            <span>负责人：{node.custom_owner_role_code || "PM"}</span>
            <span>|</span>
            <span>工期：{node.custom_estimated_days || 1} 天</span>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-4">
        {node.is_required && (
          <Badge variant="outline" className="text-xs">
            必需
          </Badge>
        )}
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-400">启用</span>
          <Switch
            checked={node.is_enabled}
            onCheckedChange={(checked) => onToggle(node.id, checked)}
            disabled={node.is_required}
          />
        </div>
      </div>
    </Reorder.Item>
  );
}

export default function TemplateConfigEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  
  // 新建配置表单
  const [createForm, setCreateForm] = useState({
    config_code: "",
    config_name: "",
    description: "",
    base_template_code: "TPL_STANDARD",
  });

  // 展开/收起阶段
  const [expandedStages, setExpandedStages] = useState({});

  // 加载配置
  const loadConfig = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await templateConfigApi.get(id);
      setConfig(res.data || res);
    } catch (error) {
      console.error("加载配置失败:", error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  // 创建新配置
  const handleCreate = async () => {
    setSaving(true);
    try {
      await templateConfigApi.create({
        ...createForm,
        config: { stages: [] },
        stages: [],
      });
      setShowCreateDialog(false);
      navigate("/template-configs");
    } catch (error) {
      alert("创建失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  // 保存配置
  const handleSave = async () => {
    if (!id || !config) return;
    setSaving(true);
    try {
      // 更新 sequence
      const updatedStages = config.stages.map((stage, index) => ({
        ...stage,
        sequence: index,
        nodes: stage.nodes.map((node, nodeIndex) => ({
          ...node,
          sequence: nodeIndex,
        })),
      }));
      
      await templateConfigApi.update(id, {
        config_name: config.config_name,
        description: config.description,
        config: { stages: updatedStages },
        stages: updatedStages,
      });
      alert("保存成功");
    } catch (error) {
      alert("保存失败：" + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  // 切换阶段启用状态
  const toggleStage = (stageId, enabled) => {
    setConfig(prev => ({
      ...prev,
      stages: prev.stages.map(s =>
        s.id === stageId ? { ...s, is_enabled: enabled } : s
      ),
    }));
  };

  // 切换节点启用状态
  const toggleNode = (stageId, nodeId, enabled) => {
    setConfig(prev => ({
      ...prev,
      stages: prev.stages.map(s => {
        if (s.id !== stageId) return s;
        return {
          ...s,
          nodes: s.nodes.map(n =>
            n.id === nodeId ? { ...n, is_enabled: enabled } : n
          ),
        };
      }),
    }));
  };

  // 拖拽调整节点顺序
  const handleReorderNodes = (stageId, newNodes) => {
    setConfig(prev => ({
      ...prev,
      stages: prev.stages.map(s =>
        s.id === stageId ? { ...s, nodes: newNodes } : s
      ),
    }));
  };

  // 拖拽调整阶段顺序
  const handleReorderStages = (newStages) => {
    setConfig(prev => ({
      ...prev,
      stages: newStages,
    }));
  };

  // 展开/收起阶段
  const toggleExpand = (stageCode) => {
    setExpandedStages(prev => ({
      ...prev,
      [stageCode]: !prev[stageCode],
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <PageHeader
            title={id ? "编辑模板配置" : "新建模板配置"}
            description="可视化配置项目模板，自定义阶段和节点（支持拖拽调整顺序）"
            actions={
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => navigate("/template-configs")}>
                  返回列表
                </Button>
                <Button onClick={handleSave} disabled={saving || !id}>
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? "保存中..." : "保存配置"}
                </Button>
              </div>
            }
          />

          {/* 基本信息 */}
          {config && (
            <Card>
              <CardHeader>
                <CardTitle>基本信息</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>配置名称</Label>
                    <Input
                      value={config.config_name}
                      onChange={(e) => setConfig({ ...config, config_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>基础模板</Label>
                    <Input value={config.base_template_code} disabled />
                  </div>
                </div>
                <div>
                  <Label>描述</Label>
                  <Textarea
                    value={config.description || ""}
                    onChange={(e) => setConfig({ ...config, description: e.target.value })}
                    rows={2}
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* 使用说明 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="w-5 h-5 text-blue-500" />
                使用说明
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>✅ <strong>拖拽调整顺序：</strong> 拖动阶段标题或节点左侧的 ⋮⋮ 图标调整顺序</li>
                <li>✅ <strong>启用/禁用：</strong> 使用开关控制阶段和节点的启用状态</li>
                <li>✅ <strong>必需项：</strong> 标记为"必需"的阶段/节点不可禁用</li>
                <li>✅ <strong>保存配置：</strong> 修改后点击右上角"保存配置"按钮</li>
              </ul>
            </CardContent>
          </Card>

          {/* 阶段和节点配置 - 支持拖拽 */}
          {config && (
            <Reorder.Group
              axis="y"
              values={config.stages || []}
              onReorder={handleReorderStages}
              className="space-y-4"
            >
              {(config.stages || []).map((stage) => {
                const stageInfo = STAGE_DESCRIPTIONS[stage.stage_code] || {};
                return (
                  <Reorder.Item key={stage.id} value={stage || "unknown"} id={stage.id}>
                    <Card>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <GripVertical className="w-5 h-5 text-slate-600 cursor-grab" />
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleExpand(stage.stage_code)}
                            >
                              {expandedStages[stage.stage_code] ? (
                                <ChevronDown className="w-4 h-4" />
                              ) : (
                                <ChevronRight className="w-4 h-4" />
                              )}
                            </Button>
                            <div>
                              <CardTitle className="text-lg">
                                {stage.stage_code} - {stage.stage_name || stageInfo.name}
                              </CardTitle>
                              <CardDescription className="flex items-center gap-2">
                                {stage.custom_description || stageInfo.desc}
                                <Badge variant="outline" className="text-xs">
                                  {stage.custom_estimated_days || stageInfo.days || 7} 天
                                </Badge>
                              </CardDescription>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <Badge variant={stage.is_enabled ? "default" : "secondary"}>
                              {stage.is_enabled ? "已启用" : "已禁用"}
                            </Badge>
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-slate-400">启用</span>
                              <Switch
                                checked={stage.is_enabled}
                                onCheckedChange={(checked) => toggleStage(stage.id, checked)}
                              />
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      
                      {expandedStages[stage.stage_code] && (
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                              <GripVertical className="w-4 h-4" />
                              阶段节点（拖拽 ⋮⋮ 调整顺序，勾选启用的节点会在创建项目时自动生成）
                            </div>
                            <Reorder.Group
                              axis="y"
                              values={stage.nodes || []}
                              onReorder={(newNodes) => handleReorderNodes(stage.id, newNodes)}
                              className="space-y-2"
                            >
                              {(stage.nodes || []).map((node) => (
                                <NodeItem
                                  key={node.id}
                                  node={node}
                                  onToggle={(enabled) => toggleNode(stage.id, node.id, enabled)}
                                  onReorder={(newNodes) => handleReorderNodes(stage.id, newNodes)}
                                />
                              ))}
                            </Reorder.Group>
                          </div>
                        </CardContent>
                      )}
                    </Card>
                  </Reorder.Item>
                );
              })}
            </Reorder.Group>
          )}

          {/* 创建对话框 */}
          <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>创建新模板配置</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <Label>配置编码</Label>
                  <Input
                    value={createForm.config_code}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, config_code: e.target.value })
                    }
                    placeholder="例如：CFG_CUSTOM_001"
                  />
                </div>
                <div>
                  <Label>配置名称</Label>
                  <Input
                    value={createForm.config_name}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, config_name: e.target.value })
                    }
                    placeholder="例如：简易版标准流程"
                  />
                </div>
                <div>
                  <Label>描述</Label>
                  <Textarea
                    value={createForm.description}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, description: e.target.value })
                    }
                    rows={3}
                  />
                </div>
                <div>
                  <Label>基础模板</Label>
                  <select
                    className="w-full h-10 px-3 rounded-lg bg-slate-700 border border-slate-600 text-white"
                    value={createForm.base_template_code}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, base_template_code: e.target.value })
                    }
                  >
                    {PRESET_TEMPLATES.map((t) => (
                      <option key={t.code} value={t.code}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  取消
                </Button>
                <Button onClick={handleCreate} disabled={saving}>
                  {saving ? "创建中..." : "创建"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </motion.div>
      </div>
    </div>
  );
}
