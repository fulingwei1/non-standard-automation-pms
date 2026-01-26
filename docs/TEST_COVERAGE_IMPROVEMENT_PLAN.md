# 测试覆盖率提升计划

## 概述

本文档记录了测试覆盖率分析结果和改进建议。

**当前状态**：约32%覆盖率
**目标状态**：80%覆盖率

## 已完成的工作

### 新增/改进的测试文件

1. **test_bonus_distribution_service.py** - 重写完整测试（原为TODO占位符）
   - `validate_sheet_for_distribution` - 8个测试用例
   - `create_calculation_from_team_allocation` - 4个测试用例
   - `create_distribution_record` - 2个测试用例
   - `check_distribution_exists` - 3个测试用例
   - 集成测试 - 1个测试用例

2. **test_acceptance_bonus_service.py** - 新建测试文件
   - `get_active_rules` - 2个测试用例
   - `calculate_sales_bonus` - 4个测试用例
   - `calculate_presale_bonus` - 4个测试用例
   - `calculate_project_bonus` - 4个测试用例
   - 集成测试 - 2个测试用例

3. **test_data_scope_services.py** - 新建测试文件
   - `UserScopeService` - 12个测试用例
   - `ProjectFilterService` - 10个测试用例
   - `check_project_access` - 8个测试用例
   - `DataScopeService` - 1个测试用例

---

## 高优先级改进建议

### 1. 零覆盖率服务（0%）

以下服务需要立即添加测试：

| 服务 | 文件位置 | 业务重要性 | 建议优先级 |
|------|----------|------------|------------|
| `alert_pdf_service.py` | app/services/ | 报表生成 | P1 |
| `alert_response_service.py` | app/services/ | 告警处理 | P1 |
| `alert_trend_service.py` | app/services/ | 告警分析 | P2 |
| `alert_subscription_service.py` | app/services/ | 告警订阅 | P2 |
| `collaboration_rating_service.py` | app/services/ | 协作评分 | P2 |
| `delay_root_cause_service.py` | app/services/ | 延期分析 | P2 |
| `assembly_attr_recommender.py` | app/services/ | 推荐系统 | P3 |
| `assembly_kit_optimizer.py` | app/services/ | 优化算法 | P3 |

### 2. 低覆盖率API端点（<20%）

需要增加API集成测试的模块：

- `/api/v1/approval/` - 审批流程
- `/api/v1/costs/` - 成本管理
- `/api/v1/alerts/` - 告警管理
- `/api/v1/analytics/` - 数据分析
- `/api/v1/reports/` - 报表生成

### 3. 业务流程集成测试

需要新增的端到端测试场景：

1. **项目完整生命周期** (S1→S9)
   - 各阶段门禁检查
   - 阶段推进触发器
   - 状态变更通知

2. **审批工作流**
   - 多级审批链
   - 审批委托
   - 审批超时处理

3. **奖金计算流程**
   - 验收完成触发
   - 团队奖金分配
   - 个人发放记录

4. **成本超支预警**
   - 预警触发条件
   - 预警升级机制
   - 预警响应处理

---

## 测试质量改进

### 1. 修复/清理遗留测试

`tests/.broken_tests/` 目录中有12个失效测试需要处理：

```
tests/.broken_tests/
├── approval_workflow_legacy/  # 5个文件 - 评估后删除或重写
├── test_bonus_allocation_parser.py  # 评估是否仍需要
├── test_business_workflows.py  # 已被新测试替代
├── test_critical_apis.py  # 已被集成测试替代
└── ...
```

**建议**：评估每个文件，可恢复的修复并移回主目录，已废弃的删除。

### 2. 增加边界条件测试

以下场景需要更多边界测试：

- 金额为0或负数的处理
- 日期边界（跨月、跨年）
- 空数据集处理
- 并发操作冲突
- 事务回滚场景

### 3. 增加错误处理测试

需要验证的异常场景：

- 数据库连接失败
- 外部服务超时
- 无效输入数据
- 权限不足
- 资源不存在

---

## 测试执行指南

### 运行所有测试

```bash
pytest tests/ -v
```

### 按类别运行

```bash
# 单元测试
pytest tests/unit/ -v

# API测试
pytest tests/api/ -v

# 集成测试
pytest tests/integration/ -v

# 带覆盖率报告
pytest --cov=app --cov-report=html
```

### 运行新增测试

```bash
# 奖金服务测试
pytest tests/unit/test_bonus_distribution_service.py -v
pytest tests/unit/test_acceptance_bonus_service.py -v

# 数据权限测试
pytest tests/unit/test_data_scope_services.py -v
```

---

## 覆盖率目标路线图

| 阶段 | 目标覆盖率 | 主要工作 |
|------|------------|----------|
| 当前 | ~32% | 基础测试框架完善 |
| Phase 1 | 40% | 完成零覆盖服务测试 |
| Phase 2 | 50% | 增加API集成测试 |
| Phase 3 | 60% | 增加业务流程测试 |
| Phase 4 | 70% | 增加边界/异常测试 |
| Phase 5 | 80% | 完善遗漏场景 |

---

## CI/CD 集成建议

### 1. 覆盖率门禁

在 `pytest.ini` 中添加：

```ini
[pytest]
addopts = --cov-fail-under=40
```

### 2. PR 检查

在 CI 流程中添加：

```yaml
- name: Run tests with coverage
  run: pytest --cov=app --cov-report=xml

- name: Check coverage threshold
  run: coverage report --fail-under=40
```

### 3. 覆盖率报告

生成并存档覆盖率报告：

```yaml
- name: Upload coverage report
  uses: codecov/codecov-action@v3
  with:
    files: coverage.xml
```

---

## 总结

通过本次分析和改进，我们已经：

1. 识别了21个零覆盖率服务
2. 识别了684个低覆盖率API端点
3. 创建了3个新测试文件，新增约50个测试用例
4. 制定了覆盖率提升路线图

下一步重点工作：
1. 完成剩余零覆盖率服务的测试
2. 增加API集成测试
3. 清理遗留测试
4. 在CI/CD中集成覆盖率检查
