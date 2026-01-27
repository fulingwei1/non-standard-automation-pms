# -*- coding: utf-8 -*-
"""
StatusUpdateService 单元测试

测试通用状态更新服务的各项功能
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from app.services.status_update_service import StatusUpdateResult, StatusUpdateService
from app.models.user import User


@pytest.mark.unit
class TestStatusUpdateResult:
    """测试 StatusUpdateResult 类"""

    def test_success_result(self):
        """测试成功结果"""
        entity = Mock()
        result = StatusUpdateResult(
            success=True,
            entity=entity,
            old_status="PENDING",
            new_status="APPROVED",
            message="状态已更新",
        )

        assert result.success is True
        assert result.entity == entity
        assert result.old_status == "PENDING"
        assert result.new_status == "APPROVED"
        assert result.message == "状态已更新"
        assert result.errors == []

    def test_failure_result(self):
        """测试失败结果"""
        result = StatusUpdateResult(
            success=False,
            old_status="PENDING",
            new_status="INVALID",
            errors=["无效的状态值"],
        )

        assert result.success is False
        assert result.errors == ["无效的状态值"]


@pytest.mark.unit
class TestStatusUpdateService:
    """测试 StatusUpdateService 类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        return db

    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = Mock(spec=User)
        user.id = 1
        user.real_name = "测试用户"
        user.username = "testuser"
        return user

    @pytest.fixture
    def mock_entity(self):
        """创建模拟实体"""
        entity = Mock()
        entity.id = 100
        entity.status = "PENDING"
        return entity

    def test_update_status_success(self, mock_db, mock_user, mock_entity):
        """测试成功更新状态"""
        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
            valid_statuses=["PENDING", "APPROVED", "REJECTED"],
        )

        assert result.success is True
        assert result.old_status == "PENDING"
        assert result.new_status == "APPROVED"
        assert mock_entity.status == "APPROVED"
        mock_db.add.assert_called_once_with(mock_entity)
        mock_db.commit.assert_called_once()

    def test_update_status_no_change(self, mock_db, mock_user, mock_entity):
        """测试状态未变化"""
        mock_entity.status = "APPROVED"
        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
        )

        assert result.success is True
        assert result.message == "状态未发生变化"
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_update_status_invalid_status(self, mock_db, mock_user, mock_entity):
        """测试无效状态值"""
        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="INVALID",
            operator=mock_user,
            valid_statuses=["PENDING", "APPROVED", "REJECTED"],
        )

        assert result.success is False
        assert "无效的状态值" in result.errors[0]
        assert mock_entity.status == "PENDING"  # 状态未改变
        mock_db.commit.assert_not_called()

    def test_update_status_transition_rule_violation(self, mock_db, mock_user, mock_entity):
        """测试状态转换规则违反"""
        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
            transition_rules={
                "PENDING": ["REJECTED"],  # 只能转换到REJECTED
            },
        )

        assert result.success is False
        assert "不允许的状态转换" in result.errors[0]
        assert mock_entity.status == "PENDING"  # 状态未改变

    def test_update_status_timestamp_fields(self, mock_db, mock_user, mock_entity):
        """测试时间戳字段自动设置"""
        mock_entity.resolved_time = None
        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="RESOLVED",
            operator=mock_user,
            timestamp_fields={
                "RESOLVED": "resolved_time",
            },
        )

        assert result.success is True
        assert mock_entity.resolved_time is not None
        assert isinstance(mock_entity.resolved_time, datetime)

    def test_update_status_timestamp_not_set_if_exists(self, mock_db, mock_user, mock_entity):
        """测试时间戳字段已存在时不覆盖"""
        existing_time = datetime(2025, 1, 1, 10, 0, 0)
        mock_entity.resolved_time = existing_time
        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="RESOLVED",
            operator=mock_user,
            timestamp_fields={
                "RESOLVED": "resolved_time",
            },
        )

        assert result.success is True
        assert mock_entity.resolved_time == existing_time  # 未覆盖

    def test_update_status_related_entities(self, mock_db, mock_user, mock_entity):
        """测试关联实体状态更新"""
        related_entity = Mock()
        related_entity.status = "IDLE"
        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="STARTED",
            operator=mock_user,
            related_entities=[{
                "entity": related_entity,
                "field": "status",
                "value": "WORKING",
            }],
        )

        assert result.success is True
        assert related_entity.status == "WORKING"
        mock_db.add.assert_any_call(related_entity)

    def test_update_status_history_callback(self, mock_db, mock_user, mock_entity):
        """测试历史记录回调"""
        history_called = []

        def history_callback(entity, old_status, new_status, operator, reason):
            history_called.append({
                "entity": entity,
                "old_status": old_status,
                "new_status": new_status,
                "operator": operator,
                "reason": reason,
            })

        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
            history_callback=history_callback,
            reason="测试原因",
        )

        assert result.success is True
        assert len(history_called) == 1
        assert history_called[0]["old_status"] == "PENDING"
        assert history_called[0]["new_status"] == "APPROVED"
        assert history_called[0]["operator"] == mock_user
        assert history_called[0]["reason"] == "测试原因"

    def test_update_status_before_update_callback(self, mock_db, mock_user, mock_entity):
        """测试更新前回调"""
        callback_called = []

        def before_callback(entity, old_status, new_status, operator):
            callback_called.append({
                "entity": entity,
                "old_status": old_status,
                "new_status": new_status,
            })

        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
            before_update_callback=before_callback,
        )

        assert result.success is True
        assert len(callback_called) == 1
        assert callback_called[0]["old_status"] == "PENDING"
        assert callback_called[0]["new_status"] == "APPROVED"

    def test_update_status_after_update_callback(self, mock_db, mock_user, mock_entity):
        """测试更新后回调"""
        callback_called = []

        def after_callback(entity, old_status, new_status, operator):
            callback_called.append({
                "entity": entity,
                "old_status": old_status,
                "new_status": new_status,
            })

        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
            after_update_callback=after_callback,
        )

        assert result.success is True
        assert len(callback_called) == 1
        assert callback_called[0]["old_status"] == "PENDING"
        assert callback_called[0]["new_status"] == "APPROVED"

    def test_update_status_before_callback_failure(self, mock_db, mock_user, mock_entity):
        """测试更新前回调失败"""
        def before_callback(entity, old_status, new_status, operator):
            raise ValueError("回调失败")

        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
            before_update_callback=before_callback,
        )

        assert result.success is False
        assert "更新前回调执行失败" in result.errors[0]
        assert mock_entity.status == "PENDING"  # 状态未改变

    def test_update_status_history_callback_failure(self, mock_db, mock_user, mock_entity):
        """测试历史记录回调失败不影响主流程"""
        def history_callback(entity, old_status, new_status, operator, reason):
            raise ValueError("历史记录失败")

        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
            history_callback=history_callback,
        )

        # 历史记录失败不影响主流程，但会记录错误
        assert result.success is True
        assert mock_entity.status == "APPROVED"
        assert len(result.errors) > 0
        assert "历史记录失败" in result.errors[0]

    def test_update_status_database_commit_failure(self, mock_db, mock_user, mock_entity):
        """测试数据库提交失败"""
        mock_db.commit.side_effect = Exception("数据库错误")

        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
        )

        assert result.success is False
        assert "数据库提交失败" in result.errors[0]
        mock_db.rollback.assert_called_once()

    def test_update_status_custom_status_field(self, mock_db, mock_user, mock_entity):
        """测试自定义状态字段名"""
        mock_entity.state = "DRAFT"  # 使用state字段而不是status
        service = StatusUpdateService(mock_db)

        result = service.update_status(
            entity=mock_entity,
            new_status="PUBLISHED",
            operator=mock_user,
            status_field="state",
        )

        assert result.success is True
        assert mock_entity.state == "PUBLISHED"
        assert result.old_status == "DRAFT"
        assert result.new_status == "PUBLISHED"

    def test_update_status_with_transition_log(self, mock_db, mock_user, mock_entity):
        """测试使用统一状态转换日志"""
        service = StatusUpdateService(mock_db)

        result = service.update_status_with_transition_log(
            entity=mock_entity,
            new_status="APPROVED",
            operator=mock_user,
            entity_type="SERVICE_TICKET",
            valid_statuses=["PENDING", "APPROVED"],
            action_type="STATUS_UPDATE",
            reason="测试原因",
        )

        assert result.success is True
        # 验证创建了日志记录
        assert mock_db.add.call_count >= 1  # 至少添加了实体和日志
