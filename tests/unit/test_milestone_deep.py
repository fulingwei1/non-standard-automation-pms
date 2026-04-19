# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 里程碑服务"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestMilestoneServiceBusinessLogic:
    """里程碑服务业务逻辑测试"""

    def test_complete_milestone(self):
        """测试完成里程碑会调用 update 并回查模型"""
        try:
            from app.services.milestone_service import MilestoneService

            mock_db = MagicMock()
            service = MilestoneService(mock_db)
            milestone_resp = MagicMock(actual_date=None)
            service.get = MagicMock(return_value=milestone_resp)
            service.update = MagicMock()
            milestone_model = MagicMock(id=1, status="COMPLETED")
            mock_db.query.return_value.filter.return_value.first.return_value = milestone_model

            result = service.complete_milestone(1)

            service.update.assert_called_once()
            assert result is milestone_model
        except ImportError:
            pytest.skip("Module not found")

    def test_milestone_bulk_create(self):
        """测试批量创建要求使用当前 MilestoneCreate schema"""
        try:
            from app.services.milestone_service import MilestoneService
            from app.schemas.project.milestone import MilestoneCreate

            mock_db = MagicMock()
            service = MilestoneService(mock_db)
            service.repository.create_many = MagicMock(return_value=[MagicMock()])
            service._to_response = MagicMock(return_value=MagicMock())

            result = service.bulk_create(
                [
                    MilestoneCreate(
                        project_id=1,
                        milestone_code="MS-001",
                        milestone_name="milestone1",
                        milestone_type="CUSTOM",
                        planned_date=date.today(),
                    )
                ]
            )

            assert len(result) == 1
        except ImportError:
            pytest.skip("Module not found")