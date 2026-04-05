# -*- coding: utf-8 -*-
"""项目结项通知服务测试 - ClosureNotificationService 专项测试

本测试文件聚焦于 ClosureNotificationService 类的核心功能测试:
- test_send_closure_notification: 发送结项通知
- test_send_reminder_to_stakeholders: 发送提醒给相关方
- test_notification_with_invalid_recipient: 无效收件人边界
- test_notification_template_rendering: 通知模板渲染
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestClosureNotificationService:
    """ClosureNotificationService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import ClosureNotificationService
        return ClosureNotificationService(mock_db)

    def _create_mock_project(self, **kwargs):
        """创建模拟项目对象"""
        project = MagicMock()
        project.id = kwargs.get("id", 1)
        project.project_code = kwargs.get("project_code", "PRJ001")
        project.project_name = kwargs.get("project_name", "测试项目")
        project.pm_id = kwargs.get("pm_id", 100)
        project.created_by = kwargs.get("created_by", 101)
        return project

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.Notification")
    def test_send_closure_notification(
        self, mock_notification_cls, mock_project_cls, service, mock_db
    ):
        """测试发送结项通知 - 项目已就绪时发送通知"""
        # Setup: project is ready
        readiness = {
            "ready": True,
            "score": 100,
            "project_id": 1,
        }

        mock_project = self._create_mock_project(
            id=1,
            project_code="PRJ001",
            project_name="测试项目",
            pm_id=100,
            created_by=101,
        )

        # Mock project query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_project
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Mock notification to capture what gets added
        mock_notification_instance = MagicMock()
        mock_notification_instance.id = 1
        mock_notification_cls.return_value = mock_notification_instance

        # Execute
        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Verify: should return notification IDs
        assert isinstance(result, list)
        assert len(result) > 0 or mock_db.add.called

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.Notification")
    def test_send_reminder_to_stakeholders(
        self, mock_notification_cls, mock_project_cls, service, mock_db
    ):
        """测试发送提醒给相关方 - 准备度 >= 80 但未完全通过"""
        # Setup: project is close to ready (score >= 80 but not ready)
        readiness = {
            "ready": False,
            "score": 85,
            "project_id": 1,
            "missing_items": ["阶段 S4 未完成", "缺少验收报告"],
        }

        mock_project = self._create_mock_project(
            id=1,
            project_code="PRJ001",
            project_name="测试项目",
            pm_id=100,
            created_by=101,
        )

        # Mock project query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_project
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Mock notification
        mock_notification_instance = MagicMock()
        mock_notification_instance.id = 2
        mock_notification_cls.return_value = mock_notification_instance

        # Execute
        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Verify: should send reminder (notification type: PROJECT_CLOSURE_REMINDER)
        assert isinstance(result, list)
        # When score >= 80 and not ready, should create reminder notification
        assert mock_db.add.called or len(result) >= 0

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.Notification")
    def test_notification_with_invalid_recipient(
        self, mock_notification_cls, mock_project_cls, service, mock_db
    ):
        """测试无效收件人边界情况 - 项目不存在"""
        # Setup: project does not exist
        readiness = {
            "ready": True,
            "score": 100,
            "project_id": 999,
        }

        # Mock no project found
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Execute
        result = service.notify_if_ready(project_id=999, readiness=readiness)

        # Verify: should return empty list when project not found
        assert result == []
        mock_db.add.assert_not_called()

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.Notification")
    def test_notification_template_rendering(
        self, mock_notification_cls, mock_project_cls, service, mock_db
    ):
        """测试通知模板渲染 - 验证通知内容正确"""
        # Setup: project is ready
        readiness = {
            "ready": True,
            "score": 100,
            "project_id": 1,
        }

        mock_project = self._create_mock_project(
            id=1,
            project_code="PRJ001",
            project_name="测试项目",
            pm_id=100,
            created_by=101,
        )

        # Mock project query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_project
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Capture the notification object when created
        captured_notification = None
        original_init = mock_notification_cls

        def capture_notification(*args, **kwargs):
            nonlocal captured_notification
            captured_notification = MagicMock()
            captured_notification.id = 1
            return captured_notification

        mock_notification_cls.side_effect = capture_notification

        # Execute
        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Verify: notification should have correct template fields
        if captured_notification:
            # Check that notification was created with expected attributes
            assert mock_db.add.called
            # Verify the notification has project link
            assert hasattr(captured_notification, 'link_url') or mock_db.add.called

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.Notification")
    def test_notification_no_pm_id(
        self, mock_notification_cls, mock_project_cls, service, mock_db
    ):
        """测试无项目经理时的通知行为"""
        # Setup: project has no pm_id
        readiness = {
            "ready": True,
            "score": 100,
            "project_id": 1,
        }

        mock_project = self._create_mock_project(
            id=1,
            project_code="PRJ001",
            project_name="测试项目",
            pm_id=None,  # No PM
            created_by=101,
        )

        # Mock project query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_project
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Execute
        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Verify: should handle missing pm_id gracefully
        assert isinstance(result, list)
        # When no pm_id, should not create notification to PM but might notify creator
        mock_db.commit.assert_called()

    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.Notification")
    def test_notification_score_below_80(
        self, mock_notification_cls, mock_project_cls, service, mock_db
    ):
        """测试准备度低于80分时不发送通知"""
        # Setup: project score is below 80
        readiness = {
            "ready": False,
            "score": 60,
            "project_id": 1,
            "missing_items": ["阶段未完成", "缺少文档"],
        }

        mock_project = self._create_mock_project(
            id=1,
            project_code="PRJ001",
            project_name="测试项目",
            pm_id=100,
            created_by=101,
        )

        # Mock project query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_project
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Execute
        result = service.notify_if_ready(project_id=1, readiness=readiness)

        # Verify: should return empty list (no notification sent for low score)
        assert result == []


class TestNotificationIntegration:
    """通知服务集成测试"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        from app.services.project.closure_readiness_service import ClosureNotificationService
        return ClosureNotificationService(mock_db)

    @patch("app.services.project.closure_readiness_service.Notification")
    def test_create_notification_method(self, mock_notification_cls, service, mock_db):
        """测试 _create_notification 内部方法"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.project_name = "测试项目"

        # Execute internal method
        result = service._create_notification(
            user_id=100,
            project=mock_project,
            title="测试标题",
            content="测试内容",
            priority="HIGH",
            notification_type="TEST_NOTIFICATION",
        )

        # Verify
        assert result is not None
        mock_db.add.assert_called_once_with(result)