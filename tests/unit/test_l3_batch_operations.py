# -*- coding: utf-8 -*-
"""
L3组 单元测试 - app/utils/batch_operations.py
BatchOperationResult: 纯逻辑
BatchOperationExecutor: mock db
"""

import pytest
from unittest.mock import MagicMock, patch


from app.utils.batch_operations import BatchOperationResult, BatchOperationExecutor


# =============================================================================
# BatchOperationResult - 纯逻辑
# =============================================================================

class TestBatchOperationResult:

    def test_initial_counts_are_zero(self):
        result = BatchOperationResult()
        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.failed_items == []

    def test_add_success_increments_count(self):
        result = BatchOperationResult()
        result.add_success()
        result.add_success()
        assert result.success_count == 2

    def test_add_failure_increments_count(self):
        result = BatchOperationResult()
        result.add_failure(1, "error msg")
        assert result.failed_count == 1

    def test_add_failure_appends_item(self):
        result = BatchOperationResult()
        result.add_failure(42, "not found")
        assert len(result.failed_items) == 1
        assert result.failed_items[0]["reason"] == "not found"

    def test_add_failure_with_custom_id_field(self):
        result = BatchOperationResult()
        result.add_failure(99, "invalid", id_field="task_id")
        assert result.failed_items[0]["task_id"] == 99

    def test_to_dict_basic(self):
        result = BatchOperationResult()
        result.add_success()
        result.add_failure(1, "fail reason")
        d = result.to_dict()
        assert d["success_count"] == 1
        assert d["failed_count"] == 1
        assert isinstance(d["failed_items"], list)

    def test_to_dict_custom_id_field(self):
        result = BatchOperationResult()
        result.add_failure(7, "err", id_field="task_id")
        d = result.to_dict(id_field="task_id")
        assert d["failed_items"][0]["task_id"] == 7

    def test_multiple_successes_and_failures(self):
        result = BatchOperationResult()
        for i in range(5):
            result.add_success()
        for i in range(3):
            result.add_failure(i, f"error {i}")
        assert result.success_count == 5
        assert result.failed_count == 3
        assert len(result.failed_items) == 3

    def test_to_dict_empty(self):
        result = BatchOperationResult()
        d = result.to_dict()
        assert d["success_count"] == 0
        assert d["failed_count"] == 0
        assert d["failed_items"] == []


# =============================================================================
# BatchOperationExecutor - mock db
# =============================================================================

class SimpleModel:
    """简单模型用于测试"""
    __tablename__ = "tasks"

    def __init__(self, id_, status="PENDING", is_active=True):
        self.id = id_
        self.status = status
        self.is_active = is_active
        self.updated_by = None


def make_executor_with_entities(entities, db=None):
    """创建 executor 并注入预过滤函数（绕过 SQLAlchemy 查询）"""
    if db is None:
        db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()

    user = MagicMock()
    user.id = 1

    entity_map = {e.id: e for e in entities}

    def pre_filter(db_, ids):
        return [entity_map[i] for i in ids if i in entity_map]

    executor = BatchOperationExecutor(
        model=SimpleModel,
        db=db,
        current_user=user,
    )
    return executor, pre_filter, db


class TestBatchOperationExecutor:

    def test_empty_ids_returns_empty_result(self):
        db = MagicMock()
        user = MagicMock()
        executor = BatchOperationExecutor(SimpleModel, db, user)
        result = executor.execute([], operation_func=lambda e: None)
        assert result.success_count == 0
        assert result.failed_count == 0

    def test_successful_operation(self):
        entities = [SimpleModel(1), SimpleModel(2), SimpleModel(3)]
        executor, pre_filter, db = make_executor_with_entities(entities)

        results_seen = []
        def op(entity):
            results_seen.append(entity.id)

        result = executor.execute(
            entity_ids=[1, 2, 3],
            operation_func=op,
            pre_filter_func=pre_filter,
        )

        assert result.success_count == 3
        assert result.failed_count == 0
        assert sorted(results_seen) == [1, 2, 3]

    def test_missing_entity_counted_as_failure(self):
        entities = [SimpleModel(1)]
        executor, pre_filter, db = make_executor_with_entities(entities)

        result = executor.execute(
            entity_ids=[1, 999],
            operation_func=lambda e: None,
            pre_filter_func=pre_filter,
        )

        assert result.success_count == 1
        assert result.failed_count == 1

    def test_validator_rejects_entity(self):
        entities = [SimpleModel(1, status="COMPLETED"), SimpleModel(2, status="PENDING")]
        executor, pre_filter, db = make_executor_with_entities(entities)

        result = executor.execute(
            entity_ids=[1, 2],
            operation_func=lambda e: setattr(e, "status", "DONE"),
            validator_func=lambda e: e.status != "COMPLETED",
            error_message="已完成，不可修改",
            pre_filter_func=pre_filter,
        )

        assert result.success_count == 1
        assert result.failed_count == 1
        assert "已完成" in result.failed_items[0]["reason"]

    def test_operation_exception_counted_as_failure(self):
        entities = [SimpleModel(1)]
        executor, pre_filter, db = make_executor_with_entities(entities)

        def bad_op(entity):
            raise ValueError("operation failed")

        result = executor.execute(
            entity_ids=[1],
            operation_func=bad_op,
            pre_filter_func=pre_filter,
        )

        assert result.success_count == 0
        assert result.failed_count == 1
        assert "operation failed" in result.failed_items[0]["reason"]

    def test_log_func_called(self):
        entities = [SimpleModel(1)]
        executor, pre_filter, db = make_executor_with_entities(entities)

        log_calls = []
        def log_fn(entity, op_type):
            log_calls.append((entity.id, op_type))

        result = executor.execute(
            entity_ids=[1],
            operation_func=lambda e: None,
            log_func=log_fn,
            operation_type="TEST_OP",
            pre_filter_func=pre_filter,
        )

        assert result.success_count == 1
        assert len(log_calls) == 1
        assert log_calls[0] == (1, "TEST_OP")

    def test_updated_by_set_when_no_log_func(self):
        e = SimpleModel(1)
        e.updated_by = None
        executor, pre_filter, db = make_executor_with_entities([e])

        result = executor.execute(
            entity_ids=[1],
            operation_func=lambda ent: None,
            operation_type="BATCH_UPDATE",
            pre_filter_func=pre_filter,
        )

        assert result.success_count == 1
        assert e.updated_by == 1  # current_user.id = 1

    def test_db_add_called_for_each_success(self):
        entities = [SimpleModel(1), SimpleModel(2)]
        db = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        user = MagicMock()
        user.id = 1
        entity_map = {e.id: e for e in entities}

        executor = BatchOperationExecutor(SimpleModel, db, user)

        result = executor.execute(
            entity_ids=[1, 2],
            operation_func=lambda e: None,
            pre_filter_func=lambda db_, ids: [entity_map[i] for i in ids if i in entity_map],
        )

        assert result.success_count == 2
        assert db.add.call_count == 2
        db.commit.assert_called_once()


# =============================================================================
# BatchOperationExecutor 便利方法
# =============================================================================

def make_executor_with_scope_filter(entities, db=None):
    """创建 executor，通过 scope_filter_func 注入实体（支持 batch_update/delete/status_update）"""
    if db is None:
        db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()

    user = MagicMock()
    user.id = 1

    entity_map = {e.id: e for e in entities}

    def scope_filter(db_, ids, user_):
        return [entity_map[i] for i in ids if i in entity_map]

    executor = BatchOperationExecutor(
        model=SimpleModel,
        db=db,
        current_user=user,
        scope_filter_func=scope_filter,
    )
    return executor, db


class TestBatchUpdateAndDelete:

    def test_batch_update(self):
        entities = [SimpleModel(1, status="PENDING"), SimpleModel(2, status="PENDING")]
        executor, db = make_executor_with_scope_filter(entities)

        result = executor.batch_update(
            entity_ids=[1, 2],
            update_func=lambda e: setattr(e, "status", "DONE"),
        )

        assert result.success_count == 2
        assert entities[0].status == "DONE"
        assert entities[1].status == "DONE"

    def test_batch_delete_soft(self):
        entities = [SimpleModel(1), SimpleModel(2)]
        executor, db = make_executor_with_scope_filter(entities)

        result = executor.batch_delete(
            entity_ids=[1, 2],
            soft_delete=True,
        )

        assert result.success_count == 2
        assert entities[0].is_active is False
        assert entities[1].is_active is False

    def test_batch_delete_hard(self):
        entities = [SimpleModel(1)]
        executor, db = make_executor_with_scope_filter(entities)

        result = executor.batch_delete(
            entity_ids=[1],
            soft_delete=False,
        )

        assert result.success_count == 1
        db.delete.assert_called_once_with(entities[0])

    def test_batch_status_update(self):
        entities = [SimpleModel(1, status="PENDING"), SimpleModel(2, status="PENDING")]
        executor, db = make_executor_with_scope_filter(entities)

        result = executor.batch_status_update(
            entity_ids=[1, 2],
            new_status="APPROVED",
        )

        assert result.success_count == 2
        assert entities[0].status == "APPROVED"
        assert entities[1].status == "APPROVED"

    def test_batch_status_update_missing_field_raises(self):
        """状态字段不存在时应失败"""
        entities = [SimpleModel(1)]
        executor, db = make_executor_with_scope_filter(entities)

        result = executor.batch_status_update(
            entity_ids=[1],
            new_status="DONE",
            status_field="nonexistent_field",
        )

        # 操作抛异常，计为失败
        assert result.failed_count == 1

    def test_batch_update_with_validator(self):
        entities = [SimpleModel(1, status="LOCKED"), SimpleModel(2, status="OPEN")]
        executor, db = make_executor_with_scope_filter(entities)

        result = executor.batch_update(
            entity_ids=[1, 2],
            update_func=lambda e: setattr(e, "status", "DONE"),
            validator_func=lambda e: e.status != "LOCKED",
            error_message="已锁定",
        )

        assert result.success_count == 1
        assert result.failed_count == 1
