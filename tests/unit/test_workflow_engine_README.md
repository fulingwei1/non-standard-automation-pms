# WorkflowEngine 单元测试文档

## 测试文件
`tests/unit/test_workflow_engine.py`

## 测试策略
1. **只mock外部依赖**：db.query, db.add, db.commit等数据库操作
2. **业务逻辑真正执行**：让WorkflowEngine的核心业务逻辑代码真正运行
3. **参考mock策略**：参考了 `test_condition_parser_rewrite.py` 的最佳实践

## 测试覆盖

### WorkflowEngine 核心方法
- ✅ `create_instance()` - 创建审批实例
- ✅ `get_current_node()` - 获取当前节点
- ✅ `evaluate_node_conditions()` - 评估节点条件
- ✅ `_build_condition_context()` - 构建条件上下文
- ✅ `_get_business_entity_data()` - 获取业务实体数据
- ✅ `submit_approval()` - 提交审批
- ✅ `_get_approver_name()` - 获取审批人姓名
- ✅ `_get_approver_role()` - 获取审批角色
- ✅ `_update_instance_status()` - 更新实例状态
- ✅ `_find_next_node()` - 查找下一个节点
- ✅ `_find_previous_node()` - 查找上一个节点
- ✅ `_get_first_node_timeout()` - 获取首节点超时时间
- ✅ `is_expired()` - 检查实例是否超时
- ✅ `_generate_instance_no()` - 生成实例编号

### ApprovalFlowResolver 测试
- ✅ `get_approval_flow()` - 获取审批流程（通过flow_code和module_name）
- ✅ `determine_approval_flow()` - 确定审批流程

### ApprovalRouter 测试
- ✅ `get_approval_flow()` - 获取审批流程
- ✅ `determine_approval_flow()` - 确定审批流程（ECN、SALES_INVOICE、SALES_QUOTE）

## 测试结果
- **总测试数**: 49个
- **通过率**: 100% (49/49)
- **失败数**: 0
- **跳过数**: 0

## 边界情况测试
- ✅ 流程不存在
- ✅ 节点无条件表达式
- ✅ 条件评估失败
- ✅ 无当前节点
- ✅ 条件不满足
- ✅ 审批人不存在
- ✅ 业务实体不存在
- ✅ 实例超时检查（due_date和created_at两种方式）
- ✅ 查找节点不存在

## 运行测试
```bash
# 运行所有测试
python3 -m pytest tests/unit/test_workflow_engine.py -v

# 运行特定测试类
python3 -m pytest tests/unit/test_workflow_engine.py::TestWorkflowEngineCore -v

# 运行特定测试方法
python3 -m pytest tests/unit/test_workflow_engine.py::TestWorkflowEngineCore::test_create_instance_success -v
```

## 注意事项
1. 所有测试使用MagicMock模拟数据库对象和查询
2. 不依赖真实数据库，测试速度快
3. 业务逻辑代码真正执行，确保代码质量
4. 测试与生产代码解耦，便于维护
