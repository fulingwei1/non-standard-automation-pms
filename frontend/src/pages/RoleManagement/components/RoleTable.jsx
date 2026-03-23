/**
 * 角色列表表格组件
 * 展示角色信息、对比选择、操作按钮
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

export default function RoleTable({
  roles,
  loading,
  selectedForCompare,
  toggleCompareSelection,
  onViewDetail,
  onEdit,
  onDelete,
}) {
  if (loading) {
    return <div className="text-center py-8 text-slate-400">加载中...</div>;
  }

  if (roles.length === 0) {
    return <div className="text-center py-8 text-slate-400">暂无角色数据</div>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-10">
            <input type="checkbox" className="rounded" onChange={() => {}} checked={false} />
          </TableHead>
          <TableHead>角色编码</TableHead>
          <TableHead>角色名称</TableHead>
          <TableHead>继承自</TableHead>
          <TableHead>数据权限</TableHead>
          <TableHead>权限数</TableHead>
          <TableHead>状态</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {(roles || []).map((role) => (
          <TableRow
            key={role.id}
            className={selectedForCompare.includes(role.id) ? 'bg-blue-50' : ''}
          >
            <TableCell>
              <input
                type="checkbox"
                className="rounded"
                checked={selectedForCompare.includes(role.id)}
                onChange={() => toggleCompareSelection(role.id)}
              />
            </TableCell>
            <TableCell className="font-mono text-sm">{role.role_code}</TableCell>
            <TableCell className="font-medium">{role.role_name}</TableCell>
            <TableCell>
              {role.parent_name ? (
                <span className="text-blue-600 text-sm">
                  <GitBranch className="w-3 h-3 inline mr-1" />
                  {role.parent_name}
                </span>
              ) : (
                <span className="text-slate-400 text-sm">-</span>
              )}
            </TableCell>
            <TableCell>{renderDataScopeBadge(role.data_scope)}</TableCell>
            <TableCell>
              <span className="text-sm">
                {role.permission_count || 0}
                {role.inherited_permission_count > 0 && (
                  <span className="text-blue-500 ml-1">
                    (+{role.inherited_permission_count})
                  </span>
                )}
              </span>
            </TableCell>
            <TableCell>
              {role.is_system ? (
                <Badge variant="secondary">系统</Badge>
              ) : role.is_active ? (
                <Badge variant="success">启用</Badge>
              ) : (
                <Badge variant="destructive">禁用</Badge>
              )}
            </TableCell>
            <TableCell className="text-right">
              <div className="flex items-center justify-end gap-1">
                <Button variant="ghost" size="sm" onClick={() => onViewDetail(role.id)} title="查看详情">
                  <Eye className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => onEdit(role.id)} title="编辑">
                  <Edit3 className="w-4 h-4" />
                </Button>
                {!role.is_system && (
                  <Button variant="ghost" size="sm" onClick={() => onDelete(role.id)} title="删除">
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
