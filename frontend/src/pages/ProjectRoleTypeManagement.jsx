import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Search,
  Edit3,
  Trash2,
  Users,
  Shield,
  Briefcase,
  Settings,
  GripVertical,
  CheckCircle,
  XCircle,
  ClipboardList,
  Wrench,
  Zap,
  Code,
  Package,
  Headphones,
  ClipboardCheck,
  UserCog,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { projectRoleApi } from "../services/api";

// 角色分类常量
const ROLE_CATEGORIES = {
  MANAGEMENT: {
    label: "管理类",
    color: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  },
  TECHNICAL: {
    label: "技术类",
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  },
  SUPPORT: {
    label: "支持类",
    color: "bg-green-500/20 text-green-400 border-green-500/30",
  },
  GENERAL: {
    label: "通用类",
    color: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  },
};

// 角色编码对应的图标
const ROLE_ICONS = {
  PM: ClipboardList,
  TECH_LEAD: Settings,
  ME_LEAD: Wrench,
  EE_LEAD: Zap,
  SW_LEAD: Code,
  PROC_LEAD: Package,
  CS_LEAD: Headphones,
  QA_LEAD: ClipboardCheck,
  PMC_LEAD: UserCog,
  INSTALL_LEAD: Users,
};

export default function ProjectRoleTypeManagement() {
  const [roleTypes, setRoleTypes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedRoleType, setSelectedRoleType] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterActive, setFilterActive] = useState("all");

  const [formData, setFormData] = useState({
    role_code: "",
    role_name: "",
    role_category: "GENERAL",
    description: "",
    can_have_team: false,
    is_required: false,
    sort_order: 0,
    is_active: true,
  });

  // 加载角色类型列表
  const loadRoleTypes = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }
      if (filterCategory !== "all") {
        params.category = filterCategory;
      }
      if (filterActive !== "all") {
        params.is_active = filterActive === "active";
      }

      const response = await projectRoleApi.types.list(params);
      const data = response.data;
      setRoleTypes(data.items || data || []);
    } catch (error) {
      console.error("加载角色类型列表失败:", error);
      // Mock data for demo
      setRoleTypes([
        {
          id: 1,
          role_code: "PM",
          role_name: "项目经理",
          role_category: "MANAGEMENT",
          description: "负责项目整体规划、进度管控、资源协调和客户沟通",
          can_have_team: true,
          is_required: true,
          sort_order: 1,
          is_active: true,
        },
        {
          id: 2,
          role_code: "TECH_LEAD",
          role_name: "技术负责人",
          role_category: "TECHNICAL",
          description: "负责项目整体技术方案设计和技术决策",
          can_have_team: true,
          is_required: false,
          sort_order: 2,
          is_active: true,
        },
        {
          id: 3,
          role_code: "ME_LEAD",
          role_name: "机械负责人",
          role_category: "TECHNICAL",
          description: "负责机械设计、装配工艺和机械部件选型",
          can_have_team: true,
          is_required: false,
          sort_order: 3,
          is_active: true,
        },
        {
          id: 4,
          role_code: "EE_LEAD",
          role_name: "电气负责人",
          role_category: "TECHNICAL",
          description: "负责电气设计、PLC编程和电气元器件选型",
          can_have_team: true,
          is_required: false,
          sort_order: 4,
          is_active: true,
        },
        {
          id: 5,
          role_code: "SW_LEAD",
          role_name: "软件负责人",
          role_category: "TECHNICAL",
          description: "负责上位机软件、视觉算法和系统集成",
          can_have_team: false,
          is_required: false,
          sort_order: 5,
          is_active: true,
        },
        {
          id: 6,
          role_code: "PROC_LEAD",
          role_name: "采购负责人",
          role_category: "SUPPORT",
          description: "负责物料采购、供应商管理和交期跟踪",
          can_have_team: false,
          is_required: false,
          sort_order: 6,
          is_active: true,
        },
        {
          id: 7,
          role_code: "CS_LEAD",
          role_name: "客服负责人",
          role_category: "SUPPORT",
          description: "负责客户沟通、售后服务和问题协调",
          can_have_team: true,
          is_required: false,
          sort_order: 7,
          is_active: true,
        },
        {
          id: 8,
          role_code: "QA_LEAD",
          role_name: "质量负责人",
          role_category: "SUPPORT",
          description: "负责质量检验、过程监控和验收标准",
          can_have_team: false,
          is_required: false,
          sort_order: 8,
          is_active: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [searchKeyword, filterCategory, filterActive]);

  useEffect(() => {
    loadRoleTypes();
  }, [loadRoleTypes]);

  const resetForm = () => {
    setFormData({
      role_code: "",
      role_name: "",
      role_category: "GENERAL",
      description: "",
      can_have_team: false,
      is_required: false,
      sort_order: 0,
      is_active: true,
    });
  };

  const handleCreateClick = () => {
    resetForm();
    setFormData((prev) => ({
      ...prev,
      sort_order: roleTypes.length + 1,
    }));
    setShowCreateDialog(true);
  };

  const handleEditClick = (roleType) => {
    setSelectedRoleType(roleType);
    setFormData({
      role_code: roleType.role_code,
      role_name: roleType.role_name,
      role_category: roleType.role_category,
      description: roleType.description || "",
      can_have_team: roleType.can_have_team,
      is_required: roleType.is_required,
      sort_order: roleType.sort_order,
      is_active: roleType.is_active,
    });
    setShowEditDialog(true);
  };

  const handleDeleteClick = (roleType) => {
    setSelectedRoleType(roleType);
    setShowDeleteDialog(true);
  };

  const handleFormChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleCreate = async () => {
    try {
      await projectRoleApi.types.create(formData);
      setShowCreateDialog(false);
      resetForm();
      loadRoleTypes();
    } catch (error) {
      console.error("创建角色类型失败:", error);
      alert("创建失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdate = async () => {
    try {
      await projectRoleApi.types.update(selectedRoleType.id, formData);
      setShowEditDialog(false);
      setSelectedRoleType(null);
      resetForm();
      loadRoleTypes();
    } catch (error) {
      console.error("更新角色类型失败:", error);
      alert("更新失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async () => {
    try {
      await projectRoleApi.types.delete(selectedRoleType.id);
      setShowDeleteDialog(false);
      setSelectedRoleType(null);
      loadRoleTypes();
    } catch (error) {
      console.error("删除角色类型失败:", error);
      alert("删除失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleToggleActive = async (roleType) => {
    try {
      await projectRoleApi.types.update(roleType.id, {
        is_active: !roleType.is_active,
      });
      loadRoleTypes();
    } catch (error) {
      console.error("切换状态失败:", error);
      // Update locally for demo
      setRoleTypes((prev) =>
        prev.map((rt) =>
          rt.id === roleType.id ? { ...rt, is_active: !rt.is_active } : rt,
        ),
      );
    }
  };

  const getRoleIcon = (roleCode) => {
    const IconComponent = ROLE_ICONS[roleCode] || Shield;
    return <IconComponent className="h-5 w-5" />;
  };

  const filteredRoleTypes = roleTypes
    .filter((rt) => {
      if (
        searchKeyword &&
        !rt.role_name.includes(searchKeyword) &&
        !rt.role_code.includes(searchKeyword.toUpperCase())
      ) {
        return false;
      }
      if (filterCategory !== "all" && rt.role_category !== filterCategory) {
        return false;
      }
      if (filterActive !== "all") {
        const isActive = filterActive === "active";
        if (rt.is_active !== isActive) return false;
      }
      return true;
    })
    .sort((a, b) => a.sort_order - b.sort_order);

  // 统计数据
  const stats = {
    total: roleTypes.length,
    active: roleTypes.filter((rt) => rt.is_active).length,
    required: roleTypes.filter((rt) => rt.is_required).length,
    withTeam: roleTypes.filter((rt) => rt.can_have_team).length,
  };

  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader
        title="项目角色类型管理"
        subtitle="配置项目中可用的角色类型，如项目经理、技术负责人、采购负责人等"
        icon={Shield}
        actions={
          <Button onClick={handleCreateClick}>
            <Plus className="h-4 w-4 mr-2" />
            新增角色类型
          </Button>
        }
      />

      <div className="p-6 space-y-6">
        {/* 统计卡片 */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-4 gap-4"
        >
          {[
            {
              label: "角色总数",
              value: stats.total,
              icon: Shield,
              color: "text-violet-400",
            },
            {
              label: "已启用",
              value: stats.active,
              icon: CheckCircle,
              color: "text-emerald-400",
            },
            {
              label: "必需角色",
              value: stats.required,
              icon: ClipboardList,
              color: "text-amber-400",
            },
            {
              label: "可带团队",
              value: stats.withTeam,
              icon: Users,
              color: "text-blue-400",
            },
          ].map((stat, index) => (
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
                    <div
                      className={cn("p-3 rounded-xl bg-white/5", stat.color)}
                    >
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
                  placeholder="搜索角色名称或编码..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  className="pl-10 bg-white/5 border-white/10"
                />
              </div>
              <Select value={filterCategory} onValueChange={setFilterCategory}>
                <SelectTrigger className="w-[150px] bg-white/5 border-white/10">
                  <SelectValue placeholder="角色分类" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部分类</SelectItem>
                  <SelectItem value="MANAGEMENT">管理类</SelectItem>
                  <SelectItem value="TECHNICAL">技术类</SelectItem>
                  <SelectItem value="SUPPORT">支持类</SelectItem>
                  <SelectItem value="GENERAL">通用类</SelectItem>
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

        {/* 角色类型列表 */}
        <Card className="bg-surface-100 border-white/5">
          <CardHeader className="border-b border-white/5">
            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
              <Shield className="h-5 w-5 text-violet-400" />
              角色类型列表
              <Badge variant="secondary" className="ml-2">
                {filteredRoleTypes.length} 项
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-white/5 hover:bg-transparent">
                    <TableHead className="text-slate-400 w-[60px]">
                      排序
                    </TableHead>
                    <TableHead className="text-slate-400">角色编码</TableHead>
                    <TableHead className="text-slate-400">角色名称</TableHead>
                    <TableHead className="text-slate-400">分类</TableHead>
                    <TableHead className="text-slate-400">描述</TableHead>
                    <TableHead className="text-slate-400 text-center">
                      可带团队
                    </TableHead>
                    <TableHead className="text-slate-400 text-center">
                      必需
                    </TableHead>
                    <TableHead className="text-slate-400 text-center">
                      状态
                    </TableHead>
                    <TableHead className="text-slate-400 text-right">
                      操作
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <AnimatePresence>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={9} className="text-center py-10">
                          <div className="flex items-center justify-center gap-2 text-slate-400">
                            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-violet-500" />
                            加载中...
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : filteredRoleTypes.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={9}
                          className="text-center py-10 text-slate-400"
                        >
                          暂无数据
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredRoleTypes.map((roleType, index) => (
                        <motion.tr
                          key={roleType.id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ delay: index * 0.03 }}
                          className="border-white/5 hover:bg-white/[0.02]"
                        >
                          <TableCell className="text-slate-400">
                            <div className="flex items-center gap-1">
                              <GripVertical className="h-4 w-4 text-slate-600 cursor-grab" />
                              {roleType.sort_order}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className="p-2 rounded-lg bg-white/5 text-violet-400">
                                {getRoleIcon(roleType.role_code)}
                              </div>
                              <code className="text-sm font-mono text-slate-300 bg-white/5 px-2 py-0.5 rounded">
                                {roleType.role_code}
                              </code>
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="text-white font-medium">
                              {roleType.role_name}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={cn(
                                "border",
                                ROLE_CATEGORIES[roleType.role_category]
                                  ?.color || ROLE_CATEGORIES.GENERAL.color,
                              )}
                            >
                              {ROLE_CATEGORIES[roleType.role_category]?.label ||
                                "通用类"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span className="text-slate-400 text-sm line-clamp-1 max-w-[200px]">
                              {roleType.description || "-"}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            {roleType.can_have_team ? (
                              <div className="flex items-center justify-center">
                                <Users className="h-4 w-4 text-blue-400" />
                              </div>
                            ) : (
                              <span className="text-slate-600">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            {roleType.is_required ? (
                              <div className="flex items-center justify-center">
                                <CheckCircle className="h-4 w-4 text-amber-400" />
                              </div>
                            ) : (
                              <span className="text-slate-600">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            <Switch
                              checked={roleType.is_active}
                              onCheckedChange={() =>
                                handleToggleActive(roleType)
                              }
                              className="data-[state=checked]:bg-emerald-500"
                            />
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-1">
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleEditClick(roleType)}
                              >
                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleDeleteClick(roleType)}
                                className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
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
              新增角色类型
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>角色编码 *</Label>
                <Input
                  placeholder="如 PM、TECH_LEAD"
                  value={formData.role_code}
                  onChange={(e) =>
                    handleFormChange("role_code", e.target.value.toUpperCase())
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
              <div className="space-y-2">
                <Label>角色名称 *</Label>
                <Input
                  placeholder="如 项目经理"
                  value={formData.role_name}
                  onChange={(e) =>
                    handleFormChange("role_name", e.target.value)
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>角色分类</Label>
                <Select
                  value={formData.role_category}
                  onValueChange={(v) => handleFormChange("role_category", v)}
                >
                  <SelectTrigger className="bg-white/5 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MANAGEMENT">管理类</SelectItem>
                    <SelectItem value="TECHNICAL">技术类</SelectItem>
                    <SelectItem value="SUPPORT">支持类</SelectItem>
                    <SelectItem value="GENERAL">通用类</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>排序顺序</Label>
                <Input
                  type="number"
                  value={formData.sort_order}
                  onChange={(e) =>
                    handleFormChange(
                      "sort_order",
                      parseInt(e.target.value) || 0,
                    )
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>角色描述</Label>
              <Textarea
                placeholder="描述该角色的职责..."
                value={formData.description}
                onChange={(e) =>
                  handleFormChange("description", e.target.value)
                }
                className="bg-white/5 border-white/10 min-h-[80px]"
              />
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  id="can_have_team"
                  checked={formData.can_have_team}
                  onCheckedChange={(v) => handleFormChange("can_have_team", v)}
                />
                <Label htmlFor="can_have_team" className="cursor-pointer">
                  可带团队
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  id="is_required"
                  checked={formData.is_required}
                  onCheckedChange={(v) => handleFormChange("is_required", v)}
                />
                <Label htmlFor="is_required" className="cursor-pointer">
                  必需角色
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  id="is_active"
                  checked={formData.is_active}
                  onCheckedChange={(v) => handleFormChange("is_active", v)}
                />
                <Label htmlFor="is_active" className="cursor-pointer">
                  启用
                </Label>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setShowCreateDialog(false)}
            >
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
              编辑角色类型
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>角色编码 *</Label>
                <Input
                  placeholder="如 PM、TECH_LEAD"
                  value={formData.role_code}
                  onChange={(e) =>
                    handleFormChange("role_code", e.target.value.toUpperCase())
                  }
                  className="bg-white/5 border-white/10"
                  disabled
                />
              </div>
              <div className="space-y-2">
                <Label>角色名称 *</Label>
                <Input
                  placeholder="如 项目经理"
                  value={formData.role_name}
                  onChange={(e) =>
                    handleFormChange("role_name", e.target.value)
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>角色分类</Label>
                <Select
                  value={formData.role_category}
                  onValueChange={(v) => handleFormChange("role_category", v)}
                >
                  <SelectTrigger className="bg-white/5 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MANAGEMENT">管理类</SelectItem>
                    <SelectItem value="TECHNICAL">技术类</SelectItem>
                    <SelectItem value="SUPPORT">支持类</SelectItem>
                    <SelectItem value="GENERAL">通用类</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>排序顺序</Label>
                <Input
                  type="number"
                  value={formData.sort_order}
                  onChange={(e) =>
                    handleFormChange(
                      "sort_order",
                      parseInt(e.target.value) || 0,
                    )
                  }
                  className="bg-white/5 border-white/10"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>角色描述</Label>
              <Textarea
                placeholder="描述该角色的职责..."
                value={formData.description}
                onChange={(e) =>
                  handleFormChange("description", e.target.value)
                }
                className="bg-white/5 border-white/10 min-h-[80px]"
              />
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Switch
                  id="edit_can_have_team"
                  checked={formData.can_have_team}
                  onCheckedChange={(v) => handleFormChange("can_have_team", v)}
                />
                <Label htmlFor="edit_can_have_team" className="cursor-pointer">
                  可带团队
                </Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch
                  id="edit_is_required"
                  checked={formData.is_required}
                  onCheckedChange={(v) => handleFormChange("is_required", v)}
                />
                <Label htmlFor="edit_is_required" className="cursor-pointer">
                  必需角色
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
            <Button
              variant="secondary"
              onClick={() => setShowEditDialog(false)}
            >
              取消
            </Button>
            <Button onClick={handleUpdate}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-400">
              <Trash2 className="h-5 w-5" />
              确认删除
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            <p className="text-slate-300">
              确定要删除角色类型{" "}
              <span className="text-white font-medium">
                {selectedRoleType?.role_name}
              </span>{" "}
              吗？
            </p>
            <p className="text-sm text-slate-500 mt-2">
              此操作不可撤销，已分配此角色的项目成员将受到影响。
            </p>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="secondary"
              onClick={() => setShowDeleteDialog(false)}
            >
              取消
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
