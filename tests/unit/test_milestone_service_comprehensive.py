# -*- coding: utf-8 -*-
"""
MilestoneService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- get_by_project: 获取项目里程碑
- complete_milestone: 完成里程碑
"""

from unittest.mock import MagicMock, patch
from datetime import date, datetime

import pytest


class TestMilestoneServiceInit:
    """测试 MilestoneService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.milestone_service import MilestoneService

        mock_db = MagicMock()

        service = MilestoneService(mock_db)

        assert service.db == mock_db
        assert service.resource_name == "里程碑"

    def test_sets_correct_model(self):
        """测试设置正确的模型"""
        from app.services.milestone_service import MilestoneService
        from app.models.project import ProjectMilestone

        mock_db = MagicMock()

        service = MilestoneService(mock_db)

        assert service.model == ProjectMilestone


class TestGetByProject:
    """测试 get_by_project 方法"""

    def test_returns_project_milestones(self):
        """测试返回项目里程碑列表"""
        from app.services.milestone_service import MilestoneService

        mock_db = MagicMock()
        service = MilestoneService(mock_db)

        mock_milestone1 = MagicMock()
        mock_milestone1.id = 1
        mock_milestone1.name = "设计完成"
        mock_milestone1.planned_date = date(2024, 3, 1)

        mock_milestone2 = MagicMock()
        mock_milestone2.id = 2
        mock_milestone2.name = "验收完成"
        mock_milestone2.planned_date = date(2024, 6, 1)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            mock_milestone1, mock_milestone2
        ]
        mock_db.query.return_value = mock_query

        result = service.get_by_project(project_id=1)

        assert len(result) == 2
        assert result[0].name == "设计完成"
        assert result[1].name == "验收完成"

    def test_returns_empty_list_for_no_milestones(self):
        """测试没有里程碑时返回空列表"""
        from app.services.milestone_service import MilestoneService

        mock_db = MagicMock()
        service = MilestoneService(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.get_by_project(project_id=999)

        assert result == []

    def test_orders_by_planned_date(self):
        """测试按计划日期排序"""
        from app.services.milestone_service import MilestoneService
        from app.models.project import ProjectMilestone

        mock_db = MagicMock()
        service = MilestoneService(mock_db)

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_query.filter.return_value = mock_filter
        mock_filter.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service.get_by_project(project_id=1)

        mock_filter.order_by.assert_called_once()


class TestCompleteMilestone:
    """测试 complete_milestone 方法"""

    def test_completes_milestone_with_actual_date(self):
        """测试使用指定日期完成里程碑"""
        from app.services.milestone_service import MilestoneService
        from app.models.project import ProjectMilestone

        mock_db = MagicMock()
        service = MilestoneService(mock_db)

        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.actual_date = None

        with patch.object(service, 'get', return_value=mock_milestone):
            with patch.object(service, 'update') as mock_update:
                # 模拟数据库查询返回更新后的里程碑
                updated_milestone = MagicMock()
                updated_milestone.id = 1
                updated_milestone.status = "COMPLETED"
                mock_db.query.return_value.filter.return_value.first.return_value = updated_milestone

                actual_date = date(2024, 3, 15)
                result = service.complete_milestone(
                    milestone_id=1,
                    actual_date=actual_date
                )

                mock_update.assert_called_once()
                update_data = mock_update.call_args[0][1]
                assert update_data.status == "COMPLETED"
                assert update_data.actual_date == actual_date

    def test_completes_milestone_with_today(self):
        """测试使用今天日期完成里程碑"""
        from app.services.milestone_service import MilestoneService

        mock_db = MagicMock()
        service = MilestoneService(mock_db)

        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.actual_date = None

        with patch.object(service, 'get', return_value=mock_milestone):
            with patch.object(service, 'update') as mock_update:
                updated_milestone = MagicMock()
                updated_milestone.id = 1
                updated_milestone.status = "COMPLETED"
                mock_db.query.return_value.filter.return_value.first.return_value = updated_milestone

                result = service.complete_milestone(milestone_id=1)

                mock_update.assert_called_once()
                update_data = mock_update.call_args[0][1]
                assert update_data.status == "COMPLETED"
                assert update_data.actual_date == date.today()

    def test_uses_existing_actual_date_if_available(self):
        """测试使用已有的实际日期"""
        from app.services.milestone_service import MilestoneService

        mock_db = MagicMock()
        service = MilestoneService(mock_db)

        existing_date = date(2024, 3, 10)
        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.actual_date = existing_date

        with patch.object(service, 'get', return_value=mock_milestone):
            with patch.object(service, 'update') as mock_update:
                updated_milestone = MagicMock()
                mock_db.query.return_value.filter.return_value.first.return_value = updated_milestone

                result = service.complete_milestone(milestone_id=1)

                update_data = mock_update.call_args[0][1]
                assert update_data.actual_date == existing_date

    def test_returns_updated_milestone_model(self):
        """测试返回更新后的里程碑模型"""
        from app.services.milestone_service import MilestoneService

        mock_db = MagicMock()
        service = MilestoneService(mock_db)

        mock_milestone = MagicMock()
        mock_milestone.id = 1
        mock_milestone.actual_date = None

        updated_milestone = MagicMock()
        updated_milestone.id = 1
        updated_milestone.status = "COMPLETED"

        with patch.object(service, 'get', return_value=mock_milestone):
            with patch.object(service, 'update'):
                mock_db.query.return_value.filter.return_value.first.return_value = updated_milestone

                result = service.complete_milestone(milestone_id=1)

                assert result == updated_milestone
                assert result.status == "COMPLETED"
