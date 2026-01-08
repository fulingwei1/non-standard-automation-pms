# 商务支持模块待开发功能清单

## 检查日期
2025-01-15

## 已完成功能 ✅

### 核心功能
- ✅ 投标管理（项目登记、文件管理、结果跟踪）
- ✅ 合同审核（创建、审批）
- ✅ 合同盖章邮寄（创建、更新）
- ✅ 回款催收（创建、查询）
- ✅ 文件归档（创建、查询）
- ✅ 工作台统计（基础指标）

---

## 待开发功能 ❌

### 1. 工作台功能完善

#### 1.1 待办任务/紧急任务
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 从任务中心（TaskCenter）获取分配给商务支持专员的待办任务
- 筛选紧急任务（priority=URGENT 或 is_urgent=true）
- 筛选今日待办（deadline为今天或已逾期）
- 支持任务类型筛选（合同审核、开票申请、催款跟进、验收跟踪、标书编制、出货审批等）

**API需要**:
```python
GET /business-support/dashboard/todos
- 返回紧急任务列表
- 返回今日待办列表
- 从TaskUnified表查询，task_type包含商务支持相关类型
```

**优先级**: 🔴 高

---

#### 1.2 进行中的合同列表
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 工作台显示进行中的合同卡片
- 显示合同基本信息（项目名称、客户、金额、回款进度）
- 显示支付阶段（签约款、进度款、验收款、质保金）
- 显示发票状态和验收状态

**API需要**:
```python
GET /business-support/dashboard/active-contracts
- 返回进行中的合同列表（status=SIGNED或EXECUTING）
- 包含回款进度、发票状态、验收状态
- 关联查询project_payment_plans获取回款信息
```

**优先级**: 🔴 高

---

#### 1.3 进行中的投标列表
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 工作台显示进行中的投标项目卡片
- 显示投标进度、截止日期倒计时
- 显示标书状态（技术/商务/资质文件就绪情况）

**API需要**:
```python
GET /business-support/dashboard/active-bidding
- 返回进行中的投标列表（status=draft/preparing/submitted）
- 计算截止日期倒计时
- 包含标书文件状态
```

**优先级**: 🔴 高

---

#### 1.4 本月绩效指标
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 工作台右侧显示本月绩效指标
- 新签合同数、回款完成率、开票及时率、文件流转数

**API需要**:
```python
GET /business-support/dashboard/performance
- 返回本月绩效指标
- 新签合同数（本月签订的合同）
- 回款完成率（本月实际回款/计划回款）
- 开票及时率（按时开票数/应开票数）
- 文件流转数（本月处理的文件数）
```

**优先级**: 🟡 中

---

### 2. 订单管理

#### 2.1 销售订单录入
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 创建销售订单
- 关联合同、客户、项目
- 订单明细管理
- 订单状态跟踪

**数据模型需要**:
```python
class SalesOrder(Base, TimestampMixin):
    - order_no: 订单编号
    - contract_id: 合同ID
    - customer_id: 客户ID
    - project_id: 项目ID
    - order_amount: 订单金额
    - order_status: 订单状态
    - project_no_assigned: 是否已分配项目号
    - project_notice_sent: 是否已发项目通知单
```

**API需要**:
```python
POST /business-support/sales-orders - 创建销售订单
GET /business-support/sales-orders - 获取订单列表
PUT /business-support/sales-orders/{id} - 更新订单
POST /business-support/sales-orders/{id}/assign-project - 分配项目号
POST /business-support/sales-orders/{id}/send-notice - 发送项目通知单
```

**优先级**: 🔴 高

---

#### 2.2 项目号分配
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 为订单分配项目号
- 项目号生成规则
- 项目号分配记录

**API需要**:
```python
POST /business-support/sales-orders/{id}/assign-project
- 分配项目号
- 更新project_no_assigned状态
- 记录分配时间
```

**优先级**: 🔴 高

---

#### 2.3 项目通知单
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 生成项目通知单
- 发送通知给相关部门（PMC、生产、采购等）
- 通知单模板管理

**API需要**:
```python
POST /business-support/sales-orders/{id}/send-notice
- 生成项目通知单
- 发送通知
- 记录发送时间
```

**优先级**: 🟡 中

---

### 3. 发货管理

#### 3.1 出货审批
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 创建发货单
- 出货审批流程
- 特殊审批规则（预付款未收、有逾期应收款、超出信用额度）
- 审批记录

**数据模型需要**:
```python
class DeliveryOrder(Base, TimestampMixin):
    - delivery_no: 送货单号
    - order_id: 销售订单ID
    - contract_id: 合同ID
    - customer_id: 客户ID
    - delivery_date: 发货日期
    - delivery_type: 发货方式
    - approval_status: 审批状态
    - special_approval: 是否特殊审批
    - delivery_status: 送货单状态
```

**API需要**:
```python
POST /business-support/delivery-orders - 创建发货单
GET /business-support/delivery-orders - 获取发货单列表
POST /business-support/delivery-orders/{id}/approve - 审批发货单
GET /business-support/delivery-orders/pending-approval - 待审批发货单
```

**优先级**: 🔴 高

---

#### 3.2 送货单管理
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 送货单打印
- 送货单回收
- 送货单归档
- 送货单状态跟踪

**API需要**:
```python
POST /business-support/delivery-orders/{id}/print - 打印送货单
POST /business-support/delivery-orders/{id}/return - 回收送货单
GET /business-support/delivery-orders/{id} - 获取送货单详情
```

**优先级**: 🟡 中

---

### 4. 对账开票

#### 4.1 客户对账单
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 生成客户对账单
- 对账单包含：合同金额、已开票金额、已回款金额、未回款金额
- 对账单导出（PDF/Excel）

**API需要**:
```python
POST /business-support/reconciliation - 生成对账单
GET /business-support/reconciliation/{id} - 获取对账单
GET /business-support/reconciliation/{id}/export - 导出对账单
```

**优先级**: 🟡 中

---

#### 4.2 开票申请
**状态**: ✅ 已实现（2026-01-07）
**说明**: 新增 `invoice_requests` 模型与 `/invoice-requests` API，支持创建、审批（自动生成发票并回写收款计划）、驳回及列表查询，附件使用 JSON 存储。
- 审批通过后自动生成 `Invoice` 记录并把 `project_payment_plans` 状态更新为 `INVOICED`
- 回款更新时，系统自动同步 `invoice_requests.receipt_status`（UNPAID/PARTIAL/PAID）

**优先级**: 🟡 中（仅需持续迭代审批策略）

---

### 5. 客户管理

#### 5.1 客户供应商建档
**状态**: ⚠️ 部分实现
**说明**: 已有Customer表，但可能缺少供应商入驻相关功能

**需要检查**:
- 客户供应商入驻流程
- 入驻资料管理
- 入驻状态跟踪

**优先级**: 🟢 低

---

#### 5.2 客户供应商入驻管理
**状态**: ✅ 已实现（2026-01-07）
**说明**: 新增 `customer_supplier_registrations` 表与 `/customer-registrations` API，覆盖创建、更新、审批/驳回与分页查询，支持上传入驻资料和记录外部同步结果。

**优先级**: 🟢 低（后续根据对接平台扩展同步能力）

---

### 6. 验收管理

#### 6.1 验收单跟踪
**状态**: ✅ 已实现（2025-01-15）
**说明**: 已实现商务支持角度的验收单跟踪功能

**已实现功能**:
- ✅ 验收单状态跟踪（从商务支持角度）
- ✅ 验收条件检查
- ✅ 验收单催签功能
- ✅ 验收报告跟踪
- ✅ 质保期跟踪
- ✅ 跟踪记录明细（记录每次操作历史）

**优先级**: 🟡 中

---

### 7. 报表中心

#### 7.1 销售报表
**状态**: ✅ 已实现（2025-01-15）
**需求**: 
- 销售日报/周报/月报
- 回款统计报表
- 合同执行报表
- 开票统计报表

**API需要**:
```python
GET /business-support/reports/sales-daily - 销售日报
GET /business-support/reports/sales-weekly - 销售周报
GET /business-support/reports/sales-monthly - 销售月报
GET /business-support/reports/payment - 回款统计报表
GET /business-support/reports/contract - 合同执行报表
GET /business-support/reports/invoice - 开票统计报表
```

**优先级**: 🟡 中

---

## 开发优先级建议

### 🔴 高优先级（核心功能）
1. ✅ **待办任务/紧急任务** - 工作台核心功能 - **已完成**
2. ✅ **进行中的合同列表** - 工作台核心功能 - **已完成**
3. ✅ **进行中的投标列表** - 工作台核心功能 - **已完成**
4. ✅ **销售订单管理** - 核心业务流程 - **已完成**
5. ✅ **出货审批** - 核心业务流程 - **已完成**

### 🟡 中优先级（重要功能）
1. **本月绩效指标** - 工作台完善
2. **项目号分配** - 订单管理完善
3. **项目通知单** - 订单管理完善
4. **送货单管理** - 发货管理完善
5. **客户对账单** - 对账开票完善
6. **验收单跟踪** - 验收管理完善
7. **销售报表** - 报表中心

### 🟢 低优先级（辅助功能）
1. **客户供应商入驻管理** - 辅助功能

---

## 实现建议

### 第一阶段：工作台完善
1. ✅ 实现待办任务/紧急任务API（从TaskCenter获取） - **已完成**
2. ✅ 实现进行中的合同列表API - **已完成**
3. ✅ 实现进行中的投标列表API - **已完成**
4. 实现本月绩效指标API

### 第二阶段：订单和发货管理
1. ✅ 创建销售订单数据模型和API - **已完成**
2. ✅ 实现项目号分配功能 - **已完成**
3. ✅ 实现项目通知单功能 - **已完成**
4. ✅ 创建发货单数据模型和API - **已完成**
5. ✅ 实现出货审批流程 - **已完成**

### 第三阶段：对账和报表
1. 实现客户对账单功能
2. 完善开票申请流程
3. 实现各类销售报表

### 第四阶段：辅助功能
1. 实现客户供应商入驻管理
2. 完善验收单跟踪功能

---

## 相关文档

- 设计文档：`claude 设计方案/project-progress-module/docs/BUSINESS_SUPPORT_DESIGN.md`
- 前端页面：`frontend/src/pages/BusinessSupportWorkstation.jsx`
- 任务中心API：`app/api/v1/endpoints/task_center.py`

---

**最后更新**: 2025-01-15
