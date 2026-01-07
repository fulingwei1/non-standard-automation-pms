# 采购订单和齐套分析模块权限控制实现文档

## 概述

本文档记录了为"采购订单"和"齐套分析"模块实现的完整权限控制系统。该系统确保只有授权角色才能访问这些敏感的业务模块。

## 实现范围

### 前端权限控制

#### 1. 角色配置 (`frontend/src/lib/roleConfig.js`)

- **新增函数**: `hasProcurementAccess(roleCode)`
  - 判断指定角色是否有采购和物料管理模块的访问权限
  - 返回 `true` 或 `false`

- **修改函数**: `getNavForRole(roleCode)`
  - 自动过滤采购相关的导航菜单项
  - 根据角色权限动态生成导航配置

#### 2. 侧边栏菜单 (`frontend/src/components/layout/Sidebar.jsx`)

- **新增函数**: `filterNavItemsByRole(navGroups, role)`
  - 根据角色权限过滤导航菜单项
  - 过滤路径：`/purchases`、`/materials`、`/bom-analysis`
  - 自动移除过滤后为空的导航组

- **修改函数**: `getNavGroupsForRole(role)`
  - 统一应用权限过滤逻辑
  - 适用于所有导航组，包括从 `roleConfig.js` 获取的导航组

#### 3. 路由保护 (`frontend/src/App.jsx`)

- **新增组件**: `ProcurementProtectedRoute`
  - 路由级别的权限保护组件
  - 无权限用户访问时显示友好的无权限页面
  - 提供返回上一页的按钮

- **保护的路由**:
  - `/purchases` - 采购订单列表
  - `/purchases/:id` - 采购订单详情
  - `/materials` - 物料跟踪/齐套分析
  - `/material-analysis` - 物料分析

#### 4. API 错误处理优化 (`frontend/src/services/api.js` & `frontend/src/utils/errorHandler.js`)

- **优化响应拦截器**:
  - 区分 401（认证错误）和 403（权限错误）
  - 403 错误不自动跳转，由组件处理

- **新增函数**: `isPermissionError(error)`
  - 检查是否为权限错误（403）

- **优化函数**: `handleApiError(error, options)`
  - 新增 `onPermissionError` 回调选项
  - 区分处理认证错误和权限错误

### 后端权限控制

#### 1. 权限检查函数 (`app/core/security.py`)

- **新增函数**: `has_procurement_access(user) -> bool`
  - 检查用户是否有采购和物料管理模块的访问权限
  - 支持超级管理员自动通过
  - 基于角色代码进行判断

- **新增函数**: `require_procurement_access()`
  - FastAPI 依赖注入函数
  - 用于 API 端点的权限检查
  - 无权限时返回 403 错误

#### 2. API 端点保护

**采购订单 API** (`app/api/v1/endpoints/purchase.py`):
- ✅ `GET /purchase-orders/` - 获取采购订单列表
- ✅ `GET /purchase-orders/{order_id}` - 获取采购订单详情
- ✅ `POST /purchase-orders/` - 创建采购订单
- ✅ `PUT /purchase-orders/{order_id}` - 更新采购订单
- ✅ `PUT /purchase-orders/{order_id}/approve` - 审批采购订单
- ✅ `GET /purchase-orders/{order_id}/items` - 获取订单明细
- ✅ `GET /purchase-orders/goods-receipts/` - 获取收货记录列表
- ✅ `POST /purchase-orders/goods-receipts/` - 创建收货单
- ✅ `GET /purchase-orders/goods-receipts/{receipt_id}` - 获取收货单详情
- ✅ `GET /purchase-orders/goods-receipts/{receipt_id}/items` - 获取收货单明细
- ✅ `PUT /purchase-orders/goods-receipts/{receipt_id}/receive` - 更新收货单状态
- ✅ `PUT /purchase-orders/purchase-order-items/{item_id}/receive` - 更新订单明细收货状态

**物料管理 API** (`app/api/v1/endpoints/materials.py`):
- ✅ `GET /materials/` - 获取物料列表
- ✅ `GET /materials/{material_id}` - 获取物料详情
- ✅ `POST /materials/` - 创建新物料
- ✅ `PUT /materials/{material_id}` - 更新物料信息
- ✅ `GET /materials/categories/` - 获取物料分类列表
- ✅ `GET /materials/{material_id}/suppliers` - 获取物料供应商列表

**齐套分析 API** (`app/api/v1/endpoints/kit_rate.py`):
- ✅ `GET /projects/{project_id}/kit-rate` - 计算项目齐套率
- ✅ `GET /machines/{machine_id}/kit-rate` - 计算机台齐套率
- ✅ `GET /machines/{machine_id}/material-status` - 获取机台物料状态
- ✅ `GET /projects/{project_id}/material-status` - 获取项目物料状态
- ✅ `GET /projects/{project_id}/critical-shortage` - 获取项目关键物料缺口
- ✅ `GET /kit-rate/dashboard` - 获取齐套看板数据

## 有权限的角色列表

以下角色可以访问采购订单和齐套分析模块：

### 采购相关角色
- `procurement_engineer` - 采购工程师
- `procurement_manager` - 采购部经理
- `procurement` - 采购专员
- `buyer` - 采购员

### 计划管理角色
- `pmc` - PMC 计划员

### 生产管理角色
- `production_manager` - 生产部经理
- `manufacturing_director` - 制造总监

### 管理层角色
- `gm` - 总经理
- `chairman` - 董事长
- `admin` - 系统管理员
- `super_admin` - 超级管理员

### 项目管理角色
- `pm` - 项目经理

## 权限控制流程

### 前端流程

1. **菜单显示控制**
   - 用户登录后，系统根据角色获取导航配置
   - `filterNavItemsByRole()` 函数过滤掉无权限的菜单项
   - 无权限用户看不到"采购订单"和"齐套分析"菜单

2. **路由访问控制**
   - 用户尝试访问受保护的路由时
   - `ProcurementProtectedRoute` 组件检查用户权限
   - 无权限时显示无权限页面，不跳转到登录页

3. **API 调用控制**
   - 前端调用 API 时，后端会进行权限验证
   - 如果返回 403 错误，前端错误处理机制会捕获
   - 组件可以自定义权限错误的处理方式

### 后端流程

1. **API 请求拦截**
   - 所有采购相关 API 端点使用 `require_procurement_access()` 依赖
   - FastAPI 自动调用权限检查函数

2. **权限验证**
   - `has_procurement_access()` 检查用户角色
   - 超级管理员自动通过
   - 普通用户检查角色代码是否在授权列表中

3. **错误响应**
   - 无权限时返回 403 HTTP 状态码
   - 错误消息："您没有权限访问采购和物料管理模块"

## 安全特性

1. **多层防护**
   - 前端菜单隐藏（第一层）
   - 前端路由保护（第二层）
   - 后端 API 权限验证（第三层）

2. **用户体验**
   - 无权限用户看不到相关菜单，避免困惑
   - 直接访问 URL 时显示友好的无权限页面
   - API 错误有明确的错误提示

3. **代码一致性**
   - 前后端使用相同的角色代码列表
   - 权限判断逻辑统一
   - 易于维护和扩展

## 测试建议

### 前端测试

1. **菜单显示测试**
   - 使用不同角色登录，验证菜单是否正确显示/隐藏
   - 验证有权限角色能看到采购相关菜单
   - 验证无权限角色看不到采购相关菜单

2. **路由保护测试**
   - 无权限用户直接访问 `/purchases` 等路由
   - 验证是否显示无权限页面
   - 验证返回按钮功能正常

3. **API 错误处理测试**
   - 模拟 403 错误响应
   - 验证错误消息正确显示
   - 验证不会错误跳转到登录页

### 后端测试

1. **权限检查测试**
   - 使用不同角色调用采购相关 API
   - 验证有权限角色可以正常访问
   - 验证无权限角色返回 403 错误

2. **边界情况测试**
   - 测试超级管理员权限
   - 测试未登录用户
   - 测试无效角色代码

## 维护说明

### 添加新角色权限

1. **前端** (`frontend/src/lib/roleConfig.js`):
   ```javascript
   const procurementRoles = [
     // ... 现有角色
     'new_role_code',  // 添加新角色
   ]
   ```

2. **后端** (`app/core/security.py`):
   ```python
   procurement_roles = [
       # ... 现有角色
       'new_role_code',  # 添加新角色
   ]
   ```

### 添加新的受保护路由

1. **前端路由** (`frontend/src/App.jsx`):
   ```jsx
   <Route path="/new-route" element={
     <ProcurementProtectedRoute>
       <NewComponent />
     </ProcurementProtectedRoute>
   } />
   ```

2. **后端 API** (`app/api/v1/endpoints/xxx.py`):
   ```python
   @router.get("/new-endpoint")
   def new_endpoint(
       current_user: User = Depends(security.require_procurement_access()),
   ):
       # ...
   ```

## 相关文件清单

### 前端文件
- `frontend/src/lib/roleConfig.js` - 角色配置和权限判断
- `frontend/src/components/layout/Sidebar.jsx` - 侧边栏菜单过滤
- `frontend/src/App.jsx` - 路由保护
- `frontend/src/services/api.js` - API 拦截器
- `frontend/src/utils/errorHandler.js` - 错误处理工具

### 后端文件
- `app/core/security.py` - 权限检查函数
- `app/api/v1/endpoints/purchase.py` - 采购订单 API
- `app/api/v1/endpoints/materials.py` - 物料管理 API
- `app/api/v1/endpoints/kit_rate.py` - 齐套分析 API

## 更新日志

- **2025-01-XX**: 初始实现
  - 完成前端菜单过滤
  - 完成前端路由保护
  - 完成后端 API 权限验证
  - 完成错误处理优化



