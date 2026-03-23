/**
 * 角色详情对话框组件
 * 展示角色基本信息、直接权限和继承权限
 */

import { DATA_SCOPE_MAP } from '../constants';

// 渲染数据权限标签
function renderDataScopeBadge(scope) {
  const config = DATA_SCOPE_MAP[scope] || DATA_SCOPE_MAP['OWN'];
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  );
}

export default function DetailDialog({ open, onOpenChange, selectedRole }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>角色详情</DialogTitle>
        </DialogHeader>
        <DialogBody>
          {selectedRole && (
            <div className="space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">角色编码</div>
                  <div className="font-mono">{selectedRole.role_code}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">角色名称</div>
                  <div>{selectedRole.role_name}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">继承自</div>
                  <div>
                    {selectedRole.parent_name ? (
                      <span className="text-blue-600">
                        <GitBranch className="w-4 h-4 inline mr-1" />
                        {selectedRole.parent_name}
                      </span>
                    ) : (
                      <span className="text-slate-400">无（顶级角色）</span>
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">数据权限</div>
                  <div>{renderDataScopeBadge(selectedRole.data_scope)}</div>
                </div>
              </div>

              {selectedRole.description && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">描述</div>
                  <div>{selectedRole.description}</div>
                </div>
              )}

              {/* 权限列表 */}
              <Tabs defaultValue="direct" className="w-full">
                <TabsList>
                  <TabsTrigger value="direct">
                    直接权限
                    <Badge variant="secondary" className="ml-2">
                      {selectedRole.direct_permissions?.length || 0}
                    </Badge>
                  </TabsTrigger>
                  <TabsTrigger value="inherited">
                    继承权限
                    <Badge variant="secondary" className="ml-2">
                      {selectedRole.inherited_permissions?.length || 0}
                    </Badge>
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="direct" className="mt-4">
                  {selectedRole.direct_permissions?.length > 0 ? (
                    <div className="max-h-60 overflow-y-auto border rounded">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>权限编码</TableHead>
                            <TableHead>权限名称</TableHead>
                            <TableHead>模块</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {(selectedRole.direct_permissions || []).map((perm) => (
                            <TableRow key={perm.id}>
                              <TableCell className="font-mono text-xs">
                                {perm.permission_code}
                              </TableCell>
                              <TableCell>{perm.permission_name}</TableCell>
                              <TableCell>
                                <Badge variant="outline">{perm.module || '-'}</Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-center py-4 text-slate-400">暂无直接分配的权限</div>
                  )}
                </TabsContent>
                <TabsContent value="inherited" className="mt-4">
                  {selectedRole.inherited_permissions?.length > 0 ? (
                    <div className="max-h-60 overflow-y-auto border rounded">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>权限编码</TableHead>
                            <TableHead>权限名称</TableHead>
                            <TableHead>继承自</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {(selectedRole.inherited_permissions || []).map((perm) => (
                            <TableRow key={perm.id}>
                              <TableCell className="font-mono text-xs">
                                {perm.permission_code}
                              </TableCell>
                              <TableCell>{perm.permission_name}</TableCell>
                              <TableCell>
                                <span className="text-blue-600 text-sm">
                                  {perm.inherited_from}
                                </span>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <div className="text-center py-4 text-slate-400">无继承权限</div>
                  )}
                </TabsContent>
              </Tabs>
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
