# 审批流程执行日志 - 快速演示

本文档展示如何在实际审批代码中使用 `ApprovalExecutionLogger`。

## 简单示例：提交审批

```python
from datetime import datetime
from app.models.base import get_db_session
from app.models.approval import ApprovalInstance, User
from app.services.approval_engine.execution_logger import ApprovalExecutionLogger

def submit_quote_approval(user_id: int, quote_id: int):
    """
    提交报价审批
    """
    with get_db_session() as db:
        # 1. 获取用户和报价信息
        user = db.query(User).filter(User.id == user_id).first()
        
        # 2. 记录开始时间（性能追踪）
        start_time = datetime.now()
        
        # 3. 获取报价信息
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        
        # 4. 初始化日志记录器
        exec_logger = ApprovalExecutionLogger(db)
        
        # 5. 记录审批实例创建
        # 假设已经创建了审批实例
        instance = ApprovalInstance(
            entity_type="QUOTE",
            entity_id=quote_id,
            instance_no=f"QT{datetime.now().strftime('%y%m%d')}001",
            status="PENDING",
            current_node_id=None,
            submitted_by=user.id,
            submitted_at=datetime.now(),
            # ...
        )
        
        exec_logger.log_instance_created(
            instance=instance,
            initiator=user,
            context={
                "quote_no": quote.quote_no,
                "amount": quote.total_amount,
                "customer_name": quote.customer_name,
            }
        )
        
        print(f"✅ 审批实例创建: {instance.instance_no}")
        return instance
```

## 示例 2：记录路由决策

```python
from app.services.approval_engine.execution_logger import ApprovalExecutionLogger

def select_quote_approval_flow(instance: ApprovalInstance, db: Session):
    """
    选择报价审批流程（带详细日志）
    """
    exec_logger = ApprovalExecutionLogger(db)
    
    amount = instance.form_data.get("amount", 0)
    
    # 记录开始
    start_time = datetime.now()
    
    # 评估路由条件
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
    
    # 记录性能指标
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    exec_logger.log_performance_metric(
        instance=instance,
        metric_name="flow_selection_time",
        value=duration_ms,
        unit="ms",
    )
    
    print(f"✅ 路由决策: {flow_name}")
    return flow_id
```

## 示例 3：记录任务创建

```python
from app.services.approval_engine.execution_logger import ApprovalExecutionLogger

def create_approval_tasks(instance: ApprovalInstance, node: ApprovalNodeDefinition, db: Session):
    """
    为节点创建审批任务（带性能追踪）
    """
    exec_logger = ApprovalExecutionLogger(db)
    
    start_time = datetime.now()
    
    # 解析审批人
    approver_ids = [1, 2, 3]  # 从节点配置解析
    
    # 创建任务
    tasks = []
    for idx, approver_id in enumerate(approver_ids):
        task = ApprovalTask(
            instance_id=instance.id,
            node_id=node.id,
            task_type="APPROVAL",
            task_order=idx + 1,
            assignee_id=approver_id,
            status="PENDING",
        )
        tasks.append(task)
        db.add(task)
    
    db.commit()
    
    # 记录批量任务创建
    exec_logger.log_batch_task_creation(tasks, node)
    
    # 记录性能
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    exec_logger.log_performance_metric(
        instance=instance,
        metric_name="task_creation_time",
        value=duration_ms,
        unit="ms",
    )
    
    print(f"✅ 创建 {len(tasks)} 个审批任务")
    return tasks
```

## 示例 4：记录审批决策

```python
from app.services.approval_engine.execution_logger import ApprovalExecutionLogger

def submit_approval_decision(task_id: int, decision: str, comment: str, user_id: int, db: Session):
    """
    提交审批决策（带完整日志）
    """
    exec_logger = ApprovalExecutionLogger(db)
    
    start_time = datetime.now()
    
    # 获取任务和用户
    task = db.query(ApprovalTask).filter(ApprovalTask.id == task_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    node = task.node
    
    # 更新任务状态
    task.status = "APROVED" if decision == "APPROVE" else "REJECTED"
    task.approved_at = datetime.now()
    task.approval_comment = comment
    
    db.commit()
    
    # 记录任务完成
    exec_logger.log_task_completed(
        task=task,
        operator=user,
        decision=decision,
        comment=comment,
    )
    
    # 记录节点流转（如果需要）
    next_node = find_next_node(task.node)
    if next_node:
        exec_logger.log_node_transition(
            instance=task.instance,
            from_node=node,
            to_node=next_node,
            reason=f"审批{decision},自动流转",
        )
    
    # 记录性能
    duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    exec_logger.log_performance_metric(
        instance=task.instance,
        metric_name="approval_decision_time",
        value=duration_ms,
        unit="ms",
    )
    
    print(f"✅ 审批决策: {decision}")
    return task
```

## 示例 5：记录错误

```python
from app.services.approval_engine.execution_logger import ApprovalExecutionLogger

def process_approval_with_error_handling(instance_id: int, db: Session):
    """
    处理审批（带错误处理）
    """
    exec_logger = ApprovalExecutionLogger(db)
    instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
    
    try:
        # 步骤1：验证表单
        validate_form_data(instance)
        exec_logger.log_debug_info(
            instance_id=instance_id,
            message="开始验证表单数据",
            context={"validation_time": datetime.now().isoformat()}
        )
        
        # 步骤2：创建任务
        node = get_current_node(instance)
        tasks = create_approval_tasks(instance, node, db)
        exec_logger.log_debug_info(
            instance_id=instance_id,
            message="任务创建完成",
            context={"task_count": len(tasks)}
        )
        
        # 步骤3：发送通知
        send_notifications(tasks, db)
        exec_logger.log_debug_info(
            instance_id=instance_id,
            message="通知发送完成",
            context={"notification_count": len(tasks)}
        )
        
    except ValueError as e:
        # 记录验证错误
        exec_logger.log_validation_error(
            instance=instance,
            validation_type="FORM_DATA",
            validation_error=str(e),
            context={"form_data": instance.form_data}
        )
        raise
        
    except Exception as e:
        # 记录系统错误
        exec_logger.log_error(
            instance=instance,
            error=e,
            operation="PROCESS_APPROVAL",
            context={"error_details": str(e)},
        )
        raise
```

## 完整执行日志示例

假设提交一个报价审批，执行路径如下：

### 1. 实例创建
```sql
INSERT INTO workflow_execution_logs (
    instance_id, instance_no, entity_type, entity_id,
    execution_stage, execution_phase, operation, operator_id,
    started_at, completed_at
) VALUES (
    1, 'QT250125001', 'QUOTE', 1005,
    'INSTANCE_INIT', 'CREATE_INSTANCE', 'CREATE',
    5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);
```

### 2. 路由决策
```sql
INSERT INTO workflow_execution_logs (
    instance_id, execution_stage, execution_phase, operation,
    flow_id, flow_name, routing_rule_id, routing_condition,
    started_at, completed_at
) VALUES (
    1, 'ROUTING', 'SELECT_FLOW',
    2, 'QUOTE_FLOW_SELECT',
    1, '报价单级流程', 1,
    'amount < 100000',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);
```

### 3. 任务创建
```sql
INSERT INTO workflow_execution_logs (
    instance_id, node_id, node_name, task_id,
    execution_stage, execution_phase, operation,
    duration_ms,
    started_at, completed_at
) VALUES (
    1, 1, '销售经理审批', NULL,
    'TASK_ASSIGN', 'CREATE_TASK',
    15, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);
```

### 4. 审批决策
```sql
INSERT INTO workflow_execution_logs (
    instance_id, node_id, node_name, task_id,
    execution_stage, execution_phase, operation,
    operator_id, operator_name, decision, comment,
    old_status, new_status,
    started_at, completed_at
) VALUES (
    1, 1, '销售经理审批', 123,
    'APPROVAL', 'APPROVE', '同意',
    'PENDING', 'APPROVED',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
);
```

## 调试技巧

### 1. 查看完整执行历史
```sql
SELECT 
    execution_stage,
    execution_phase,
    operation,
    operator_name,
    decision,
    comment,
    old_status,
    new_status,
    duration_ms,
    error_level,
    error_message
FROM workflow_execution_logs
WHERE instance_id = 1
ORDER BY started_at;
```

### 2. 查看性能瓶颈
```sql
SELECT 
    execution_stage,
    operation,
    AVG(duration_ms) as avg_ms,
    MAX(duration_ms) as max_ms,
    COUNT(*) as count
FROM v_approval_performance_summary
WHERE instance_id = 1
GROUP BY execution_stage, operation
ORDER BY avg_ms DESC;
```

### 3. 查看错误统计
```sql
SELECT 
    error_type,
    execution_stage,
    execution_phase,
    operation,
    error_count,
    last_occurred_at
FROM v_approval_error_summary
WHERE instance_id = 1
ORDER BY error_count DESC
LIMIT 10;
```

### 4. 查看某个节点的所有操作
```sql
SELECT 
    execution_stage,
    operation,
    operator_name,
    decision,
    comment,
    duration_ms
FROM workflow_execution_logs
WHERE instance_id = 1 AND node_id = 1
ORDER BY started_at;
```

## 日志级别使用建议

- **DEBUG**: 开发调试时使用，记录详细信息
- **INFO**: 生产环境默认级别，记录关键操作
- **WARNING**: 记录需要注意但不严重的问题
- **ERROR**: 记录错误和异常
- **CRITICAL**: 记录严重错误，需要立即处理

## 性能优化建议

1. 批量操作使用 `log_batch_task_creation()` 而不是循环调用 `log_task_created()`
2. 频繁操作的日志可以考虑异步写入
3. 定期清理历史日志数据（保留最近 3 个月）
4. 性能瓶颈考虑添加缓存或优化算法
