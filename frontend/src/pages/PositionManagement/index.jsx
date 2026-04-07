import { useState, useEffect, useCallback } from "react";
import { staggerContainer } from "../../lib/animations";
import { organizationApi, roleApi } from "../../services/api";
import { DEFAULT_FORM_DATA } from "./categoryConstants";

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
  const [formData, setFormData] = useState({ ...DEFAULT_FORM_DATA });

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
    setFormData({ ...DEFAULT_FORM_DATA });
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

      <StatsCards positions={positions} />

      <PositionTable
        positions={positions}
        loading={loading}
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterCategory={filterCategory}
        setFilterCategory={setFilterCategory}
        total={total}
        page={page}
        setPage={setPage}
        pageSize={pageSize}
        onView={handleView}
        onEdit={handleEdit}
        onRoleMapping={handleOpenRoleMapping}
        onDelete={handleDeleteConfirm}
      />

      <CreateDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        formData={formData}
        handleFormChange={handleFormChange}
        setFormData={setFormData}
        orgUnits={orgUnits}
        resetForm={resetForm}
        onSubmit={handleCreateSubmit}
      />

      <EditDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        formData={formData}
        handleFormChange={handleFormChange}
        setFormData={setFormData}
        orgUnits={orgUnits}
        onSubmit={handleEditSubmit}
      />

      <DetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        position={selectedPosition}
      />

      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="确认删除"
        description={`确定要删除岗位"${selectedPosition?.position_name}"吗？此操作不可恢复。`}
        confirmText="删除"
        onConfirm={handleDelete}
      />

      <RoleMappingDialog
        open={showRoleDialog}
        onOpenChange={setShowRoleDialog}
        position={selectedPosition}
        roles={roles}
        selectedRoleIds={selectedRoleIds}
        toggleRole={toggleRole}
        onSave={handleSaveRoles}
      />
    </motion.div>
  );
}
