# -*- coding: utf-8 -*-
"""
Unit tests for batch_operations.py
Covers: app/utils/batch_operations.py
"""

import pytest
from unittest.mock import MagicMock, patch, call
from typing import List

from app.utils.batch_operations import BatchOperationResult, BatchOperationExecutor


class TestBatchOperationResult:
    """Tests for BatchOperationResult class."""

    def test_initial_state(self):
        """Fresh result has zero counts and empty failed_items."""
        result = BatchOperationResult()
        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.failed_items == []

    def test_add_success_increments_count(self):
        """add_success increments success_count."""
        result = BatchOperationResult()
        result.add_success()
        result.add_success()
        assert result.success_count == 2

    def test_add_failure_increments_count_and_records_item(self):
        """add_failure increments failed_count and records item info."""
        result = BatchOperationResult()
        result.add_failure(entity_id=42, reason="实体不存在", id_field="task_id")
        assert result.failed_count == 1
        assert result.failed_items[0]["task_id"] == 42
        assert result.failed_items[0]["reason"] == "实体不存在"

    def test_to_dict_returns_correct_structure(self):
        """to_dict returns dict with success_count, failed_count, failed_items."""
        result = BatchOperationResult()
        result.add_success()
        result.add_success()
        result.add_failure(entity_id=5, reason="验证失败")

        d = result.to_dict()
        assert d["success_count"] == 2
        assert d["failed_count"] == 1
        assert isinstance(d["failed_items"], list)

    def test_to_dict_with_custom_id_field(self):
        """to_dict supports custom id_field parameter."""
        result = BatchOperationResult()
        result.add_failure(entity_id=10, reason="error", id_field="project_id")
        d = result.to_dict(id_field="project_id")
        assert d["failed_count"] == 1

    def test_mixed_success_and_failure(self):
        """Multiple successes and failures tracked independently."""
        result = BatchOperationResult()
        for i in range(3):
            result.add_success()
        for i in range(2):
            result.add_failure(entity_id=i, reason=f"error {i}")
        assert result.success_count == 3
        assert result.failed_count == 2


class TestBatchOperationExecutor:
    """Tests for BatchOperationExecutor class."""

    def _make_executor(self, entities=None, id_field="id"):
        """Helper to create executor with mocked DB."""
        model = MagicMock()
        model.__tablename__ = "tasks"
        db = MagicMock()
        current_user = MagicMock()
        current_user.id = 1

        if entities is not None:
            db.query.return_value.filter.return_value.all.return_value = entities

        executor = BatchOperationExecutor(
            model=model,
            db=db,
            current_user=current_user,
            id_field=id_field,
        )
        return executor, db, model

    def test_execute_empty_ids_returns_empty_result(self):
        """Executing with empty id list returns empty BatchOperationResult."""
        executor, db, _ = self._make_executor()
        result = executor.execute(entity_ids=[], operation_func=lambda e: None)
        assert result.success_count == 0
        assert result.failed_count == 0

    def test_execute_missing_entity_adds_failure(self):
        """Entities not found in DB are added as failures."""
        executor, db, model = self._make_executor(entities=[])
        # Model has no id column to match - entity not found
        model.__tablename__ = "tasks"

        result = executor.execute(
            entity_ids=[1, 2],
            operation_func=lambda e: None,
        )
        assert result.failed_count == 2
        assert result.success_count == 0

    def test_execute_success_with_valid_entities(self):
        """Entities found are operated on and counted as successes."""
        entity1 = MagicMock()
        entity1.id = 1
        entity2 = MagicMock()
        entity2.id = 2
        entities = [entity1, entity2]

        executor, db, model = self._make_executor(entities=entities)

        operated = []
        result = executor.execute(
            entity_ids=[1, 2],
            operation_func=lambda e: operated.append(e.id),
        )
        assert result.success_count == 2
        assert result.failed_count == 0
        assert sorted(operated) == [1, 2]

    def test_execute_validator_failure_adds_to_failed(self):
        """Entities failing validator are added as failures."""
        entity = MagicMock()
        entity.id = 1

        executor, db, model = self._make_executor(entities=[entity])

        result = executor.execute(
            entity_ids=[1],
            operation_func=lambda e: None,
            validator_func=lambda e: False,  # always fails
            error_message="状态不允许",
        )
        assert result.failed_count == 1
        assert result.success_count == 0

    def test_execute_validator_success_allows_operation(self):
        """Entities passing validator are operated on."""
        entity = MagicMock()
        entity.id = 5

        executor, db, model = self._make_executor(entities=[entity])

        operated = []
        result = executor.execute(
            entity_ids=[5],
            operation_func=lambda e: operated.append(e.id),
            validator_func=lambda e: True,
        )
        assert result.success_count == 1
        assert 5 in operated

    def test_execute_operation_exception_adds_failure(self):
        """Exception during operation_func adds entity to failures."""
        entity = MagicMock()
        entity.id = 3

        executor, db, model = self._make_executor(entities=[entity])

        def bad_op(e):
            raise RuntimeError("操作失败")

        result = executor.execute(entity_ids=[3], operation_func=bad_op)
        assert result.failed_count == 1
        assert result.success_count == 0

    def test_batch_update_delegates_to_execute(self):
        """batch_update calls execute with the provided update_func."""
        entity = MagicMock()
        entity.id = 10

        executor, db, model = self._make_executor(entities=[entity])

        updated = []
        result = executor.batch_update(
            entity_ids=[10],
            update_func=lambda e: updated.append(e.id),
        )
        assert result.success_count == 1
        assert 10 in updated

    def test_execute_commits_on_success(self):
        """DB commit is called after executing operations."""
        entity = MagicMock()
        entity.id = 1

        executor, db, model = self._make_executor(entities=[entity])
        executor.execute(entity_ids=[1], operation_func=lambda e: None)
        db.commit.assert_called_once()

    def test_execute_with_pre_filter_func(self):
        """pre_filter_func overrides default DB query."""
        entity = MagicMock()
        entity.id = 7

        executor, db, model = self._make_executor()

        result = executor.execute(
            entity_ids=[7],
            operation_func=lambda e: None,
            pre_filter_func=lambda db_, ids: [entity],
        )
        assert result.success_count == 1

    def test_execute_with_log_func(self):
        """log_func is called for each successfully processed entity."""
        entity = MagicMock()
        entity.id = 2

        executor, db, model = self._make_executor(entities=[entity])

        log_calls = []
        result = executor.execute(
            entity_ids=[2],
            operation_func=lambda e: None,
            log_func=lambda e, op: log_calls.append((e.id, op)),
            operation_type="TEST_OP",
        )
        assert result.success_count == 1
        assert (2, "TEST_OP") in log_calls
