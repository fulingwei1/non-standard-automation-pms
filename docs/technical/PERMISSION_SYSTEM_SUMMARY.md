# 权限控制系统总结文档

## 系统概述

本系统实现了完整的基于角色的访问控制（RBAC）机制，确保不同岗位的用户只能访问其职责范围内的功能模块。

## 已实现的权限控制模块

### 1. 采购与物料管理模块 ✅

**前端保护**：
- ✅ 路由保护：`/purchases`, `/purchases/:id`, `/materials`, `/material-analysis`
- ✅ 菜单过滤：无权限用户看不到相关菜单
- ✅ 权限判断函数：`hasProcurementAccess()`

**后端保护**：
- ✅ 所有采购订单 API 端点（12个）
- ✅ 所有物料管理 API 端点（6个）
- ✅ 所有齐套分析 API 端点（6个）
- ✅ 权限检查函数：`has_procurement_access()`, `require_procurement_access()`

**有权限的角色**：
- 采购相关：采购工程师、采购经理、采购员
- PMC 计划员
- 生产相关：生产经理、制造总监
- 管理层：总经理、董事长、管理员
- 项目经理

### 2. 财务管理模块 ✅

**前端保护**：
- ✅ 路由保护：`/finance-manager-dashboard`, `/payments`, `/invoices`
- ✅ 权限判断函数：`hasFinanceAccess()`
- ✅ 保护组件：`FinanceProtectedRoute`

**后端保护**：
- ⚠️ 待实现：财务相关 API 端点需要添加权限检查

**有权限的角色**：
- 财务相关：财务经理、财务人员
- 管理层：总经理、董事长、管理员
- 商务支持：商务支持专员

### 3. 生产管理模块 ✅

**前端保护**：
- ✅ 路由保护：`/production-dashboard`, `/manufacturing-director-dashboard`
- ✅ 权限判断函数：`hasProductionAccess()`
- ✅ 保护组件：`ProductionProtectedRoute`

**后端保护**：
- ⚠️ 待实现：生产相关 API 端点需要添加权限检查

**有权限的角色**：
- 生产相关：生产经理、制造总监
- PMC 计划员
- 装配相关：装配技工、装配钳工、装配电工
- 管理层：总经理、董事长、管理员

## 通用权限保护组件系统

### ProtectedRoute 组件

创建了通用的权限保护组件系统，支持：

1. **通用保护组件** (`ProtectedRoute`)
   - 可配置的权限检查函数
   - 自定义权限名称
   - 自定义重定向路径

2. **专用保护组件**
   - `ProcurementProtectedRoute` - 采购权限
   - `FinanceProtectedRoute` - 财务权限
   - `ProductionProtectedRoute` - 生产权限

3. **扩展性**
   - 易于添加新的权限类型
   - 统一的错误处理
   - 一致的用户体验

### 使用示例

```javascript
// 使用通用组件
<ProtectedRoute
  checkPermission={hasProcurementAccess}
  permissionName="采购和物料管理模块"
>
  <PurchaseOrders />
</ProtectedRoute>

// 使用专用组件（推荐）
<ProcurementProtectedRoute>
  <PurchaseOrders />
</ProcurementProtectedRoute>

// 添加新的权限类型
export function SalesProtectedRoute({ children }) {
  return (
    <ProtectedRoute
      checkPermission={hasSalesAccess}
      permissionName="销售管理模块"
    >
      {children}
    </ProtectedRoute>
  )
}
```

## 权限判断函数

### 前端权限函数 (`roleConfig.js`)

```javascript
// 采购权限
export function hasProcurementAccess(roleCode) { ... }

// 财务权限
export function hasFinanceAccess(roleCode) { ... }

// 生产权限
export function hasProductionAccess(roleCode) { ... }
```

### 后端权限函数 (`security.py`)

```python
# 采购权限
def has_procurement_access(user: User) -> bool: ...
def require_procurement_access(): ...

# TODO: 财务权限
def has_finance_access(user: User) -> bool: ...
def require_finance_access(): ...

# TODO: 生产权限
def has_production_access(user: User) -> bool: ...
def require_production_access(): ...
```

## 权限控制流程

### 前端流程

```
用户访问路由
    ↓
ProtectedRoute 组件检查
    ↓
调用权限判断函数
    ↓
有权限？ → 是 → 渲染页面
    ↓
    否
    ↓
显示无权限页面
```

### 后端流程

```
API 请求到达
    ↓
FastAPI 依赖注入
    ↓
require_xxx_access() 检查
    ↓
has_xxx_access() 验证角色
    ↓
有权限？ → 是 → 执行 API
    ↓
    否
    ↓
返回 403 错误
```

## 菜单权限控制

### 实现方式

1. **角色配置** (`roleConfig.js`)
   - 定义每个角色的导航组
   - 自动过滤采购相关菜单

2. **菜单过滤** (`Sidebar.jsx`)
   - `filterNavItemsByRole()` 函数
   - 根据角色动态显示/隐藏菜单项

3. **路径过滤**
   - `/purchases` - 采购订单
   - `/materials` - 齐套分析
   - `/bom-analysis` - BOM 分析

## API 错误处理

### 错误类型区分

1. **401 认证错误**
   - 未登录或 Token 失效
   - 自动跳转到登录页

2. **403 权限错误**
   - 已登录但无权限
   - 显示无权限提示，不跳转

3. **其他错误**
   - 网络错误、服务器错误等
   - 显示相应错误消息

### 错误处理函数

```javascript
// 检查是否为权限错误
export function isPermissionError(error) {
  return error.response?.status === 403
}

// 处理 API 错误
export function handleApiError(error, options = {}) {
  const { onPermissionError, ... } = options
  // ...
}
```

## 待完成工作

### 高优先级

1. **财务模块后端权限**
   - [ ] 添加 `has_finance_access()` 函数
   - [ ] 添加 `require_finance_access()` 依赖
   - [ ] 为财务相关 API 添加权限检查

2. **生产模块后端权限**
   - [ ] 添加 `has_production_access()` 函数
   - [ ] 添加 `require_production_access()` 依赖
   - [ ] 为生产相关 API 添加权限检查

3. **页面 API 集成**
   - [ ] 采购相关页面（6个）
   - [ ] 财务相关页面（3个）
   - [ ] 生产相关页面（3个）

### 中优先级

4. **其他模块权限控制**
   - [ ] 销售模块权限细化
   - [ ] 人事模块权限控制
   - [ ] 行政模块权限控制

5. **数据权限控制**
   - [ ] 项目级数据权限
   - [ ] 部门级数据权限
   - [ ] 个人数据权限

### 低优先级

6. **权限管理界面**
   - [ ] 角色权限配置界面
   - [ ] 权限分配界面
   - [ ] 权限审计日志

## 最佳实践

### 1. 添加新权限类型

**步骤**：
1. 在 `roleConfig.js` 中添加权限判断函数
2. 在 `security.py` 中添加后端权限函数
3. 创建专用保护组件（可选）
4. 在路由中使用保护组件
5. 在后端 API 中使用权限依赖

**示例**：
```javascript
// 1. 前端权限函数
export function hasSalesAccess(roleCode) {
  const salesRoles = ['sales', 'sales_manager', ...]
  return salesRoles.includes(roleCode)
}

// 2. 后端权限函数
def has_sales_access(user: User) -> bool:
    sales_roles = ['sales', 'sales_manager', ...]
    # 检查逻辑
    return True

// 3. 保护组件
export function SalesProtectedRoute({ children }) {
  return (
    <ProtectedRoute
      checkPermission={hasSalesAccess}
      permissionName="销售管理模块"
    >
      {children}
    </ProtectedRoute>
  )
}

// 4. 路由使用
<Route path="/sales" element={
  <SalesProtectedRoute>
    <SalesPage />
  </SalesProtectedRoute>
} />

// 5. 后端 API
@router.get("/sales/...")
def get_sales_data(
    current_user: User = Depends(security.require_sales_access()),
):
    # ...
```

### 2. 权限测试

**测试场景**：
1. 有权限用户能正常访问
2. 无权限用户看到无权限提示
3. 无权限用户无法看到菜单
4. 直接访问 URL 时权限检查生效
5. API 调用时权限检查生效

### 3. 权限维护

**维护清单**：
- 定期审查权限列表
- 更新角色定义
- 同步前后端权限规则
- 记录权限变更日志

## 相关文档

1. [权限控制实现文档](./PROCUREMENT_PERMISSION_IMPLEMENTATION.md)
2. [前端页面统计文档](./FRONTEND_PAGES_STATISTICS.md)
3. [API 集成实现指南](./PROCUREMENT_PAGES_IMPLEMENTATION_GUIDE.md)
4. [前端实现总结报告](./FRONTEND_IMPLEMENTATION_SUMMARY.md)

## 更新日志

- **2025-01-XX**: 完成采购模块权限控制
- **2025-01-XX**: 创建通用权限保护组件系统
- **2025-01-XX**: 添加财务和生产模块权限判断
- **2025-01-XX**: 为财务相关路由添加权限保护



