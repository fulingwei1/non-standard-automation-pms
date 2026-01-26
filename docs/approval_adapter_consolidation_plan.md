# 审批适配器整合计划

> 日期: 2026-01-25
> 状态: 执行前准备完成

## 目标

整合两套适配器系统，消除重复，删除冗余的适配器版本，统一为单一的适配器架构。

## 当前架构分析

### 系统一：标准适配器（6个）

| 适配器 | 文件 | 继承 | 用途 |
|--------|------|------|------|
| EcnApprovalAdapter | adapters/ecn.py | ApprovalAdapter | WorkflowEngine使用 |
| QuoteApprovalAdapter | adapters/quote.py | ApprovalAdapter | WorkflowEngine使用 |
| ContractApprovalAdapter | adapters/contract.py | ApprovalAdapter | WorkflowEngine使用 |
| InvoiceApprovalAdapter | adapters/invoice.py | ApprovalAdapter | WorkflowEngine使用 |
| ProjectApprovalAdapter | adapters/project.py | ApprovalAdapter | WorkflowEngine使用 |
| TimesheetApprovalAdapter | adapters/timesheet.py | ApprovalAdapter | WorkflowEngine使用 |

**特点**:
- 继承 ApprovalAdapter 基类
- 实现标准回调方法（on_submit, on_approved, on_rejected等）
- 通过 ADAPTER_REGISTRY 注册
- WorkflowEngine 通过 get_adapter() 调用

### 系统二：高级适配器（2个）

| 适配器 | 文件 | 继承 | 用途 |
|--------|------|------|------|
| EcnApprovalAdapter | adapters/ecn_adapter.py | 无 | API端点直接使用 |
| SalesApprovalAdapter | adapters/sales_adapter.py | 无 | API端点直接使用 |

**特点**:
- 不继承 ApprovalAdapter 基类
- 包含额外的高级方法
- API端点直接导入使用
- 内部调用 WorkflowEngine

### 高级适配器的额外方法

#### EcnApprovalAdapter (ecn_adapter.py) - 10个方法
1. `submit_for_approval()` - 提交ECN到审批
2. `sync_from_approval_instance()` - 同步实例状态到ECN
3. `create_ecn_approval_records()` - 创建审批记录
4. `update_ecn_approval_from_action()` - 更新审批记录
5. `get_ecn_approvers()` - 获取审批人
6. `get_approval_status()` - 获取审批状态
7. `get_required_evaluators()` - 获取评估部门
8. `create_evaluation_tasks()` - 创建评估任务
9. `check_evaluation_complete()` - 检查评估完成
10. `_determine_approval_level()` - 确定审批层级

#### SalesApprovalAdapter (sales_adapter.py) - 7个方法
1. `submit_quote_for_approval()` - 提交报价审批
2. `submit_contract_for_approval()` - 提交合同审批
3. `submit_invoice_for_approval()` - 提交发票审批
4. `create_sales_approval_records()` - 创建审批记录
5. `update_sales_approval_from_action()` - 更新审批记录
6. `get_approval_status()` - 获取审批状态
7. `_create_quote_approval()` - 创建报价审批记录
8. `_create_contract_approval()` - 创建合同审批记录
9. `_create_invoice_approval()` - 创建发票审批记录

## 整合方案

### 核心策略

**将高级适配器的额外方法迁移到标准适配器，删除冗余的高级适配器文件。**

### Phase 1: 扩展标准适配器（添加高级方法）

#### 任务 1.1: 扩展 EcnApprovalAdapter (adapters/ecn.py)
**目标**: 添加 ecn_adapter.py 中的 10 个方法

**添加的方法**:
1. `submit_for_approval(ecn, initiator_id, title, summary, urgency, cc_user_ids)` - 使用 WorkflowEngine
2. `sync_from_approval_instance(instance, ecn)` - 同步状态
3. `create_ecn_approval_records(instance, ecn)` - 创建审批记录
4. `update_ecn_approval_from_action(task, action, comment)` - 更新记录
5. `get_ecn_approvers(ecn, level, matrix)` - 获取审批人
6. `get_approval_status(ecn)` - 获取审批状态
7. `get_required_evaluators(entity_id)` - 获取评估部门
8. `create_evaluation_tasks(entity_id, instance)` - 创建评估任务
9. `check_evaluation_complete(entity_id)` - 检查评估完成
10. `_determine_approval_level(node_id, ecn)` - 确定层级

**实现细节**:
- 方法内部调用 WorkflowEngine.create_instance()
- 创建 EcnApproval 记录到 ecn_approvals 表
- 从 ApprovalTask 同步到 EcnApproval
- 利用已有的回调方法（on_submit, on_approved等）

#### 任务 1.2: 扩展 QuoteApprovalAdapter (adapters/quote.py)
**目标**: 添加 SalesApprovalAdapter 中的报价相关方法

**添加的方法**:
1. `submit_for_approval(quote_version, initiator_id, title, summary, urgency, cc_user_ids)` - 使用 WorkflowEngine
2. `create_quote_approval(instance, task)` - 创建 QuoteApproval 记录
3. `update_quote_approval_from_action(task, action, comment)` - 更新 QuoteApproval

#### 任务 1.3: 扩展 ContractApprovalAdapter (adapters/contract.py)
**目标**: 添加 SalesApprovalAdapter 中的合同相关方法

**添加的方法**:
1. `submit_for_approval(contract, initiator_id, title, summary, urgency, cc_user_ids)` - 使用 WorkflowEngine
2. `create_contract_approval(instance, task)` - 创建 ContractApproval 记录
3. `update_contract_approval_from_action(task, action, comment)` - 更新 ContractApproval

#### 任务 1.4: 扩展 InvoiceApprovalAdapter (adapters/invoice.py)
**目标**: 添加 SalesApprovalAdapter 中的发票相关方法

**添加的方法**:
1. `submit_for_approval(invoice, initiator_id, title, summary, urgency, cc_user_ids)` - 使用 WorkflowEngine
2. `create_invoice_approval(instance, task)` - 创建 InvoiceApproval 记录
3. `update_invoice_approval_from_action(task, action, comment)` - 更新 InvoiceApproval

### Phase 2: 删除冗余适配器

#### 任务 2.1: 删除 ecn_adapter.py
- 文件: `app/services/approval_engine/adapters/ecn_adapter.py`
- 原因: 功能已迁移到 adapters/ecn.py

#### 任务 2.2: 删除 sales_adapter.py
- 文件: `app/services/approval_engine/adapters/sales_adapter.py`
- 原因: 功能已迁移到各标准适配器

### Phase 3: 更新导出和注册表

#### 任务 3.1: 更新 adapters/__init__.py
- 从 ADAPTER_REGISTRY 中删除（如有的话）
- 确保只包含 6 个标准适配器
- 所有标准适配器都支持 WorkflowEngine 调用

#### 任务 3.2: 更新 approval_engine/__init__.py
- 删除对 ecn_adapter.py 的导入
- 删除对 sales_adapter.py 的导入
- 确保只从 adapters 模块导入标准适配器

### Phase 4: 更新 API 端点

#### 任务 4.1: 更新 /api/v1/endpoints/approvals/router.py

**当前代码** (第 91-107 行):
```python
if request.entity_type == "ECN":
    adapter = EcnApprovalAdapter(db)
    instance = adapter.submit_for_approval(
        ecn=ecn,
        initiator_id=current_user.id,
        ...
    )
```

**修改为使用 WorkflowEngine**:
```python
from app.services.approval_engine.workflow_engine import WorkflowEngine
from app.models.ecn import Ecn

workflow_engine = WorkflowEngine(db)

if request.entity_type == "ECN":
    ecn = db.query(Ecn).filter(Ecn.id == request.entity_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail=f"ECN {request.entity_id} 不存在")
    
    instance = workflow_engine.submit_approval(
        template_code="ECN_STANDARD",
        entity_type="ECN",
        entity_id=request.entity_id,
        form_data={...},  # 从 ecn 构建
        initiator_id=current_user.id,
        title=request.title,
        summary=request.summary,
        urgency=request.urgency,
        cc_user_ids=request.cc_user_ids,
    )
```

**对所有 entity_type 应用相同模式**:
- QUOTE → WorkflowEngine.submit_approval(template_code="SALES_QUOTE", ...)
- CONTRACT → WorkflowEngine.submit_approval(template_code="SALES_CONTRACT", ...)
- INVOICE → WorkflowEngine.submit_approval(template_code="SALES_INVOICE", ...)

#### 任务 4.2: 更新审批操作端点 (approve, reject)

**当前代码** (第 240-300 行):
- 直接更新旧的审批记录表（QuoteApproval, ContractApproval等）

**修改为使用标准适配器的回调**:
- 通过 WorkflowEngine.execute_action() 执行审批
- WorkflowEngine 会调用标准适配器的 on_approved() 或 on_rejected()
- 标准适配器的回调会自动更新业务实体状态

**新代码模式**:
```python
from app.services.approval_engine.workflow_engine import WorkflowEngine

workflow_engine = WorkflowEngine(db)

# 执行审批
record = workflow_engine.execute_approval(
    instance_id=instance_id,
    approver_id=current_user.id,
    action="APPROVE",  # 或 "REJECT"
    comment=request.comment,
)
```

### Phase 5: 测试

#### 任务 5.1: 运行现有测试
```bash
# 运行所有审批相关测试
pytest tests/unit/test_approval_engine* -v
```

#### 任务 5.2: 手动测试流程
1. 测试 ECN 提交审批
2. 测试报价提交审批
3. 测试合同提交审批
4. 测试发票提交审批
5. 测试审批通过/驳回

### Phase 6: 文档更新

#### 任务 6.1: 更新统一审批系统迁移指南.md
- 添加整合说明
- 更新 API 使用示例
- 标注高级适配器方法已迁移到标准适配器

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 破坏现有 API | 高 | 保留旧 API 端点逻辑，逐步迁移 |
| 审批记录丢失 | 高 | 迁移前备份 ecn_approvals 等表数据 |
| WorkflowEngine 不支持某些方法 | 中 | 在迁移前验证 WorkflowEngine 有需要的方法 |
| 性能下降 | 低 | 性能基准测试 |
| 数据不一致 | 中 | 充分测试，回滚计划 |

## 回滚计划

如果整合出现问题：
1. 恢复删除的适配器文件（从 git）
2. 恢复 API 端点的旧实现
3. 重新部署到上一个稳定版本

## 成功标准

1. ✅ 所有 6 个标准适配器都添加了高级方法
2. ✅ ecn_adapter.py 已删除
3. ✅ sales_adapter.py 已删除
4. ✅ adapters/__init__.py 不再导入高级适配器
5. ✅ approval_engine/__init__.py 不再导入高级适配器
6. ✅ API 端点使用 WorkflowEngine 而不是高级适配器
7. ✅ 所有现有测试通过
8. ✅ 手动测试所有审批流程成功
9. ✅ 文档更新完成

## 实施顺序

1. Phase 1: 扩展标准适配器
2. Phase 2: 删除冗余适配器
3. Phase 3: 更新导出和注册表
4. Phase 4: 更新 API 端点
5. Phase 5: 测试
6. Phase 6: 文档更新

## 预计工作量

| Phase | 任务数 | 预计时间 |
|-------|--------|----------|
| Phase 1 | 4 个适配器扩展 | 2-3 小时 |
| Phase 2 | 删除 2 个文件 | 5 分钟 |
| Phase 3 | 更新 2 个文件 | 10 分钟 |
| Phase 4 | 更新 API 端点 | 1-2 小时 |
| Phase 5 | 测试 | 1 小时 |
| Phase 6 | 文档更新 | 30 分钟 |

**总计**: 约 5-7 小时

## 下一步

等待确认后开始执行 Phase 1（扩展标准适配器）。
