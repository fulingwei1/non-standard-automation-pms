# 审批适配器方法检查清单

> 日期: 2026-01-25

## ApprovalAdapter 基类方法要求

### 必需方法（抽象方法）

| 方法 | 说明 |
|------|------|
| `get_entity(entity_id)` | 获取业务实体对象 |
| `get_entity_data(entity_id)` | 获取实体数据（用于条件路由） |
| `on_submit(entity_id, instance)` | 提交时的回调 |
| `on_approved(entity_id, instance)` | 审批通过时的回调 |
| `on_rejected(entity_id, instance)` | 审批驳回时的回调 |

### 可选方法（有默认实现）

| 方法 | 说明 | 默认实现 |
|------|------|----------|
| `on_withdrawn(entity_id, instance)` | 撤回时的回调 | 空实现 |
| `on_terminated(entity_id, instance)` | 终止时的回调 | 空实现 |
| `resolve_approvers(node, context)` | 动态解析审批人 | 返回空列表 |
| `get_title(entity_id)` | 生成审批标题 | 返回默认格式 |
| `get_summary(entity_id)` | 生成审批摘要 | 返回空字符串 |
| `get_form_data(entity_id)` | 获取表单数据 | 返回 `get_entity_data()` |
| `validate_submit(entity_id)` | 验证是否可提交 | 返回 (True, None) |
| `get_cc_user_ids(entity_id)` | 获取默认抄送人 | 返回空列表 |

## 各适配器方法实现检查

### 1. EcnApprovalAdapter (adapters/ecn.py)

| 方法 | 状态 | 备注 |
|------|------|------|
| `get_entity()` | ✅ | 获取 Ecn 对象 |
| `get_entity_data()` | ✅ | 包含 ECN 评估汇总 |
| `on_submit()` | ✅ | 更新状态为 EVALUATING |
| `on_approved()` | ✅ | 更新状态为 APPROVED |
| `on_rejected()` | ✅ | 更新状态为 REJECTED |
| `on_withdrawn()` | ✅ | 更新状态为 DRAFT |
| `on_terminated()` | ⚠️ | 使用默认实现（空） |
| `resolve_approvers()` | ⚠️ | 使用默认实现（返回空） |
| `get_title()` | ✅ | 返回 "ECN审批 - {ecn_no}: {ecn_title}" |
| `get_summary()` | ✅ | 返回类型、项目、成本、工期、优先级 |
| `get_form_data()` | ⚠️ | 使用默认实现 |
| `validate_submit()` | ✅ | 检查状态、变更原因、变更描述 |
| `get_cc_user_ids()` | ⚠️ | 使用默认实现（返回空） |

**额外方法（ECN 特有）**:
- `get_required_evaluators(entity_id)` - 获取需要的评估部门列表
- `create_evaluation_tasks(entity_id, instance)` - 创建评估任务
- `check_evaluation_complete(entity_id)` - 检查评估是否完成

### 2. QuoteApprovalAdapter (adapters/quote.py)

| 方法 | 状态 | 备注 |
|------|------|------|
| `get_entity()` | ✅ | 获取 Quote 对象 |
| `get_entity_data()` | ✅ | 包含版本、毛利率、交期等 |
| `on_submit()` | ✅ | 更新状态为 PENDING_APPROVAL |
| `on_approved()` | ✅ | 更新状态为 APPROVED |
| `on_rejected()` | ✅ | 更新状态为 REJECTED |
| `on_withdrawn()` | ✅ | 更新状态为 DRAFT |
| `on_terminated()` | ⚠️ | 使用默认实现（空） |
| `resolve_approvers()` | ⚠️ | 使用默认实现（返回空） |
| `get_title()` | ✅ | 返回 "报价审批 - {quote_code} ({customer})" |
| `get_summary()` | ✅ | 返回客户、总价、毛利率、交期 |
| `get_form_data()` | ⚠️ | 使用默认实现 |
| `validate_submit()` | ✅ | 检查状态、版本 |
| `get_cc_user_ids()` | ⚠️ | 使用默认实现（返回空） |

### 3. ContractApprovalAdapter (adapters/contract.py)

| 方法 | 状态 | 备注 |
|------|------|------|
| `get_entity()` | ✅ | 获取 Contract 对象 |
| `get_entity_data()` | ✅ | 包含合同金额、客户等 |
| `on_submit()` | ✅ | 更新状态为 PENDING_APPROVAL |
| `on_approved()` | ✅ | 更新状态为 APPROVED |
| `on_rejected()` | ✅ | 更新状态为 REJECTED |
| `on_withdrawn()` | ✅ | 更新状态为 DRAFT |
| `on_terminated()` | ⚠️ | 使用默认实现（空） |
| `resolve_approvers()` | ⚠️ | 使用默认实现（返回空） |
| `get_title()` | ✅ | 返回 "合同审批 - {contract_code} ({customer})" |
| `get_summary()` | ✅ | 返回客户、合同金额、签订日期 |
| `get_form_data()` | ⚠️ | 使用默认实现 |
| `validate_submit()` | ✅ | 检查状态、金额 |
| `get_cc_user_ids()` | ⚠️ | 使用默认实现（返回空） |

### 4. InvoiceApprovalAdapter (adapters/invoice.py)

| 方法 | 状态 | 备注 |
|------|------|------|
| `get_entity()` | ✅ | 获取 Invoice 对象 |
| `get_entity_data()` | ✅ | 包含发票金额、类型等 |
| `on_submit()` | ✅ | 更新状态为 PENDING_APPROVAL |
| `on_approved()` | ✅ | 更新状态为 APPROVED |
| `on_rejected()` | ✅ | 更新状态为 REJECTED |
| `on_withdrawn()` | ✅ | 更新状态为 DRAFT |
| `on_terminated()` | ⚠️ | 使用默认实现（空） |
| `resolve_approvers()` | ⚠️ | 使用默认实现（返回空） |
| `get_title()` | ✅ | 返回 "发票审批 - {invoice_code} ({buyer})" |
| `get_summary()` | ✅ | 返回购买方、金额、类型、合同 |
| `get_form_data()` | ⚠️ | 使用默认实现 |
| `validate_submit()` | ✅ | 检查状态、金额、购买方名称 |
| `get_cc_user_ids()` | ⚠️ | 使用默认实现（返回空） |

### 5. ProjectApprovalAdapter (adapters/project.py)

| 方法 | 状态 | 备注 |
|------|------|------|
| `get_entity()` | ✅ | 获取 Project 对象 |
| `get_entity_data()` | ✅ | 包含项目信息、金额、进度等 |
| `on_submit()` | ✅ | 更新状态为 PENDING_APPROVAL |
| `on_approved()` | ✅ | 根据阶段更新状态为 ST02 |
| `on_rejected()` | ✅ | 更新状态为 REJECTED |
| `on_withdrawn()` | ✅ | 更新状态为 ST01（草稿） |
| `on_terminated()` | ⚠️ | 使用默认实现（空） |
| `resolve_approvers()` | ⚠️ | 使用默认实现（返回空） |
| `get_title()` | ✅ | 返回 "项目审批 - {project_code}: {project_name}" |
| `get_summary()` | ✅ | 返回客户、合同金额、项目经理、类型 |
| `get_form_data()` | ⚠️ | 使用默认实现 |
| `validate_submit()` | ✅ | 检查状态、项目名称、项目经理 |
| `get_cc_user_ids()` | ⚠️ | 使用默认实现（返回空） |

### 6. TimesheetApprovalAdapter (adapters/timesheet.py)

| 方法 | 状态 | 备注 |
|------|------|------|
| `get_entity()` | ✅ | 获取 Timesheet 对象 |
| `get_entity_data()` | ✅ | 包含工时、日期、项目等 |
| `on_submit()` | ✅ | 更新状态为 SUBMITTED，设置提交时间 |
| `on_approved()` | ✅ | 更新状态为 APPROVED，设置审批时间 |
| `on_rejected()` | ✅ | 更新状态为 REJECTED |
| `on_withdrawn()` | ✅ | 更新状态为 DRAFT，清除提交时间 |
| `on_terminated()` | ⚠️ | 使用默认实现（空） |
| `resolve_approvers()` | ⚠️ | 使用默认实现（返回空） |
| `get_title()` | ✅ | 返回 "工时审批 - {user_name} {date}" |
| `get_summary()` | ✅ | 返回员工、日期、工时、项目、加班 |
| `get_form_data()` | ⚠️ | 使用默认实现 |
| `validate_submit()` | ✅ | 检查状态、工时、日期 |
| `get_cc_user_ids()` | ⚠️ | 使用默认实现（返回空） |

## 需要完成的工作

### 高优先级
1. ✅ 所有必需方法都已实现
2. ⚠️ 所有可选方法都有实现（部分使用默认实现）

### 中优先级
3. 实现 `get_cc_user_ids()` 方法以支持默认抄送人
4. 实现 `on_terminated()` 回调（如需要）
5. 为需要动态审批人的适配器实现 `resolve_approvers()`

### 低优先级
6. 优化 `get_form_data()` 实现以提供更结构化的表单数据
7. 为所有适配器编写单元测试
8. 更新文档说明各适配器的特性

## 总结

✅ **所有 6 个标准适配器都已完整实现必需方法**
⚠️ **可选方法都有实现（大部分使用默认实现）**
⚠️ **无缺失的关键功能**

当前适配器架构基本完整，可以支持基本的审批流程。优化建议是为了增强功能性和可维护性。
