# 通用批量操作框架使用指南

> **创建时间**: 2026-01-27  
> **状态**: ✅ 已完成

---

## 一、框架概述

通用批量操作框架 (`app/utils/batch_operations.py`) 提供了统一的批量操作接口，减少代码重复，提高开发效率。

### 核心特性

1. **统一的执行流程**：获取实体 → 验证 → 执行操作 → 记录日志 → 提交事务
2. **灵活的验证机制**：支持自定义验证逻辑
3. **数据范围过滤**：支持基于权限的数据范围过滤
4. **操作日志记录**：支持自定义日志记录函数
5. **错误处理**：统一的错误处理和结果统计
6. **事务管理**：自动处理事务提交和回滚

---

## 二、核心类

### 2.1 BatchOperationExecutor

批量操作执行器，提供统一的批量操作接口。

```python
from app.utils.batch_operations import BatchOperationExecutor
from app.models.task_center import TaskUnified

executor = BatchOperationExecutor(
    model=TaskUnified,
    db=db,
    current_user=current_user
)
```

### 2.2 BatchOperationResult

批量操作结果，包含成功数量、失败数量和失败项详情。

```python
result = BatchOperationResult()
result.add_success()
result.add_failure(entity_id=123, reason="任务已完成")
```

---

## 三、使用示例

### 3.1 基础批量更新

```python
from app.utils.batch_operations import BatchOperationExecutor
from app.models.task_center import TaskUnified
from datetime import datetime

executor = BatchOperationExecutor(
    model=TaskUnified,
    db=db,
    current_user=current_user
)

# 批量完成任务
result = executor.batch_status_update(
    entity_ids=[1, 2, 3],
    new_status="COMPLETED",
    validator_func=lambda task: task.status != "COMPLETED",
    error_message="任务已完成，不能重复完成"
)
```

### 3.2 自定义操作

```python
def complete_task(task: TaskUnified):
    """完成任务的操作函数"""
    task.status = "COMPLETED"
    task.progress = 100
    task.actual_end_date = datetime.now().date()
    task.updated_by = current_user.id

result = executor.execute(
    entity_ids=[1, 2, 3],
    operation_func=complete_task,
    validator_func=lambda task: task.status != "COMPLETED",
    error_message="任务已完成",
    operation_type="BATCH_COMPLETE"
)
```

### 3.3 带数据范围过滤

```python
from app.utils.batch_operations import BatchOperationExecutor, create_scope_filter
from app.services.data_scope import DataScopeService
from app.models.issue import Issue

# 创建数据范围过滤函数
scope_filter = create_scope_filter(
    model=Issue,
    scope_service=DataScopeService,
    filter_method="filter_issues_by_scope"
)

executor = BatchOperationExecutor(
    model=Issue,
    db=db,
    current_user=current_user,
    scope_filter_func=scope_filter
)

result = executor.batch_status_update(
    entity_ids=[1, 2, 3],
    new_status="CLOSED",
    validator_func=lambda issue: issue.status != "CLOSED",
    error_message="问题已关闭"
)
```

### 3.4 带操作日志

```python
def log_issue_operation(issue: Issue, operation_type: str):
    """记录问题操作日志"""
    from app.models.issue import IssueFollowUpRecord
    
    follow_up = IssueFollowUpRecord(
        issue_id=issue.id,
        follow_up_type=operation_type,
        content=f"批量操作：{operation_type}",
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=issue.status,
        new_status=issue.status,
    )
    db.add(follow_up)

result = executor.execute(
    entity_ids=[1, 2, 3],
    operation_func=lambda issue: setattr(issue, 'status', 'CLOSED'),
    validator_func=lambda issue: issue.status != "CLOSED",
    error_message="问题已关闭",
    log_func=log_issue_operation,
    operation_type="BATCH_CLOSE"
)
```

### 3.5 批量删除

```python
result = executor.batch_delete(
    entity_ids=[1, 2, 3],
    validator_func=lambda task: task.task_type == "PERSONAL",
    error_message="只能删除个人任务",
    soft_delete=True,  # 软删除
    soft_delete_field="is_active"
)
```

---

## 四、API端点集成示例

### 4.1 任务中心批量完成

**重构前**:
```python
@router.post("/batch/complete")
def batch_complete_tasks(
    task_ids: List[int] = Body(...),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "任务已完成"})
                continue
            
            task.status = "COMPLETED"
            task.progress = 100
            task.actual_end_date = datetime.now().date()
            task.updated_by = current_user.id
            
            log_task_operation(...)
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    return BatchOperationResponse(...)
```

**重构后**:
```python
from app.utils.batch_operations import BatchOperationExecutor
from app.schemas.common import BatchOperationResponse

@router.post("/batch/complete", response_model=BatchOperationResponse)
def batch_complete_tasks(
    task_ids: List[int] = Body(...),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def complete_task(task: TaskUnified):
        task.status = "COMPLETED"
        task.progress = 100
        task.actual_end_date = datetime.now().date()
        task.updated_by = current_user.id
    
    def log_func(task: TaskUnified, op_type: str):
        from .batch_helpers import log_task_operation
        log_task_operation(
            db, task.id, "BATCH_COMPLETE", f"批量完成任务：{task.title}",
            current_user.id, current_user.real_name or current_user.username
        )
    
    # 预过滤：只处理分配给当前用户的任务
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=complete_task,
        validator_func=lambda task: task.status != "COMPLETED",
        error_message="任务已完成",
        log_func=log_func,
        operation_type="BATCH_COMPLETE",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())
```

---

## 五、优势对比

### 5.1 代码量减少

- **重构前**: 每个批量操作端点约 50-80 行代码
- **重构后**: 每个批量操作端点约 20-30 行代码
- **减少**: 约 60% 代码量

### 5.2 代码复用

- **统一的事务管理**
- **统一的错误处理**
- **统一的结果格式**
- **统一的验证机制**

### 5.3 易于维护

- **集中管理批量操作逻辑**
- **统一的测试策略**
- **易于扩展新功能**

---

## 六、迁移指南

### 6.1 迁移步骤

1. **导入框架**
   ```python
   from app.utils.batch_operations import BatchOperationExecutor
   from app.schemas.common import BatchOperationResponse
   ```

2. **创建执行器**
   ```python
   executor = BatchOperationExecutor(
       model=YourModel,
       db=db,
       current_user=current_user
   )
   ```

3. **定义操作函数**
   ```python
   def operation_func(entity: YourModel):
       # 执行具体操作
       entity.status = "NEW_STATUS"
   ```

4. **定义验证函数**（可选）
   ```python
   def validator_func(entity: YourModel) -> bool:
       return entity.status != "NEW_STATUS"
   ```

5. **执行批量操作**
   ```python
   result = executor.execute(
       entity_ids=[1, 2, 3],
       operation_func=operation_func,
       validator_func=validator_func
   )
   ```

6. **返回结果**
   ```python
   return BatchOperationResponse(**result.to_dict())
   ```

### 6.2 注意事项

1. **数据范围过滤**: 如果模块使用数据范围服务，需要使用 `create_scope_filter` 创建过滤函数
2. **操作日志**: 如果模块有特殊的日志记录需求，需要提供 `log_func`
3. **响应格式**: 统一使用 `BatchOperationResponse`，但可以扩展字段

---

## 七、最佳实践

1. **使用预过滤函数**: 对于需要特定过滤条件的场景，使用 `pre_filter_func` 而不是在循环中过滤
2. **提供清晰的错误消息**: `error_message` 应该清晰说明失败原因
3. **验证函数应该幂等**: 验证函数不应该有副作用
4. **操作函数应该简单**: 复杂的业务逻辑应该在服务层处理
5. **统一使用 BatchOperationResponse**: 保持响应格式一致

---

## 八、待迁移模块

以下模块的批量操作可以迁移到新框架：

1. ✅ **task_center** - 任务中心批量操作（9个端点）
2. ⏳ **issues** - 问题批量操作（3个端点）
3. ⏳ **projects/status** - 项目状态批量操作（3个端点）
4. ⏳ **ecn** - ECN批量操作（1个端点）

---

## 九、总结

通用批量操作框架提供了：

- ✅ **统一的接口**: 减少代码重复
- ✅ **灵活的扩展**: 支持自定义验证、操作、日志
- ✅ **完善的错误处理**: 统一的错误处理和结果统计
- ✅ **易于维护**: 集中管理批量操作逻辑

通过使用此框架，可以显著减少批量操作相关的代码量，提高代码质量和可维护性。

---

**最后更新**: 2026-01-27
