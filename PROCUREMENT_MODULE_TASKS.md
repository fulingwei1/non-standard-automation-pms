# 采购模块开发任务清单

## 一、已完成功能 ✅

### 1. 采购订单管理
- ✅ 采购订单列表（支持分页、搜索、筛选）
- ✅ 采购订单详情查看
- ✅ 创建采购订单（前端对话框 + 后端API）
- ✅ 编辑采购订单（仅草稿状态）
- ✅ 删除采购订单（仅草稿状态）
- ✅ 提交采购订单
- ✅ 审批采购订单（通过/驳回）
- ✅ 导出采购订单（CSV格式）
- ✅ 订单状态管理（DRAFT → SUBMITTED → APPROVED → ORDERED）
- ✅ 订单明细管理（添加、删除、编辑）
- ✅ 自动计算金额（总金额、税额、含税金额）

### 2. 收货管理
- ✅ 收货单列表（后端API已实现）
- ✅ 创建收货单（后端API已实现）
- ✅ 收货单详情（后端API已实现）
- ✅ 自动更新订单明细收货状态
- ✅ 收货单编号自动生成（GR-yymmdd-xxx）

### 3. 从BOM生成采购需求
- ✅ 后端API：`POST /api/v1/bom/{bom_id}/generate-pr`
- ✅ 按供应商分组物料
- ✅ 计算未采购数量

### 4. 采购工程师工作台
- ✅ 工作台页面（ProcurementEngineerWorkstation）
- ✅ 统计数据展示
- ✅ 待办任务列表
- ✅ 快捷操作
- ✅ 演示账号支持（mock数据）

### 5. 基础功能
- ✅ 供应商管理页面（SupplierManagement.jsx）
- ✅ 到货跟踪页面（ArrivalTrackingList.jsx）
- ✅ 到货管理页面（ArrivalManagement.jsx）
- ✅ 缺料预警页面（ShortageAlert.jsx）
- ✅ 缺料管理页面（ShortageManagement.jsx）

### 6. 自动下单联动
- ✅ BOM一键生成采购申请（`POST /api/v1/bom/{bom_id}/generate-pr?create_requests=true`）
- ✅ 采购申请审批通过后自动创建采购订单（`PUT /purchase-orders/requests/{id}/approve`）
- ✅ 采购申请详情展示已生成的采购订单，并支持手动重新触发（`POST /purchase-orders/requests/{id}/generate-orders`）

---

## 二、待开发功能 ⏳

### 1. 采购申请与审批流程 🔴 高优先级

#### 1.1 采购申请（Purchase Request）
- ✅ **前端页面**：采购申请列表页面（API联通 + 供应商显示）
- ✅ **前端页面**：创建采购申请页面（选择供应商、物料明细）
- ✅ **前端页面**：采购申请详情页面（审批、自动下单状态、生成的采购订单）
- ✅ **后端API**：采购申请CRUD接口
  - `GET /api/v1/purchase-requests` - 列表
  - `POST /api/v1/purchase-requests` - 创建
  - `GET /api/v1/purchase-requests/{id}` - 详情
  - `PUT /api/v1/purchase-requests/{id}` - 更新
  - `DELETE /api/v1/purchase-requests/{id}` - 删除
- ✅ **后端API**：采购申请提交接口
  - `PUT /api/v1/purchase-requests/{id}/submit` - 提交审批
- ✅ **后端API**：采购申请审批接口（通过后自动生成采购订单）
  - `PUT /api/v1/purchase-requests/{id}/approve` - 审批（通过/驳回）
- ✅ **数据模型**：PurchaseRequest 模型（新增来源、供应商、自动下单状态）
- ✅ **业务规则**：
  - 从BOM生成采购申请（自动写入来源、供应商、BOM行）
  - 采购申请审批通过后自动创建采购订单并回写已购数量
  - 支持手动重新触发订单生成（`/generate-orders`）

#### 1.2 采购申请审批流程
- ⏳ 审批流程配置
- ⏳ 审批历史记录
- ⏳ 审批通知

### 2. 从BOM生成采购订单 🔴 高优先级

#### 2.1 前端功能
- ⏳ **前端页面**：从BOM生成采购订单页面（当前仅支持生成采购申请数据，待联动PR流转）
- ⏳ **前端功能**：选择BOM版本
- ⏳ **前端功能**：选择供应商
- ⏳ **前端功能**：物料选择和编辑
- ⏳ **前端功能**：批量创建采购订单 / 批量生成采购申请并自动下单
- ⏳ **前端功能**：预览采购订单

#### 2.2 后端功能
- ✅ **后端API**：`POST /api/v1/bom/{bom_id}/generate-pr?create_requests=true` - 从BOM按供应商批量创建采购申请
- ⏳ **后端API**：`POST /api/v1/purchase-orders/from-bom` - 直接从BOM批量创建订单（可选）
- ⏳ **业务规则**：
  - 按供应商分组物料
  - 自动填充物料信息
  - 支持价格调整
  - 支持数量调整

### 3. 采购订单功能增强 🟡 中优先级

#### 3.1 批量操作
- ⏳ 批量创建采购订单
- ⏳ 批量审批
- ⏳ 批量提交
- ⏳ 批量导出

#### 3.2 订单状态流转
- ⏳ 订单状态历史记录
- ⏳ 状态流转日志
- ⏳ 状态变更通知

#### 3.3 订单取消
- ⏳ 取消订单功能（后端API）
- ⏳ 取消原因记录
- ⏳ 取消审批流程

### 4. 收货管理功能完善 🟡 中优先级

#### 4.1 前端页面完善
- ⏳ **前端页面**：收货单列表页面（已有ArrivalManagement.jsx，需完善）
- ⏳ **前端页面**：创建收货单页面（已有ArrivalNew.jsx，需完善）
- ⏳ **前端页面**：收货单详情页面（已有ArrivalDetail.jsx，需完善）
- ⏳ **前端功能**：收货单状态管理
- ⏳ **前端功能**：收货单质检流程

#### 4.2 质检管理
- ⏳ 质检单创建
- ⏳ 质检结果记录
- ⏳ 不合格品处理
- ⏳ 质检报告生成

#### 4.3 入库管理
- ⏳ 入库单创建（与收货单关联）
- ⏳ 入库数量确认
- ⏳ 入库位置管理

### 5. 供应商管理功能增强 🟡 中优先级

#### 5.1 供应商评价
- ⏳ 供应商评分系统
- ⏳ 供应商评价记录
- ⏳ 供应商等级管理
- ⏳ 供应商黑名单管理

#### 5.2 供应商价格管理
- ⏳ 物料价格维护
- ⏳ 历史价格记录
- ⏳ 价格对比分析
- ⏳ 价格预警

#### 5.3 供应商交期管理
- ⏳ 交期记录
- ⏳ 交期统计分析
- ⏳ 交期预警
- ⏳ 供应商交期评估

### 6. 缺料管理功能完善 🟡 中优先级

#### 6.1 缺料预警增强
- ⏳ 缺料预警规则配置
- ⏳ 缺料预警自动触发
- ⏳ 缺料预警通知
- ⏳ 缺料预警处理流程

#### 6.2 缺料分析
- ⏳ 缺料原因分析
- ⏳ 缺料影响分析
- ⏳ 缺料趋势分析

### 7. 齐套率计算和展示 🟢 低优先级

#### 7.1 齐套率计算
- ⏳ 项目齐套率计算
- ⏳ 机台齐套率计算
- ⏳ 物料齐套率计算
- ⏳ 齐套率实时更新

#### 7.2 齐套率展示
- ⏳ 齐套率看板（已有KitRateBoard.jsx，需完善）
- ⏳ 齐套率报表
- ⏳ 齐套率趋势分析

### 8. 采购报表和分析 🟢 低优先级

#### 8.1 采购报表
- ⏳ 采购订单统计报表
- ⏳ 供应商采购报表
- ⏳ 项目采购报表
- ⏳ 物料采购报表
- ⏳ 采购成本分析报表

#### 8.2 采购分析
- ⏳ 采购趋势分析
- ⏳ 供应商绩效分析
- ⏳ 采购成本分析
- ⏳ 交期分析

### 9. 价格管理 🟢 低优先级

#### 9.1 价格维护
- ⏳ 物料标准价格维护
- ⏳ 供应商报价管理
- ⏳ 价格审批流程

#### 9.2 价格分析
- ⏳ 价格对比分析
- ⏳ 价格趋势分析
- ⏳ 价格预警

### 10. 其他功能 🟢 低优先级

#### 10.1 采购合同管理
- ⏳ 采购合同创建
- ⏳ 合同模板管理
- ⏳ 合同审批流程
- ⏳ 合同执行跟踪

#### 10.2 采购发票管理
- ⏳ 发票录入
- ⏳ 发票与订单关联
- ⏳ 发票审批流程

#### 10.3 采购退货管理
- ⏳ 退货申请
- ⏳ 退货审批
- ⏳ 退货处理

---

## 三、前端页面检查清单

### 已存在页面 ✅
- ✅ `PurchaseOrders.jsx` - 采购订单列表（已完善）
- ✅ `PurchaseOrderDetail.jsx` - 采购订单详情
- ✅ `ProcurementEngineerWorkstation.jsx` - 采购工程师工作台（已修复）
- ✅ `SupplierManagement.jsx` - 供应商管理
- ✅ `SupplierManagementData.jsx` - 供应商主数据管理
- ✅ `ArrivalTrackingList.jsx` - 到货跟踪列表
- ✅ `ArrivalManagement.jsx` - 到货管理
- ✅ `ArrivalNew.jsx` - 新建到货
- ✅ `ArrivalDetail.jsx` - 到货详情
- ✅ `ShortageAlert.jsx` - 缺料预警
- ✅ `ShortageManagement.jsx` - 缺料管理
- ✅ `ShortageManagementBoard.jsx` - 缺料管理看板
- ✅ `KitCheck.jsx` - 齐套检查
- ✅ `KitRateBoard.jsx` - 齐套率看板
- ✅ `MaterialList.jsx` - 物料列表
- ✅ `MaterialAnalysis.jsx` - 物料分析
- ✅ `MaterialDemandSummary.jsx` - 物料需求汇总
- ✅ `BOMManagement.jsx` - BOM管理

### 缺失页面 ⏳
- ⏳ `PurchaseRequestList.jsx` - 采购申请列表
- ⏳ `PurchaseRequestNew.jsx` - 新建采购申请
- ⏳ `PurchaseRequestDetail.jsx` - 采购申请详情
- ⏳ `PurchaseOrderFromBOM.jsx` - 从BOM生成采购订单
- ⏳ `SupplierEvaluation.jsx` - 供应商评价
- ⏳ `SupplierPriceManagement.jsx` - 供应商价格管理
- ⏳ `ProcurementReports.jsx` - 采购报表
- ⏳ `ProcurementAnalytics.jsx` - 采购分析

---

## 四、后端API检查清单

### 已实现API ✅
- ✅ 采购订单CRUD（`/api/v1/purchase-orders`）
- ✅ 采购订单提交（`PUT /api/v1/purchase-orders/{id}/submit`）
- ✅ 采购订单审批（`PUT /api/v1/purchase-orders/{id}/approve`）
- ✅ 采购订单明细（`GET /api/v1/purchase-orders/{id}/items`）
- ✅ 收货单CRUD（`/api/v1/purchase-orders/goods-receipts`）
- ✅ 从BOM生成采购需求（`POST /api/v1/bom/{bom_id}/generate-pr`）

### 缺失API ⏳
- ⏳ 采购申请CRUD（`/api/v1/purchase-requests`）
- ⏳ 采购申请提交（`PUT /api/v1/purchase-requests/{id}/submit`）
- ⏳ 采购申请审批（`PUT /api/v1/purchase-requests/{id}/approve`）
- ⏳ 从BOM批量创建采购订单（`POST /api/v1/purchase-orders/from-bom`）
- ⏳ 采购订单取消（`PUT /api/v1/purchase-orders/{id}/cancel`）
- ⏳ 采购订单状态历史（`GET /api/v1/purchase-orders/{id}/status-history`）
- ⏳ 供应商评价（`POST /api/v1/suppliers/{id}/evaluation`）
- ⏳ 供应商价格管理（`/api/v1/supplier-prices`）
- ⏳ 采购报表API（`/api/v1/procurement/reports`）
- ⏳ 采购分析API（`/api/v1/procurement/analytics`）

---

## 五、数据模型检查清单

### 已存在模型 ✅
- ✅ `PurchaseOrder` - 采购订单
- ✅ `PurchaseOrderItem` - 采购订单明细
- ✅ `GoodsReceipt` - 收货单
- ✅ `GoodsReceiptItem` - 收货单明细
- ✅ `Material` - 物料
- ✅ `Supplier` - 供应商
- ✅ `BomHeader` - BOM头
- ✅ `BomItem` - BOM明细

### 缺失模型 ⏳
- ⏳ `PurchaseRequest` - 采购申请
- ⏳ `PurchaseRequestItem` - 采购申请明细
- ⏳ `PurchaseOrderStatusHistory` - 采购订单状态历史
- ⏳ `SupplierEvaluation` - 供应商评价
- ⏳ `SupplierPrice` - 供应商价格
- ⏳ `InspectionOrder` - 质检单
- ⏳ `InspectionItem` - 质检明细

---

## 六、优先级建议

### P0 - 核心功能（必须实现）
1. **采购申请与审批流程** - 完整的采购申请→审批→订单流程
2. **从BOM生成采购订单** - 提高采购效率的核心功能
3. **收货管理前端完善** - 完善收货单的创建和管理功能

### P1 - 重要功能（建议实现）
1. **采购订单批量操作** - 提高操作效率
2. **订单状态历史记录** - 审计和追溯
3. **供应商评价系统** - 供应商管理的重要功能

### P2 - 增强功能（可选实现）
1. **采购报表和分析** - 数据分析和决策支持
2. **价格管理** - 成本控制
3. **齐套率计算和展示** - 项目进度跟踪

---

## 七、开发建议

### 1. 开发顺序
1. **第一阶段**：采购申请与审批流程（P0）
2. **第二阶段**：从BOM生成采购订单（P0）
3. **第三阶段**：收货管理前端完善（P0）
4. **第四阶段**：批量操作和状态历史（P1）
5. **第五阶段**：供应商评价和报表（P1-P2）

### 2. 技术要点
- 前端使用 React + shadcn/ui 组件库
- 后端使用 FastAPI + SQLAlchemy
- 演示账号支持 mock 数据
- 权限控制使用 `require_procurement_access()`
- 状态流转需要严格验证

### 3. 注意事项
- 所有金额计算使用 Decimal 类型
- 订单编号自动生成（PO-yymmdd-xxx）
- 状态流转需要记录历史
- 演示账号需要完整的 mock 数据支持

---

## 八、相关文档

- `采购与物料管理模块_详细设计文档.md` - 详细设计文档
- `PURCHASE_ORDER_API_SUMMARY.md` - API实现总结
- `app/api/v1/endpoints/purchase.py` - 采购API实现
- `app/models/purchase.py` - 采购数据模型
- `app/schemas/purchase.py` - 采购Schema定义











