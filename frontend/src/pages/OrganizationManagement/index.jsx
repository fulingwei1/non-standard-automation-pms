import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  Building2,
  FolderTree,
  List,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import DeleteConfirmDialog from "../../components/common/DeleteConfirmDialog";
import { staggerContainer, fadeIn } from "../../lib/animations";
import { organizationApi } from "../../services/api";

import { UNIT_TYPES } from "./unitTypeConfig";
import OrgTreeNode from "./OrgTreeNode";
import OrgListTable from "./OrgListTable";
import StatsCards from "./StatsCards";
import CreateDialog from "./CreateDialog";
import EditDialog from "./EditDialog";
import DetailDialog from "./DetailDialog";

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
        const { orgApi } = await import("../../services/api");
        const fallbackResponse = await orgApi.departmentTree({ is_active: true });
        // 使用统一响应格式处理
        const fallbackData = fallbackResponse.formatted || fallbackResponse.data;
        const fallbackItems = fallbackData?.items || fallbackData || [];
        // 转换旧数据格式
        const convertedData = (fallbackItems || []).map(dept => ({
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
    total: orgList.length || (orgTree || []).reduce((acc, node) => {
      const countNodes = (n) => 1 + (n.children?.reduce((a, c) => a + countNodes(c), 0) || 0);
      return acc + countNodes(node);
    }, 0),
    byType: UNIT_TYPES.reduce((acc, type) => {
      acc[type.value] = (orgList || []).filter(u => u.unit_type === type.value).length;
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
      <StatsCards stats={stats} />

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
                    value={searchKeyword || "unknown"}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    className="max-w-sm"
                  />
                  <Select value={filterType || "unknown"} onValueChange={setFilterType}>
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
                  (orgTree || []).map((unit) => (
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
              <OrgListTable
                orgList={orgList}
                onView={handleView}
                onEdit={handleEdit}
                onDelete={handleDeleteConfirm}
              />
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* 创建对话框 */}
      <CreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        parentUnit={parentUnit}
        formData={formData}
        setFormData={setFormData}
        onFormChange={handleFormChange}
        onSubmit={handleCreateSubmit}
        onCancel={() => setShowCreateDialog(false)}
        resetForm={resetForm}
      />

      {/* 编辑对话框 */}
      <EditDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        formData={formData}
        setFormData={setFormData}
        onFormChange={handleFormChange}
        onSubmit={handleEditSubmit}
        onCancel={() => setShowEditDialog(false)}
      />

      {/* 详情对话框 */}
      <DetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedUnit={selectedUnit}
      />

      {/* 删除确认对话框 */}
      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="确认删除"
        description={`确定要删除组织"${selectedUnit?.unit_name}"吗？此操作不可恢复。`}
        confirmText="删除"
        onConfirm={handleDelete}
      />
    </motion.div>
  );
}
