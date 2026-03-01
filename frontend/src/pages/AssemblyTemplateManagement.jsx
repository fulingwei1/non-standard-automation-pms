/**
 * 装配工艺模板管理页面
 * 功能：
 * - 创建/编辑装配工艺模板
 * - 配置各阶段物料分类映射
 * - 设置阻塞性物料规则
 */

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Save,
  Plus,
  Trash2,
  Edit2,
  Settings,
  Layers,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer } from "../lib/animations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui";

// 预置装配阶段
const ASSEMBLY_STAGES = [
  { code: "FRAME", name: "机架装配", order: 1, color: "bg-red-500" },
  { code: "MECH", name: "机械装配", order: 2, color: "bg-orange-500" },
  { code: "ELECTRIC", name: "电气装配", order: 3, color: "bg-yellow-500" },
  { code: "WIRING", name: "接线", order: 4, color: "bg-green-500" },
  { code: "DEBUG", name: "调试", order: 5, color: "bg-blue-500" },
  { code: "COSMETIC", name: "外观", order: 6, color: "bg-purple-500" },
];

// 重要程度选项
const IMPORTANCE_LEVELS = [
  { value: "CRITICAL", label: "关键", color: "bg-red-500" },
  { value: "IMPORTANT", label: "重要", color: "bg-orange-500" },
  { value: "NORMAL", label: "普通", color: "bg-blue-500" },
  { value: "LOW", label: "次要", color: "bg-gray-500" },
];

export default function AssemblyTemplateManagement() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // 加载模板列表
  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      // TODO: 调用 API
      setTemplates([
        {
          id: 1,
          template_code: "TPL_ICT",
          template_name: "ICT 测试设备模板",
          equipment_type: "ICT",
          description: "标准 ICT 测试设备装配工艺",
          is_active: true,
        },
      ]);
    } catch (error) {
      console.error("加载模板失败:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  // 保存模板
  const handleSave = async () => {
    setSaving(true);
    try {
      // TODO: 调用 API 保存
      alert("保存成功");
      setShowEditDialog(false);
      loadTemplates();
    } catch (error) {
      alert("保存失败：" + error.message);
    } finally {
      setSaving(false);
    }
  };

  // 编辑模板
  const handleEdit = (template) => {
    setSelectedTemplate(template);
    setShowEditDialog(true);
  };

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
            title="装配工艺模板管理"
            description="配置装配工艺路线、物料分类映射、阻塞性物料规则"
            actions={
              <Button onClick={() => setShowEditDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                新建模板
              </Button>
            }
          />

          {/* 装配阶段说明 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-500" />
                装配工艺阶段
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {ASSEMBLY_STAGES.map((stage) => (
                  <div
                    key={stage.code}
                    className="p-3 rounded-lg border bg-slate-800/50"
                  >
                    <div className={`w-3 h-3 rounded-full ${stage.color} mb-2`} />
                    <div className="font-medium text-sm">{stage.name}</div>
                    <div className="text-xs text-slate-400">{stage.code}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 模板列表 */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-slate-400">加载中...</div>
            </div>
          ) : templates.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-slate-400">
                暂无模板，点击右上角"新建模板"创建
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <Card key={template.id}>
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-semibold text-lg">
                            {template.template_name}
                          </h3>
                          <Badge variant={template.is_active ? "default" : "secondary"}>
                            {template.is_active ? "启用" : "停用"}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-400">
                          {template.description || "无描述"}
                        </p>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">类型:</span>
                        <Badge variant="outline">{template.equipment_type}</Badge>
                      </div>

                      <div className="flex gap-2 pt-4 border-t">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => handleEdit(template)}
                        >
                          <Edit2 className="w-3 h-3 mr-1" />
                          编辑
                        </Button>
                        <Button variant="outline" size="sm" className="flex-1">
                          <Settings className="w-3 h-3 mr-1" />
                          映射配置
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* 编辑对话框 */}
          <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>
                  {selectedTemplate ? "编辑模板" : "新建装配工艺模板"}
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>模板编码</Label>
                    <Input placeholder="例如：TPL_ICT" />
                  </div>
                  <div>
                    <Label>设备类型</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="选择类型" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ICT">ICT 测试设备</SelectItem>
                        <SelectItem value="FCT">FCT 功能测试</SelectItem>
                        <SelectItem value="EOL">EOL 终检设备</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div>
                  <Label>模板名称</Label>
                  <Input placeholder="例如：ICT 测试设备标准工艺" />
                </div>
                <div>
                  <Label>描述</Label>
                  <Textarea rows={3} placeholder="模板描述..." />
                </div>

                {/* 物料分类映射 */}
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <Label>物料分类映射配置</Label>
                    <Button variant="outline" size="sm">
                      <Plus className="w-3 h-3 mr-1" />
                      添加映射
                    </Button>
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>物料分类</TableHead>
                        <TableHead>装配阶段</TableHead>
                        <TableHead>重要程度</TableHead>
                        <TableHead>阻塞性</TableHead>
                        <TableHead>操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>伺服电机</TableCell>
                        <TableCell>
                          <Badge>电气装配</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="destructive">关键</Badge>
                        </TableCell>
                        <TableCell>
                          <CheckCircle className="w-4 h-4 text-red-500" />
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm">
                            <Edit2 className="w-3 h-3" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowEditDialog(false)}>
                  取消
                </Button>
                <Button onClick={handleSave} disabled={saving}>
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? "保存中..." : "保存"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </motion.div>
      </div>
    </div>
  );
}
