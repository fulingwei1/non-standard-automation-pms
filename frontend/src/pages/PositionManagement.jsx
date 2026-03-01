import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  Search,
  Edit3,
  Trash2,
  Eye,
  Briefcase,
  Shield,
  Link2,
  Users,
  Building2,
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
import DeleteConfirmDialog from "../components/common/DeleteConfirmDialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { organizationApi, roleApi } from "../services/api";

// 岗位类别配置
const POSITION_CATEGORIES = [
  { value: "MANAGEMENT", label: "管理类", color: "text-purple-600 bg-purple-50" },
  { value: "TECHNICAL", label: "技术类", color: "text-blue-600 bg-blue-50" },
  { value: "SALES", label: "销售类", color: "text-green-600 bg-green-50" },
  { value: "FINANCE", label: "财务类", color: "text-yellow-600 bg-yellow-50" },
  { value: "PRODUCTION", label: "生产类", color: "text-orange-600 bg-orange-50" },
  { value: "SUPPORT", label: "支持类", color: "text-gray-600 bg-gray-50" },
];

// 获取类别配置
const getCategoryConfig = (category) => {
  return POSITION_CATEGORIES.find((c) => c.value === category) || POSITION_CATEGORIES[5];
};

export default function PositionManagement() {
  const [positions, setPositions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [orgUnits, setOrgUnits] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");

  // 对话框状态
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showRoleDialog, setShowRoleDialog] = useState(false);

  const [selectedPosition, setSelectedPosition] = useState(null);
  const [selectedRoleIds, setSelectedRoleIds] = useState([]);

  // 分页
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);

  // 表单数据
  const [formData, setFormData] = useState({
    position_code: "",
    position_name: "",
    position_category: "TECHNICAL",
    org_unit_id: null,
    description: "",
    sort_order: 0,
    is_active: true,
  });

  // 加载岗位列表
  const loadPositions = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page, page_size: pageSize };
      if (searchKeyword) {params.keyword = searchKeyword;}
      if (filterCategory !== "all") {params.category = filterCategory;}

      const response = await organizationApi.listPositions(params);
      const data = response.data;
      const posItems = data?.items || data;
      setPositions(Array.isArray(posItems) ? posItems : []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error("加载岗位列表失败:", error);
      // 使用模拟数据作为降级
      setPositions([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchKeyword, filterCategory]);

  // 加载角色列表
  const loadRoles = useCallback(async () => {
    try {
      const response = await roleApi.list({ page: 1, page_size: 100 });
      // 使用统一响应格式处理
      const listData = response.formatted || response.data;
      const roleItems = listData?.items || listData;
      setRoles(Array.isArray(roleItems) ? roleItems : []);
    } catch (error) {
      console.error("加载角色列表失败:", error);
    }
  }, []);

  // 加载组织单元列表
  const loadOrgUnits = useCallback(async () => {
    try {
      const response = await organizationApi.listOrgUnits({ limit: 100 });
      // 使用统一响应格式处理
      const listData = response.formatted || response.data;
      const orgItems = listData?.items || listData;
      setOrgUnits(Array.isArray(orgItems) ? orgItems : []);
    } catch (error) {
      console.error("加载组织单元失败:", error);
    }
  }, []);

  useEffect(() => {
    loadPositions();
    loadRoles();
    loadOrgUnits();
  }, [loadPositions, loadRoles, loadOrgUnits]);

  // 重置表单
  const resetForm = () => {
    setFormData({
      position_code: "",
      position_name: "",
      position_category: "TECHNICAL",
      org_unit_id: null,
      description: "",
      sort_order: 0,
      is_active: true,
    });
  };

  // 处理表单变更
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // 打开创建对话框
  const handleOpenCreate = () => {
    resetForm();
    setShowCreateDialog(true);
  };

  // 打开编辑对话框
  const handleEdit = (position) => {
    setSelectedPosition(position);
    setFormData({
      position_code: position.position_code || "",
      position_name: position.position_name || "",
      position_category: position.position_category || "TECHNICAL",
      org_unit_id: position.org_unit_id,
      description: position.description || "",
      sort_order: position.sort_order || 0,
      is_active: position.is_active !== false,
    });
    setShowEditDialog(true);
  };

  // 打开详情对话框
  const handleView = (position) => {
    setSelectedPosition(position);
    setShowDetailDialog(true);
  };

  // 打开删除确认对话框
  const handleDeleteConfirm = (position) => {
    setSelectedPosition(position);
    setShowDeleteDialog(true);
  };

  // 打开角色映射对话框
  const handleOpenRoleMapping = async (position) => {
    setSelectedPosition(position);
    try {
      const response = await organizationApi.getPositionRoles(position.id);
      setSelectedRoleIds(response.data?.role_ids || response.data?.items || response.data || []);
    } catch (error) {
      console.error("获取岗位角色失败:", error);
      setSelectedRoleIds([]);
    }
    setShowRoleDialog(true);
  };

  // 创建岗位
  const handleCreateSubmit = async () => {
    try {
      await organizationApi.createPosition(formData);
      setShowCreateDialog(false);
      resetForm();
      loadPositions();
    } catch (error) {
      alert("创建岗位失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 更新岗位
  const handleEditSubmit = async () => {
    try {
      await organizationApi.updatePosition(selectedPosition.id, formData);
      setShowEditDialog(false);
      setSelectedPosition(null);
      loadPositions();
    } catch (error) {
      alert("更新岗位失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 删除岗位
  const handleDelete = async () => {
    try {
      await organizationApi.deletePosition(selectedPosition.id);
      setShowDeleteDialog(false);
      setSelectedPosition(null);
      loadPositions();
    } catch (error) {
      alert("删除岗位失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 保存角色映射
  const handleSaveRoles = async () => {
    try {
      await organizationApi.setPositionRoles(selectedPosition.id, selectedRoleIds);
      setShowRoleDialog(false);
      loadPositions();
      alert("角色映射保存成功！");
    } catch (error) {
      alert("保存角色映射失败: " + (error.response?.data?.detail || error.message));
    }
  };

  // 切换角色选择
  const toggleRole = (roleId) => {
    setSelectedRoleIds((prev) => {
      if (prev.includes(roleId)) {
        return (prev || []).filter((id) => id !== roleId);
      } else {
        return [...prev, roleId];
      }
    });
  };

  // 统计信息
  const stats = POSITION_CATEGORIES.reduce((acc, cat) => {
    acc[cat.value] = (positions || []).filter((p) => p.position_category === cat.value).length;
    return acc;
  }, {});

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="岗位管理"
        description="管理公司岗位体系，配置岗位与角色的映射关系"
        actions={
          <Button onClick={handleOpenCreate}>
            <Plus className="mr-2 h-4 w-4" /> 新增岗位
          </Button>
        }
      />

      {/* 统计卡片 */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-6 gap-4">
        {POSITION_CATEGORIES.map((cat) => (
          <Card key={cat.value}>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2">
                <Briefcase className={cn("h-5 w-5", cat.color.split(" ")[0])} />
                <div>
                  <div className="text-2xl font-bold">{stats[cat.value] || 0}</div>
                  <p className="text-xs text-muted-foreground">{cat.label}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* 主内容区 */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>岗位列表</CardTitle>
            <div className="flex items-center space-x-2">
              <Input
                placeholder="搜索岗位名称/编码..."
                value={searchKeyword || "unknown"}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="max-w-sm"
              />
              <Select value={filterCategory || "unknown"} onValueChange={setFilterCategory}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="筛选类别" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">所有类别</SelectItem>
                  {POSITION_CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="p-8 text-center text-muted-foreground">加载中...</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-border">
                    <thead>
                      <tr className="bg-muted/50">
                        <th className="px-4 py-2 text-left text-sm font-semibold">岗位编码</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold">岗位名称</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold">类别</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold">所属组织</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold">默认角色</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold">状态</th>
                        <th className="px-4 py-2 text-left text-sm font-semibold">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {(positions || []).map((position) => {
                        const catConfig = getCategoryConfig(position.position_category);
                        return (
                          <tr key={position.id}>
                            <td className="px-4 py-2 text-sm font-mono">{position.position_code}</td>
                            <td className="px-4 py-2 text-sm font-medium">{position.position_name}</td>
                            <td className="px-4 py-2 text-sm">
                              <Badge variant="outline" className={catConfig.color}>
                                {catConfig.label}
                              </Badge>
                            </td>
                            <td className="px-4 py-2 text-sm text-muted-foreground">
                              {position.org_unit_name || "-"}
                            </td>
                            <td className="px-4 py-2 text-sm">
                              <div className="flex flex-wrap gap-1">
                                {position.roles?.length > 0 ? (
                                  position.roles.slice(0, 3).map((role, idx) => (
                                    <Badge key={idx} variant="secondary" className="text-xs">
                                      {role.role_name || role}
                                    </Badge>
                                  ))
                                ) : (
                                  <span className="text-muted-foreground">未配置</span>
                                )}
                                {position.roles?.length > 3 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{position.roles?.length - 3}
                                  </Badge>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-2 text-sm">
                              <Badge variant={position.is_active ? "default" : "secondary"}>
                                {position.is_active ? "启用" : "禁用"}
                              </Badge>
                            </td>
                            <td className="px-4 py-2 text-sm">
                              <div className="flex items-center space-x-1">
                                <Button variant="ghost" size="sm" onClick={() => handleView(position)}>
                                  <Eye className="h-4 w-4" />
                                </Button>
                                <Button variant="ghost" size="sm" onClick={() => handleEdit(position)}>
                                  <Edit3 className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleOpenRoleMapping(position)}
                                  title="配置角色映射"
                                  className="text-blue-600 hover:text-blue-700"
                                >
                                  <Link2 className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-destructive"
                                  onClick={() => handleDeleteConfirm(position)}
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
                </div>
                {positions.length === 0 && (
                  <div className="p-8 text-center text-muted-foreground">
                    <Briefcase className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                    <p>暂无岗位数据</p>
                    <p className="text-sm mt-2">点击"新增岗位"开始创建岗位</p>
                  </div>
                )}
                {total > pageSize && (
                  <div className="mt-4 flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        上一页
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.min(Math.ceil(total / pageSize), p + 1))}
                        disabled={page >= Math.ceil(total / pageSize)}
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* 创建对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={(open) => { setShowCreateDialog(open); if (!open) {resetForm();} }}>
        <DialogContent className="sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle>新增岗位</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">岗位编码 *</Label>
              <div className="col-span-3 space-y-1">
                <Input
                  name="position_code"
                  value={formData.position_code}
                  onChange={handleFormChange}
                  placeholder="如：PM_SENIOR, ENGINEER_L3"
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground">建议使用大写字母和下划线</p>
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">岗位名称 *</Label>
              <Input
                name="position_name"
                value={formData.position_name}
                onChange={handleFormChange}
                className="col-span-3"
                placeholder="如：高级项目经理"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">岗位类别 *</Label>
              <Select
                value={formData.position_category}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, position_category: value }))}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {POSITION_CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">所属组织</Label>
              <Select
                value={formData.org_unit_id?.toString() || "none"}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, org_unit_id: value === "none" ? null : parseInt(value) }))}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="选择所属组织（可选）" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">不限制组织</SelectItem>
                  {(orgUnits || []).map((org) => (
                    <SelectItem key={org.id} value={org.id.toString()}>
                      {org.unit_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">描述</Label>
              <Textarea
                name="description"
                value={formData.description}
                onChange={handleFormChange}
                className="col-span-3"
                rows={2}
                placeholder="岗位职责描述..."
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
            <DialogTitle>编辑岗位</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">岗位编码</Label>
              <Input value={formData.position_code} className="col-span-3 font-mono" disabled />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">岗位名称 *</Label>
              <Input
                name="position_name"
                value={formData.position_name}
                onChange={handleFormChange}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">岗位类别</Label>
              <Select
                value={formData.position_category}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, position_category: value }))}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {POSITION_CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right">所属组织</Label>
              <Select
                value={formData.org_unit_id?.toString() || "none"}
                onValueChange={(value) => setFormData((prev) => ({ ...prev, org_unit_id: value === "none" ? null : parseInt(value) }))}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="选择所属组织" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">不限制组织</SelectItem>
                  {(orgUnits || []).map((org) => (
                    <SelectItem key={org.id} value={org.id.toString()}>
                      {org.unit_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
            <DialogTitle>岗位详情</DialogTitle>
          </DialogHeader>
          {selectedPosition && (
            <div className="grid gap-4 py-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">岗位编码</Label>
                  <p className="font-medium font-mono">{selectedPosition.position_code}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">岗位名称</Label>
                  <p className="font-medium">{selectedPosition.position_name}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">岗位类别</Label>
                  <p className="font-medium">
                    <Badge variant="outline" className={getCategoryConfig(selectedPosition.position_category).color}>
                      {getCategoryConfig(selectedPosition.position_category).label}
                    </Badge>
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">状态</Label>
                  <p className="font-medium">
                    <Badge variant={selectedPosition.is_active ? "default" : "secondary"}>
                      {selectedPosition.is_active ? "启用" : "禁用"}
                    </Badge>
                  </p>
                </div>
                <div>
                  <Label className="text-muted-foreground">所属组织</Label>
                  <p className="font-medium">{selectedPosition.org_unit_name || "不限制"}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">排序号</Label>
                  <p className="font-medium">{selectedPosition.sort_order || 0}</p>
                </div>
                {selectedPosition.description && (
                  <div className="col-span-2">
                    <Label className="text-muted-foreground">描述</Label>
                    <p className="font-medium">{selectedPosition.description}</p>
                  </div>
                )}
                <div className="col-span-2">
                  <Label className="text-muted-foreground">默认角色</Label>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedPosition.roles?.length > 0 ? (
                      (selectedPosition.roles || []).map((role, idx) => (
                        <Badge key={idx} variant="secondary">
                          <Shield className="h-3 w-3 mr-1" />
                          {role.role_name || role}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-muted-foreground">未配置默认角色</span>
                    )}
                  </div>
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
      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="确认删除"
        description={`确定要删除岗位"${selectedPosition?.position_name}"吗？此操作不可恢复。`}
        confirmText="删除"
        onConfirm={handleDelete}
      />

      {/* 角色映射对话框 */}
      <Dialog open={showRoleDialog} onOpenChange={setShowRoleDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>配置默认角色 - {selectedPosition?.position_name}</DialogTitle>
            <DialogDescription>
              选择该岗位的默认角色，员工分配到此岗位时将自动获得这些角色的权限
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto py-4">
            <div className="space-y-2">
              {(roles || []).map((role) => (
                <label
                  key={role.id}
                  className={cn(
                    "flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors",
                    selectedRoleIds.includes(role.id)
                      ? "bg-primary/10 border-primary"
                      : "hover:bg-muted"
                  )}
                >
                  <input
                    type="checkbox"
                    checked={selectedRoleIds.includes(role.id)}
                    onChange={() => toggleRole(role.id)}
                    className="rounded"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{role.role_name}</span>
                      <Badge variant="outline" className="text-xs font-mono">
                        {role.role_code}
                      </Badge>
                      {role.role_type === "SYSTEM" && (
                        <Badge variant="destructive" className="text-xs">
                          <Shield className="h-3 w-3 mr-1" /> 系统
                        </Badge>
                      )}
                    </div>
                    {role.description && (
                      <p className="text-sm text-muted-foreground mt-1">{role.description}</p>
                    )}
                  </div>
                </label>
              ))}
            </div>
          </div>
          <DialogFooter className="border-t pt-4">
            <div className="flex-1 text-sm text-muted-foreground">
              已选择 {selectedRoleIds.length} 个角色
            </div>
            <Button variant="outline" onClick={() => setShowRoleDialog(false)}>取消</Button>
            <Button onClick={handleSaveRoles}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
