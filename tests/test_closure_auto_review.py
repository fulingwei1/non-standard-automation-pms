# -*- coding: utf-8 -*-
"""LessonsCollectionService (ClosureAutoReviewService) 测试

本测试文件测试项目结项时自动触发回顾的功能
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

import pytest


class TestClosureAutoReviewService:
    """ClosureAutoReviewService (LessonsCollectionService) 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import LessonsCollectionService
        return LessonsCollectionService(mock_db)

    def _make_project_mock(self, **kwargs):
        """创建项目 mock"""
        p = MagicMock()
        p.id = kwargs.get("id", 1)
        p.project_code = kwargs.get("project_code", "PRJ001")
        p.project_name = kwargs.get("project_name", "测试项目")
        p.budget_amount = kwargs.get("budget_amount")
        p.actual_cost = kwargs.get("actual_cost")
        p.planned_start_date = kwargs.get("planned_start_date")
        p.planned_end_date = kwargs.get("planned_end_date")
        p.actual_start_date = kwargs.get("actual_start_date")
        p.actual_end_date = kwargs.get("actual_end_date")
        return p

    @patch("app.services.project.closure_readiness_service.date")
    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_auto_review_trigger_conditions(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, mock_date, service, mock_db
    ):
        """测试自动回顾触发条件 - 项目结项时自动触发"""
        mock_date.today.return_value = date(2025, 8, 1)

        # Create mock project
        mock_project = self._make_project_mock(
            id=1, project_code="PRJ001", project_name="测试项目",
            budget_amount=Decimal("100000"), actual_cost=Decimal("95000"),
            planned_start_date=date(2025, 1, 1), planned_end_date=date(2025, 6, 30),
            actual_start_date=date(2025, 1, 1), actual_end_date=date(2025, 7, 15)
        )

        # Use side_effect to handle multiple queries
        call_index = [0]
        def query_side_effect(*args):
            call_index[0] += 1
            result = MagicMock()
            if call_index[0] == 1:
                # First query: Project
                result.filter.return_value.first.return_value = mock_project
            elif call_index[0] == 2:
                # Second query: ProjectReview (existing review)
                result.filter.return_value.first.return_value = None
            elif call_index[0] == 3:
                # Third query: func.count
                result.filter.return_value.scalar.return_value = 0
            return result

        mock_db.query.side_effect = query_side_effect

        # Mock review object
        mock_review = MagicMock()
        mock_review.id = 100
        mock_review.review_no = "REV-PRJ001-001"
        mock_review_cls.return_value = mock_review

        # Execute
        result = service.auto_collect(project_id=1, triggered_by=1)

        # Verify
        assert "review_id" in result
        assert result["review_id"] == 100
        assert result["already_exists"] is False
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @patch("app.services.project.closure_readiness_service.date")
    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_generate_retrospective_report(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, mock_date, service, mock_db
    ):
        """测试生成回顾报告 - 验证报告模板结构"""
        mock_date.today.return_value = date(2025, 8, 1)

        mock_project = self._make_project_mock(
            id=1, project_code="PRJ002", project_name="完整数据项目",
            budget_amount=Decimal("200000"), actual_cost=Decimal("180000"),
            planned_start_date=date(2025, 1, 1), planned_end_date=date(2025, 12, 31),
            actual_start_date=date(2025, 1, 1), actual_end_date=date(2025, 12, 31)
        )

        call_index = [0]
        def query_side_effect(*args):
            call_index[0] += 1
            result = MagicMock()
            if call_index[0] == 1:
                result.filter.return_value.first.return_value = mock_project
            elif call_index[0] == 2:
                result.filter.return_value.first.return_value = None
            elif call_index[0] == 3:
                result.filter.return_value.scalar.return_value = 0
            return result

        mock_db.query.side_effect = query_side_effect

        mock_review = MagicMock()
        mock_review.id = 200
        mock_review.review_no = "REV-PRJ002-001"
        mock_review_cls.return_value = mock_review

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert result["review_id"] == 200
        assert "lessons_count" in result
        assert "best_practices_count" in result
        assert "message" in result

    @patch("app.services.project.closure_readiness_service.date")
    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_retrospective_with_no_data(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, mock_date, service, mock_db
    ):
        """测试无数据边界 - 项目数据为空或缺失时的处理"""
        mock_date.today.return_value = date(2025, 8, 1)

        mock_project = self._make_project_mock(
            id=1, project_code="PRJ003", project_name="空数据项目",
            budget_amount=None, actual_cost=None,
            planned_start_date=None, planned_end_date=None,
            actual_start_date=None, actual_end_date=None
        )

        call_index = [0]
        def query_side_effect(*args):
            call_index[0] += 1
            result = MagicMock()
            if call_index[0] == 1:
                result.filter.return_value.first.return_value = mock_project
            elif call_index[0] == 2:
                result.filter.return_value.first.return_value = None
            elif call_index[0] == 3:
                result.filter.return_value.scalar.return_value = 0
            return result

        mock_db.query.side_effect = query_side_effect

        mock_review = MagicMock()
        mock_review.id = 300
        mock_review.review_no = "REV-PRJ003-001"
        mock_review_cls.return_value = mock_review

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert "review_id" in result
        assert result["review_id"] == 300
        assert "lessons_count" in result
        assert "best_practices_count" in result

    @patch("app.services.project.closure_readiness_service.date")
    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_extract_lessons_learned(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, mock_date, service, mock_db
    ):
        """测试提取经验教训 - 从项目数据中自动提取正反经验"""
        mock_date.today.return_value = date(2025, 8, 15)

        mock_project = self._make_project_mock(
            id=1, project_code="PRJ004", project_name="延期超支项目",
            budget_amount=Decimal("100000"), actual_cost=Decimal("130000"),
            planned_start_date=date(2025, 1, 1), planned_end_date=date(2025, 6, 30),
            actual_start_date=date(2025, 1, 1), actual_end_date=date(2025, 8, 15)
        )

        call_index = [0]
        def query_side_effect(*args):
            call_index[0] += 1
            result = MagicMock()
            if call_index[0] == 1:
                result.filter.return_value.first.return_value = mock_project
            elif call_index[0] == 2:
                result.filter.return_value.first.return_value = None
            elif call_index[0] == 3:
                result.filter.return_value.scalar.return_value = 0
            return result

        mock_db.query.side_effect = query_side_effect

        # Track created lessons
        created_lessons = []
        def capture_lesson(*args, **kwargs):
            lesson = MagicMock()
            lesson.id = len(created_lessons) + 1
            created_lessons.append(lesson)
            return lesson

        mock_lesson_cls.side_effect = capture_lesson

        mock_review = MagicMock()
        mock_review.id = 400
        mock_review.review_no = "REV-PRJ004-001"
        mock_review_cls.return_value = mock_review

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert result["lessons_count"] >= 1
        assert mock_db.add.call_count >= 1

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.Project")
    def test_retrospective_already_exists(
        self, mock_project_cls, mock_review_cls, service, mock_db
    ):
        """测试回顾已存在 - 不重复创建"""
        mock_project = self._make_project_mock(
            id=1, project_code="PRJ005", project_name="已有回顾项目"
        )

        mock_existing_review = MagicMock()
        mock_existing_review.id = 500
        mock_existing_review.review_no = "REV-PRJ005-001"

        call_index = [0]
        def query_side_effect(*args):
            call_index[0] += 1
            result = MagicMock()
            if call_index[0] == 1:
                result.filter.return_value.first.return_value = mock_project
            elif call_index[0] == 2:
                result.filter.return_value.first.return_value = mock_existing_review
            return result

        mock_db.query.side_effect = query_side_effect

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert result["already_exists"] is True
        assert result["review_id"] == 500
        assert "message" in result
        mock_db.add.assert_not_called()

    @patch("app.services.project.closure_readiness_service.Project")
    def test_retrospective_project_not_found(
        self, mock_project_cls, service, mock_db
    ):
        """测试项目不存在时的边界情况"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.auto_collect(project_id=999, triggered_by=1)

        assert "error" in result
        assert result["error"] == "项目不存在"
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()