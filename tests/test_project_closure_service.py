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

@pytest.fixture
def mock_db_review():
    return MagicMock()


def make_lesson_service(db):
    """创建经验收集服务实例"""
    from app.services.project.closure_readiness_service import LessonsCollectionService
    return LessonsCollectionService(db)


class TestClosureAutoReviewService:
    """ClosureAutoReviewService (LessonsCollectionService) 测试 - 项目结项时自动触发回顾"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        from app.services.project.closure_readiness_service import LessonsCollectionService
        return LessonsCollectionService(mock_db)

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_auto_review_trigger_conditions(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, service, mock_db
    ):
        """测试自动回顾触发条件 - 项目结项时自动触发"""
        # Create project with REAL string attributes (not MagicMock)
        proj = MagicMock()
        proj.id = 1
        proj.project_code = "PRJ001"  # Real string!
        proj.project_name = "测试项目"
        proj.project_type = "EOL"
        proj.industry = "汽车电子"
        proj.budget_amount = Decimal("100000")
        proj.actual_cost = Decimal("95000")
        proj.planned_start_date = date(2025, 1, 1)
        proj.planned_end_date = date(2025, 6, 30)
        proj.actual_start_date = date(2025, 1, 1)
        proj.actual_end_date = date(2025, 7, 15)

        # Set up query chain
        mock_q = MagicMock()
        mock_f = MagicMock()
        mock_f.first.side_effect = [proj, None]  # First call returns project, second returns None (no existing review)
        mock_q.filter.return_value = mock_f
        mock_db.query.return_value = mock_q

        mock_func.count.return_value.scalar.return_value = 0

        mock_review = MagicMock()
        mock_review.id = 100
        mock_review.review_no = "REV-PRJ001-001"
        mock_review_cls.return_value = mock_review

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert "review_id" in result
        assert result["review_id"] == 100
        assert result["already_exists"] is False
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_generate_retrospective_report(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, service, mock_db
    ):
        """测试生成回顾报告 - 验证报告模板结构"""
        proj = MagicMock()
        proj.id = 1
        proj.project_code = "PRJ002"
        proj.project_name = "完整数据项目"
        proj.project_type = "EOL"
        proj.industry = "汽车电子"
        proj.budget_amount = Decimal("200000")
        proj.actual_cost = Decimal("180000")
        proj.planned_start_date = date(2025, 1, 1)
        proj.planned_end_date = date(2025, 12, 31)
        proj.actual_start_date = date(2025, 1, 1)
        proj.actual_end_date = date(2025, 12, 31)

        mock_q = MagicMock()
        mock_f = MagicMock()
        mock_f.first.side_effect = [proj, None]
        mock_q.filter.return_value = mock_f
        mock_db.query.return_value = mock_q

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

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_retrospective_with_no_data(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, service, mock_db
    ):
        """测试无数据边界 - 项目数据为空或缺失时的处理"""
        proj = MagicMock()
        proj.id = 1
        proj.project_code = "PRJ003"
        proj.project_name = "空数据项目"
        proj.project_type = None
        proj.industry = None
        proj.budget_amount = None
        proj.actual_cost = None
        proj.planned_start_date = None
        proj.planned_end_date = None
        proj.actual_start_date = None
        proj.actual_end_date = None

        mock_q = MagicMock()
        mock_f = MagicMock()
        mock_f.first.side_effect = [proj, None]
        mock_q.filter.return_value = mock_f
        mock_db.query.return_value = mock_q

        mock_func.count.return_value.scalar.return_value = 0

        mock_review = MagicMock()
        mock_review.id = 300
        mock_review.review_no = "REV-PRJ003-001"
        mock_review_cls.return_value = mock_review

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert "review_id" in result
        assert result["review_id"] == 300

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_extract_lessons_learned(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, service, mock_db
    ):
        """测试提取经验教训 - 从项目数据中自动提取正反经验"""
        proj = MagicMock()
        proj.id = 1
        proj.project_code = "PRJ004"
        proj.project_name = "延期超支项目"
        proj.project_type = "EOL"
        proj.industry = "汽车电子"
        proj.budget_amount = Decimal("100000")
        proj.actual_cost = Decimal("130000")  # 30% overrun
        proj.planned_start_date = date(2025, 1, 1)
        proj.planned_end_date = date(2025, 6, 30)
        proj.actual_start_date = date(2025, 1, 1)
        proj.actual_end_date = date(2025, 8, 15)  # 46 days delay

        mock_q = MagicMock()
        mock_f = MagicMock()
        mock_f.first.side_effect = [proj, None]
        mock_q.filter.return_value = mock_f
        mock_db.query.return_value = mock_q

        mock_func.count.return_value.scalar.return_value = 0

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
        proj = MagicMock()
        proj.id = 1
        proj.project_code = "PRJ005"
        proj.project_name = "已有回顾项目"

        existing_review = MagicMock()
        existing_review.id = 500
        existing_review.review_no = "REV-PRJ005-001"

        mock_q = MagicMock()
        mock_f = MagicMock()
        mock_f.first.side_effect = [proj, existing_review]
        mock_q.filter.return_value = mock_f
        mock_db.query.return_value = mock_q

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert result["already_exists"] is True
        assert result["review_id"] == 500
        mock_db.add.assert_not_called()

    @patch("app.services.project.closure_readiness_service.Project")
    def test_retrospective_project_not_found(
        self, mock_project_cls, service, mock_db
    ):
        """测试项目不存在时的边界情况"""
        mock_q = MagicMock()
        mock_f = MagicMock()
        mock_f.first.return_value = None
        mock_q.filter.return_value = mock_f
        mock_db.query.return_value = mock_q

        result = service.auto_collect(project_id=999, triggered_by=1)

        assert "error" in result
        assert result["error"] == "项目不存在"
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
