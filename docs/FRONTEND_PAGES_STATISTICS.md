# 前端页面详细统计文档

## 概述

本文档统计了系统中所有前端页面的实现情况，重点关注采购和物料管理相关页面的权限控制和 API 集成状态。

## 页面分类统计

### 总页面数：88 个

### 按功能模块分类

#### 1. 采购与物料管理模块（需要权限控制）

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `PurchaseOrders.jsx` | `/purchases` | 采购权限 | ❌ 待集成 | ⚠️ 使用 Mock 数据 |
| `PurchaseOrderDetail.jsx` | `/purchases/:id` | 采购权限 | ❌ 待集成 | ⚠️ 使用 Mock 数据 |
| `MaterialTracking.jsx` | `/materials` | 采购权限 | ❌ 待集成 | ⚠️ 使用 Mock 数据 |
| `MaterialAnalysis.jsx` | `/material-analysis` | 采购权限 | ❌ 待集成 | ⚠️ 使用 Mock 数据 |
| `ProcurementEngineerWorkstation.jsx` | `/procurement-dashboard` | 采购权限 | ❌ 待集成 | ⚠️ 使用 Mock 数据 |
| `ProcurementManagerDashboard.jsx` | `/procurement-manager-dashboard` | 采购权限 | ❌ 待集成 | ⚠️ 使用 Mock 数据 |

**状态说明**：
- ✅ 已完成
- ⚠️ 部分完成（使用 Mock 数据）
- ❌ 未完成
- 🔄 进行中

#### 2. 项目管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `ProjectList.jsx` | `/projects` | 项目权限 | ✅ 已集成 | ✅ |
| `ProjectDetail.jsx` | `/projects/:id` | 项目权限 | ✅ 已集成 | ✅ |
| `ProjectBoard.jsx` | `/board` | 项目权限 | ✅ 已集成 | ✅ |
| `ScheduleBoard.jsx` | `/schedule` | 项目权限 | ✅ 已集成 | ✅ |
| `TaskCenter.jsx` | `/tasks` | 项目权限 | ✅ 已集成 | ✅ |

#### 3. 生产管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `ProductionManagerDashboard.jsx` | `/production-dashboard` | 生产权限 | ⚠️ 部分集成 | ⚠️ |
| `ManufacturingDirectorDashboard.jsx` | `/manufacturing-director-dashboard` | 生产权限 | ⚠️ 部分集成 | ⚠️ |
| `AssemblerTaskCenter.jsx` | `/assembly-tasks` | 装配权限 | ⚠️ 部分集成 | ⚠️ |

#### 4. 销售管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `SalesWorkstation.jsx` | `/sales-dashboard` | 销售权限 | ✅ 已集成 | ✅ |
| `SalesDirectorWorkstation.jsx` | `/sales-director-dashboard` | 销售权限 | ✅ 已集成 | ✅ |
| `SalesManagerWorkstation.jsx` | `/sales-manager-dashboard` | 销售权限 | ✅ 已集成 | ✅ |
| `CustomerList.jsx` | `/customers` | 销售权限 | ✅ 已集成 | ✅ |
| `OpportunityBoard.jsx` | `/opportunities` | 销售权限 | ✅ 已集成 | ✅ |
| `ContractList.jsx` | `/contracts` | 销售权限 | ✅ 已集成 | ✅ |
| `ContractDetail.jsx` | `/contracts/:id` | 销售权限 | ✅ 已集成 | ✅ |
| `QuotationList.jsx` | `/quotations` | 销售权限 | ✅ 已集成 | ✅ |
| `PaymentManagement.jsx` | `/payments` | 销售权限 | ✅ 已集成 | ✅ |
| `InvoiceManagement.jsx` | `/invoices` | 销售权限 | ✅ 已集成 | ✅ |

#### 5. 售前管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `PresalesWorkstation.jsx` | `/presales-dashboard` | 售前权限 | ✅ 已集成 | ✅ |
| `PresalesManagerWorkstation.jsx` | `/presales-manager-dashboard` | 售前权限 | ✅ 已集成 | ✅ |
| `PresalesTasks.jsx` | `/presales-tasks` | 售前权限 | ✅ 已集成 | ✅ |
| `SolutionList.jsx` | `/solutions` | 售前权限 | ✅ 已集成 | ✅ |
| `SolutionDetail.jsx` | `/solutions/:id` | 售前权限 | ✅ 已集成 | ✅ |
| `BiddingCenter.jsx` | `/bidding` | 售前权限 | ✅ 已集成 | ✅ |
| `BiddingDetail.jsx` | `/bidding/:id` | 售前权限 | ✅ 已集成 | ✅ |

#### 6. 质量验收模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `Acceptance.jsx` | `/acceptance` | 质量权限 | ⚠️ 部分集成 | ⚠️ |
| `ApprovalCenter.jsx` | `/approvals` | 审批权限 | ⚠️ 部分集成 | ⚠️ |
| `IssueManagement.jsx` | `/issues` | 问题权限 | ⚠️ 部分集成 | ⚠️ |

#### 7. 预警与异常管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `AlertCenter.jsx` | `/alerts` | 预警权限 | ✅ 已集成 | ✅ |
| `AlertDetail.jsx` | `/alerts/:id` | 预警权限 | ✅ 已集成 | ✅ |
| `AlertRuleConfig.jsx` | `/alert-rules` | 预警权限 | ✅ 已集成 | ✅ |

#### 8. 管理层工作台

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `ChairmanWorkstation.jsx` | `/chairman-dashboard` | 董事长权限 | ✅ 已集成 | ✅ |
| `GeneralManagerWorkstation.jsx` | `/gm-dashboard` | 总经理权限 | ✅ 已集成 | ✅ |
| `AdminDashboard.jsx` | `/admin-dashboard` | 管理员权限 | ✅ 已集成 | ✅ |

#### 9. 财务管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `FinanceManagerDashboard.jsx` | `/finance-manager-dashboard` | 财务权限 | ⚠️ 部分集成 | ⚠️ |

#### 10. 人事管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `HRManagerDashboard.jsx` | `/hr-manager-dashboard` | 人事权限 | ⚠️ 部分集成 | ⚠️ |

#### 11. 行政管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `AdministrativeManagerWorkstation.jsx` | `/administrative-dashboard` | 行政权限 | ⚠️ 部分集成 | ⚠️ |
| `OfficeSuppliesManagement.jsx` | `/office-supplies` | 行政权限 | ⚠️ 部分集成 | ⚠️ |
| `MeetingManagement.jsx` | `/meetings` | 行政权限 | ⚠️ 部分集成 | ⚠️ |
| `VehicleManagement.jsx` | `/vehicles` | 行政权限 | ⚠️ 部分集成 | ⚠️ |
| `FixedAssetsManagement.jsx` | `/fixed-assets` | 行政权限 | ⚠️ 部分集成 | ⚠️ |

#### 12. 客服管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `CustomerServiceDashboard.jsx` | `/customer-service-dashboard` | 客服权限 | ✅ 已集成 | ✅ |

#### 13. 个人中心模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `Dashboard.jsx` | `/` | 通用 | ✅ 已集成 | ✅ |
| `NotificationCenter.jsx` | `/notifications` | 通用 | ✅ 已集成 | ✅ |
| `Timesheet.jsx` | `/timesheet` | 通用 | ✅ 已集成 | ✅ |
| `Settings.jsx` | `/settings` | 通用 | ✅ 已集成 | ✅ |
| `PunchIn.jsx` | `/punch-in` | 通用 | ⚠️ 部分集成 | ⚠️ |

#### 14. 系统管理模块

| 页面文件 | 路由路径 | 权限要求 | API 集成 | 状态 |
|---------|---------|---------|---------|------|
| `UserManagement.jsx` | `/users` | 管理员权限 | ✅ 已集成 | ✅ |
| `RoleManagement.jsx` | `/roles` | 管理员权限 | ✅ 已集成 | ✅ |
| `DepartmentManagement.jsx` | `/departments` | 管理员权限 | ✅ 已集成 | ✅ |
| `SupplierManagement.jsx` | `/suppliers` | 供应商权限 | ✅ 已集成 | ✅ |

## 采购与物料管理页面详细分析

### 1. PurchaseOrders.jsx - 采购订单列表页

**当前状态**：
- ✅ 路由保护：已添加 `ProcurementProtectedRoute`
- ❌ API 集成：使用 Mock 数据
- ⚠️ 错误处理：需要添加权限错误处理

**需要完成的工作**：
1. 集成 `purchaseApi.orders.list()` API
2. 集成 `purchaseApi.orders.create()` API
3. 添加权限错误处理
4. 添加加载状态和错误提示

**建议实现**：
```javascript
import { purchaseApi } from '../services/api'
import { useApi } from '../hooks/useApi'
import { isPermissionError } from '../utils/errorHandler'

// 在组件中使用
const { execute: fetchOrders, loading, error } = useApi(
  (params) => purchaseApi.orders.list(params),
  {
    onPermissionError: () => {
      // 显示权限错误提示
      toast.error('您没有权限访问采购订单')
    }
  }
)
```

### 2. PurchaseOrderDetail.jsx - 采购订单详情页

**当前状态**：
- ✅ 路由保护：已添加 `ProcurementProtectedRoute`
- ❌ API 集成：使用 Mock 数据
- ⚠️ 错误处理：需要添加权限错误处理

**需要完成的工作**：
1. 集成 `purchaseApi.orders.get(id)` API
2. 集成 `purchaseApi.orders.update(id, data)` API
3. 集成 `purchaseApi.orders.approve(id, data)` API
4. 集成 `purchaseApi.receipts` 相关 API

### 3. MaterialTracking.jsx - 物料跟踪页

**当前状态**：
- ✅ 路由保护：已添加 `ProcurementProtectedRoute`
- ❌ API 集成：使用 Mock 数据
- ⚠️ 错误处理：需要添加权限错误处理

**需要完成的工作**：
1. 集成 `materialApi.list()` API
2. 集成齐套分析相关 API（`kit_rate`）
3. 添加物料状态实时更新

### 4. MaterialAnalysis.jsx - 物料分析页

**当前状态**：
- ✅ 路由保护：已添加 `ProcurementProtectedRoute`
- ❌ API 集成：使用 Mock 数据
- ⚠️ 错误处理：需要添加权限错误处理

**需要完成的工作**：
1. 集成齐套分析 API
2. 集成物料需求分析 API
3. 添加图表数据可视化

### 5. ProcurementEngineerWorkstation.jsx - 采购工程师工作台

**当前状态**：
- ✅ 路由保护：已添加（通过角色路由映射）
- ❌ API 集成：使用 Mock 数据
- ⚠️ 错误处理：需要添加权限错误处理

**需要完成的工作**：
1. 集成采购订单统计 API
2. 集成物料跟踪统计 API
3. 集成待办事项 API

### 6. ProcurementManagerDashboard.jsx - 采购经理工作台

**当前状态**：
- ✅ 路由保护：已添加（通过角色路由映射）
- ❌ API 集成：使用 Mock 数据
- ⚠️ 错误处理：需要添加权限错误处理

**需要完成的工作**：
1. 集成采购管理统计 API
2. 集成供应商管理 API
3. 集成审批流程 API

## API 集成优先级

### 高优先级（核心功能）

1. **采购订单管理**
   - `purchaseApi.orders.list()` - 订单列表
   - `purchaseApi.orders.get(id)` - 订单详情
   - `purchaseApi.orders.create()` - 创建订单
   - `purchaseApi.orders.update()` - 更新订单

2. **物料管理**
   - `materialApi.list()` - 物料列表
   - `materialApi.get(id)` - 物料详情
   - 齐套分析 API

### 中优先级（增强功能）

3. **收货管理**
   - `purchaseApi.receipts.list()` - 收货单列表
   - `purchaseApi.receipts.create()` - 创建收货单

4. **物料分析**
   - 齐套率计算 API
   - 物料状态查询 API

### 低优先级（辅助功能）

5. **统计报表**
   - 采购统计 API
   - 物料统计 API

## 权限控制检查清单

### 前端路由保护

- [x] `/purchases` - 已保护
- [x] `/purchases/:id` - 已保护
- [x] `/materials` - 已保护
- [x] `/material-analysis` - 已保护
- [x] `/procurement-dashboard` - 已保护（角色路由）
- [x] `/procurement-manager-dashboard` - 已保护（角色路由）

### 菜单显示控制

- [x] 侧边栏菜单根据角色动态显示/隐藏
- [x] 无权限角色看不到采购相关菜单

### API 错误处理

- [x] API 拦截器区分 401 和 403 错误
- [ ] 页面组件添加权限错误处理（待完成）
- [ ] 权限错误时显示友好提示（待完成）

## 待完成工作清单

### 立即需要完成

1. **API 集成**
   - [ ] 为所有采购相关页面集成真实 API
   - [ ] 替换所有 Mock 数据
   - [ ] 添加 API 调用错误处理

2. **权限错误处理**
   - [ ] 在页面组件中添加权限错误处理
   - [ ] 显示友好的权限错误提示
   - [ ] 处理 API 返回的 403 错误

3. **加载状态**
   - [ ] 添加数据加载状态
   - [ ] 添加骨架屏或加载动画
   - [ ] 优化用户体验

### 后续优化

4. **性能优化**
   - [ ] 添加数据缓存
   - [ ] 优化 API 调用频率
   - [ ] 添加分页和虚拟滚动

5. **功能增强**
   - [ ] 添加数据导出功能
   - [ ] 添加批量操作
   - [ ] 添加高级筛选

## 统计汇总

### 页面完成度

- **总页面数**：88 个
- **已完成**：45 个（51%）
- **部分完成**：38 个（43%）
- **未完成**：5 个（6%）

### 采购模块完成度

- **总页面数**：6 个
- **路由保护**：6/6（100%）
- **API 集成**：0/6（0%）
- **错误处理**：0/6（0%）

### 权限控制完成度

- **前端路由保护**：✅ 100%
- **菜单显示控制**：✅ 100%
- **后端 API 保护**：✅ 100%
- **页面错误处理**：⚠️ 0%（待完成）

## 下一步行动

1. **立即行动**：为采购相关页面集成真实 API
2. **短期目标**：完成所有页面的权限错误处理
3. **中期目标**：优化用户体验和性能
4. **长期目标**：完善所有功能模块

## 更新日志

- **2025-01-XX**: 创建页面统计文档
- **2025-01-XX**: 完成权限控制实现
- **2025-01-XX**: 待完成 API 集成和错误处理



