# 审批适配器完成与优化计划

> 日期: 2026-01-25
> 状态: 待实施

## 当前状态

### ✅ 已实现的适配器（继承自 ApprovalAdapter）

| 适配器 | 文件 | 功能状态 | 测试状态 |
|--------|------|----------|----------|
| EcnApprovalAdapter | adapters/ecn.py | 100% | ❌ |
| QuoteApprovalAdapter | adapters/quote.py | 100% | ❌ |
| ContractApprovalAdapter | adapters/contract.py | 100% | ❌ |
| InvoiceApprovalAdapter | adapters/invoice.py | 100% | ❌ |
| ProjectApprovalAdapter | adapters/project.py | 100% | ❌ |
| TimesheetApprovalAdapter | adapters/timesheet.py | 100% | ❌ |

### ⚠️ 架构问题

#### 问题 1: 双套适配器系统
- **标准适配器**（继承 ApprovalAdapter）：供 WorkflowEngine 内部使用
- **高级适配器**（不继承基类）：供 API 端点直接使用
- 造成代码重复和维护困难

#### 问题 2: 适配器重复
- `EcnApprovalAdapter` 存在两个版本：
  - `adapters/ecn.py` - 继承自 ApprovalAdapter
  - `adapters/ecn_adapter.py` - 独立类

#### 问题 3: 注册表不完整
`ADAPTER_REGISTRY` 只包含 6 个标准适配器，缺少：
- `SalesApprovalAdapter`（高级适配器）
- `ecn_adapter.py` 中的 `EcnApprovalAdapter`

#### 问题 4: 缺少方法验证
部分适配器可能缺少以下可选方法的实现：
- `resolve_approvers()` - 动态解析审批人
- `get_cc_user_ids()` - 获取默认抄送人
- `get_form_data()` - 获取表单数据
- `on_terminated()` - 终止回调

## 优化方案

### 方案 A: 保持现状（最小改动）
- 保留双套适配器系统
- 确保所有标准适配器完全实现
- 更新注册表包含所有适配器
- 为两套系统编写独立测试

**优点**:
- 改动最小，风险低
- 不影响现有功能

**缺点**:
- 维护两套系统
- 代码重复
- 潜在不一致

### 方案 B: 整合为统一系统（推荐）
- 将高级适配器的功能整合到标准适配器中
- 删除重复适配器
- 所有适配器都继承 ApprovalAdapter
- 更新 API 端点使用统一接口

**优点**:
- 统一架构，易维护
- 消除代码重复
- 一致的行为

**缺点**:
- 改动较大
- 需要全面测试

## 具体任务（方案 B）

### Phase 1: 扩展标准适配器
1. 为每个标准适配器添加高级方法
   - `submit_for_approval()` - 提交审批到引擎
   - `sync_from_approval_instance()` - 从引擎同步状态
   - `create_approval_records()` - 创建审批记录

### Phase 2: 删除重复适配器
1. 删除 `adapters/ecn_adapter.py`
2. 删除 `adapters/sales_adapter.py`
3. 更新 `app/services/approval_engine/__init__.py` 的导入

### Phase 3: 更新注册表
1. 更新 `ADAPTER_REGISTRY` 确保包含所有业务类型

### Phase 4: 更新 API 端点
1. 修改 API 端点使用 `WorkflowEngine` 而不是直接调用高级适配器
2. 使用标准适配器的扩展方法

### Phase 5: 测试
1. 为每个适配器编写单元测试
2. 编写集成测试验证审批流程
3. 测试所有业务实体的提交、审批、驳回流程

## 立即行动项

### 高优先级
1. 验证所有标准适配器的必需方法
2. 检查可选方法实现
3. 修复任何缺失的方法
4. 统一适配器架构

### 中优先级
5. 为每个适配器编写单元测试
6. 更新注册表
7. 删除重复适配器

### 低优先级
8. 编写集成测试
9. 更新文档
10. 性能优化

## 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 破坏现有 API | 高 | 中 | 保留旧端点，逐步迁移 |
| 数据不一致 | 高 | 低 | 充分测试，回滚计划 |
| 性能下降 | 中 | 低 | 性能基准测试 |
| 适配器方法缺失 | 中 | 中 | 完整的方法检查列表 |

## 成功标准

1. 所有 6 个标准适配器 100% 实现所有方法
2. 所有适配器都有单元测试覆盖
3. API 端点正确使用统一适配器
4. 无重复或未使用的适配器
5. 所有测试通过
6. 文档更新完整

## 下一步

等待确认采用哪个方案后开始实施。
