# -*- coding: utf-8 -*-
"""项目结项准备度服务测试 - ClosureReadinessService 专项测试

本测试文件聚焦于 ClosureReadinessService 类的核心功能测试
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


def make_service(db):
    """创建服务实例"""
    from app.services.project.closure_readiness_service import ClosureReadinessService
    return ClosureReadinessService(db)


def test_complete_readiness(mock_db):
    """测试结项就绪检查（完成状态）"""
    with patch("app.services.project.closure_readiness_service.Project") as MockPrj, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNode, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApp, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        proj = MagicMock()
        proj.id = 1
        proj.project_code = "PRJ001"
        proj.project_name = "Test"
        proj.budget_amount = Decimal("100000")
        proj.actual_cost = Decimal("95000")
        proj.invoice_issued = True
        proj.final_payment_completed = True
        
        def query_handler(*args):
            m = MagicMock()
            m.filter.return_value.first.return_value = proj
            m.filter.return_value.all.return_value = []
            return m
        
        mock_db.query.side_effect = query_handler
        
        mock_count_expr = MagicMock()
        mock_count_expr.filter.return_value.scalar.return_value = 10
        MockFunc.count.return_value = mock_count_expr
        
        service = make_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert result["ready"] is True
    assert result["score"] == 100


def test_project_not_found(mock_db):
    """测试项目不存在"""
    with patch("app.services.project.closure_readiness_service.Project"):
        with patch("app.services.project.closure_readiness_service.ProjectStageInstance"):
            with patch("app.services.project.closure_readiness_service.ProjectStage"):
                with patch("app.services.project.closure_readiness_service.ProjectNodeInstance"):
                    with patch("app.services.project.closure_readiness_service.ProjectDocument"):
                        with patch("app.services.project.closure_readiness_service.ProjectCost"):
                            with patch("app.services.project.closure_readiness_service.ApprovalInstance"):
                                with patch("app.services.project.closure_readiness_service.func"):
                                    mock_db.query.return_value.filter.return_value.first.return_value = None
                                    
                                    service = make_service(mock_db)
                                    result = service.check_readiness(project_id=999)

    assert result["ready"] is False
    assert result["score"] == 0
    assert "项目不存在" in result["missing_items"]


# ============================================================================
# ClosureAutoReviewService (LessonsCollectionService) 核心测试
# ============================================================================

class MockProject:
    """简单 mock 项目类，避免 MagicMock f-string 格式化问题"""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.project_code = kwargs.get("project_code", "PRJ001")
        self.project_name = kwargs.get("project_name", "测试项目")
        self.budget_amount = kwargs.get("budget_amount")
        self.actual_cost = kwargs.get("actual_cost")
        self.planned_start_date = kwargs.get("planned_start_date")
        self.planned_end_date = kwargs.get("planned_end_date")
        self.actual_start_date = kwargs.get("actual_start_date")
        self.actual_end_date = kwargs.get("actual_end_date")


@pytest.fixture
def mock_db_review():
    return MagicMock()


def make_lesson_service(db):
    """创建经验收集服务实例"""
    from app.services.project.closure_readiness_service import LessonsCollectionService
    return LessonsCollectionService(db)


class TestClosureAutoReviewService:
    """ClosureAutoReviewService 测试 - 项目结项时自动触发回顾
    
    只测试 2 个核心方法:
    - test_generate_retrospective_report: 生成回顾报告
    - test_extract_lessons_learned: 提取经验教训
    """

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return make_lesson_service(mock_db)

    @patch("app.services.project.closure_readiness_service.date")
    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.func")
    def test_generate_retrospective_report(
        self, mock_func, mock_practice_cls, mock_lesson_cls, mock_review_cls, mock_date, service, mock_db
    ):
        """测试生成回顾报告 - 验证报告模板结构"""
        mock_date.today.return_value = date(2025, 8, 1)
        
        # 使用简单 MockProject 类 - 不 patch Project，直接用 mock_db.query 返回
        mock_project = MockProject(
            id=1,
            project_code="PRJ002",
            project_name="完整数据项目",
            budget_amount=Decimal("200000"),
            actual_cost=Decimal("180000"),
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 12, 31),
            actual_start_date=date(2025, 1, 1),
            actual_end_date=date(2025, 12, 31),
        )

        # 直接设置 mock_db.query 返回我们的 MockProject
        mock_query = MagicMock()
        mock_filter = MagicMock()
        # 第一次调用返回项目，第二次返回 None（无已有回顾）
        mock_filter.first.side_effect = [mock_project, None]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        mock_func.count.return_value.scalar.return_value = 0

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
    @patch("app.services.project.closure_readiness_service.func")
    def test_extract_lessons_learned(
        self, mock_func, mock_practice_cls, mock_lesson_cls, mock_review_cls, mock_date, service, mock_db
    ):
        """测试提取经验教训 - 从项目数据中自动提取正反经验"""
        mock_date.today.return_value = date(2025, 8, 15)
        
        # 使用简单 MockProject 类
        mock_project = MockProject(
            id=1,
            project_code="PRJ004",
            project_name="延期超支项目",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("130000"),
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 6, 30),
            actual_start_date=date(2025, 1, 1),
            actual_end_date=date(2025, 8, 15),
        )

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.side_effect = [mock_project, None]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        mock_func.count.return_value.scalar.return_value = 0

        mock_review = MagicMock()
        mock_review.id = 400
        mock_review.review_no = "REV-PRJ004-001"
        mock_review_cls.return_value = mock_review

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert result["lessons_count"] >= 1
        assert mock_db.add.call_count >= 1