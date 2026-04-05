# -*- coding: utf-8 -*-
"""
项目交付服务测试
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestProjectDeliveryService:
    """项目交付服务测试"""

    def test_create_schedule(self):
        """测试创建交付计划"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        service = ProjectDeliveryService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        result = service.create_schedule(
            project_id=1,
            title="Test Schedule",
            created_by=1
        )
        assert isinstance(result, dict)

    def test_get_schedule(self):
        """测试获取交付计划"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        service = ProjectDeliveryService(mock_db)

        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule

        result = service.get_schedule(schedule_id=1)
        assert result is not None

    def test_get_schedule_not_found(self):
        """测试计划不存在"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = ProjectDeliveryService(mock_db)

        result = service.get_schedule(schedule_id=999)
        assert result is None

    def test_list_schedules(self):
        """测试列出交付计划"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        service = ProjectDeliveryService(mock_db)

        result = service.list_schedules(project_id=1)
        assert isinstance(result, list)

    def test_update_schedule(self):
        """测试更新交付计划"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule
        service = ProjectDeliveryService(mock_db)

        result = service.update_schedule(schedule_id=1, title="Updated Title")
        assert isinstance(result, dict)

    def test_confirm_schedule(self):
        """测试确认交付计划"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule
        service = ProjectDeliveryService(mock_db)

        result = service.confirm_schedule(schedule_id=1, confirmed_by=1)
        assert isinstance(result, dict)

    def test_create_task(self):
        """测试创建任务"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        mock_schedule = MagicMock()
        mock_schedule.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_schedule
        service = ProjectDeliveryService(mock_db)

        result = service.create_task(
            schedule_id=1,
            name="Test Task",
            assignee_id=1
        )
        assert isinstance(result, dict)

    def test_get_gantt_data(self):
        """测试获取甘特图数据"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        service = ProjectDeliveryService(mock_db)

        result = service.get_gantt_data(schedule_id=1)
        assert isinstance(result, dict)

    def test_detect_conflicts(self):
        """测试检测冲突"""
        from app.services.project_delivery_service import ProjectDeliveryService

        mock_db = MagicMock()
        service = ProjectDeliveryService(mock_db)

        result = service.detect_conflicts(schedule_id=1)
        assert isinstance(result, dict)