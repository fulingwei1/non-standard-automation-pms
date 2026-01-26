import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  Search,
  Edit3,
  Trash2,
  Eye,
  Building2,
  Users,
  ChevronRight,
  ChevronDown,
  FolderTree,
  List,
  Network,
  UserCircle,
  MoreHorizontal,
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
  DialogDescription,
} from "../components/ui/dialog";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { organizationApi } from "../services/api";

// 组织单元类型配置
const UNIT_TYPES = [
  { value: "COMPANY", label: "公司", icon: Building2, color: "text-purple-600" },
  { value: "BUSINESS_UNIT", label: "事业部", icon: Network, color: "text-blue-600" },
  { value: "DEPARTMENT", label: "部门", icon: FolderTree, color: "text-green-600" },
  { value: "TEAM", label: "团队", icon: Users, color: "text-orange-600" },
];

// 获取类型配置
const getUnitTypeConfig = (type) => {
  return UNIT_TYPES.find((t) => t.value === type) || UNIT_TYPES[2];
};

// 组织树节点组件
function OrgTreeNode({ unit, level = 0, onEdit, onView, onDelete, onAddChild, allUnits }) {
  const [expanded, setExpanded] = useState(level < 2);
  const typeConfig = getUnitTypeConfig(unit.unit_type);
  const Icon = typeConfig.icon;

  // 获取可添加的子类型
  const getAvailableChildTypes = () => {
    const typeOrder = ["COMPANY", "BUSINESS_UNIT", "DEPARTMENT", "TEAM"];
    const currentIndex = typeOrder.indexOf(unit.unit_type);
    return UNIT_TYPES.filter((t) => typeOrder.indexOf(t.value) > currentIndex);
  };

  const availableChildTypes = getAvailableChildTypes();

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 p-2 rounded hover:bg-muted/50 group",
          level > 0 && "ml-4"
        )}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
      >
        {unit.children && unit.children.length > 0 ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 hover:bg-muted rounded"
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        ) : (
          <div className="w-6" />
        )}
        <Icon className={cn("h-4 w-4", typeConfig.color)} />
        <span className="flex-1 font-medium">{unit.unit_name}</span>
        <Badge variant="outline" className="text-xs font-mono">
          {unit.unit_code}
        </Badge>
        <Badge variant="secondary" className={cn("text-xs", typeConfig.color)}>
          {typeConfig.label}
        </Badge>
        {unit.manager_name && (
          <Badge variant="outline" className="text-xs">
            <UserCircle className="h-3 w-3 mr-1" />
            {unit.manager_name}
          </Badge>
        )}
        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="ghost" size="sm" onClick={() => onView(unit)}>
            <Eye className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onEdit(unit)}>
            <Edit3 className="h-4 w-4" />
          </Button>
          {availableChildTypes.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Plus className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                {availableChildTypes.map((childType) => (
                  <DropdownMenuItem
                    key={childType.value}
                    onClick={() => onAddChild(unit, childType.value)}
                  >
                    <childType.icon className={cn("h-4 w-4 mr-2", childType.color)} />
                    添加{childType.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {!unit.children?.length && (
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
              onClick={() => onDelete(unit)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      {expanded && unit.children && unit.children.length > 0 && (
        <div>
          {unit.children.map((child) => (
            <OrgTreeNode
              key={child.id}
              unit={child}
              level={level + 1}
              onEdit={onEdit}
              onView={onView}
              onDelete={onDelete}
              onAddChild={onAddChild}
              allUnits={allUnits}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function OrganizationManagement() {
  const [orgTree, setOrgTree] = useState([]);
  const [orgList, setOrgList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState("tree"); // 'tree' or 'list'
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("all");

  // 对话框状态
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const [selectedUnit, setSelectedUnit] = useState(null);
  const [parentUnit, setParentUnit] = useState(null);

  // 表单数据
  const [formData, setFormData] = useState({
    unit_code: "",
    unit_name: "",
    unit_type: "DEPARTMENT",
    parent_id: null,
    manager_id: null,
    sort_order: 0,
    description: "",
    is_active: true,
  });

  // 加载组织树
  const loadOrgTree = useCallback(async () => {
    setLoading(true);
    try {
      const response = await organizationApi.getOrgTree({ is_active: true });
      // 使用统一响应格式处理
      const listData = response.formatted || response.data;
      setOrgTree(listData?.items || listData || []);
    } catch (error) {
      console.error("加载组织树失败:", error);
      // 如果新 API 不可用，尝试使用旧的部门树 API
      try {
        const { orgApi } = await import("../services/api");
        const fallbackResponse = await orgApi.departmentTree({ is_active: true });
        // 使用统一响应格式处理
        const fallbackData = fallbackResponse.formatted || fallbackResponse.data;
        const fallbackItems = fallbackData?.items || fallbackData || [];
        // 转换旧数据格式
        const convertedData = fallbackItems.map(dept => ({
          id: dept.id,
          unit_code: dept.dept_code,
          unit_name: dept.dept_name,
          unit_type: "DEPARTMENT",
          parent_id: dept.parent_id,
          manager_name: dept.manager_name,
          children: dept.children?.map(child => ({
            id: child.id,
            unit_code: child.dept_code,
            unit_name: child.dept_name,
            unit_type: "DEPARTMENT",
            parent_id: child.parent_id,
            manager_name: child.manager_name,
            children: child.children,
          })),
        }));
        setOrgTree(convertedData);
      } catch (fallbackError) {
        console.error("降级加载也失败:", fallbackError);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载组织列表
  const loadOrgList = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchKeyword) {params.keyword = searchKeyword;}
      if (filterType !== "all") {params.unit_type = filterType;}

      const response = await organizationApi.listOrgUnits(params);
      // 使用统一响应格式处理
      const listData = response.formatted || response.data;
      setOrgList(listData?.items || listData || []);
    } catch (error) {
      console.error("加载组织列表失败:", error);
    } finally {
      setLoading(false);
    }
  }, [searchKeyword, filterType]);

  useEffect(() => {
    if (viewMode === "tree") {
      loadOrgTree();
    } else {
      loadOrgList();
    }
  }, [viewMode, loadOrgTree, loadOrgList]);

  // 重置表单
  const resetForm = () => {
    setFormData({
      unit_code: "",
      unit_name: "",
      unit_type: "DEPARTMENT",
      parent_id: null,
      manager_id: null,
      sort_order: 0,
      description: "",
      is_active: true,
    });
    setParentUnit(null);
  };

  // 处理表单变更
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // 打开创建对话框
  const handleOpenCreate = (parent = null, unitType = "DEPARTMENT") => {
    resetForm();
    setParentUnit(parent);
    setFormData((prev) => ({
      ...prev,
      unit_type: unitType,
      parent_id: parent?.id || null,
    }));
    setShowCreateDialog(true);
  };

  // 打开编辑对话框
  const handleEdit = (unit) => {
    setSelectedUnit(unit);
    setFormData({
      unit_code: unit.unit_code || "",
      unit_name: unit.unit_name || "",
      unit_type: unit.unit_type || "DEPARTMENT",
      parent_id: unit.parent_id,
      manager_id: unit.manager_id,
      sort_order: unit.sort_order || 0,
      description: unit.description || "",
      is_active: unit.is_active !== false,
    });
    setShowEditDialog(true);
  };

  // 打开详情对话框
  const handleView = (unit) => {
    setSelectedUnit(unit);
    setShowDetailDialog(true);
  };

  // 打开删除确认对话框
  const handleDeleteConfirm = (unit) => {
    setSelectedUnit(unit);
    setShowDeleteDialog(true);
  };

  // 创建组织单元
  const handleCreateSubmit = async () => {
    try {
      await organizationApi.createOrgUnit(formData);
      setShowCreateDialog(false);
      resetForm();
      loadOrgTree();
      loadOrgList();
    } catch (error) {
      alert("创建组织单元失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 更新组织单元
  const handleEditSubmit = async () => {
    try {
      await organizationApi.updateOrgUnit(selectedUnit.id, formData);
      setShowEditDialog(false);
      setSelectedUnit(null);
      loadOrgTree();
      loadOrgList();
    } catch (error) {
      alert("更新组织单元失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 删除组织单元
  const handleDelete = async () => {
    try {
      await organizationApi.deleteOrgUnit(selectedUnit.id);
      setShowDeleteDialog(false);
      setSelectedUnit(null);
      loadOrgTree();
      loadOrgList();
    } catch (error) {
      alert("删除组织单元失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 统计信息
  const stats = {
    total: orgList.length || orgTree.reduce((acc, node) => {
      const countNodes = (n) => 1 + (n.children?.reduce((a, c) => a + countNodes(c), 0) || 0);
      return acc + countNodes(node);
    }, 0),
    byType: UNIT_TYPES.reduce((acc, type) => {
      acc[type.value] = orgList.filter(u => u.unit_type === type.value).length;
      return acc;
    }, {}),
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="组织架构管理"
        description="管理公司、事业部、部门、团队等组织层级结构"
        actions={
          <Button onClick={() => handleOpenCreate(null, "COMPANY")}>
            <Plus className="mr-2 h-4 w-4" /> 新增组织
          </Button>
        }
      />

      {/* 统计卡片 */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">组织单元总数</p>
          </CardContent>
        </Card>
        {UNIT_TYPES.map((type) => {
          const Icon = type.icon;
          return (
            <Card key={type.value}>
              <CardContent className="pt-4">
                <div className="flex items-center gap-2">
                  <Icon className={cn("h-5 w-5", type.color)} />
                  <div>
                    <div className="text-2xl font-bold">{stats.byType[type.value] || 0}</div>
                    <p className="text-xs text-muted-foreground">{type.label}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </motion.div>

      {/* 主内容区 */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>组织架构</CardTitle>
            <div className="flex items-center space-x-2">
              {viewMode === "list" && (
                <>
                  <Input
                    placeholder="搜索组织名称/编码..."
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    className="max-w-sm"
                  />
                  <Select value={filterType} onValueChange={setFilterType}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue placeholder="筛选类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">所有类型</SelectItem>
                      {UNIT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </>
              )}
              <div className="flex rounded-md border">
                <Button
                  variant={viewMode === "tree" ? "secondary" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode("tree")}
                >
                  <FolderTree className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === "list" ? "secondary" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode("list")}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="p-8 text-center text-muted-foreground">加载中...</div>
            ) : viewMode === "tree" ? (
              <div className="space-y-1">
                {orgTree.length > 0 ? (
                  orgTree.map((unit) => (
                    <OrgTreeNode
                      key={unit.id}
                      unit={unit}
                      onEdit={handleEdit}
                      onView={handleView}
                      onDelete={handleDeleteConfirm}
                      onAddChild={handleOpenCreate}
                      allUnits={orgList}
                    />
                  ))
                ) : (
                  <div className="p-8 text-center text-muted-foreground">
                    <Building2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                    <p>暂无组织架构数据</p>
                    <p className="text-sm mt-2">点击"新增组织"开始构建组织架构</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-border">
                  <thead>
                    <tr className="bg-muted/50">
                      <th className="px-4 py-2 text-left text-sm font-semibold">组织编码</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">组织名称</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">类型</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">上级组织</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">负责人</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">状态</th>
                      <th className="px-4 py-2 text-left text-sm font-semibold">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {orgList.map((unit) => {
                      const typeConfig = getUnitTypeConfig(unit.unit_type);
                      const Icon = typeConfig.icon;
                      return (
                        <tr key={unit.id}>
                          <td className="px-4 py-2 text-sm font-mono">{unit.unit_code}</td>
                          <td className="px-4 py-2 text-sm font-medium">{unit.unit_name}</td>
                          <td className="px-4 py-2 text-sm">
                            <Badge variant="outline" className={typeConfig.color}>
                              <Icon className="h-3 w-3 mr-1" />
                              {typeConfig.label}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            {unit.parent_name || "-"}
                          </td>
                          <td className="px-4 py-2 text-sm text-muted-foreground">
                            {unit.manager_name || "-"}
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <Badge variant={unit.is_active ? "default" : "secondary"}>
                              {unit.is_active ? "启用" : "禁用"}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-sm">
                            <div className="flex items-center space-x-1">
                              <Button variant="ghost" size="sm" onClick={() => handleView(unit)}>
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleEdit(unit)}>
                                <Edit3 className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-destructive"
                                onClick={() => handleDeleteConfirm(unit)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {orgList.length === 0 && (
                  <p className="p-4 text-center text-muted-foreground">没有找到符合条件的组织单元</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* 创建对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={(open) => { setShowCreateDialog(open); if (!open) {resetForm();} }}>
        <DialogContent className="sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle>
              {parentUnit ? `在"${parentUnit.unit_name}"下新增组织` : "新增组织"}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">组织类型 *</Label>
              <Select
                value={formData.unit_type}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, unit_type: value }))}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {UNIT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center gap-2">
                        <type.icon className={cn("h-4 w-4", type.color)} />
                        {type.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">组织编码 *</Label>
              <div className="col-span-3 space-y-1">
                <Input
                  name="unit_code"
                  value={formData.unit_code}
                  onChange={handleFormChange}
                  placeholder="如：BU001, DEPT_SALES"
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground">建议使用大写字母和下划线</p>
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">组织名称 *</Label>
              <Input
                name="unit_name"
                value={formData.unit_name}
                onChange={handleFormChange}
                className="col-span-3"
                placeholder="如：销售一部"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">排序号</Label>
              <Input
                name="sort_order"
                type="number"
                value={formData.sort_order}
                onChange={handleFormChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">描述</Label>
              <Textarea
                name="description"
                value={formData.description}
                onChange={handleFormChange}
                className="col-span-3"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>取消</Button>
            <Button onClick={handleCreateSubmit}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑对话框 */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle>编辑组织</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">组织类型</Label>
              <div className="col-span-3">
                <Badge variant="outline" className={getUnitTypeConfig(formData.unit_type).color}>
                  {getUnitTypeConfig(formData.unit_type).label}
                </Badge>
                <p className="text-xs text-muted-foreground mt-1">类型创建后不可修改</p>
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">组织编码</Label>
              <Input
                value={formData.unit_code}
                className="col-span-3 font-mono"
                disabled
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">组织名称 *</Label>
              <Input
                name="unit_name"
                value={formData.unit_name}
                onChange={handleFormChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">排序号</Label>
              <Input
                name="sort_order"
                type="number"
                value={formData.sort_order}
                onChange={handleFormChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">描述</Label>
              <Textarea
                name="description"
                value={formData.description}
                onChange={handleFormChange}
                className="col-span-3"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">状态</Label>
              <Select
                value={formData.is_active ? "active" : "inactive"}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, is_active: value === "active" }))}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">启用</SelectItem>
                  <SelectItem value="inactive">禁用</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditDialog(false)}>取消</Button>
            <Button onClick={handleEditSubmit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>组织详情</DialogTitle>
          </DialogHeader>
          {selectedUnit && (
            <div className="grid gap-4 py-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">组织编码</Label>
                  <p className="font-medium font-mono">{selectedUnit.unit_code}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">组织名称</Label>
                  <p className="font-medium">{selectedUnit.unit_name}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">组织类型</Label>
                  <p className="font-medium">
                    <Badge variant="outline" className={getUnitTypeConfig(selectedUnit.unit_type).color}>
                      {getUnitTypeConfig(selectedUnit.unit_type).label}
                    </Badge>
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">状态</Label>
                  <p className="font-medium">
                    <Badge variant={selectedUnit.is_active ? "default" : "secondary"}>
                      {selectedUnit.is_active ? "启用" : "禁用"}
                    </Badge>
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">上级组织</Label>
                  <p className="font-medium">{selectedUnit.parent_name || "-"}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">负责人</Label>
                  <p className="font-medium">{selectedUnit.manager_name || "-"}</p>
                </div>
                {selectedUnit.description && (
                  <div className="col-span-2">
                    <Label className="text-muted-foreground">描述</Label>
                    <p className="font-medium">{selectedUnit.description}</p>
                  </div>
                )}
                <div>
                  <Label className="text-muted-foreground">层级</Label>
                  <p className="font-medium">{selectedUnit.level || 1}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">路径</Label>
                  <p className="font-medium font-mono text-xs">{selectedUnit.path || "-"}</p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button onClick={() => setShowDetailDialog(false)}>关闭</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除组织"{selectedUnit?.unit_name}"吗？此操作不可恢复。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>取消</Button>
            <Button variant="destructive" onClick={handleDelete}>删除</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
