# -*- coding: utf-8 -*-
"""
Tests for milestone_service
里程碑服务测试
"""

import pytest
from datetime import date
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.models.project import ProjectMilestone


@pytest.mark.unit
class TestMilestoneService:
    """里程碑服务测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """创建 MilestoneService 实例"""
        from app.services.milestone_service import MilestoneService
        return MilestoneService(mock_db)

    def test_init(self, mock_db):
        """测试服务初始化"""
        from app.services.milestone_service import MilestoneService
        service = MilestoneService(mock_db)
        assert service.db == mock_db
        assert service.model == ProjectMilestone
        assert service.resource_name == "里程碑"

    def test_get_by_project(self, service, mock_db):
        """测试获取项目里程碑"""
        mock_milestones = [
            Mock(id=1, project_id=100, name="M1", planned_date=date(2026, 1, 1)),
            Mock(id=2, project_id=100, name="M2", planned_date=date(2026, 2, 1)),
        ]

        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_milestones
        mock_db.query.return_value = mock_query

        result = service.get_by_project(100)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        mock_db.query.assert_called_with(ProjectMilestone)

    def test_get_by_project_empty(self, service, mock_db):
        """测试获取空项目里程碑"""
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service.get_by_project(999)

        assert result == []

    def test_complete_milestone(self, service, mock_db):
        """测试完成里程碑"""
        mock_milestone = Mock(
            id=1,
            project_id=100,
            name="Test Milestone",
            status="PENDING",
            planned_date=date(2026, 1, 15),
            actual_date=None
        )

        # Mock get method
        with patch.object(service, 'get', return_value=mock_milestone):
            with patch.object(service, 'update') as mock_update:
                # Mock the final query
                mock_db.query.return_value.filter.return_value.first.return_value = mock_milestone

                result = service.complete_milestone(1)

                assert result == mock_milestone
                mock_update.assert_called_once()
                update_call = mock_update.call_args
                assert update_call[0][0] == 1  # milestone_id

    def test_complete_milestone_with_actual_date(self, service, mock_db):
        """测试用指定日期完成里程碑"""
        mock_milestone = Mock(
            id=1,
            project_id=100,
            name="Test Milestone",
            status="PENDING",
            planned_date=date(2026, 1, 15),
            actual_date=None
        )
        actual_completion_date = date(2026, 1, 10)

        with patch.object(service, 'get', return_value=mock_milestone):
            with patch.object(service, 'update') as mock_update:
                mock_db.query.return_value.filter.return_value.first.return_value = mock_milestone

                result = service.complete_milestone(1, actual_date=actual_completion_date)

                assert result == mock_milestone
                mock_update.assert_called_once()
                update_call = mock_update.call_args
                update_data = update_call[0][1]
                assert update_data.actual_date == actual_completion_date

    def test_complete_milestone_preserves_existing_actual_date(self, service, mock_db):
        """测试完成里程碑时保留已有的实际日期"""
        existing_actual_date = date(2026, 1, 8)
        mock_milestone = Mock(
            id=1,
            project_id=100,
            name="Test Milestone",
            status="PENDING",
            planned_date=date(2026, 1, 15),
            actual_date=existing_actual_date
        )

        with patch.object(service, 'get', return_value=mock_milestone):
            with patch.object(service, 'update') as mock_update:
                mock_db.query.return_value.filter.return_value.first.return_value = mock_milestone

                result = service.complete_milestone(1)

                mock_update.assert_called_once()
                update_call = mock_update.call_args
                update_data = update_call[0][1]
                assert update_data.actual_date == existing_actual_date
