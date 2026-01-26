-- 审批流程执行日志表迁移
--
创建用于追踪和调试审批流程执行的日志表

-- ============================================================
-- 1. 审批流程执行日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS workflow_execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 审批实例信息
    instance_id INTEGER NOT NULL,
    instance_no VARCHAR(50),
    entity_type VARCHAR(50),
    entity_id INTEGER,
    
    -- 执行阶段
    execution_stage VARCHAR(30) NOT NULL COMMENT "执行阶段：INSTANCE_INIT/TASK_ASSIGN/ROUTING/APPROVAL/COMPLETION/ERROR",
    execution_phase VARCHAR(50) COMMENT "执行阶段详细描述：如 CREATE_INSTANCE, EVALUATE_CONDITION, CREATE_TASK 等",
    
    -- 操作信息
    operation VARCHAR(50) NOT NULL COMMENT "操作类型",
    operator_type VARCHAR(20) COMMENT "操作人类型：USER/SYSTEM/DELEGATED",
    operator_id INTEGER COMMENT "操作人ID",
    operator_name VARCHAR(50) COMMENT "操作人姓名",
    
    -- 节点信息
    node_id INTEGER,
    node_code VARCHAR(50),
    node_name VARCHAR(100),
    task_id INTEGER,
    
    -- 审批决策（用于 APPROVAL 阶段）
    decision VARCHAR(20) COMMENT "审批决策：APPROVED/REJECTED/RETURNED/TRANSFERRED/TIMEOUT",
    comment TEXT COMMENT "审批意见",
    
    -- 状态变更
    old_status VARCHAR(20) COMMENT "操作前状态",
    new_status VARCHAR(20) COMMENT "操作后状态",
    
    -- 路由信息（用于 ROUTING 阶段）
    flow_id INTEGER,
    flow_name VARCHAR(100),
    routing_rule_id INTEGER,
    routing_condition TEXT COMMENT "路由条件表达式",
    
    -- 上下文信息
    context_data JSON COMMENT "执行上下文（表单数据、条件参数等）",
    
    -- 性能指标
    duration_ms INTEGER COMMENT "操作耗时（毫秒）",
    -- 性能指标
    performance_metrics JSON COMMENT "性能指标：如 任务数、查询次数等",
    
    -- 错误信息
    error_level VARCHAR(10) COMMENT "错误级别：DEBUG/INFO/WARNING/ERROR/CRITICAL",
    error_type VARCHAR(100) COMMENT "错误类型",
    error_message TEXT COMMENT "错误消息",
    error_trace TEXT COMMENT "错误堆栈",
    
    -- 审计信息
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    
    -- 时间戳
    started_at DATETIME COMMENT "操作开始时间",
    completed_at DATETIME COMMENT "操作完成时间",
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键
    FOREIGN KEY (instance_id) REFERENCES approval_instances(id),
    FOREIGN KEY (node_id) REFERENCES approval_node_definitions(id),
    FOREIGN KEY (task_id) REFERENCES approval_tasks(id),
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

-- ============================================================
-- 2. 创建索引
-- ============================================================

-- 审批实例查询索引
CREATE INDEX IF NOT EXISTS idx_exec_log_instance ON workflow_execution_logs(instance_id);
CREATE INDEX IF NOT EXISTS idx_exec_log_instance_no ON workflow_execution_logs(instance_no);
CREATE INDEX IF NOT EXISTS idx_exec_log_entity ON workflow_execution_logs(entity_type, entity_id);

-- 执行阶段索引
CREATE INDEX IF NOT EXISTS idx_exec_log_stage ON workflow_execution_logs(execution_stage);
CREATE INDEX IF NOT EXISTS idx_exec_log_phase ON workflow_execution_logs(execution_phase);

-- 操作和节点索引
CREATE INDEX IF NOT EXISTS idx_exec_log_operation ON workflow_execution_logs(operation);
CREATE INDEX IF NOT EXISTS idx_exec_log_node ON workflow_execution_logs(node_id);
CREATE INDEX IF NOT EXISTS idx_exec_log_task ON workflow_execution_logs(task_id);

-- 操作人索引
CREATE INDEX IF NOT EXISTS idx_exec_log_operator ON workflow_execution_logs(operator_id);
CREATE INDEX IF NOT EXISTS idx_exec_log_time ON workflow_execution_logs(started_at DESC);

-- 错误索引
CREATE INDEX IF NOT EXISTS idx_exec_log_error ON workflow_execution_logs(error_level, error_type);
CREATE INDEX IF NOT EXISTS idx_exec_log_time_range ON workflow_execution_logs(started_at, completed_at);

-- ============================================================
-- 3. 性能视图（用于分析审批性能）
-- ============================================================

CREATE VIEW IF NOT EXISTS v_approval_performance_summary AS
SELECT
    instance_id,
    instance_no,
    entity_type,
    execution_stage,
    operation,
    COUNT(*) as operation_count,
    SUM(duration_ms) as total_duration_ms,
    AVG(duration_ms) as avg_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    COUNT(CASE WHEN error_level IN ('ERROR', 'CRITICAL') THEN 1 END) as error_count
FROM workflow_execution_logs
GROUP BY instance_id, instance_no, entity_type, execution_stage, operation;

-- ============================================================
-- 4. 错误统计视图（用于分析常见错误）
-- ============================================================

CREATE VIEW IF NOT EXISTS v_approval_error_summary AS
SELECT
    error_type,
    execution_stage,
    execution_phase,
    operation,
    COUNT(*) as error_count,
    COUNT(DISTINCT instance_id) as affected_instances,
    MAX(started_at) as last_occurred_at
FROM workflow_execution_logs
WHERE error_level IN ('ERROR', 'CRITICAL')
GROUP BY error_type, execution_stage, execution_phase, operation
ORDER BY error_count DESC;

-- ============================================================
-- 迁移说明
-- ============================================================

-- 本次迁移创建以下内容：
--
-- 1. workflow_execution_logs 表：
--    - 完整记录审批流程的每个执行步骤
--    - 包含操作人、节点、决策、状态变更等信息
--    - 支持性能指标和错误追踪
--    - 包含审计信息（IP、User-Agent）
--
-- 2. 索引：
--    - 按审批实例查询完整执行历史
--    - 按执行阶段/操作类型查询
--    - 按操作人和时间查询
--    - 按错误级别和类型查询
--
-- 3. 性能分析视图 v_approval_performance_summary：
--    - 统计每个操作的执行次数和耗时
--    - 计算平均、最小、最大耗时
--    - 统计错误次数
--
-- 4. 错误统计视图 v_approval_error_summary：
--    - 统计各类错误的发生次数和频率
--    - 记录最近发生时间
--    - 标识受影响的审批实例
--
-- 使用场景：
-- 1. 审批流程追踪和调试：
--    - 查询完整执行历史：SELECT * FROM workflow_execution_logs WHERE instance_id = ? ORDER BY started_at
--    - 查看某个阶段的所有操作：SELECT * FROM workflow_execution_logs WHERE instance_id = ? AND execution_stage = 'ROUTING'
--
-- 2. 性能分析：
--    - 查看操作耗时：SELECT * FROM v_approval_performance_summary WHERE instance_id = ?
--    - 识别慢操作：SELECT * FROM workflow_execution_logs WHERE duration_ms > 5000 ORDER BY duration_ms DESC
--
-- 3. 错误排查：
--    - 查看常见错误：SELECT * FROM v_approval_error_summary
--    - 查看特定错误历史：SELECT * FROM workflow_execution_logs WHERE error_type = ? ORDER BY started_at DESC
--
-- 4. 审计追踪：
--    - 查看某个人的操作历史：SELECT * FROM workflow_execution_logs WHERE operator_id = ? ORDER BY started_at DESC
--    - 查看某个审批实例的所有操作：SELECT * FROM workflow_execution_logs WHERE instance_no = ? ORDER BY started_at
