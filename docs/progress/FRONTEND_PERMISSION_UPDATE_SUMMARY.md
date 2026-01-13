# 前端权限控制更新总结

> 更新日期：2026-01-10

## 一、更新概述

成功更新前端权限控制逻辑，从粗粒度角色检查转换为细粒度权限检查，支持purchase模块的19个权限。

## 二、新增文件

### 2.1 权限工具库

**文件**：`frontend/src/lib/permissionUtils.js`

**功能**：
- 从localStorage获取用户权限列表
- 提供细粒度权限检查函数
- Purchase模块专用权限检查函数
- 权限检查Hook

**主要函数**：
```javascript
// 基础权限检查
hasPermission(permissionCode)
hasAnyPermission(permissionCodes)
hasAllPermissions(permissionCodes)

// Purchase模块权限检查
hasPurchaseOrderRead()
hasPurchaseOrderCreate()
hasPurchaseOrderUpdate()
hasPurchaseOrderDelete()
hasPurchaseOrderSubmit()
hasPurchaseOrderApprove()
hasPurchaseOrderReceive()
hasPurchaseReceiptRead()
hasPurchaseReceiptCreate()
hasPurchaseReceiptUpdate()
hasPurchaseReceiptInspect()
hasPurchaseRequestRead()
hasPurchaseRequestCreate()
hasPurchaseRequestUpdate()
hasPurchaseRequestDelete()
hasPurchaseRequestSubmit()
hasPurchaseRequestApprove()
hasPurchaseRequestGenerate()
hasPurchaseBomGenerate()
hasAnyPurchasePermission()
```

### 2.2 权限守卫组件

**文件**：`frontend/src/components/common/PermissionGuard.jsx`

**功能**：
- 在组件内部进行权限检查
- 支持单个权限或权限数组
- 支持条件渲染

**使用示例**：
```jsx
import { PermissionGuard } from '../components/common/PermissionGuard'

// 单个权限检查
<PermissionGuard permission="purchase:order:create">
  <Button>创建订单</Button>
</PermissionGuard>

// 多个权限（任意一个）
<PermissionGuard permission={['purchase:order:create', 'purchase:order:update']}>
  <Button>编辑订单</Button>
</PermissionGuard>

// 多个权限（全部需要）
<PermissionGuard permission={['purchase:order:read', 'purchase:order:approve']} requireAll>
  <Button>审批订单</Button>
</PermissionGuard>
```

## 三、更新的文件

### 3.1 ProtectedRoute组件

**文件**：`frontend/src/components/common/ProtectedRoute.jsx`

**更新内容**：
- 更新 `ProcurementProtectedRoute` 组件，支持细粒度权限检查
- 支持两种模式：
  - **粗粒度检查**（向后兼容）：基于角色代码
  - **细粒度检查**（推荐）：基于权限编码

**使用示例**：
```jsx
// 粗粒度检查（默认，向后兼容）
<ProcurementProtectedRoute>
  <PurchaseOrders />
</ProcurementProtectedRoute>

// 细粒度检查（推荐）
<ProcurementProtectedRoute requiredPermission="purchase:order:read">
  <PurchaseOrders />
</ProcurementProtectedRoute>

// 强制使用细粒度检查
<ProcurementProtectedRoute useFineGrained={true}>
  <PurchaseOrders />
</ProcurementProtectedRoute>
```

### 3.2 登录页面

**文件**：`frontend/src/pages/Login.jsx`

**更新内容**：
- 确保从后端获取的权限列表被保存到localStorage
- 在用户信息中添加 `permissions` 字段
- 添加权限日志输出

## 四、权限检查流程

### 4.1 用户登录流程

```
1. 用户登录
   ↓
2. 调用 /auth/me 获取用户信息
   ↓
3. 后端返回用户信息（包含 permissions 数组）
   ↓
4. 前端保存到 localStorage
   {
     ...userInfo,
     permissions: ['purchase:order:read', 'purchase:order:create', ...]
   }
```

### 4.2 权限检查流程

```
1. 组件需要检查权限
   ↓
2. 调用 hasPermission('purchase:order:read')
   ↓
3. 从 localStorage 读取用户信息
   ↓
4. 检查 permissions 数组是否包含该权限
   ↓
5. 超级管理员自动通过
   ↓
6. 返回 true/false
```

## 五、使用指南

### 5.1 路由保护

**方式1：使用细粒度权限（推荐）**
```jsx
<Route path="/purchases" element={
  <ProcurementProtectedRoute requiredPermission="purchase:order:read">
    <PurchaseOrders />
  </ProcurementProtectedRoute>
} />
```

**方式2：使用粗粒度权限（向后兼容）**
```jsx
<Route path="/purchases" element={
  <ProcurementProtectedRoute>
    <PurchaseOrders />
  </ProcurementProtectedRoute>
} />
```

### 5.2 组件内权限检查

**方式1：使用PermissionGuard组件**
```jsx
import { PermissionGuard } from '../components/common/PermissionGuard'

function PurchaseOrderList() {
  return (
    <div>
      <PermissionGuard permission="purchase:order:create">
        <Button onClick={handleCreate}>创建订单</Button>
      </PermissionGuard>
      
      <PermissionGuard permission="purchase:order:approve">
        <Button onClick={handleApprove}>审批订单</Button>
      </PermissionGuard>
    </div>
  )
}
```

**方式2：使用权限检查函数**
```jsx
import { hasPurchaseOrderCreate, hasPurchaseOrderApprove } from '../../lib/permissionUtils'

function PurchaseOrderList() {
  const canCreate = hasPurchaseOrderCreate()
  const canApprove = hasPurchaseOrderApprove()
  
  return (
    <div>
      {canCreate && <Button onClick={handleCreate}>创建订单</Button>}
      {canApprove && <Button onClick={handleApprove}>审批订单</Button>}
    </div>
  )
}
```

**方式3：使用Hook**
```jsx
import { useHasPermission } from '../components/common/PermissionGuard'

function PurchaseOrderList() {
  const canCreate = useHasPermission('purchase:order:create')
  const canApprove = useHasPermission('purchase:order:approve')
  
  return (
    <div>
      {canCreate && <Button onClick={handleCreate}>创建订单</Button>}
      {canApprove && <Button onClick={handleApprove}>审批订单</Button>}
    </div>
  )
}
```

## 六、权限映射表

### 6.1 采购订单权限

| 权限编码 | 权限名称 | 使用场景 |
|---------|---------|---------|
| `purchase:order:read` | 采购订单查看 | 查看订单列表、详情 |
| `purchase:order:create` | 采购订单创建 | 创建新订单 |
| `purchase:order:update` | 采购订单更新 | 编辑订单信息 |
| `purchase:order:delete` | 采购订单删除 | 删除订单 |
| `purchase:order:submit` | 采购订单提交 | 提交订单审批 |
| `purchase:order:approve` | 采购订单审批 | 审批订单 |
| `purchase:order:receive` | 采购订单收货 | 处理订单收货 |

### 6.2 收货单权限

| 权限编码 | 权限名称 | 使用场景 |
|---------|---------|---------|
| `purchase:receipt:read` | 收货单查看 | 查看收货单列表、详情 |
| `purchase:receipt:create` | 收货单创建 | 创建收货单 |
| `purchase:receipt:update` | 收货单更新 | 更新收货单状态 |
| `purchase:receipt:inspect` | 收货单质检 | 进行质检操作 |

### 6.3 采购申请权限

| 权限编码 | 权限名称 | 使用场景 |
|---------|---------|---------|
| `purchase:request:read` | 采购申请查看 | 查看申请列表、详情 |
| `purchase:request:create` | 采购申请创建 | 创建采购申请 |
| `purchase:request:update` | 采购申请更新 | 编辑申请信息 |
| `purchase:request:delete` | 采购申请删除 | 删除申请 |
| `purchase:request:submit` | 采购申请提交 | 提交申请审批 |
| `purchase:request:approve` | 采购申请审批 | 审批申请 |
| `purchase:request:generate` | 采购申请生成订单 | 从申请生成订单 |

### 6.4 BOM相关权限

| 权限编码 | 权限名称 | 使用场景 |
|---------|---------|---------|
| `purchase:bom:generate` | 从BOM生成采购 | 从BOM生成采购申请或订单 |

## 七、角色权限对应

| 角色 | 权限范围 | 权限数量 |
|------|---------|---------|
| 采购助理 (PU_ASSISTANT) | 仅查看 | 3个 |
| 采购专员 (PU) | 创建、更新、提交 | 12个 |
| 采购工程师 (PU_ENGINEER) | 所有操作（除审批） | 15个 |
| 采购经理 (PU_MGR) | 所有权限 | 19个 |

## 八、向后兼容性

### 8.1 兼容策略

1. **路由保护**：`ProcurementProtectedRoute` 默认使用粗粒度检查，保持向后兼容
2. **角色检查**：`hasProcurementAccess()` 函数仍然可用
3. **权限获取**：如果后端未返回权限列表，前端会初始化为空数组

### 8.2 迁移建议

1. **逐步迁移**：可以逐步将路由从粗粒度检查迁移到细粒度检查
2. **混合使用**：粗粒度和细粒度检查可以同时使用
3. **优先使用细粒度**：新功能优先使用细粒度权限检查

## 九、测试建议

### 9.1 功能测试

1. **登录测试**：
   - 验证权限列表是否正确保存到localStorage
   - 验证不同角色的权限列表是否正确

2. **路由保护测试**：
   - 测试有权限用户能正常访问
   - 测试无权限用户被正确拦截

3. **组件权限测试**：
   - 测试按钮/功能根据权限显示/隐藏
   - 测试权限边界情况

### 9.2 权限边界测试

- 采购助理：只能查看，不能操作
- 采购专员：可以创建、更新、提交，不能审批
- 采购工程师：可以所有操作，不能审批和删除
- 采购经理：拥有所有权限

## 十、相关文档

- [Purchase模块权限转换完成总结](./PURCHASE_PERMISSION_IMPLEMENTATION_COMPLETE.md)
- [功能转换为权限完整指南](./FUNCTION_TO_PERMISSION_CONVERSION_GUIDE.md)
