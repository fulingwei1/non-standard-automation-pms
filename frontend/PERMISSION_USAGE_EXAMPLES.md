# 前端权限使用示例

> 更新日期：2026-01-10

本文档提供前端权限控制的使用示例，帮助开发者快速集成细粒度权限检查。

## 一、路由保护

### 1.1 使用细粒度权限（推荐）

```jsx
import { ProcurementProtectedRoute } from '../components/common/ProtectedRoute'

// 在 routeConfig.jsx 中
<Route path="/purchases" element={
  <ProcurementProtectedRoute requiredPermission="purchase:order:read">
    <PurchaseOrders />
  </ProcurementProtectedRoute>
} />

<Route path="/purchases/new" element={
  <ProcurementProtectedRoute requiredPermission="purchase:order:create">
    <PurchaseOrderNew />
  </ProcurementProtectedRoute>
} />

<Route path="/purchases/:id/approve" element={
  <ProcurementProtectedRoute requiredPermission="purchase:order:approve">
    <PurchaseOrderApprove />
  </ProcurementProtectedRoute>
} />
```

### 1.2 使用粗粒度权限（向后兼容）

```jsx
// 不指定 requiredPermission，使用角色检查
<Route path="/purchases" element={
  <ProcurementProtectedRoute>
    <PurchaseOrders />
  </ProcurementProtectedRoute>
} />
```

## 二、组件内权限检查

### 2.1 使用 PermissionGuard 组件

```jsx
import { PermissionGuard } from '../components/common/PermissionGuard'

function PurchaseOrderList() {
  return (
    <div>
      <h1>采购订单列表</h1>
      
      {/* 创建按钮 - 需要创建权限 */}
      <PermissionGuard permission="purchase:order:create">
        <Button onClick={handleCreate}>创建订单</Button>
      </PermissionGuard>
      
      {/* 审批按钮 - 需要审批权限 */}
      <PermissionGuard permission="purchase:order:approve">
        <Button onClick={handleApprove}>审批订单</Button>
      </PermissionGuard>
      
      {/* 删除按钮 - 需要删除权限 */}
      <PermissionGuard permission="purchase:order:delete">
        <Button onClick={handleDelete} variant="destructive">删除订单</Button>
      </PermissionGuard>
    </div>
  )
}
```

### 2.2 使用权限检查函数

```jsx
import { 
  hasPurchaseOrderCreate, 
  hasPurchaseOrderApprove,
  hasPurchaseOrderDelete 
} from '../../lib/permissionUtils'

function PurchaseOrderList() {
  const canCreate = hasPurchaseOrderCreate()
  const canApprove = hasPurchaseOrderApprove()
  const canDelete = hasPurchaseOrderDelete()
  
  return (
    <div>
      <h1>采购订单列表</h1>
      
      {canCreate && (
        <Button onClick={handleCreate}>创建订单</Button>
      )}
      
      {canApprove && (
        <Button onClick={handleApprove}>审批订单</Button>
      )}
      
      {canDelete && (
        <Button onClick={handleDelete} variant="destructive">删除订单</Button>
      )}
    </div>
  )
}
```

### 2.3 使用 useHasPermission Hook

```jsx
import { useHasPermission } from '../components/common/PermissionGuard'

function PurchaseOrderList() {
  const canCreate = useHasPermission('purchase:order:create')
  const canApprove = useHasPermission('purchase:order:approve')
  const canDelete = useHasPermission('purchase:order:delete')
  
  return (
    <div>
      <h1>采购订单列表</h1>
      
      {canCreate && <Button onClick={handleCreate}>创建订单</Button>}
      {canApprove && <Button onClick={handleApprove}>审批订单</Button>}
      {canDelete && <Button onClick={handleDelete}>删除订单</Button>}
    </div>
  )
}
```

## 三、复杂权限场景

### 3.1 多个权限（任意一个）

```jsx
import { PermissionGuard } from '../components/common/PermissionGuard'

// 有创建或更新权限即可显示编辑按钮
<PermissionGuard permission={['purchase:order:create', 'purchase:order:update']}>
  <Button onClick={handleEdit}>编辑订单</Button>
</PermissionGuard>
```

### 3.2 多个权限（全部需要）

```jsx
// 需要同时有查看和审批权限
<PermissionGuard 
  permission={['purchase:order:read', 'purchase:order:approve']} 
  requireAll
>
  <Button onClick={handleApprove}>审批订单</Button>
</PermissionGuard>
```

### 3.3 条件渲染

```jsx
import { hasPermission } from '../../lib/permissionUtils'

function PurchaseOrderDetail({ order }) {
  const canApprove = hasPermission('purchase:order:approve')
  const canDelete = hasPermission('purchase:order:delete')
  
  return (
    <div>
      <h1>订单详情</h1>
      
      {/* 根据权限显示不同的操作按钮 */}
      {order.status === 'SUBMITTED' && canApprove && (
        <Button onClick={handleApprove}>审批订单</Button>
      )}
      
      {order.status === 'DRAFT' && canDelete && (
        <Button onClick={handleDelete} variant="destructive">删除订单</Button>
      )}
    </div>
  )
}
```

## 四、表格操作列权限控制

```jsx
import { hasPermission } from '../../lib/permissionUtils'

function PurchaseOrderTable({ orders, onEdit, onApprove, onDelete }) {
  const canEdit = hasPermission('purchase:order:update')
  const canApprove = hasPermission('purchase:order:approve')
  const canDelete = hasPermission('purchase:order:delete')
  
  const columns = [
    { key: 'order_no', label: '订单号' },
    { key: 'supplier_name', label: '供应商' },
    { key: 'total_amount', label: '金额' },
    { key: 'status', label: '状态' },
    {
      key: 'actions',
      label: '操作',
      render: (order) => (
        <div className="flex gap-2">
          {canEdit && order.status === 'DRAFT' && (
            <Button size="sm" onClick={() => onEdit(order.id)}>编辑</Button>
          )}
          {canApprove && order.status === 'SUBMITTED' && (
            <Button size="sm" onClick={() => onApprove(order.id)}>审批</Button>
          )}
          {canDelete && order.status === 'DRAFT' && (
            <Button size="sm" variant="destructive" onClick={() => onDelete(order.id)}>删除</Button>
          )}
        </div>
      )
    }
  ]
  
  return <Table data={orders} columns={columns} />
}
```

## 五、表单提交权限控制

```jsx
import { hasPermission } from '../../lib/permissionUtils'

function PurchaseOrderForm({ onSubmit, order }) {
  const canCreate = hasPermission('purchase:order:create')
  const canUpdate = hasPermission('purchase:order:update')
  const canSubmit = hasPermission('purchase:order:submit')
  
  const isEdit = !!order
  const canEdit = isEdit ? canUpdate : canCreate
  
  const handleSubmit = async (data) => {
    if (!canEdit) {
      alert('您没有权限执行此操作')
      return
    }
    
    await onSubmit(data)
  }
  
  return (
    <form onSubmit={handleSubmit}>
      {/* 表单字段 */}
      
      <div className="flex gap-2">
        <Button type="submit" disabled={!canEdit}>
          {isEdit ? '更新' : '创建'}
        </Button>
        
        {canSubmit && order?.status === 'DRAFT' && (
          <Button type="button" onClick={handleSubmitOrder}>
            提交审批
          </Button>
        )}
      </div>
    </form>
  )
}
```

## 六、菜单权限控制

```jsx
import { hasAnyPurchasePermission } from '../../lib/permissionUtils'

function Sidebar() {
  const hasPurchaseAccess = hasAnyPurchasePermission()
  
  const menuItems = [
    { path: '/projects', label: '项目管理' },
    { path: '/materials', label: '物料管理' },
    // 根据权限显示采购菜单
    ...(hasPurchaseAccess ? [
      { path: '/purchases', label: '采购订单' },
      { path: '/purchase-requests', label: '采购申请' },
    ] : []),
  ]
  
  return <NavMenu items={menuItems} />
}
```

## 七、API调用权限检查

```jsx
import { hasPermission } from '../../lib/permissionUtils'
import { purchaseApi } from '../../services/api'

function PurchaseOrderList() {
  const canCreate = hasPermission('purchase:order:create')
  
  const handleCreate = async () => {
    if (!canCreate) {
      alert('您没有权限创建采购订单')
      return
    }
    
    try {
      await purchaseApi.create(orderData)
      // 成功处理
    } catch (error) {
      if (error.response?.status === 403) {
        alert('权限不足，无法创建订单')
      }
    }
  }
  
  return (
    <div>
      {canCreate && (
        <Button onClick={handleCreate}>创建订单</Button>
      )}
    </div>
  )
}
```

## 八、权限调试

### 8.1 查看当前用户权限

```jsx
import { getUserPermissions } from '../../lib/permissionUtils'

function PermissionDebug() {
  const permissions = getUserPermissions()
  
  return (
    <div>
      <h2>当前用户权限</h2>
      <ul>
        {permissions.map(perm => (
          <li key={perm}>{perm}</li>
        ))}
      </ul>
    </div>
  )
}
```

### 8.2 权限检查测试

```jsx
import { 
  hasPermission, 
  hasPurchaseOrderRead,
  hasPurchaseOrderCreate 
} from '../../lib/permissionUtils'

function PermissionTest() {
  const testPermissions = [
    'purchase:order:read',
    'purchase:order:create',
    'purchase:order:approve',
  ]
  
  return (
    <div>
      <h2>权限检查测试</h2>
      <table>
        <thead>
          <tr>
            <th>权限编码</th>
            <th>检查结果</th>
          </tr>
        </thead>
        <tbody>
          {testPermissions.map(perm => (
            <tr key={perm}>
              <td>{perm}</td>
              <td>{hasPermission(perm) ? '✅' : '❌'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <div>
        <p>hasPurchaseOrderRead: {hasPurchaseOrderRead() ? '✅' : '❌'}</p>
        <p>hasPurchaseOrderCreate: {hasPurchaseOrderCreate() ? '✅' : '❌'}</p>
      </div>
    </div>
  )
}
```

## 九、最佳实践

### 9.1 权限检查时机

1. **路由级别**：使用 `ProcurementProtectedRoute` 保护整个页面
2. **组件级别**：使用 `PermissionGuard` 或权限检查函数控制功能显示
3. **API调用前**：在调用API前检查权限，提供更好的用户体验

### 9.2 权限检查顺序

```jsx
// 推荐：先检查权限，再渲染
{hasPermission('purchase:order:create') && (
  <Button onClick={handleCreate}>创建订单</Button>
)}

// 不推荐：先渲染，再在事件处理中检查
<Button onClick={() => {
  if (!hasPermission('purchase:order:create')) {
    alert('无权限')
    return
  }
  handleCreate()
}}>创建订单</Button>
```

### 9.3 错误处理

```jsx
import { hasPermission } from '../../lib/permissionUtils'

async function handleAction() {
  if (!hasPermission('purchase:order:create')) {
    // 前端检查失败
    alert('您没有权限执行此操作')
    return
  }
  
  try {
    await api.create(data)
  } catch (error) {
    if (error.response?.status === 403) {
      // 后端检查失败（可能是权限变更）
      alert('权限不足，请刷新页面后重试')
      // 可以重新获取用户信息
      await refreshUserInfo()
    }
  }
}
```

## 十、常见问题

### Q1: 权限列表为空怎么办？

**A**: 检查：
1. 用户是否已登录
2. `/auth/me` 是否返回了权限列表
3. localStorage 中的用户信息是否包含 `permissions` 字段

### Q2: 权限检查不生效？

**A**: 检查：
1. 权限编码是否正确（如 `purchase:order:read`）
2. 用户是否有该权限（查看 localStorage 中的 permissions 数组）
3. 是否使用了正确的权限检查函数

### Q3: 如何调试权限问题？

**A**: 
1. 在浏览器控制台查看 localStorage 中的用户信息
2. 使用 `getUserPermissions()` 查看权限列表
3. 使用权限调试组件测试权限检查

## 十一、相关文档

- [前端权限控制更新总结](../docs/FRONTEND_PERMISSION_UPDATE_SUMMARY.md)
- [Purchase模块权限转换完成总结](../docs/PURCHASE_PERMISSION_IMPLEMENTATION_COMPLETE.md)
