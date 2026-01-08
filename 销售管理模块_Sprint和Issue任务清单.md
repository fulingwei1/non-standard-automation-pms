# 销售管理模块 Sprint 和 Issue 任务清单

> **文档版本**: v1.0  
> **创建日期**: 2026-01-15  
> **基于**: 销售管理模块完成情况评估 + 缺失功能清单  
> **估算单位**: Story Point (SP)，1 SP ≈ 0.5 人天

---

## 一、Issue 快速参考表

| Issue | 标题 | Sprint | 优先级 | 估算 | 负责人 | 状态 |
|-------|------|--------|:------:|:----:|--------|:----:|
| 1.1 | G1 阶段门自动检查（线索→商机） | Sprint 1 | P0 | 8 SP | Backend | ⬜ |
| 1.2 | G2 阶段门自动检查（商机→报价） | Sprint 1 | P0 | 8 SP | Backend | ⬜ |
| 1.3 | G3 阶段门自动检查（报价→合同） | Sprint 1 | P0 | 10 SP | Backend | ⬜ |
| 1.4 | G4 阶段门自动检查（合同→项目） | Sprint 1 | P0 | 8 SP | Backend | ⬜ |
| 1.5 | 收款计划与里程碑自动绑定 | Sprint 1 | P0 | 6 SP | Backend | ⬜ |
| 2.1 | 审批流程配置数据模型 | Sprint 2 | P0 | 5 SP | Backend | ⬜ |
| 2.2 | 审批历史记录数据模型 | Sprint 2 | P0 | 5 SP | Backend | ⬜ |
| 2.3 | 审批工作流引擎 | Sprint 2 | P0 | 10 SP | Backend | ⬜ |
| 2.4 | 报价审批工作流集成 | Sprint 2 | P0 | 5 SP | Backend | ⬜ |
| 2.5 | 合同审批工作流集成 | Sprint 2 | P0 | 5 SP | Backend | ⬜ |
| 2.6 | 发票审批工作流集成 | Sprint 2 | P0 | 5 SP | Backend | ⬜ |
| 3.1 | 通知服务基础框架 | Sprint 3 | P0 | 5 SP | Backend | ⬜ |
| 3.2 | 阶段门到期提醒 | Sprint 3 | P0 | 5 SP | Backend | ⬜ |
| 3.3 | 报价过期提醒 | Sprint 3 | P0 | 4 SP | Backend | ⬜ |
| 3.4 | 合同到期提醒 | Sprint 3 | P0 | 4 SP | Backend | ⬜ |
| 3.5 | 收款逾期提醒 | Sprint 3 | P0 | 4 SP | Backend | ⬜ |
| 3.6 | 审批待处理提醒 | Sprint 3 | P0 | 3 SP | Backend | ⬜ |
| 4.1 | Excel 导出基础框架 | Sprint 4 | P1 | 4 SP | Backend | ⬜ |
| 4.2 | 线索/商机列表 Excel 导出 | Sprint 4 | P1 | 3 SP | Backend | ⬜ |
| 4.3 | 报价单/合同列表 Excel 导出 | Sprint 4 | P1 | 3 SP | Backend | ⬜ |
| 4.4 | 发票/应收账款 Excel 导出 | Sprint 4 | P1 | 3 SP | Backend | ⬜ |
| 4.5 | PDF 导出功能（报价单/合同/发票） | Sprint 4 | P1 | 7 SP | Backend | ⬜ |
| 5.1 | 统一审批中心页面 | Sprint 5 | P1 | 8 SP | Frontend | ⬜ |
| 5.2 | 审批详情页面 | Sprint 5 | P1 | 6 SP | Frontend | ⬜ |
| 5.3 | 销售工作台完善 | Sprint 5 | P1 | 6 SP | Frontend | ⬜ |
| 5.4 | 销售看板页面 | Sprint 5 | P1 | 5 SP | Frontend | ⬜ |
| 5.5 | 销售漏斗可视化页面 | Sprint 5 | P1 | 5 SP | Frontend | ⬜ |
| 6.1 | 客户360视图完善 | Sprint 6 | P2 | 8 SP | Full Stack | ⬜ |
| 6.2 | CPQ 配置化报价 UI | Sprint 6 | P2 | 10 SP | Frontend | ⬜ |
| 6.3 | 销售预测增强 | Sprint 6 | P2 | 8 SP | Backend | ⬜ |
| 6.4 | 销售团队管理和业绩排名 | Sprint 6 | P2 | 5 SP | Full Stack | ⬜ |
| 6.5 | 销售目标管理 | Sprint 6 | P2 | 4 SP | Full Stack | ⬜ |
| 7.1 | 销售数据权限过滤 | Sprint 7 | P1 | 6 SP | Backend | ⬜ |
| 7.2 | 操作权限控制细化 | Sprint 7 | P1 | 5 SP | Backend | ⬜ |
| 7.3 | 项目进度影响收款计划 | Sprint 7 | P1 | 8 SP | Backend | ⬜ |
| 7.4 | 里程碑验收自动触发开票 | Sprint 7 | P1 | 6 SP | Backend | ⬜ |
| 8.1 | 销售模块单元测试完善 | Sprint 8 | P1 | 8 SP | QA+Backend | ⬜ |
| 8.2 | 销售模块集成测试 | Sprint 8 | P1 | 6 SP | QA+Backend | ⬜ |
| 8.3 | API 文档完善 | Sprint 8 | P1 | 3 SP | Backend | ⬜ |
| 8.4 | 用户使用手册 | Sprint 8 | P1 | 3 SP | Product | ⬜ |

**状态说明**: ⬜ 待开始 | 🚧 进行中 | ✅ 已完成 | ❌ 已取消

---

## 二、Sprint 规划总览

| Sprint | 主题 | 优先级 | 预计工时 | 依赖关系 | 目标 |
|--------|------|:------:|:--------:|---------|------|
| **Sprint 1** | 阶段门自动检查与收款计划绑定 | 🔴 P0 | 40 SP | 无 | 核心业务规则自动化 |
| **Sprint 2** | 审批工作流系统 | 🔴 P0 | 35 SP | Sprint 1 | 多级审批流程 |
| **Sprint 3** | 通知提醒系统 | 🔴 P0 | 25 SP | Sprint 1, 2 | 关键节点提醒 |
| **Sprint 4** | 数据导出功能 | 🟡 P1 | 20 SP | 无 | Excel/PDF 导出 |
| **Sprint 5** | 前端页面完善 | 🟡 P1 | 30 SP | Sprint 2, 3 | 审批中心、工作台 |
| **Sprint 6** | 高级功能增强 | 🟢 P2 | 35 SP | Sprint 1-5 | 客户360、CPQ UI、预测增强 |
| **Sprint 7** | 权限控制细化与集成功能 | 🟡 P1 | 25 SP | Sprint 1, 2, 3 | 数据权限、项目集成 |
| **Sprint 8** | 测试与文档完善 | 🟡 P1 | 20 SP | Sprint 1-7 | 单元测试、集成测试、文档 |

**总计**: 230 SP（约 115 人天，按 1 人计算约 5.75 个月，按 2 人计算约 2.9 个月）

---

## 三、Sprint 1: 阶段门自动检查与收款计划绑定（P0）

**目标**: 实现 G1-G4 阶段门自动验证，完成收款计划与里程碑的自动绑定

**预计工时**: 40 SP  
**预计周期**: 2 周

### Issue 1.1: G1 阶段门自动检查（线索→商机）

**优先级**: 🔴 P0  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
实现线索转商机时的自动验证逻辑，检查必填项和数据完整性。

**验收标准**:
- [ ] 实现 `validate_g1_lead_to_opportunity()` 函数，检查以下必填项：
  - 客户名称、联系人、联系电话
  - 行业、产品对象、节拍、接口、现场约束、验收依据
- [ ] 在 `/sales/leads/{id}/convert` 接口中集成自动验证
- [ ] 验证失败时返回详细的错误列表
- [ ] 验证通过后自动更新线索状态为 `CONVERTED`
- [ ] 添加单元测试覆盖所有验证场景

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 复用现有的 `validate_g1_lead_to_opportunity()` 函数框架
- 补充完整的验证逻辑

**依赖**: 无

---

### Issue 1.2: G2 阶段门自动检查（商机→报价）

**优先级**: 🔴 P0  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
实现商机转报价时的自动验证逻辑，检查预算、决策链、交付窗口、验收标准等。

**验收标准**:
- [ ] 实现 `validate_g2_opportunity_to_quote()` 函数，检查：
  - 预算范围已明确
  - 决策链信息完整
  - 交付窗口已确定
  - 验收标准明确
  - 技术可行性初评通过（如果有技术评估）
- [ ] 在创建报价时自动触发验证
- [ ] 验证失败时阻止报价创建并返回错误
- [ ] 验证通过后允许创建报价
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 新增验证函数
- 集成到 `POST /sales/quotes` 接口

**依赖**: Issue 1.1（复用验证框架）

---

### Issue 1.3: G3 阶段门自动检查（报价→合同）

**优先级**: 🔴 P0  
**估算**: 10 SP  
**负责人**: Backend Team

**描述**:
实现报价转合同时的自动验证，包括成本拆解、毛利率检查、交期校验、风险条款检查。

**验收标准**:
- [ ] 实现 `validate_g3_quote_to_contract()` 函数，检查：
  - 成本拆解齐备（所有报价明细都有成本）
  - 毛利率计算正确，低于阈值时自动预警
  - 交期校验（关键物料交期 + 设计/装配/调试周期）
  - 风险条款与边界条款已补充
- [ ] 在合同创建时自动触发验证
- [ ] 毛利率低于阈值时触发审批升级（创建审批记录）
- [ ] 交期校验失败时返回详细原因
- [ ] 添加配置项：毛利率阈值（默认 15%）
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 需要集成物料交期查询（调用采购模块 API）
- 需要集成项目周期估算（调用项目模块 API）

**依赖**: Issue 1.2

---

### Issue 1.4: G4 阶段门自动检查（合同→项目）

**优先级**: 🔴 P0  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
实现合同生成项目时的自动验证，检查付款节点与交付物绑定、数据完整性。

**验收标准**:
- [ ] 实现 `validate_g4_contract_to_project()` 函数，检查：
  - 付款节点与可交付物已绑定
  - SOW/验收标准/BOM初版/里程碑基线已冻结
  - 合同交付物清单完整
- [ ] 在 `POST /sales/contracts/{id}/project` 接口中集成验证
- [ ] 验证失败时阻止项目生成
- [ ] 验证通过后自动生成项目
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 需要检查 `contract_deliverables` 表
- 需要检查合同关联的文档和 BOM

**依赖**: Issue 1.3

---

### Issue 1.5: 收款计划与里程碑自动绑定

**优先级**: 🔴 P0  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
实现合同签订后自动生成收款计划，并与项目里程碑绑定。

**验收标准**:
- [ ] 在合同签订时自动生成收款计划（`ProjectPaymentPlan`）
- [ ] 收款计划与合同交付物关联
- [ ] 收款计划与项目里程碑自动绑定（通过 `milestone_id`）
- [ ] 支持自定义收款比例和节点
- [ ] 添加 API: `GET /sales/contracts/{id}/payment-plans` 查看收款计划
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 修改 `POST /sales/contracts/{id}/sign` 接口
- 创建 `ProjectPaymentPlan` 记录
- 关联 `ContractDeliverable` 和 `ProjectMilestone`

**依赖**: Issue 1.4

---

## 四、Sprint 2: 审批工作流系统（P0）

**目标**: 实现多级审批流程，支持报价、合同、发票的审批工作流

**预计工时**: 35 SP  
**预计周期**: 2 周

### Issue 2.1: 审批流程配置数据模型

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
创建审批流程配置表，支持定义不同业务类型的审批流程。

**验收标准**:
- [ ] 创建 `approval_workflows` 表：
  - `id`, `workflow_type` (QUOTE/CONTRACT/INVOICE)
  - `workflow_name`, `description`
  - `steps` (JSON，存储审批步骤配置)
  - `is_active`, `created_at`, `updated_at`
- [ ] 创建 `approval_workflow_steps` 表：
  - `id`, `workflow_id`, `step_order`
  - `step_name`, `approver_role`, `approver_id` (可选)
  - `is_required`, `can_delegate`
- [ ] 创建 ORM 模型: `ApprovalWorkflow`, `ApprovalWorkflowStep`
- [ ] 创建 Pydantic schemas
- [ ] 生成数据库迁移脚本（SQLite + MySQL）

**技术实现**:
- 文件: `app/models/sales.py` (新增模型)
- 文件: `app/schemas/sales.py` (新增 schemas)
- 文件: `migrations/YYYYMMDD_approval_workflow_sqlite.sql`

**依赖**: 无

---

### Issue 2.2: 审批历史记录数据模型

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
创建审批历史记录表，记录所有审批操作。

**验收标准**:
- [ ] 创建 `approval_records` 表：
  - `id`, `entity_type` (QUOTE/CONTRACT/INVOICE)
  - `entity_id`, `workflow_id`, `current_step`
  - `status` (PENDING/APPROVED/REJECTED/CANCELLED)
  - `initiator_id`, `created_at`, `updated_at`
- [ ] 创建 `approval_history` 表：
  - `id`, `approval_record_id`, `step_order`
  - `approver_id`, `action` (APPROVE/REJECT/DELEGATE)
  - `comment`, `approved_at`
- [ ] 创建 ORM 模型: `ApprovalRecord`, `ApprovalHistory`
- [ ] 创建 Pydantic schemas
- [ ] 生成数据库迁移脚本

**技术实现**:
- 文件: `app/models/sales.py`
- 文件: `app/schemas/sales.py`

**依赖**: Issue 2.1

---

### Issue 2.3: 审批工作流引擎

**优先级**: 🔴 P0  
**估算**: 10 SP  
**负责人**: Backend Team

**描述**:
实现审批工作流引擎，支持多级审批、审批路由、审批委托。

**验收标准**:
- [ ] 实现 `ApprovalWorkflowService` 类：
  - `start_approval()`: 启动审批流程
  - `approve_step()`: 审批通过
  - `reject_step()`: 审批驳回
  - `delegate_step()`: 审批委托
  - `get_current_step()`: 获取当前审批步骤
  - `get_approval_history()`: 获取审批历史
- [ ] 支持审批路由规则（根据金额、类型等）
- [ ] 支持审批委托（临时委托给他人）
- [ ] 支持审批撤回（在下一级审批前）
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/services/approval_workflow_service.py` (新建)
- 集成到报价、合同、发票的审批接口

**依赖**: Issue 2.1, 2.2

---

### Issue 2.4: 报价审批工作流集成

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
将审批工作流集成到报价审批流程中。

**验收标准**:
- [ ] 修改 `POST /sales/quotes/{id}/approve` 接口，使用工作流引擎
- [ ] 支持多级审批（销售经理 → 销售总监 → 财务）
- [ ] 根据报价金额自动选择审批流程
- [ ] 审批通过后更新报价状态
- [ ] 审批驳回时允许修改后重新提交
- [ ] 添加 API: `GET /sales/quotes/{id}/approval-status` 查看审批状态

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 调用 `ApprovalWorkflowService`

**依赖**: Issue 2.3

---

### Issue 2.5: 合同审批工作流集成

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
将审批工作流集成到合同审批流程中。

**验收标准**:
- [ ] 修改 `POST /sales/contracts/{id}/submit` 接口，启动审批流程
- [ ] 支持多级审批（销售 → 法务 → 财务 → 总经理）
- [ ] 根据合同金额自动选择审批流程
- [ ] 审批通过后允许合同签订
- [ ] 添加 API: `GET /sales/contracts/{id}/approval-status` 查看审批状态
- [ ] 添加 API: `GET /sales/contracts/{id}/approval-history` 查看审批历史

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 调用 `ApprovalWorkflowService`

**依赖**: Issue 2.3

---

### Issue 2.6: 发票审批工作流集成

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
将审批工作流集成到发票审批流程中。

**验收标准**:
- [ ] 修改发票申请接口，启动审批流程
- [ ] 支持多级审批（财务 → 财务经理）
- [ ] 审批通过后允许开票
- [ ] 添加 API: `GET /sales/invoices/{id}/approval-status` 查看审批状态
- [ ] 添加 API: `GET /sales/invoices/{id}/approval-history` 查看审批历史

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 调用 `ApprovalWorkflowService`

**依赖**: Issue 2.3

---

## 五、Sprint 3: 通知提醒系统（P0）

**目标**: 实现关键节点的自动提醒和通知推送

**预计工时**: 25 SP  
**预计周期**: 1.5 周

### Issue 3.1: 通知服务基础框架

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
创建通知服务基础框架，支持多种通知渠道。

**验收标准**:
- [ ] 创建 `NotificationService` 类：
  - `send_notification()`: 发送通知
  - `send_email()`: 邮件通知
  - `send_sms()`: 短信通知（可选）
  - `send_wechat()`: 企微通知（可选）
- [ ] 支持通知模板（使用 Jinja2）
- [ ] 支持通知优先级（LOW/MEDIUM/HIGH/URGENT）
- [ ] 集成到现有的通知中心 API

**技术实现**:
- 文件: `app/services/notification_service.py` (新建)
- 复用现有的通知中心模块

**依赖**: 无

---

### Issue 3.2: 阶段门到期提醒

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
实现阶段门到期自动提醒功能。

**验收标准**:
- [ ] 创建定时任务，每天检查阶段门状态
- [ ] 阶段门提交后 3 天未处理，发送提醒
- [ ] 提醒发送给：商机负责人、销售经理
- [ ] 支持邮件和系统内通知
- [ ] 添加配置项：提醒时间阈值（默认 3 天）

**技术实现**:
- 文件: `app/services/sales_reminder_service.py` (已存在，需扩展)
- 集成 APScheduler 定时任务
- 调用 `NotificationService`

**依赖**: Issue 3.1

---

### Issue 3.3: 报价过期提醒

**优先级**: 🔴 P0  
**估算**: 4 SP  
**负责人**: Backend Team

**描述**:
实现报价过期自动提醒功能。

**验收标准**:
- [ ] 创建定时任务，每天检查报价有效期
- [ ] 报价到期前 7 天、3 天、1 天发送提醒
- [ ] 报价过期后发送过期通知
- [ ] 提醒发送给：报价负责人、销售经理
- [ ] 支持邮件和系统内通知

**技术实现**:
- 文件: `app/services/sales_reminder_service.py`
- 集成 APScheduler 定时任务

**依赖**: Issue 3.1

---

### Issue 3.4: 合同到期提醒

**优先级**: 🔴 P0  
**估算**: 4 SP  
**负责人**: Backend Team

**描述**:
实现合同到期自动提醒功能。

**验收标准**:
- [ ] 创建定时任务，每天检查合同状态
- [ ] 合同到期前 30 天、15 天、7 天发送提醒
- [ ] 提醒发送给：合同负责人、项目经理、财务
- [ ] 支持邮件和系统内通知

**技术实现**:
- 文件: `app/services/sales_reminder_service.py`
- 集成 APScheduler 定时任务

**依赖**: Issue 3.1

---

### Issue 3.5: 收款逾期提醒

**优先级**: 🔴 P0  
**估算**: 4 SP  
**负责人**: Backend Team

**描述**:
实现收款逾期自动提醒功能。

**验收标准**:
- [ ] 创建定时任务，每天检查收款计划
- [ ] 收款到期前 7 天、3 天、1 天发送提醒
- [ ] 收款逾期后按 7 天、15 天、30 天、60 天分级提醒
- [ ] 提醒发送给：收款责任人、销售、财务、销售经理
- [ ] 逾期必须选择原因并生成 `receivable_disputes` 记录
- [ ] 支持邮件和系统内通知

**技术实现**:
- 文件: `app/services/sales_reminder_service.py`
- 集成 APScheduler 定时任务
- 调用回款争议 API

**依赖**: Issue 3.1

---

### Issue 3.6: 审批待处理提醒

**优先级**: 🔴 P0  
**估算**: 3 SP  
**负责人**: Backend Team

**描述**:
实现审批待处理自动提醒功能。

**验收标准**:
- [ ] 创建定时任务，每天检查待审批事项
- [ ] 审批待处理超过 1 天发送提醒
- [ ] 提醒发送给：当前审批人
- [ ] 支持邮件和系统内通知
- [ ] 支持批量提醒（汇总所有待审批事项）

**技术实现**:
- 文件: `app/services/sales_reminder_service.py`
- 集成 APScheduler 定时任务
- 调用审批工作流 API

**依赖**: Issue 3.1, Sprint 2

---

## 六、Sprint 4: 数据导出功能（P1）

**目标**: 实现 Excel 和 PDF 导出功能

**预计工时**: 20 SP  
**预计周期**: 1 周

### Issue 4.1: Excel 导出基础框架

**优先级**: 🟡 P1  
**估算**: 4 SP  
**负责人**: Backend Team

**描述**:
创建 Excel 导出基础框架，支持通用数据导出。

**验收标准**:
- [ ] 创建 `ExcelExportService` 类：
  - `export_to_excel()`: 导出数据到 Excel
  - `format_headers()`: 格式化表头
  - `format_data()`: 格式化数据
- [ ] 支持自定义列、排序、筛选
- [ ] 支持大数据量导出（分页处理）
- [ ] 添加依赖: `openpyxl` 或 `pandas`

**技术实现**:
- 文件: `app/services/excel_export_service.py` (新建)
- 使用 `openpyxl` 或 `pandas` 库

**依赖**: 无

---

### Issue 4.2: 线索/商机列表 Excel 导出

**优先级**: 🟡 P1  
**估算**: 3 SP  
**负责人**: Backend Team

**描述**:
实现线索和商机列表的 Excel 导出功能。

**验收标准**:
- [ ] 添加 API: `GET /sales/leads/export`
- [ ] 添加 API: `GET /sales/opportunities/export`
- [ ] 支持当前筛选条件导出
- [ ] 导出字段：编码、客户、状态、金额、负责人等
- [ ] 支持批量导出（所有数据）

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 调用 `ExcelExportService`

**依赖**: Issue 4.1

---

### Issue 4.3: 报价单/合同列表 Excel 导出

**优先级**: 🟡 P1  
**估算**: 3 SP  
**负责人**: Backend Team

**描述**:
实现报价单和合同列表的 Excel 导出功能。

**验收标准**:
- [ ] 添加 API: `GET /sales/quotes/export`
- [ ] 添加 API: `GET /sales/contracts/export`
- [ ] 支持当前筛选条件导出
- [ ] 导出字段：编码、客户、金额、状态、负责人等
- [ ] 报价单导出包含明细（多 sheet）

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 调用 `ExcelExportService`

**依赖**: Issue 4.1

---

### Issue 4.4: 发票/应收账款 Excel 导出

**优先级**: 🟡 P1  
**估算**: 3 SP  
**负责人**: Backend Team

**描述**:
实现发票和应收账款列表的 Excel 导出功能。

**验收标准**:
- [ ] 添加 API: `GET /sales/invoices/export`
- [ ] 添加 API: `GET /sales/payments/export`
- [ ] 支持当前筛选条件导出
- [ ] 导出字段：编码、客户、金额、状态、到期日期等
- [ ] 应收账款导出包含账龄分析

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py`
- 调用 `ExcelExportService`

**依赖**: Issue 4.1

---

### Issue 4.5: PDF 导出功能（报价单/合同/发票）

**优先级**: 🟡 P1  
**估算**: 7 SP  
**负责人**: Backend Team

**描述**:
实现报价单、合同、发票的 PDF 导出功能。

**验收标准**:
- [ ] 创建 `PDFExportService` 类，使用 `reportlab` 或 `weasyprint`
- [ ] 添加 API: `GET /sales/quotes/{id}/pdf` 生成报价单 PDF
- [ ] 添加 API: `GET /sales/contracts/{id}/pdf` 生成合同 PDF
- [ ] 添加 API: `GET /sales/invoices/{id}/pdf` 生成发票 PDF
- [ ] PDF 包含公司 Logo、格式规范、签名区域
- [ ] 支持自定义模板

**技术实现**:
- 文件: `app/services/pdf_export_service.py` (新建)
- 使用 `reportlab` 或 `weasyprint` 库
- 创建 PDF 模板文件

**依赖**: 无

---

## 七、Sprint 5: 前端页面完善（P1）

**目标**: 完善审批中心、工作台等前端页面

**预计工时**: 30 SP  
**预计周期**: 2 周

### Issue 5.1: 统一审批中心页面

**优先级**: 🟡 P1  
**估算**: 8 SP  
**负责人**: Frontend Team

**描述**:
创建统一审批中心页面，展示所有待审批事项。

**验收标准**:
- [ ] 创建 `ApprovalCenter.jsx` 页面
- [ ] 支持筛选：审批类型（报价/合同/发票）、状态、时间范围
- [ ] 展示待审批列表，包含：事项名称、申请人、申请时间、当前审批人
- [ ] 支持批量审批操作
- [ ] 支持审批历史查看
- [ ] 集成到侧边栏导航

**技术实现**:
- 文件: `frontend/src/pages/ApprovalCenter.jsx` (新建)
- 调用审批工作流 API
- 使用 shadcn/ui 组件

**依赖**: Sprint 2

---

### Issue 5.2: 审批详情页面

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Frontend Team

**描述**:
创建审批详情页面，支持审批操作和历史查看。

**验收标准**:
- [ ] 创建 `ApprovalDetail.jsx` 页面
- [ ] 展示审批事项详情（报价/合同/发票信息）
- [ ] 展示审批流程进度（可视化流程图）
- [ ] 展示审批历史记录
- [ ] 支持审批操作：通过、驳回、委托
- [ ] 支持审批意见填写

**技术实现**:
- 文件: `frontend/src/pages/ApprovalDetail.jsx` (新建)
- 调用审批工作流 API
- 使用流程图组件（如 `react-flow`）

**依赖**: Sprint 2

---

### Issue 5.3: 销售工作台完善

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Frontend Team

**描述**:
完善销售工作台页面，增加待办事项和统计信息。

**验收标准**:
- [ ] 完善 `SalesWorkstation.jsx` 页面
- [ ] 添加待办事项卡片：待审批、待跟进、逾期提醒
- [ ] 添加统计卡片：本月线索、商机、报价、合同数量
- [ ] 添加销售漏斗可视化
- [ ] 添加最近活动时间线
- [ ] 支持快速操作：创建线索、创建商机

**技术实现**:
- 文件: `frontend/src/pages/SalesWorkstation.jsx` (已存在，需完善)
- 调用销售统计 API
- 使用图表组件（如 `recharts`）

**依赖**: Sprint 3

---

### Issue 5.4: 销售看板页面

**优先级**: 🟡 P1  
**估算**: 5 SP  
**负责人**: Frontend Team

**描述**:
创建销售看板页面，展示商机状态看板。

**验收标准**:
- [ ] 创建或完善 `OpportunityBoard.jsx` 页面
- [ ] 看板视图：按商机阶段分组（DISCOVERY/QUALIFIED/PROPOSAL/NEGOTIATION）
- [ ] 支持拖拽改变商机阶段
- [ ] 卡片展示：商机名称、客户、金额、负责人
- [ ] 支持筛选和搜索
- [ ] 支持快速创建商机

**技术实现**:
- 文件: `frontend/src/pages/OpportunityBoard.jsx` (已存在，需完善)
- 使用拖拽组件（如 `react-beautiful-dnd`）
- 调用商机管理 API

**依赖**: 无

---

### Issue 5.5: 销售漏斗可视化页面

**优先级**: 🟡 P1  
**估算**: 5 SP  
**负责人**: Frontend Team

**描述**:
完善销售漏斗可视化页面，增加交互和筛选功能。

**验收标准**:
- [ ] 完善 `SalesFunnel.jsx` 页面
- [ ] 展示销售漏斗图表（线索→商机→报价→合同）
- [ ] 支持时间范围筛选（本月/本季度/本年）
- [ ] 支持按销售、客户、行业筛选
- [ ] 展示转化率和流失率
- [ ] 支持钻取查看详情

**技术实现**:
- 文件: `frontend/src/pages/SalesFunnel.jsx` (已存在，需完善)
- 使用图表组件（如 `recharts` 或 `echarts`）
- 调用销售统计 API

**依赖**: 无

---

## 八、Sprint 6: 高级功能增强（P2）

**目标**: 完善客户360视图、CPQ UI、销售预测等高级功能

**预计工时**: 35 SP  
**预计周期**: 2 周

### Issue 6.1: 客户360视图完善

**优先级**: 🟢 P2  
**估算**: 8 SP  
**负责人**: Full Stack Team

**描述**:
完善客户360视图，增加更多维度的客户信息。

**验收标准**:
- [ ] 完善客户360视图页面
- [ ] 添加标签页：基本信息、历史订单、历史报价、历史合同、历史发票、回款记录、项目交付、满意度调查、服务记录
- [ ] 添加客户画像：价值等级、合作年限、订单频率、平均订单金额
- [ ] 添加关联分析：关联项目、关联商机
- [ ] 支持自定义指标配置

**技术实现**:
- 文件: `frontend/src/pages/Customer360.jsx` (新建或完善)
- 调用 `/customers/{id}/360` API
- 使用标签页组件

**依赖**: 无

---

### Issue 6.2: CPQ 配置化报价 UI

**优先级**: 🟢 P2  
**估算**: 10 SP  
**负责人**: Frontend Team

**描述**:
创建 CPQ 配置化报价的 UI 界面，支持产品配置和价格预览。

**验收标准**:
- [ ] 创建 `CpqConfigurator.jsx` 页面
- [ ] 产品配置器：支持选择配置项、数量、选项
- [ ] 实时价格预览：根据配置自动计算价格
- [ ] 价格调整轨迹：显示价格调整历史
- [ ] 审批提示：显示是否需要审批
- [ ] 支持保存配置为报价草稿

**技术实现**:
- 文件: `frontend/src/pages/CpqConfigurator.jsx` (新建)
- 调用 `/sales/cpq/price-preview` API
- 使用表单组件和价格计算逻辑

**依赖**: 无（CPQ 后端已实现）

---

### Issue 6.3: 销售预测增强

**优先级**: 🟢 P2  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
增强销售预测功能，使用更复杂的预测模型。

**验收标准**:
- [ ] 实现基于历史数据的预测模型：
  - 移动平均法
  - 指数平滑法
  - 线性回归（可选）
- [ ] 商机赢单概率预测：
  - 基于商机阶段、金额、历史赢单率
  - 支持自定义权重
- [ ] 收入预测模型：
  - 未来 30/60/90 天收入预测
  - 按客户、产品线、区域预测
- [ ] 添加 API: `GET /sales/statistics/prediction`
- [ ] 添加预测准确度评估

**技术实现**:
- 文件: `app/services/sales_prediction_service.py` (新建)
- 使用 `pandas` 和 `numpy` 进行数据分析
- 可选：集成 `scikit-learn` 进行机器学习

**依赖**: 无

---

### Issue 6.4: 销售团队管理和业绩排名

**优先级**: 🟢 P2  
**估算**: 5 SP  
**负责人**: Full Stack Team

**描述**:
实现销售团队管理和业绩排名功能。

**验收标准**:
- [ ] 完善 `SalesTeam.jsx` 页面
- [ ] 销售团队列表：成员、角色、负责区域
- [ ] 销售业绩排名：按线索、商机、合同、回款排名
- [ ] 支持时间范围筛选
- [ ] 支持导出排名报表
- [ ] 添加 API: `GET /sales/team/ranking`

**技术实现**:
- 文件: `frontend/src/pages/SalesTeam.jsx` (已存在，需完善)
- 文件: `app/api/v1/endpoints/sales.py` (新增 API)
- 调用销售统计 API

**依赖**: 无

---

### Issue 6.5: 销售目标管理

**优先级**: 🟢 P2  
**估算**: 4 SP  
**负责人**: Full Stack Team

**描述**:
实现销售目标管理功能，支持目标设定和进度跟踪。

**验收标准**:
- [ ] 创建 `SalesTarget.jsx` 页面
- [ ] 支持创建销售目标：个人目标、团队目标、部门目标
- [ ] 目标类型：线索数量、商机数量、合同金额、回款金额
- [ ] 目标周期：月度、季度、年度
- [ ] 目标进度跟踪：实际完成 vs 目标
- [ ] 添加 API: `GET /sales/targets`, `POST /sales/targets`

**技术实现**:
- 文件: `frontend/src/pages/SalesTarget.jsx` (新建)
- 文件: `app/models/sales.py` (新增 `SalesTarget` 模型)
- 文件: `app/api/v1/endpoints/sales.py` (新增 API)

**依赖**: 无

---

## 七、Sprint 7: 权限控制细化与集成功能（P1）

**目标**: 实现细粒度的数据权限控制和与项目模块的深度集成

**预计工时**: 25 SP  
**预计周期**: 1.5 周

### Issue 7.1: 销售数据权限过滤

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
实现细粒度的数据权限过滤，确保销售只能看到自己的数据，销售经理可以看到团队数据。

**验收标准**:
- [ ] 实现数据权限过滤中间件：
  - 销售（SALES）: 只能看到 `owner_id = current_user.id` 的数据
  - 销售经理（SALES_MANAGER）: 可以看到团队数据（同部门或下属）
  - 销售总监（SALES_DIRECTOR）: 可以看到所有数据
  - 财务（FINANCE）: 只能看到发票和收款数据
- [ ] 在以下 API 中集成权限过滤：
  - `GET /sales/leads` - 线索列表
  - `GET /sales/opportunities` - 商机列表
  - `GET /sales/quotes` - 报价列表
  - `GET /sales/contracts` - 合同列表
- [ ] 添加配置项：数据权限范围（ALL/DEPT/OWN）
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/core/security.py` (扩展权限函数)
- 文件: `app/api/v1/endpoints/sales.py` (集成权限过滤)
- 使用 SQLAlchemy 查询过滤

**依赖**: 无

---

### Issue 7.2: 操作权限控制细化

**优先级**: 🟡 P1  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
细化操作权限控制，确保不同角色有不同的操作权限。

**验收标准**:
- [ ] 实现操作权限检查函数：
  - 创建权限：销售、销售经理、销售总监
  - 编辑权限：创建人、负责人、销售经理、销售总监
  - 删除权限：仅创建人、销售总监、管理员
  - 审批权限：根据审批工作流配置
- [ ] 在以下操作中集成权限检查：
  - `PUT /sales/leads/{id}` - 更新线索
  - `DELETE /sales/leads/{id}` - 删除线索
  - `PUT /sales/opportunities/{id}` - 更新商机
  - `PUT /sales/quotes/{id}` - 更新报价
  - `PUT /sales/contracts/{id}` - 更新合同
- [ ] 权限不足时返回 403 错误
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/core/security.py` (新增权限检查函数)
- 文件: `app/api/v1/endpoints/sales.py` (集成权限检查)

**依赖**: Issue 7.1

---

### Issue 7.3: 项目进度影响收款计划

**优先级**: 🟡 P1  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
实现项目进度变化时自动调整收款计划的功能。

**验收标准**:
- [ ] 创建定时任务，监控项目里程碑状态变化
- [ ] 里程碑延期时，自动调整关联的收款计划到期日期
- [ ] 里程碑提前完成时，允许提前触发开票（需配置）
- [ ] 添加 API: `POST /sales/payments/{id}/adjust` 手动调整收款计划
- [ ] 记录调整历史（谁调整、何时调整、原因）
- [ ] 发送通知给：收款责任人、销售、财务
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/services/payment_adjustment_service.py` (新建)
- 文件: `app/api/v1/endpoints/sales.py` (新增 API)
- 集成项目里程碑状态变更事件监听

**依赖**: Issue 1.5, Sprint 3

---

### Issue 7.4: 里程碑验收自动触发开票

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
实现里程碑验收完成后自动触发开票申请的功能。

**验收标准**:
- [ ] 监听验收管理模块的验收完成事件
- [ ] 验收通过后，检查关联的收款计划
- [ ] 如果收款计划已到期且交付物齐全，自动创建发票申请
- [ ] 支持配置：是否自动开票（默认手动）
- [ ] 自动开票时发送通知给：财务、销售
- [ ] 记录自动开票日志
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/services/invoice_auto_service.py` (新建)
- 集成验收管理模块的事件
- 调用发票创建 API

**依赖**: Issue 1.5, Sprint 2

---

## 八、Sprint 8: 测试与文档完善（P1）

**目标**: 完善单元测试、集成测试和文档

**预计工时**: 20 SP  
**预计周期**: 1 周

### Issue 8.1: 销售模块单元测试完善

**优先级**: 🟡 P1  
**估算**: 8 SP  
**负责人**: QA Team + Backend Team

**描述**:
为销售模块的所有 API 端点编写完整的单元测试。

**验收标准**:
- [ ] 测试覆盖率 ≥ 80%
- [ ] 测试以下场景：
  - 线索管理：创建、更新、转化、权限检查
  - 商机管理：创建、更新、阶段门控、权限检查
  - 报价管理：创建、版本管理、审批、权限检查
  - 合同管理：创建、签订、项目生成、权限检查
  - 发票管理：创建、开票、收款、权限检查
  - 阶段门验证：G1-G4 所有验证场景
  - 审批工作流：启动、审批、驳回、委托
- [ ] 使用 pytest 和 pytest-cov
- [ ] 所有测试通过

**技术实现**:
- 文件: `tests/test_sales_api.py` (新建或完善)
- 使用 pytest fixtures 模拟数据库和用户

**依赖**: Sprint 1-7

---

### Issue 8.2: 销售模块集成测试

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: QA Team + Backend Team

**描述**:
编写端到端的集成测试，测试完整的业务流程。

**验收标准**:
- [ ] 测试完整业务流程：
  - 线索 → 商机 → 报价 → 合同 → 项目 → 发票 → 收款
- [ ] 测试阶段门控流程：
  - G1 验证失败场景
  - G2 验证失败场景
  - G3 验证失败场景
  - G4 验证失败场景
- [ ] 测试审批工作流：
  - 多级审批流程
  - 审批驳回流程
  - 审批委托流程
- [ ] 测试通知提醒：
  - 阶段门到期提醒
  - 报价过期提醒
  - 收款逾期提醒
- [ ] 所有集成测试通过

**技术实现**:
- 文件: `tests/test_sales_integration.py` (新建)
- 使用测试数据库

**依赖**: Sprint 1-7

---

### Issue 8.3: API 文档完善

**优先级**: 🟡 P1  
**估算**: 3 SP  
**负责人**: Backend Team

**描述**:
完善销售模块的 API 文档，包括所有新增接口的文档。

**验收标准**:
- [ ] 所有 API 端点都有详细的文档说明
- [ ] 包含请求参数、响应格式、错误码说明
- [ ] 包含示例请求和响应
- [ ] 使用 OpenAPI/Swagger 规范
- [ ] 文档可通过 `/docs` 访问

**技术实现**:
- 文件: `app/api/v1/endpoints/sales.py` (补充文档字符串)
- 使用 FastAPI 的自动文档生成

**依赖**: Sprint 1-7

---

### Issue 8.4: 用户使用手册

**优先级**: 🟡 P1  
**估算**: 3 SP  
**负责人**: Product Team + Tech Writer

**描述**:
编写销售模块的用户使用手册。

**验收标准**:
- [ ] 包含以下章节：
  - 模块概述
  - 线索管理操作指南
  - 商机管理操作指南
  - 报价管理操作指南
  - 合同管理操作指南
  - 发票管理操作指南
  - 审批流程说明
  - 常见问题解答
- [ ] 包含截图和操作步骤
- [ ] 文档格式：Markdown + PDF

**技术实现**:
- 文件: `docs/sales_module_user_guide.md` (新建)

**依赖**: Sprint 1-7

---

## 九、任务优先级和依赖关系图

```
Sprint 1 (阶段门 + 收款计划)
  ├─ Issue 1.1 (G1检查) ──┐
  ├─ Issue 1.2 (G2检查) ──┤
  ├─ Issue 1.3 (G3检查) ──┤
  ├─ Issue 1.4 (G4检查) ──┤
  └─ Issue 1.5 (收款绑定) ┘

Sprint 2 (审批工作流)
  ├─ Issue 2.1 (流程配置) ──┐
  ├─ Issue 2.2 (历史记录) ──┤
  ├─ Issue 2.3 (工作流引擎) ──┤
  ├─ Issue 2.4 (报价审批) ────┤
  ├─ Issue 2.5 (合同审批) ────┤
  └─ Issue 2.6 (发票审批) ────┘

Sprint 3 (通知提醒)
  ├─ Issue 3.1 (通知框架) ──┐
  ├─ Issue 3.2 (阶段门提醒) ─┤
  ├─ Issue 3.3 (报价提醒) ───┤
  ├─ Issue 3.4 (合同提醒) ───┤
  ├─ Issue 3.5 (收款提醒) ───┤
  └─ Issue 3.6 (审批提醒) ────┘
      └─ 依赖 Sprint 2

Sprint 4 (数据导出)
  ├─ Issue 4.1 (Excel框架) ──┐
  ├─ Issue 4.2 (线索/商机导出) ┤
  ├─ Issue 4.3 (报价/合同导出) ┤
  ├─ Issue 4.4 (发票/应收导出) ┤
  └─ Issue 4.5 (PDF导出) ──────┘

Sprint 5 (前端完善)
  ├─ Issue 5.1 (审批中心) ── 依赖 Sprint 2
  ├─ Issue 5.2 (审批详情) ── 依赖 Sprint 2
  ├─ Issue 5.3 (工作台) ──── 依赖 Sprint 3
  ├─ Issue 5.4 (看板) ────── 无依赖
  └─ Issue 5.5 (漏斗) ────── 无依赖

Sprint 6 (高级功能)
  ├─ Issue 6.1 (客户360) ── 无依赖
  ├─ Issue 6.2 (CPQ UI) ──── 无依赖
  ├─ Issue 6.3 (预测增强) ── 无依赖
  ├─ Issue 6.4 (团队排名) ── 无依赖
  └─ Issue 6.5 (目标管理) ── 无依赖

Sprint 7 (权限与集成)
  ├─ Issue 7.1 (数据权限) ── 无依赖
  ├─ Issue 7.2 (操作权限) ── 依赖 Issue 7.1
  ├─ Issue 7.3 (进度影响收款) ── 依赖 Issue 1.5, Sprint 3
  └─ Issue 7.4 (验收触发开票) ── 依赖 Issue 1.5, Sprint 2

Sprint 8 (测试与文档)
  ├─ Issue 8.1 (单元测试) ── 依赖 Sprint 1-7
  ├─ Issue 8.2 (集成测试) ── 依赖 Sprint 1-7
  ├─ Issue 8.3 (API文档) ── 依赖 Sprint 1-7
  └─ Issue 8.4 (用户手册) ── 依赖 Sprint 1-7
```

---

## 十、开发建议

### 9.1 开发顺序建议

1. **第一阶段（核心功能）**：
   - **先完成 Sprint 1**：阶段门自动检查和收款计划绑定是核心业务规则，必须优先完成
   - **并行开发 Sprint 2 和 Sprint 4**：审批工作流和数据导出可以并行开发，无依赖关系
   - **Sprint 3 依赖 Sprint 2**：通知提醒中的审批提醒需要审批工作流完成

2. **第二阶段（重要功能）**：
   - **Sprint 5 依赖 Sprint 2 和 3**：前端页面需要后端 API 支持
   - **Sprint 7 可以并行开发**：权限控制和集成功能可以与其他 Sprint 并行
   - **Sprint 8 最后完成**：测试和文档需要所有功能完成后进行

3. **第三阶段（增强功能）**：
   - **Sprint 6 可以穿插进行**：高级功能增强，优先级较低，可以在其他 Sprint 间隙进行

### 9.2 技术栈建议

- **后端**: FastAPI, SQLAlchemy, APScheduler, openpyxl/pandas, reportlab/weasyprint
- **前端**: React, shadcn/ui, recharts/echarts, react-beautiful-dnd
- **测试**: pytest, jest, react-testing-library

### 9.3 代码质量要求

- 所有 API 必须有单元测试，覆盖率 ≥ 80%
- 所有前端组件必须有基础测试
- 代码必须通过 lint 检查
- 所有数据库变更必须有迁移脚本
- 所有新功能必须有 API 文档

---

## 十一、总结

本任务清单将销售管理模块的待开发功能细分为 **8 个 Sprint，共 38 个 Issue**，总计 **230 SP**（约 115 人天）。

**核心 Sprint（P0）**:
- Sprint 1: 阶段门自动检查与收款计划绑定（40 SP，5个Issue）
- Sprint 2: 审批工作流系统（35 SP，6个Issue）
- Sprint 3: 通知提醒系统（25 SP，6个Issue）

**重要 Sprint（P1）**:
- Sprint 4: 数据导出功能（20 SP，5个Issue）
- Sprint 5: 前端页面完善（30 SP，5个Issue）
- Sprint 7: 权限控制细化与集成功能（25 SP，4个Issue）
- Sprint 8: 测试与文档完善（20 SP，4个Issue）

**增强 Sprint（P2）**:
- Sprint 6: 高级功能增强（35 SP，5个Issue）

### 开发时间估算

| 阶段 | Sprint | 工时 | 周期 |
|------|--------|:----:|:----:|
| **第一阶段（核心功能）** | Sprint 1-3 | 100 SP | 5.5周 |
| **第二阶段（重要功能）** | Sprint 4-5, 7-8 | 95 SP | 5.5周 |
| **第三阶段（增强功能）** | Sprint 6 | 35 SP | 2周 |
| **总计** | 8个Sprint | 230 SP | 13周（约3个月） |

### 开发建议

1. **先完成 Sprint 1-3**：核心业务规则和流程必须优先完成
2. **并行开发 Sprint 4 和 Sprint 7**：数据导出和权限控制可以并行，无依赖关系
3. **Sprint 5 依赖 Sprint 2 和 3**：前端页面需要后端 API 支持
4. **Sprint 8 最后完成**：测试和文档需要所有功能完成后进行
5. **Sprint 6 可以穿插进行**：高级功能增强，优先级较低，可以在其他 Sprint 间隙进行

### 关键里程碑

- **里程碑 1**（Sprint 1-3 完成）：核心业务流程自动化完成，可以投入使用
- **里程碑 2**（Sprint 4-5, 7 完成）：重要功能完善，用户体验提升
- **里程碑 3**（Sprint 6, 8 完成）：所有功能完成，系统全面上线

---

**文档版本**: v1.0  
**最后更新**: 2026-01-15  
**维护人**: 开发团队
