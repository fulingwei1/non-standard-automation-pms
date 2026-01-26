# 审批流程执行日志 - 使用指南

## 概述

本指南展示如何使用 `ApprovalExecutionLogger` 为审批流程添加执行日志记录。

## 架构

```
ApprovalExecutionLogger
├── Instance Lifecycle (实例生命周期)
│   ├── log_instance_created()     # 审批实例创建
│   ├── log_instance_status_change()  # 状态变更
│   └── log_instance_completed()     # 审批完成
│
├── Task Lifecycle (任务生命周期)
│   ├── log_task_created()         # 任务创建
│   ├── log_task_completed()       # 任务完成
│   └── log_task_timeout()         # 任务超时
│
├── Routing Decisions (路由决策)
│   ├── log_flow_selection()       # 流程选择
│   ├── log_node_transition()      # 节点流转
│   └── log_condition_evaluation()  # 条件评估
│
├── Performance (性能)
│   ├── log_performance_metric()  # 性能指标
│   └── log_workflow_summary()    # 工作流摘要
│
└── Error Handling (错误处理)
    ├── log_error()               # 审批流程错误
    ├── log_validation_error()      # 验证错误
    └── log_debug_info()          # 调试信息
```

## 基础使用

### 1. 初始化

```python
from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
from app.models.base import get_db_session

# 在审批服务中初始化日志记录器
with get_db_session() as db:
    exec_logger = ApprovalExecutionLogger(db)
    
    # 根据需要配置日志开关
    exec_logger.log_actions = True      # 记录审批动作
    exec_logger.log_routing = True      # 记录路由决策
    exec_logger.log_performance = True   # 记录性能指标
    exec_logger.log_errors = True         # 记录错误
```

### 2. 记录审批实例创建

```python
def submit_approval(entity_type: str, entity_id: int, form_data: dict, submitted_by: int):
    """
    提交审批申请
    """
    with get_db_session() as db:
        exec_logger = ApprovalExecutionLogger(db)
        
        # 获取发起人信息
        initiator = db.query(User).filter(User.id == submitted_by).first()
        
        # 创建审批实例
        instance = ApprovalInstance(
            entity_type=entity_type,
            entity_id=entity_id,
            form_data=form_data,
            submitted_by=submitted_by,
            # ... 其他字段
        )
        db.add(instance)
        db.commit()
        
        # 记录实例创建日志
        exec_logger.log_instance_created(
            instance=instance,
            initiator=initiator,
            context={
                "business_title": form_data.get("title"),
                "amount": form_data.get("amount"),
            }
        )
```

### 3. 记录任务创建

```python
def create_approval_tasks(instance: ApprovalInstance, node: ApprovalNodeDefinition):
    """
    为节点创建审批任务
    """
    with get_db_session() as db:
        exec_logger = ApprovalExecutionLogger(db)
        
        # 解析审批人
        approvers = resolve_approvers(node, instance.form_data)
        
        # 创建任务
        tasks = []
        for idx, approver_id in enumerate(approvers):
            task = ApprovalTask(
                instance_id=instance.id,
                node_id=node.id,
                assignee_id=approver_id,
                status="PENDING",
                task_order=idx + 1,
            )
            tasks.append(task)
            db.add(task)
        
        db.commit()
        
        # 记录每个任务创建（批量）
        exec_logger.log_batch_task_creation(tasks, node)
        
        return tasks
```

### 4. 记录审批决策

```python
def submit_approval(task_id: int, decision: str, comment: str, operator_id: int):
    """
    提交审批决策
    """
    with get_db_session() as db:
        exec_logger = ApprovalExecutionLogger(db)
        
        # 获取任务和审批人
        task = db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()
        operator = db.query(User).filter(User.id == operator_id).first()
        node = task.node
        
        # 更新任务状态
        task.status = "APPROVED" if decision == "APPROVE" else "REJECTED"
        task.approved_at = datetime.now()
        task.approval_comment = comment
        
        db.commit()
        
        # 记录任务完成日志
        exec_logger.log_task_completed(
            task=task,
            node=node,
            operator=operator,
            decision=decision,
            comment=comment,
        )
        
        # 如果所有任务都完成，检查是否需要流转到下一节点
        _check_and_advance_to_next_node(task.instance_id, db, exec_logger)
```

### 5. 记录路由决策

```python
def select_approval_flow(entity_type: str, form_data: dict):
    """
    选择审批流程
    """
    with get_db_session() as db:
        exec_logger = ApprovalExecutionLogger(db)
        
        # 评估路由条件
        flow_id = None
        flow_name = None
        rule_name = None
        
        # QUOTE 报价：根据金额路由
        if entity_type == "QUOTE":
            amount = form_data.get("amount", 0)
            if amount < 100000:
                flow_id = 1  # 销售经理流程
                flow_name = "报价单级流程"
                rule_name = "小于10万"
            elif amount < 500000:
                flow_id = 2  # 销售总监流程
                flow_name = "报价多级流程"
                rule_name = "10-50万"
            else:
                flow_id = 3  # 总经理流程
                flow_name = "报价高级流程"
                rule_name = "50万以上"
        
        # 记录路由决策
        exec_logger.log_flow_selection(
            instance=instance,
            flow_id=flow_id,
            flow_name=flow_name,
            routing_rule=rule_name,
            condition=f"amount={amount}",
        )
        
        return flow_id
```

### 6. 记录节点流转

```python
def advance_to_next_node(instance_id: int, current_task: ApprovalTask):
    """
    流转到下一节点
    """
    with get_db_session() as db:
        exec_logger = ApprovalExecutionLogger(db)
        
        # 获取当前节点
        current_node = current_task.node
        
        # 查找下一节点
        next_node = (
            db.query(ApprovalNodeDefinition)
            .filter(
                ApprovalNodeDefinition.flow_id == current_node.flow_id,
                ApprovalNodeDefinition.node_order > current_node.node_order,
                ApprovalNodeDefinition.is_active == True,
            )
            .order_by(ApprovalNodeDefinition.node_order)
            .first()
        )
        
        if next_node:
            instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
            instance.current_node_id = next_node.id
            instance.current_status = "IN_PROGRESS"
            db.commit()
            
            # 记录节点流转
            exec_logger.log_node_transition(
                instance=instance,
                from_node=current_node,
                to_node=next_node,
                reason=f"任务 {current_task.task_type} 完成，自动流转",
            )
            
            return next_node
        else:
            # 没有下一节点，审批完成
            complete_approval(instance_id, db, exec_logger)
```

### 7. 记录性能指标

```python
def complete_approval(instance_id: int, db: Session, exec_logger: ApprovalExecutionLogger):
    """
    完成审批
    """
    instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
    operator = db.query(User).filter(User.id == instance.final_approver_id).first()
    
    start_time = time.time()
    
    # 执行完成逻辑
    # ...
    
    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)
    
    # 记录性能指标
    exec_logger.log_performance_metric(
        instance=instance,
        metric_name="total_approval_time",
        value=duration_ms,
        unit="ms",
    )
    
    # 记录实例完成
    exec_logger.log_instance_completed(
        instance=instance,
        operator=operator,
        completion_reason="正常审批完成",
    )
    
    # 生成工作流摘要
    exec_logger.log_workflow_summary(instance)
```

## 高级用法

### 1. 条件表达式评估日志

```python
def evaluate_node_condition(node: ApprovalNodeDefinition, instance: ApprovalInstance):
    """
    评估节点条件
    """
    with get_db_session() as db:
        exec_logger = ApprovalExecutionLogger(db)
        
        if node.condition_expression:
            try:
                # 解析和评估条件表达式
                # 例如: "{{ amount | float >= 100000 }}"
                # 提取条件：amount >= 100000
                # 获取表单数据：form.amount = 100000
                # 评估：100000 >= 100000 -> True
                
                condition_str = extract_condition(node.condition_expression)
                form_value = get_form_value(instance, condition_str)
                result = evaluate_condition(form_value)
                
                # 记录条件评估结果
                exec_logger.log_condition_evaluation(
                    node=node,
                    instance=instance,
                    expression=condition_str,
                    result=result,
                    matched=result,
                )
                
                return result
                
            except Exception as e:
                exec_logger.log_validation_error(
                    instance=instance,
                    validation_type="CONDITION_EVALUATION",
                    validation_error=str(e),
                    context={
                        "node_code": node.node_code,
                        "expression": node.condition_expression,
                    }
                )
                # 条件评估失败时默认通过
                return True
        
        return True
```

### 2. 错误处理和日志

```python
def process_approval_step(instance_id: int):
    """
    处理审批步骤（带错误处理）
    """
    with get_db_session() as db:
        exec_logger = ApprovalExecutionLogger(db)
        instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
        
        try:
            # 步骤1: 验证表单数据
            validate_form_data(instance)
            exec_logger.log_debug_info(
                instance_id=instance_id,
                message="表单数据验证通过",
                context={"validation_time": datetime.now().isoformat()},
            )
            
            # 步骤2: 创建审批任务
            create_tasks(instance)
            exec_logger.log_debug_info(
                instance_id=instance_id,
                message="审批任务创建完成",
                context={"task_count": len(instance.tasks)},
            )
            
        except ValidationError as e:
            # 记录验证错误
            exec_logger.log_error(
                instance=instance,
                error=e,
                operation="VALIDATE_FORM",
                context={"validation_errors": e.errors},
            )
            raise
        except DatabaseError as e:
            # 记录数据库错误
            exec_logger.log_error(
                instance=instance,
                error=e,
                operation="CREATE_TASKS",
            )
            raise
        except Exception as e:
            # 记录未知错误
            exec_logger.log_error(
                instance=instance,
                error=e,
                operation="UNKNOWN",
            )
            raise
```

### 3. 批量操作日志

```python
def batch_create_tasks(instance: ApprovalInstance, tasks_data: list):
    """
    批量创建任务（带性能追踪）
    """
    import time
    
    with get_db_session() as db:
        exec_logger = ApprovalExecutionLogger(db)
        
        start_time = time.time()
        
        # 批量创建任务
        tasks = []
        for task_data in tasks_data:
            task = ApprovalTask(**task_data)
            db.add(task)
            tasks.append(task)
        
        db.commit()
        
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        
        # 记录批量操作日志
        exec_logger.log_batch_task_creation(
            tasks=tasks,
            node=tasks[0].node if tasks else None,
        )
        
        # 记录性能指标
        exec_logger.log_performance_metric(
            instance=instance,
            metric_name="batch_task_creation",
            value=duration_ms,
            unit="ms",
        )
```

## 日志查询和分析

### 1. 查询审批实例的完整执行历史

```sql
SELECT 
    instance_no,
    execution_stage,
    operation,
    operator_name,
    decision,
    old_status,
    new_status,
    duration_ms,
    started_at,
    completed_at
FROM workflow_execution_logs
WHERE instance_id = ?
ORDER BY started_at;
```

### 2. 查看性能统计

```sql
SELECT 
    execution_stage,
    operation,
    operation_count,
    avg_duration_ms,
    max_duration_ms
FROM v_approval_performance_summary
WHERE instance_id = ?
ORDER BY total_duration_ms DESC;
```

### 3. 查看常见错误

```sql
SELECT 
    error_type,
    execution_stage,
    operation,
    error_count,
    last_occurred_at
FROM v_approval_error_summary
WHERE instance_id = ?
ORDER BY error_count DESC;
```

### 4. 查看特定节点的执行情况

```sql
SELECT 
    execution_stage,
    operation,
    operator_name,
    decision,
    comment,
    duration_ms
FROM workflow_execution_logs
WHERE instance_id = ? AND node_id = ?
ORDER BY started_at;
```

## 集成到现有代码

### 集成到 ApprovalEngineCore

```python
# app/services/approval_engine/engine/core.py

from ..execution_logger import ApprovalExecutionLogger

class ApprovalEngineCore:
    def __init__(self, db: Session):
        self.db = db
        self.router = ApprovalRouterService(db)
        self.executor = ApprovalNodeExecutor(db)
        self.notify = ApprovalNotifyService(db)
        self.delegate_service = ApprovalDelegateService(db)
        
        # 新增：初始化执行日志记录器
        self.exec_logger = ApprovalExecutionLogger(db)
        self.exec_logger.log_actions = True
        self.exec_logger.log_routing = True
        self.exec_logger.log_performance = True
        self.exec_logger.log_errors = True
    
    def create_instance(self, ...) -> ApprovalInstance:
        """创建审批实例"""
        # ... 现有逻辑 ...
        
        # 新增：记录实例创建
        initiator = self.db.query(User).filter(User.id == submitted_by).first()
        self.exec_logger.log_instance_created(
            instance=instance,
            initiator=initiator,
            context=config or {},
        )
        
        return instance
    
    def _advance_to_next_node(self, ...):
        """流转到下一节点"""
        # ... 现有逻辑 ...
        
        # 新增：记录节点流转
        self.exec_logger.log_node_transition(
            instance=instance,
            from_node=current_node,
            to_node=next_node,
            reason="审批通过，自动流转",
        )
```

### 集成到 ApprovalRouterService

```python
# app/services/approval_engine/router.py

from .execution_logger import ApprovalExecutionLogger

class ApprovalRouterService:
    def __init__(self, db: Session):
        self.db = db
        
        # 新增：初始化日志记录器
        self.exec_logger = ApprovalExecutionLogger(db)
    
    def determine_approval_flow(
        self,
        business_type: str,
        business_data: Dict[str, Any],
        instance: Optional[ApprovalInstance] = None,
    ) -> Optional[int]:
        """确定审批流程"""
        # ... 现有路由逻辑 ...
        
        # 新增：记录路由决策
        if instance:
            self.exec_logger.log_flow_selection(
                instance=instance,
                flow_id=flow_id,
                flow_name=flow.flow_name,
                routing_rule=matched_rule,
                condition=condition_evaluated,
            )
        
        return flow_id
```

## 调试场景

### 场景 1：审批实例卡在某个节点

```sql
-- 查看实例当前状态和最后的操作
SELECT 
    i.instance_no,
    i.current_status,
    i.current_node_id,
    n.node_name as current_node,
    MAX(wel.started_at) as last_action_at,
    wel.operation as last_operation,
    wel.operator_name
FROM approval_instances i
LEFT JOIN approval_node_definitions n ON i.current_node_id = n.id
LEFT JOIN workflow_execution_logs wel ON i.id = wel.instance_id
WHERE i.id = ?
GROUP BY i.id;
```

### 场景 2：条件路由失败

```sql
-- 查看某个实例的所有条件评估记录
SELECT 
    node_code,
    node_name,
    expression,
    evaluation_result,
    matched,
    started_at
FROM workflow_execution_logs
WHERE instance_id = ? AND execution_stage = 'ROUTING'
ORDER BY started_at;
```

### 场景 3：性能分析

```sql
-- 查看所有审批的平均耗时
SELECT 
    execution_stage,
    operation,
    COUNT(*) as count,
    AVG(duration_ms) as avg_ms,
    MAX(duration_ms) as max_ms,
    MIN(duration_ms) as min_ms
FROM workflow_execution_logs
WHERE started_at >= datetime('now', '-7 days')
GROUP BY execution_stage, operation
ORDER BY avg_duration_ms DESC;
```

### 场景 4：错误排查

```sql
-- 查看最近的错误
SELECT 
    instance_no,
    execution_stage,
    operation,
    error_type,
    error_message,
    started_at
FROM workflow_execution_logs
WHERE error_level IN ('ERROR', 'CRITICAL')
  AND started_at >= datetime('now', '-7 days')
ORDER BY started_at DESC
LIMIT 50;
```

## 性能优化建议

1. **批量记录**：使用 `log_batch_task_creation()` 批量记录多个任务
2. **异步日志**：如果性能敏感，考虑将日志写入改为异步
3. **日志级别**：生产环境建议关闭 DEBUG 级别的 `log_debug_info()`
4. **定期清理**：workflow_execution_logs 表会快速增长，需要定期归档或清理历史数据

## 最佳实践

1. **始终记录**：在审批流程的每个关键步骤都记录日志
2. **上下文完整**：包含所有相关信息（实例ID、节点、操作人等）
3. **错误追踪**：异常必须记录完整的堆栈信息
4. **性能监控**：关键操作记录耗时，识别性能瓶颈
5. **结构化查询**：使用提供的视图快速分析日志
