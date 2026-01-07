# 权限控制检查清单

## 概述

本文档提供了完整的权限控制检查清单，确保系统的所有敏感功能都得到适当的权限保护。

## 前端权限控制检查

### 路由保护 ✅

- [x] `/purchases` - 采购订单列表
- [x] `/purchases/:id` - 采购订单详情
- [x] `/materials` - 物料跟踪
- [x] `/material-analysis` - 物料分析
- [x] `/finance-manager-dashboard` - 财务经理工作台
- [x] `/payments` - 付款管理
- [x] `/invoices` - 发票管理
- [x] `/production-dashboard` - 生产经理工作台
- [x] `/manufacturing-director-dashboard` - 制造总监工作台

### 菜单权限控制 ✅

- [x] 采购订单菜单 - 根据角色显示/隐藏
- [x] 齐套分析菜单 - 根据角色显示/隐藏
- [ ] 财务管理菜单 - 待实现
- [ ] 生产管理菜单 - 待实现

### 权限判断函数 ✅

- [x] `hasProcurementAccess()` - 采购权限
- [x] `hasFinanceAccess()` - 财务权限
- [x] `hasProductionAccess()` - 生产权限

### 保护组件 ✅

- [x] `ProtectedRoute` - 通用保护组件
- [x] `ProcurementProtectedRoute` - 采购保护组件
- [x] `FinanceProtectedRoute` - 财务保护组件
- [x] `ProductionProtectedRoute` - 生产保护组件

## 后端权限控制检查

### 采购模块 API ✅

- [x] `GET /purchase-orders/` - 获取采购订单列表
- [x] `GET /purchase-orders/{order_id}` - 获取采购订单详情
- [x] `POST /purchase-orders/` - 创建采购订单
- [x] `PUT /purchase-orders/{order_id}` - 更新采购订单
- [x] `PUT /purchase-orders/{order_id}/approve` - 审批采购订单
- [x] `GET /purchase-orders/{order_id}/items` - 获取订单明细
- [x] `GET /purchase-orders/goods-receipts/` - 获取收货记录列表
- [x] `POST /purchase-orders/goods-receipts/` - 创建收货单
- [x] `GET /purchase-orders/goods-receipts/{receipt_id}` - 获取收货单详情
- [x] `GET /purchase-orders/goods-receipts/{receipt_id}/items` - 获取收货单明细
- [x] `PUT /purchase-orders/goods-receipts/{receipt_id}/receive` - 更新收货单状态
- [x] `PUT /purchase-orders/purchase-order-items/{item_id}/receive` - 更新订单明细收货状态

### 物料管理 API ✅

- [x] `GET /materials/` - 获取物料列表
- [x] `GET /materials/{material_id}` - 获取物料详情
- [x] `POST /materials/` - 创建新物料
- [x] `PUT /materials/{material_id}` - 更新物料信息
- [x] `GET /materials/categories/` - 获取物料分类列表
- [x] `GET /materials/{material_id}/suppliers` - 获取物料供应商列表

### 齐套分析 API ✅

- [x] `GET /projects/{project_id}/kit-rate` - 计算项目齐套率
- [x] `GET /machines/{machine_id}/kit-rate` - 计算机台齐套率
- [x] `GET /machines/{machine_id}/material-status` - 获取机台物料状态
- [x] `GET /projects/{project_id}/material-status` - 获取项目物料状态
- [x] `GET /projects/{project_id}/critical-shortage` - 获取项目关键物料缺口
- [x] `GET /kit-rate/dashboard` - 获取齐套看板数据

### 财务模块 API ⚠️

- [ ] `GET /sales/invoices` - 获取发票列表（需要财务权限）
- [ ] `POST /sales/invoices` - 创建发票（需要财务权限）
- [ ] `POST /sales/invoices/{invoice_id}/issue` - 开具发票（需要财务权限）
- [ ] `GET /sales/payments` - 获取付款列表（需要财务权限）
- [ ] `POST /sales/payments` - 创建付款（需要财务权限）
- [ ] `GET /outsourcing/outsourcing-payments` - 获取外协付款列表（需要财务权限）
- [ ] `POST /outsourcing/outsourcing-payments` - 创建外协付款（需要财务权限）

### 生产模块 API ⚠️

- [ ] `GET /production/dashboard` - 生产驾驶舱（需要生产权限）
- [ ] `GET /production-plans` - 获取生产计划列表（需要生产权限）
- [ ] `POST /production-plans` - 创建生产计划（需要生产权限）
- [ ] `GET /work-orders` - 获取工单列表（需要生产权限）
- [ ] `POST /work-orders` - 创建工单（需要生产权限）
- [ ] `GET /workshops` - 获取车间列表（需要生产权限）
- [ ] `POST /workshops` - 创建车间（需要生产权限）

## 权限函数检查

### 前端权限函数 ✅

- [x] `hasProcurementAccess(roleCode)` - 采购权限
- [x] `hasFinanceAccess(roleCode)` - 财务权限
- [x] `hasProductionAccess(roleCode)` - 生产权限

### 后端权限函数 ✅

- [x] `has_procurement_access(user)` - 采购权限
- [x] `require_procurement_access()` - 采购权限依赖
- [x] `has_finance_access(user)` - 财务权限
- [x] `require_finance_access()` - 财务权限依赖
- [x] `has_production_access(user)` - 生产权限
- [x] `require_production_access()` - 生产权限依赖

## 错误处理检查

### 前端错误处理 ✅

- [x] API 拦截器区分 401 和 403 错误
- [x] `isPermissionError()` 函数
- [x] `handleApiError()` 支持权限错误回调
- [ ] 页面组件权限错误处理（待完成）

### 后端错误处理 ✅

- [x] 403 错误返回明确的错误消息
- [x] 权限检查函数统一实现
- [x] 错误消息中文化

## 测试检查清单

### 功能测试

- [ ] 有权限用户能正常访问页面
- [ ] 有权限用户能正常调用 API
- [ ] 无权限用户看到无权限提示
- [ ] 无权限用户无法看到菜单
- [ ] 直接访问 URL 时权限检查生效
- [ ] API 调用时权限检查生效

### 边界测试

- [ ] 未登录用户访问受保护路由
- [ ] 无效 Token 访问
- [ ] 角色代码大小写不敏感
- [ ] 超级管理员权限验证
- [ ] 多角色用户权限验证

### 集成测试

- [ ] 前后端权限规则一致性
- [ ] 菜单显示与路由保护一致性
- [ ] API 权限与路由权限一致性
- [ ] 错误处理完整性

## 待完成工作优先级

### P0 - 立即完成

1. **财务模块后端权限**
   - [ ] 为发票 API 添加财务权限检查
   - [ ] 为付款 API 添加财务权限检查
   - [ ] 为外协付款 API 添加财务权限检查

2. **生产模块后端权限**
   - [ ] 为生产计划 API 添加生产权限检查
   - [ ] 为工单 API 添加生产权限检查
   - [ ] 为车间 API 添加生产权限检查

### P1 - 近期完成

3. **菜单权限控制扩展**
   - [ ] 财务相关菜单根据角色显示/隐藏
   - [ ] 生产相关菜单根据角色显示/隐藏

4. **页面错误处理**
   - [ ] 所有页面添加权限错误处理
   - [ ] 统一的错误提示组件

### P2 - 后续优化

5. **权限管理界面**
   - [ ] 角色权限配置界面
   - [ ] 权限分配界面

6. **数据权限控制**
   - [ ] 项目级数据权限
   - [ ] 部门级数据权限

## 权限规则总结

### 采购权限角色

```
procurement_engineer, procurement_manager, procurement, buyer,
pmc, production_manager, manufacturing_director,
gm, chairman, admin, super_admin, pm
```

### 财务权限角色

```
finance_manager, finance,
gm, chairman, admin, super_admin,
business_support
```

### 生产权限角色

```
production_manager, manufacturing_director, pmc,
assembler, assembler_mechanic, assembler_electrician,
gm, chairman, admin, super_admin
```

## 代码质量检查

### 代码规范

- [x] 函数命名清晰
- [x] 注释完整
- [x] 代码复用
- [x] 错误处理统一

### 文档完善

- [x] 实现文档
- [x] API 文档
- [x] 使用指南
- [x] 检查清单

## 更新记录

- **2025-01-XX**: 创建检查清单
- **2025-01-XX**: 完成采购模块权限控制
- **2025-01-XX**: 完成通用权限保护组件系统
- **2025-01-XX**: 添加财务和生产模块权限函数



