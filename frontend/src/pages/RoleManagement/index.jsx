/**
 * 角色管理页面（增强版本）
 *
 * 新增功能：
 * - 角色继承（parent_id）展示
 * - 数据权限范围展示
 * - 权限数量统计（直接 + 继承）
 * - 角色详情含直接/继承权限分离
 * - 角色对比功能
 * - 角色模板快速创建
 */

import { motion } from 'framer-motion';
import { Plus, Search, GitBranch, FileText } from 'lucide-react';
import { PageHeader } from '../../components/layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { fadeIn, staggerContainer } from '../../lib/animations';
import { useRoleManagement } from './hooks';
import {
  RoleTable,
  CreateRoleDialog,
  EditRoleDialog,
  DetailDialog,
  CompareDialog,
  TemplateDialog,
} from './components';

export default function RoleManagement() {
  const mgmt = useRoleManagement();

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="角色管理"
        description="管理系统角色、权限配置和角色继承关系"
      />

      {/* 搜索和操作 */}
      <motion.div variants={fadeIn} className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="搜索角色..."
            value={mgmt.roleData.searchKeyword}
            onChange={(e) => mgmt.roleData.setSearchKeyword(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          {mgmt.selectedForCompare.length >= 2 && (
            <Button variant="outline" onClick={mgmt.handleCompare}>
              <GitBranch className="w-4 h-4 mr-2" />
              对比 ({mgmt.selectedForCompare.length})
            </Button>
          )}
          {mgmt.templates.length > 0 && (
            <Button variant="outline" onClick={() => mgmt.setShowTemplateDialog(true)}>
              <FileText className="w-4 h-4 mr-2" />
              从模板创建
            </Button>
          )}
          <Button onClick={() => mgmt.setShowCreateDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            新建角色
          </Button>
        </div>
      </motion.div>

      {/* 角色列表 */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader>
            <CardTitle>角色列表</CardTitle>
            <CardDescription>
              共 {mgmt.roles.length} 个角色
              {mgmt.selectedForCompare.length > 0 && (
                <span className="ml-2 text-blue-600">
                  | 已选择 {mgmt.selectedForCompare.length} 个角色
                  <button
                    className="ml-2 text-xs underline"
                    onClick={() => mgmt.setSelectedForCompare([])}
                  >
                    清除
                  </button>
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RoleTable
              roles={mgmt.roles}
              loading={mgmt.roleData.loading}
              selectedForCompare={mgmt.selectedForCompare}
              toggleCompareSelection={mgmt.toggleCompareSelection}
              onViewDetail={mgmt.handleViewDetail}
              onEdit={mgmt.handleEdit}
              onDelete={mgmt.handleDelete}
            />
          </CardContent>
        </Card>
      </motion.div>

      {/* 创建角色对话框 */}
      <CreateRoleDialog
        open={mgmt.showCreateDialog}
        onOpenChange={mgmt.setShowCreateDialog}
        createForm={mgmt.createForm}
        onFieldChange={mgmt.handleCreateChange}
        onSubmit={mgmt.handleCreateSubmit}
        roles={mgmt.roles}
      />

      {/* 编辑角色对话框 */}
      <EditRoleDialog
        open={mgmt.showEditDialog}
        onOpenChange={mgmt.setShowEditDialog}
        editForm={mgmt.editForm}
        onFieldChange={mgmt.handleEditChange}
        onSubmit={mgmt.handleEditSubmit}
        roles={mgmt.roles}
        activeEditTab={mgmt.activeEditTab}
        setActiveEditTab={mgmt.setActiveEditTab}
        selectedPermissionIds={mgmt.selectedPermissionIds}
        inheritedPermissionIds={mgmt.inheritedPermissionIds}
        permissionSearch={mgmt.permissionSearch}
        setPermissionSearch={mgmt.setPermissionSearch}
        permissionModuleFilter={mgmt.permissionModuleFilter}
        setPermissionModuleFilter={mgmt.setPermissionModuleFilter}
        allPermissions={mgmt.allPermissions}
        getFilteredPermissions={mgmt.getFilteredPermissions}
        getAllModules={mgmt.getAllModules}
        handleTogglePermission={mgmt.handleTogglePermission}
        handleToggleAllPermissions={mgmt.handleToggleAllPermissions}
      />

      {/* 角色详情对话框 */}
      <DetailDialog
        open={mgmt.showDetailDialog}
        onOpenChange={mgmt.setShowDetailDialog}
        selectedRole={mgmt.selectedRole}
      />

      {/* 角色对比对话框 */}
      <CompareDialog
        open={mgmt.showCompareDialog}
        onOpenChange={mgmt.setShowCompareDialog}
        compareResult={mgmt.compareResult}
        onClose={() => {
          mgmt.setShowCompareDialog(false);
          mgmt.setSelectedForCompare([]);
          mgmt.setCompareResult(null);
        }}
      />

      {/* 从模板创建对话框 */}
      <TemplateDialog
        open={mgmt.showTemplateDialog}
        onOpenChange={mgmt.setShowTemplateDialog}
        templateForm={mgmt.templateForm}
        setTemplateForm={mgmt.setTemplateForm}
        onSubmit={mgmt.handleTemplateCreate}
        templates={mgmt.templates}
      />
    </motion.div>
  );
}
