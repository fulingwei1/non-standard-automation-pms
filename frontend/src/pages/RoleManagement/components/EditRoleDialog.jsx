/**
 * 编辑角色对话框组件
 * 包含基本信息编辑和权限管理两个 Tab
 */

import { DATA_SCOPE_MAP } from '../constants';

export default function EditRoleDialog({
  open,
  onOpenChange,
  editForm,
  onFieldChange,
  onSubmit,
  roles,
  // 权限相关
  activeEditTab,
  setActiveEditTab,
  selectedPermissionIds,
  inheritedPermissionIds,
  permissionSearch,
  setPermissionSearch,
  permissionModuleFilter,
  setPermissionModuleFilter,
  allPermissions,
  getFilteredPermissions,
  getAllModules,
  handleTogglePermission,
  handleToggleAllPermissions,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-6xl w-[95vw] h-[90vh] bg-slate-900 border-slate-700 text-white p-0 overflow-hidden flex flex-col">
        <DialogHeader className="px-6 py-4 border-b border-slate-700 shrink-0">
          <DialogTitle>编辑角色 - {editForm.role_name}</DialogTitle>
        </DialogHeader>
        <DialogBody className="flex-1 overflow-y-auto px-6">
          <Tabs value={activeEditTab || "unknown"} onValueChange={setActiveEditTab} className="w-full h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-2 shrink-0">
              <TabsTrigger value="basic">基本信息</TabsTrigger>
              <TabsTrigger value="permissions">
                权限管理
                <Badge variant="secondary" className="ml-2">
                  {selectedPermissionIds.length}
                </Badge>
              </TabsTrigger>
            </TabsList>

            {/* 基本信息 Tab */}
            <TabsContent value="basic" className="mt-6 space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">角色编码</label>
                <Input value={editForm.role_code} disabled className="bg-slate-800 border-slate-700" />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">角色名称</label>
                <Input
                  value={editForm.role_name}
                  onChange={(e) => onFieldChange('role_name', e.target.value)}
                  className="bg-slate-800 border-slate-700"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">继承自</label>
                <Select
                  value={editForm.parent_id?.toString() || ''}
                  onValueChange={(v) => onFieldChange('parent_id', v ? parseInt(v) : null)}
                >
                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue placeholder="选择父角色（可选）" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">无（顶级角色）</SelectItem>
                    {roles
                      .filter(r => r.is_active && r.id !== editForm.id)
                      .map((role) => (
                        <SelectItem key={role.id} value={role.id.toString()}>
                          {role.role_name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">数据权限范围</label>
                <Select
                  value={editForm.data_scope}
                  onValueChange={(v) => onFieldChange('data_scope', v)}
                >
                  <SelectTrigger className="bg-slate-800 border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(DATA_SCOPE_MAP).map(([key, config]) => (
                      <SelectItem key={key} value={key || "unknown"}>
                        {config.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <Input
                  value={editForm.description}
                  onChange={(e) => onFieldChange('description', e.target.value)}
                  className="bg-slate-800 border-slate-700"
                />
              </div>
            </TabsContent>

            {/* 权限管理 Tab */}
            <TabsContent value="permissions" className="mt-6 flex-1 overflow-hidden flex flex-col">
              <div className="space-y-4 h-full flex flex-col">
                {/* 搜索和筛选 */}
                <div className="flex items-center gap-4 shrink-0">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="搜索权限编码或名称..."
                      value={permissionSearch || "unknown"}
                      onChange={(e) => setPermissionSearch(e.target.value)}
                      className="pl-9 bg-slate-800 border-slate-700"
                    />
                  </div>
                  <Select
                    value={permissionModuleFilter || "unknown"}
                    onValueChange={setPermissionModuleFilter}
                  >
                    <SelectTrigger className="w-40 bg-slate-800 border-slate-700">
                      <SelectValue placeholder="模块" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部模块</SelectItem>
                      {getAllModules().map(module => (
                        <SelectItem key={module} value={module || "unknown"}>
                          {module}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleToggleAllPermissions}
                    className="shrink-0"
                  >
                    {getFilteredPermissions().length > 0 && getFilteredPermissions().every(p => selectedPermissionIds.includes(p.id))
                      ? '取消全选'
                      : '全选'}
                  </Button>
                  <div className="text-sm text-slate-400">
                    已选: {selectedPermissionIds.length} / 总数: {allPermissions.length}
                  </div>
                </div>

                {/* 权限表格 */}
                <div className="flex-1 border border-slate-700 rounded-lg overflow-hidden flex flex-col">
                  {allPermissions.length === 0 ? (
                    <div className="flex-1 flex items-center justify-center text-slate-400">
                      加载权限中...
                    </div>
                  ) : getFilteredPermissions().length === 0 ? (
                    <div className="flex-1 flex items-center justify-center text-slate-400">
                      没有找到匹配的权限
                    </div>
                  ) : (
                    <div className="flex-1 overflow-auto">
                      <Table>
                        <TableHeader className="sticky top-0 bg-slate-800 z-10">
                          <TableRow className="hover:bg-slate-800">
                            <TableHead className="w-12">
                              <input
                                type="checkbox"
                                checked={getFilteredPermissions().length > 0 && getFilteredPermissions().every(p => selectedPermissionIds.includes(p.id))}
                                onChange={handleToggleAllPermissions}
                                className="w-4 h-4"
                              />
                            </TableHead>
                            <TableHead>权限编码</TableHead>
                            <TableHead>权限名称</TableHead>
                            <TableHead>功能描述</TableHead>
                            <TableHead>模块</TableHead>
                            <TableHead className="text-right">操作</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {getFilteredPermissions().map((permission) => {
                            const isInherited = inheritedPermissionIds.includes(permission.id);
                            const isDirectSelected = selectedPermissionIds.includes(permission.id);

                            return (
                              <TableRow
                                key={permission.id}
                                className={
                                  isInherited ? 'bg-purple-500/5 opacity-75' :
                                  isDirectSelected ? 'bg-blue-500/10' : ''
                                }
                              >
                                <TableCell>
                                  {isInherited ? (
                                    <div className="flex items-center justify-center w-6 h-6 text-purple-400" title="继承权限">
                                      <CheckSquare className="w-4 h-4" />
                                    </div>
                                  ) : (
                                    <button
                                      onClick={() => handleTogglePermission(permission.id)}
                                      className="flex items-center justify-center w-6 h-6 rounded border border-slate-600 hover:border-blue-500 transition-colors"
                                    >
                                      {isDirectSelected ? (
                                        <CheckSquare className="w-4 h-4 text-blue-500" />
                                      ) : (
                                        <Square className="w-4 h-4 text-slate-500" />
                                      )}
                                    </button>
                                  )}
                                </TableCell>
                                <TableCell className="font-mono text-sm">
                                  {permission.perm_code || permission.permission_code}
                                  {isInherited && (
                                    <Badge variant="outline" className="ml-2 text-xs text-purple-400 border-purple-500/30">
                                      继承
                                    </Badge>
                                  )}
                                </TableCell>
                                <TableCell className={isInherited ? 'text-slate-500' : ''}>
                                  {permission.perm_name || permission.permission_name}
                                </TableCell>
                                <TableCell className="text-sm text-slate-400 max-w-xs truncate" title={permission.description}>
                                  {permission.description || '-'}
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline">{permission.module || '-'}</Badge>
                                </TableCell>
                                <TableCell className="text-right">
                                  {isInherited ? (
                                    <span className="text-xs text-slate-500">来自父角色</span>
                                  ) : (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleTogglePermission(permission.id)}
                                      className={isDirectSelected
                                        ? 'text-red-400 hover:text-red-300'
                                        : 'text-blue-400 hover:text-blue-300'}
                                    >
                                      {isDirectSelected ? '移除' : '添加'}
                                    </Button>
                                  )}
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </DialogBody>
        <DialogFooter className="px-6 py-4 border-t border-slate-700 shrink-0">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit} className="bg-blue-600 hover:bg-blue-700">
            保存
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
