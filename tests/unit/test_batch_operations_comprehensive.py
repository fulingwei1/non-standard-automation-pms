# -*- coding: utf-8 -*-
"""
批量操作框架全面测试

测试 app/utils/batch_operations.py 中的所有类和函数
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.utils.batch_operations import (
    BatchOperationResult,
    BatchOperationExecutor,
    create_scope_filter,
)


class TestBatchOperationResult:
    """测试BatchOperationResult类"""

    def test_初始状态(self):
        """测试初始状态"""
        result = BatchOperationResult()
        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.failed_items == []
    
    def test_add_success(self):
        """测试添加成功记录"""
        result = BatchOperationResult()
        result.add_success()
        result.add_success()
        assert result.success_count == 2
        assert result.failed_count == 0
    
    def test_add_failure_default_id_field(self):
        """测试添加失败记录（默认ID字段）"""
        result = BatchOperationResult()
        result.add_failure(entity_id=123, reason="测试错误")
        
        assert result.success_count == 0
        assert result.failed_count == 1
        assert len(result.failed_items) == 1
        assert result.failed_items[0]["id"] == 123
        assert result.failed_items[0]["reason"] == "测试错误"
    
    def test_add_failure_custom_id_field(self):
        """测试添加失败记录（自定义ID字段）"""
        result = BatchOperationResult()
        result.add_failure(entity_id=456, reason="自定义错误", id_field="project_id")
        
        assert result.failed_items[0]["project_id"] == 456
        assert result.failed_items[0]["reason"] == "自定义错误"
    
    def test_multiple_failures(self):
        """测试多个失败记录"""
        result = BatchOperationResult()
        result.add_failure(1, "错误1")
        result.add_failure(2, "错误2")
        result.add_failure(3, "错误3")
        
        assert result.failed_count == 3
        assert len(result.failed_items) == 3
    
    def test_to_dict_default_id_field(self):
        """测试转换为字典（默认ID字段）"""
        result = BatchOperationResult()
        result.add_success()
        result.add_success()
        result.add_failure(123, "测试错误")
        
        dict_result = result.to_dict()
        
        assert dict_result["success_count"] == 2
        assert dict_result["failed_count"] == 1
        assert len(dict_result["failed_items"]) == 1
        assert dict_result["failed_items"][0]["id"] == 123
    
    def test_to_dict_custom_id_field(self):
        """测试转换为字典（自定义ID字段）"""
        result = BatchOperationResult()
        result.add_failure(456, "错误", id_field="task_id")
        
        dict_result = result.to_dict(id_field="task_id")
        
        assert dict_result["failed_items"][0]["task_id"] == 456
    
    def test_mixed_operations(self):
        """测试混合操作"""
        result = BatchOperationResult()
        result.add_success()
        result.add_failure(1, "失败1")
        result.add_success()
        result.add_failure(2, "失败2")
        result.add_success()
        
        assert result.success_count == 3
        assert result.failed_count == 2


class TestBatchOperationExecutor:
    """测试BatchOperationExecutor类"""

    @pytest.fixture
    def mock_model(self):
        """Mock模型类"""
        model = Mock()
        model.__tablename__ = "tasks"
        return model
    
    @pytest.fixture
    def mock_db(self):
        """Mock数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        """Mock用户"""
        user = Mock()
        user.id = 1
        user.username = "test_user"
        return user
    
    @pytest.fixture
    def executor(self, mock_model, mock_db, mock_user):
        """创建执行器实例"""
        return BatchOperationExecutor(
            model=mock_model,
            db=mock_db,
            current_user=mock_user
        )
    
    def test_初始化(self, mock_model, mock_db, mock_user):
        """测试初始化"""
        executor = BatchOperationExecutor(
            model=mock_model,
            db=mock_db,
            current_user=mock_user,
            id_field="custom_id"
        )
        
        assert executor.model == mock_model
        assert executor.db == mock_db
        assert executor.current_user == mock_user
        assert executor.id_field == "custom_id"
    
    def test_execute_empty_list(self, executor):
        """测试执行空列表"""
        result = executor.execute(
            entity_ids=[],
            operation_func=lambda x: None
        )
        
        assert result.success_count == 0
        assert result.failed_count == 0
    
    def test_execute_successful_operation(self, executor, mock_db):
        """测试成功的批量操作"""
        # 准备测试数据
        entity1 = Mock()
        entity1.id = 1
        entity1.status = "PENDING"
        
        entity2 = Mock()
        entity2.id = 2
        entity2.status = "PENDING"
        
        # Mock查询结果
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity1, entity2]
        mock_db.query.return_value = mock_query
        
        # 定义操作函数
        def update_status(entity):
            entity.status = "COMPLETED"
        
        # 执行批量操作
        result = executor.execute(
            entity_ids=[1, 2],
            operation_func=update_status
        )
        
        # 验证结果
        assert result.success_count == 2
        assert result.failed_count == 0
        assert entity1.status == "COMPLETED"
        assert entity2.status == "COMPLETED"
        
        # 验证数据库操作
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()
    
    def test_execute_with_validator(self, executor, mock_db):
        """测试带验证器的批量操作"""
        # 准备测试数据
        entity1 = Mock()
        entity1.id = 1
        entity1.status = "PENDING"
        
        entity2 = Mock()
        entity2.id = 2
        entity2.status = "COMPLETED"
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity1, entity2]
        mock_db.query.return_value = mock_query
        
        # 验证器：只处理PENDING状态的实体
        def validator(entity):
            return entity.status == "PENDING"
        
        def update_status(entity):
            entity.status = "COMPLETED"
        
        # 执行批量操作
        result = executor.execute(
            entity_ids=[1, 2],
            operation_func=update_status,
            validator_func=validator,
            error_message="状态不是PENDING"
        )
        
        # 验证结果
        assert result.success_count == 1
        assert result.failed_count == 1
        assert result.failed_items[0]["id"] == 2
        assert result.failed_items[0]["reason"] == "状态不是PENDING"
    
    def test_execute_entity_not_found(self, executor, mock_db):
        """测试实体不存在的情况"""
        # Mock查询结果：只返回一个实体
        entity1 = Mock()
        entity1.id = 1
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity1]
        mock_db.query.return_value = mock_query
        
        # 执行批量操作，请求ID包括不存在的ID
        result = executor.execute(
            entity_ids=[1, 2, 3],
            operation_func=lambda x: None
        )
        
        # 验证结果
        assert result.success_count == 1
        assert result.failed_count == 2
    
    def test_execute_operation_exception(self, executor, mock_db):
        """测试操作抛出异常"""
        entity1 = Mock()
        entity1.id = 1
        
        entity2 = Mock()
        entity2.id = 2
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity1, entity2]
        mock_db.query.return_value = mock_query
        
        # 操作函数会抛出异常
        def failing_operation(entity):
            if entity.id == 2:
                raise ValueError("操作失败")
        
        result = executor.execute(
            entity_ids=[1, 2],
            operation_func=failing_operation
        )
        
        # 验证结果
        assert result.success_count == 1
        assert result.failed_count == 1
        assert "操作失败" in result.failed_items[0]["reason"]
    
    def test_execute_commit_failure(self, executor, mock_db):
        """测试提交失败"""
        entity1 = Mock()
        entity1.id = 1
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity1]
        mock_db.query.return_value = mock_query
        
        # Mock提交失败
        mock_db.commit.side_effect = Exception("数据库提交失败")
        
        result = executor.execute(
            entity_ids=[1],
            operation_func=lambda x: None
        )
        
        # 验证结果
        mock_db.rollback.assert_called_once()
    
    def test_batch_update(self, executor, mock_db):
        """测试batch_update方法"""
        entity = Mock()
        entity.id = 1
        entity.name = "Old Name"
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity]
        mock_db.query.return_value = mock_query
        
        def update_name(e):
            e.name = "New Name"
        
        result = executor.batch_update(
            entity_ids=[1],
            update_func=update_name
        )
        
        assert result.success_count == 1
        assert entity.name == "New Name"
    
    def test_batch_delete_soft(self, executor, mock_db):
        """测试软删除"""
        entity = Mock()
        entity.id = 1
        entity.is_active = True
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity]
        mock_db.query.return_value = mock_query
        
        result = executor.batch_delete(
            entity_ids=[1],
            soft_delete=True
        )
        
        assert result.success_count == 1
        assert entity.is_active is False
    
    def test_batch_delete_hard(self, executor, mock_db):
        """测试硬删除"""
        entity = Mock()
        entity.id = 1
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity]
        mock_db.query.return_value = mock_query
        
        result = executor.batch_delete(
            entity_ids=[1],
            soft_delete=False
        )
        
        assert result.success_count == 1
        mock_db.delete.assert_called_once_with(entity)
    
    def test_batch_delete_missing_soft_delete_field(self, executor, mock_db):
        """测试软删除字段不存在"""
        entity = Mock(spec=[])  # 没有is_active字段
        entity.id = 1
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity]
        mock_db.query.return_value = mock_query
        
        result = executor.batch_delete(
            entity_ids=[1],
            soft_delete=True
        )
        
        # 应该失败
        assert result.failed_count == 1
    
    def test_batch_status_update(self, executor, mock_db):
        """测试批量状态更新"""
        entity = Mock()
        entity.id = 1
        entity.status = "PENDING"
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity]
        mock_db.query.return_value = mock_query
        
        result = executor.batch_status_update(
            entity_ids=[1],
            new_status="COMPLETED"
        )
        
        assert result.success_count == 1
        assert entity.status == "COMPLETED"
    
    def test_batch_status_update_custom_field(self, executor, mock_db):
        """测试批量状态更新（自定义字段）"""
        entity = Mock()
        entity.id = 1
        entity.state = "OPEN"
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity]
        mock_db.query.return_value = mock_query
        
        result = executor.batch_status_update(
            entity_ids=[1],
            new_status="CLOSED",
            status_field="state"
        )
        
        assert result.success_count == 1
        assert entity.state == "CLOSED"
    
    def test_batch_status_update_missing_field(self, executor, mock_db):
        """测试状态字段不存在"""
        entity = Mock(spec=[])  # 没有status字段
        entity.id = 1
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity]
        mock_db.query.return_value = mock_query
        
        result = executor.batch_status_update(
            entity_ids=[1],
            new_status="COMPLETED"
        )
        
        # 应该失败
        assert result.failed_count == 1
    
    def test_with_log_func(self, executor, mock_db):
        """测试日志记录函数"""
        entity = Mock()
        entity.id = 1
        
        mock_query = Mock()
        mock_query.filter().all.return_value = [entity]
        mock_db.query.return_value = mock_query
        
        # Mock日志函数
        log_func = Mock()
        
        result = executor.execute(
            entity_ids=[1],
            operation_func=lambda x: None,
            log_func=log_func,
            operation_type="TEST_OPERATION"
        )
        
        # 验证日志函数被调用
        log_func.assert_called_once_with(entity, "TEST_OPERATION")
    
    def test_with_scope_filter_func(self, mock_model, mock_db, mock_user):
        """测试数据范围过滤函数"""
        # 自定义范围过滤函数
        def scope_filter(db, entity_ids, user):
            # 只返回用户有权限的实体
            return [Mock(id=i) for i in entity_ids if i <= 2]
        
        executor = BatchOperationExecutor(
            model=mock_model,
            db=mock_db,
            current_user=mock_user,
            scope_filter_func=scope_filter
        )
        
        result = executor.execute(
            entity_ids=[1, 2, 3, 4],
            operation_func=lambda x: None
        )
        
        # 只有1和2通过了范围过滤
        assert result.success_count == 2
        assert result.failed_count == 2
    
    def test_with_pre_filter_func(self, executor, mock_db):
        """测试预过滤函数"""
        # 预过滤函数
        def pre_filter(db, entity_ids):
            return [Mock(id=i) for i in entity_ids if i % 2 == 0]
        
        result = executor.execute(
            entity_ids=[1, 2, 3, 4],
            operation_func=lambda x: None,
            pre_filter_func=pre_filter
        )
        
        # 只有偶数ID通过了预过滤
        assert result.success_count == 2
        assert result.failed_count == 2


class TestCreateScopeFilter:
    """测试create_scope_filter函数"""

    def test_create_scope_filter(self):
        """测试创建数据范围过滤函数"""
        mock_model = Mock()
        mock_model.id = Mock()
        
        mock_scope_service = Mock()
        mock_scope_service.filter_projects_by_scope = Mock(
            return_value=Mock(all=Mock(return_value=[]))
        )
        
        # 创建过滤函数
        filter_func = create_scope_filter(
            model=mock_model,
            scope_service=mock_scope_service,
            filter_method="filter_projects_by_scope"
        )
        
        # 使用过滤函数
        mock_db = Mock()
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        mock_user = Mock()
        
        result = filter_func(mock_db, [1, 2, 3], mock_user)
        
        # 验证调用
        mock_db.query.assert_called_once_with(mock_model)
        mock_scope_service.filter_projects_by_scope.assert_called_once()


class TestIntegrationScenarios:
    """集成测试场景"""

    def test_批量更新任务状态场景(self):
        """测试批量更新任务状态的完整流程"""
        # 准备数据
        task1 = Mock()
        task1.id = 1
        task1.status = "PENDING"
        task1.updated_by = None
        
        task2 = Mock()
        task2.id = 2
        task2.status = "PENDING"
        task2.updated_by = None
        
        task3 = Mock()
        task3.id = 3
        task3.status = "COMPLETED"
        task3.updated_by = None
        
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter().all.return_value = [task1, task2, task3]
        mock_db.query.return_value = mock_query
        
        mock_user = Mock()
        mock_user.id = 1
        
        mock_model = Mock()
        mock_model.__tablename__ = "tasks"
        
        # 创建执行器
        executor = BatchOperationExecutor(
            model=mock_model,
            db=mock_db,
            current_user=mock_user
        )
        
        # 执行批量更新，只更新PENDING状态的任务
        result = executor.batch_status_update(
            entity_ids=[1, 2, 3],
            new_status="IN_PROGRESS",
            validator_func=lambda task: task.status == "PENDING",
            error_message="任务已完成，无法更新"
        )
        
        # 验证结果
        assert result.success_count == 2
        assert result.failed_count == 1
        assert task1.status == "IN_PROGRESS"
        assert task2.status == "IN_PROGRESS"
        assert task3.status == "COMPLETED"  # 未变化
    
    def test_批量删除场景(self):
        """测试批量删除的完整流程"""
        # 准备数据
        item1 = Mock()
        item1.id = 1
        item1.is_active = True
        item1.can_delete = True
        
        item2 = Mock()
        item2.id = 2
        item2.is_active = True
        item2.can_delete = False  # 不可删除
        
        mock_db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter().all.return_value = [item1, item2]
        mock_db.query.return_value = mock_query
        
        mock_user = Mock()
        mock_user.id = 1
        
        mock_model = Mock()
        mock_model.__tablename__ = "items"
        
        # 创建执行器
        executor = BatchOperationExecutor(
            model=mock_model,
            db=mock_db,
            current_user=mock_user
        )
        
        # 执行批量删除
        result = executor.batch_delete(
            entity_ids=[1, 2],
            validator_func=lambda item: item.can_delete,
            error_message="该项不可删除",
            soft_delete=True
        )
        
        # 验证结果
        assert result.success_count == 1
        assert result.failed_count == 1
        assert item1.is_active is False
        assert item2.is_active is True  # 未变化
