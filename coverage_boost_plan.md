# 代码覆盖率提升计划

## 当前状态
- **总体覆盖率**: 12.65%
- **目标覆盖率**: 60%+
- **需要提升**: 47.35%

## 策略
由于有 2070 个测试文件和大量未覆盖的模块，我们采用分批次、优先级驱动的方法：

### 批次 1: Core 模块（高优先级）
优先处理代码行数 > 50 且覆盖率为 0% 的核心模块：

1. app/core/state_machine/base.py (169行)
2. app/core/schemas/validators.py (171行)
3. app/core/state_machine/acceptance.py (148行)
4. app/core/secret_manager.py (122行)
5. app/core/csrf.py (116行)
6. app/core/permissions/timesheet.py (105行)
7. app/core/state_machine/ecn.py (103行)
8. app/core/exception_handlers.py (95行)
9. app/core/state_machine/issue.py (94行)
10. app/core/state_machine/milestone.py (91行)

### 批次 2: Services 模块（核心业务）
优先处理业务关键模块：

1. app/services/ai_emotion_service.py (215行)
2. app/services/account_lockout_service.py (177行)
3. app/services/ai_planning/resource_optimizer.py (151行)
4. app/services/ai_planning/schedule_optimizer.py (143行)
5. app/services/acceptance_completion_service.py (139行)

### 批次 3: 更多 Services 模块
根据批次 1-2 的进展，继续补充更多模块测试。

## 执行步骤

### 第一批（预计覆盖率提升至 25-30%）
1. 为 Core 模块的前 10 个文件补充测试
2. 运行测试验证
3. 提交到 GitHub

### 第二批（预计覆盖率提升至 40-50%）
1. 为 Services 模块的前 15 个文件补充测试
2. 运行测试验证
3. 提交到 GitHub

### 第三批（预计覆盖率提升至 60%+）
1. 根据最新覆盖率报告，补充剩余模块测试
2. 运行测试验证
3. 提交到 GitHub

## 测试编写原则
- 使用 pytest + Mock
- 覆盖核心业务逻辑（if/else 分支）
- 覆盖错误处理路径
- 覆盖边界条件
- 确保测试可维护性

## 环境变量
```bash
SECRET_KEY="test-secret-key-for-ci-with-32-chars-minimum!"
DATABASE_URL="sqlite:///:memory:"
REDIS_URL="redis://localhost:6379/0"
```

## 进度追踪
- [ ] 批次 1 完成
- [ ] 批次 2 完成
- [ ] 批次 3 完成
- [ ] 最终报告生成
