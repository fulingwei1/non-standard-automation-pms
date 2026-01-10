# Purchase模块权限转换完成总结

> 完成日期：2026-01-10

## 一、转换概述

成功将 `purchase` 模块从粗粒度权限检查（`require_procurement_access()`）转换为细粒度权限控制（基于权限编码的权限检查）。

## 二、权限定义

### 2.1 权限结构

共创建 **19个权限**，分为4个资源类型：

#### 采购订单权限（7个）
- `purchase:order:read` - 采购订单查看
- `purchase:order:create` - 采购订单创建
- `purchase:order:update` - 采购订单更新
- `purchase:order:delete` - 采购订单删除
- `purchase:order:submit` - 采购订单提交
- `purchase:order:approve` - 采购订单审批
- `purchase:order:receive` - 采购订单收货

#### 收货单权限（4个）
- `purchase:receipt:read` - 收货单查看
- `purchase:receipt:create` - 收货单创建
- `purchase:receipt:update` - 收货单更新
- `purchase:receipt:inspect` - 收货单质检

#### 采购申请权限（7个）
- `purchase:request:read` - 采购申请查看
- `purchase:request:create` - 采购申请创建
- `purchase:request:update` - 采购申请更新
- `purchase:request:delete` - 采购申请删除
- `purchase:request:submit` - 采购申请提交
- `purchase:request:approve` - 采购申请审批
- `purchase:request:generate` - 采购申请生成订单

#### BOM相关权限（1个）
- `purchase:bom:generate` - 从BOM生成采购

### 2.2 迁移脚本

- `migrations/20260110_purchase_permissions_sqlite.sql` - SQLite版本
- `migrations/20260110_purchase_permissions_mysql.sql` - MySQL版本

## 三、API端点权限映射

### 3.1 采购订单端点（6个）

| 端点 | 方法 | 权限 |
|------|------|------|
| `GET /` | GET | `purchase:order:read` |
| `GET /{order_id}` | GET | `purchase:order:read` |
| `POST /` | POST | `purchase:order:create` |
| `PUT /{order_id}` | PUT | `purchase:order:update` |
| `PUT /{order_id}/submit` | PUT | `purchase:order:submit` |
| `PUT /{order_id}/approve` | PUT | `purchase:order:approve` |
| `GET /{order_id}/items` | GET | `purchase:order:read` |
| `PUT /purchase-order-items/{item_id}/receive` | PUT | `purchase:order:receive` |

### 3.2 收货单端点（6个）

| 端点 | 方法 | 权限 |
|------|------|------|
| `GET /goods-receipts/` | GET | `purchase:receipt:read` |
| `POST /goods-receipts/` | POST | `purchase:receipt:create` |
| `GET /goods-receipts/{receipt_id}` | GET | `purchase:receipt:read` |
| `GET /goods-receipts/{receipt_id}/items` | GET | `purchase:receipt:read` |
| `PUT /goods-receipts/{receipt_id}/receive` | PUT | `purchase:receipt:update` |
| `PUT /goods-receipts/{receipt_id}/items/{item_id}/inspect` | PUT | `purchase:receipt:inspect` |

### 3.3 采购申请端点（9个）

| 端点 | 方法 | 权限 |
|------|------|------|
| `GET /requests` | GET | `purchase:request:read` |
| `GET /requests/{request_id}` | GET | `purchase:request:read` |
| `POST /requests` | POST | `purchase:request:create` |
| `PUT /requests/{request_id}` | PUT | `purchase:request:update` |
| `PUT /requests/{request_id}/submit` | PUT | `purchase:request:submit` |
| `PUT /requests/{request_id}/approve` | PUT | `purchase:request:approve` |
| `POST /requests/{request_id}/generate-orders` | POST | `purchase:request:generate` |
| `DELETE /requests/{request_id}` | DELETE | `purchase:request:delete` |
| `POST /from-bom` | POST | `purchase:bom:generate` |

## 四、角色权限分配

### 4.1 权限分配规则

| 角色 | 权限范围 | 说明 |
|------|---------|------|
| **采购助理** (PU_ASSISTANT) | `read` | 只有查看权限 |
| **采购专员** (PU) | `read`, `create`, `update`, `submit` | 可以创建、更新、提交，但不能审批和删除 |
| **采购工程师** (PU_ENGINEER) | `read`, `create`, `update`, `submit`, `receive`, `inspect` | 所有操作权限（除审批和删除） |
| **采购经理** (PU_MGR) | 所有权限 | 包括审批、删除、BOM生成等所有权限 |

### 4.2 权限分配详情

#### 采购助理 (PU_ASSISTANT) - 3个权限
- `purchase:order:read`
- `purchase:receipt:read`
- `purchase:request:read`

#### 采购专员 (PU) - 12个权限
- 订单：`read`, `create`, `update`, `submit`
- 收货单：`read`, `create`, `update`
- 申请：`read`, `create`, `update`, `submit`

#### 采购工程师 (PU_ENGINEER) - 15个权限
- 订单：`read`, `create`, `update`, `submit`, `receive`
- 收货单：`read`, `create`, `update`, `inspect`
- 申请：`read`, `create`, `update`, `submit`

#### 采购经理 (PU_MGR) - 19个权限（全部）
- 订单：所有权限（包括 `approve`, `delete`）
- 收货单：所有权限
- 申请：所有权限（包括 `approve`, `delete`, `generate`）
- BOM：`generate`

## 五、代码变更

### 5.1 文件变更

**主要文件**：
- `app/api/v1/endpoints/purchase.py` - 所有23个API端点已更新为细粒度权限检查

**变更内容**：
- 移除了所有 `require_procurement_access()` 调用
- 替换为 `require_permission("purchase:{resource}:{action}")` 调用
- 共替换了23处权限检查

### 5.2 权限检查示例

**之前**（粗粒度）：
```python
@router.get("/")
async def list_orders(
    current_user: User = Depends(security.require_procurement_access()),
):
    ...
```

**之后**（细粒度）：
```python
@router.get("/")
async def list_orders(
    current_user: User = Depends(security.require_permission("purchase:order:read")),
):
    ...
```

## 六、测试建议

### 6.1 功能测试

1. **采购助理测试**：
   - ✅ 可以查看订单、收货单、申请
   - ❌ 不能创建、更新、删除

2. **采购专员测试**：
   - ✅ 可以创建、更新、提交订单和申请
   - ❌ 不能审批、删除

3. **采购工程师测试**：
   - ✅ 可以处理收货、质检
   - ❌ 不能审批、删除

4. **采购经理测试**：
   - ✅ 拥有所有权限，包括审批、删除、BOM生成

### 6.2 权限边界测试

- 测试无权限用户访问应返回 403
- 测试有部分权限用户只能执行允许的操作
- 测试审批流程的权限控制

## 七、后续工作

1. ✅ 权限定义完成
2. ✅ API端点权限检查完成
3. ✅ 角色权限分配完成
4. ⏳ 前端权限控制更新（如需要）
5. ⏳ 权限测试验证
6. ⏳ 文档更新

## 八、相关文档

- [功能转换为权限完整指南](./FUNCTION_TO_PERMISSION_CONVERSION_GUIDE.md)
- [系统功能与权限完整对应关系](./SYSTEM_FUNCTIONS_PERMISSIONS_COMPLETE.md)
- [采购权限实现文档](./PROCUREMENT_PERMISSION_IMPLEMENTATION.md)
