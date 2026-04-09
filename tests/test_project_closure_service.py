# -*- coding: utf-8 -*-
"""项目结项准备度服务测试 - ClosureReadinessService 专项测试

本测试文件聚焦于 ClosureReadinessService 类的核心功能测试
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


def create_service(mock_db):
    """创建服务实例"""
    from app.services.project.closure_readiness_service import ClosureReadinessService
    return ClosureReadinessService(mock_db)


def test_check_closure_readiness_complete(mock_db):
    """测试结项就绪检查（完成状态）"""
    # Create project with real values inside patches
    with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInst, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        # Create project with real attributes - inside patch context
        project = MagicMock()
        # Set real values for properties that will be used in comparisons
        object.__setattr__(project, 'id', 1)
        object.__setattr__(project, 'project_code', "PRJ001")
        object.__setattr__(project, 'project_name', "测试项目")
        object.__setattr__(project, 'budget_amount', Decimal("100000"))
        object.__setattr__(project, 'actual_cost', Decimal("95000"))
        object.__setattr__(project, 'invoice_issued', True)
        object.__setattr__(project, 'final_payment_completed', True)
        
        # Also set via property to be safe
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("95000")
        project.invoice_issued = True
        project.final_payment_completed = True
        
        # Setup query results - sequence matters
        query_results = [
            (project, "first"),  # 1. Project query
            ([MagicMock(stage_code=f"S{i}", status="COMPLETED") for i in range(1, 9)], "all"),  # 2. Stage instances
            ([], "all"),  # 3. Node instances (deliverables)
            ([MagicMock(doc_type="设计文档", doc_category="设计"),
              MagicMock(doc_type="测试报告", doc_category="测试"),
              MagicMock(doc_type="验收报告", doc_category="验收"),
              MagicMock(doc_type="用户手册", doc_category="培训")], "all"),  # 4. Documents
            (MagicMock(status="APPROVED"), "first"),  # 5. Approval
            ([MagicMock()], "all"),  # 6. Costs
            ([MagicMock(stage_code="S1", status="COMPLETED")], "all"),  # 7. Fallback to ProjectStage
            ([MagicMock()], "all"),  # 8. Cost count via func
        ]
        
        query_idx = [0]
        
        def query_handler(*args, **kwargs):
            m = MagicMock()
            i = query_idx[0]
            query_idx[0] += 1
            
            if i < len(query_results):
                data, method = query_results[i]
                if method == "first":
                    m.filter.return_value.first.return_value = data
                else:
                    m.filter.return_value.all.return_value = data
            return m
        
        mock_db.query.side_effect = query_handler
        
        # Mock func.count chain
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 10
        MockFunc.count.return_value = mock_count
        
        service = create_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert result["ready"] is True
    assert result["score"] == 100
    assert result["project_id"] == 1


def test_check_closure_readiness_incomplete(mock_db):
    """测试结项未就绪"""
    with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInst, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        # Project with issues - over budget, not invoiced, not paid
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("120000")  # Over!
        project.invoice_issued = False
        project.final_payment_completed = False
        
        query_results = [
            (project, "first"),
            ([MagicMock(stage_code="S1", status="COMPLETED")], "all"),  # Only 1 stage
            ([], "all"),
            ([], "all"),  # No docs
            (None, "first"),  # No approval
            ([], "all"),  # No costs
            ([], "all"),  # Fallback stages
            ([], "all"),  # Cost count
        ]
        
        query_idx = [0]
        
        def query_handler(*args, **kwargs):
            m = MagicMock()
            i = query_idx[0]
            query_idx[0] += 1
            
            if i < len(query_results):
                data, method = query_results[i]
                if method == "first":
                    m.filter.return_value.first.return_value = data
                else:
                    m.filter.return_value.all.return_value = data
            return m
        
        mock_db.query.side_effect = query_handler
        
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 0
        MockFunc.count.return_value = mock_count
        
        service = create_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert result["ready"] is False
    assert result["score"] < 100
    assert len(result["missing_items"]) > 0


def test_get_readiness_score(mock_db):
    """测试准备度评分"""
    with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInst, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("95000")
        project.invoice_issued = True
        project.final_payment_completed = True
        
        query_results = [
            (project, "first"),
            ([MagicMock(stage_code=f"S{i}", status="COMPLETED") for i in range(1, 9)], "all"),
            ([], "all"),
            ([MagicMock(doc_type="设计文档"), MagicMock(doc_type="测试报告"),
              MagicMock(doc_type="验收报告"), MagicMock(doc_type="用户手册")], "all"),
            (MagicMock(status="APPROVED"), "first"),
            ([MagicMock()], "all"),
            ([], "all"),
            ([], "all"),
        ]
        
        query_idx = [0]
        
        def query_handler(*args, **kwargs):
            m = MagicMock()
            i = query_idx[0]
            query_idx[0] += 1
            
            if i < len(query_results):
                data, method = query_results[i]
                if method == "first":
                    m.filter.return_value.first.return_value = data
                else:
                    m.filter.return_value.all.return_value = data
            return m
        
        mock_db.query.side_effect = query_handler
        
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 5
        MockFunc.count.return_value = mock_count
        
        service = create_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert "score" in result
    assert isinstance(result["score"], int)
    assert 0 <= result["score"] <= 100
    assert result["score"] == 100


def test_readiness_with_partial_deliverables(mock_db):
    """测试部分交付物边界情况"""
    with patch("app.services.project.closure_readiness_service.Project") as MockProject, \
         patch("app.services.project.closure_readiness_service.ProjectStageInstance") as MockStageInst, \
         patch("app.services.project.closure_readiness_service.ProjectStage") as MockStage, \
         patch("app.services.project.closure_readiness_service.ProjectNodeInstance") as MockNodeInst, \
         patch("app.services.project.closure_readiness_service.ProjectDocument") as MockDoc, \
         patch("app.services.project.closure_readiness_service.ProjectCost") as MockCost, \
         patch("app.services.project.closure_readiness_service.ApprovalInstance") as MockApproval, \
         patch("app.services.project.closure_readiness_service.func") as MockFunc:
        
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("95000")
        project.invoice_issued = True
        project.final_payment_completed = True
        
        # Partial documents - only design doc
        query_results = [
            (project, "first"),
            ([MagicMock(stage_code=f"S{i}", status="COMPLETED") for i in range(1, 9)], "all"),
            ([], "all"),
            ([MagicMock(doc_type="设计文档", doc_category="设计")], "all"),  # Only 1 doc
            (MagicMock(status="APPROVED"), "first"),
            ([MagicMock()], "all"),
            ([], "all"),
            ([], "all"),
        ]
        
        query_idx = [0]
        
        def query_handler(*args, **kwargs):
            m = MagicMock()
            i = query_idx[0]
            query_idx[0] += 1
            
            if i < len(query_results):
                data, method = query_results[i]
                if method == "first":
                    m.filter.return_value.first.return_value = data
                else:
                    m.filter.return_value.all.return_value = data
            return m
        
        mock_db.query.side_effect = query_handler
        
        mock_count = MagicMock()
        mock_count.filter.return_value.scalar.return_value = 5
        MockFunc.count.return_value = mock_count
        
        service = create_service(mock_db)
        result = service.check_readiness(project_id=1)

    assert result["ready"] is False
    assert result["score"] < 100
    assert result["score"] > 0
    
    # Check deliverable check
    deliverable_check = next(
        (c for c in result["checks"] if c["key"] == "deliverable_upload"), None
    )
    assert deliverable_check is not None
    assert deliverable_check["passed"] is False


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
                                    
                                    service = create_service(mock_db)
                                    result = service.check_readiness(project_id=999)

    assert result["ready"] is False
    assert result["score"] == 0
    assert "项目不存在" in result["missing_items"]

# ==============================================================================
# ClosureAutoReviewService (LessonsCollectionService) 测试
# ==============================================================================

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

    def _create_mock_project(self, **kwargs):
        """创建模拟项目对象"""
        project = MagicMock()
        project.id = kwargs.get("id", 1)
        project.project_code = kwargs.get("project_code", "PRJ001")
        project.project_name = kwargs.get("project_name", "测试项目")
        project.project_type = kwargs.get("project_type", "EOL")
        project.industry = kwargs.get("industry", "汽车电子")
        project.budget_amount = kwargs.get("budget_amount", Decimal("100000"))
        project.actual_cost = kwargs.get("actual_cost", Decimal("95000"))
        project.planned_start_date = kwargs.get("planned_start_date")
        project.planned_end_date = kwargs.get("planned_end_date")
        project.actual_start_date = kwargs.get("actual_start_date")
        project.actual_end_date = kwargs.get("actual_end_date")
        return project

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_auto_review_trigger_conditions(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, service, mock_db
    ):
        """测试自动回顾触发条件 - 项目结项时自动触发"""
        from datetime import date
        mock_project = self._create_mock_project(
            id=1,
            project_code="PRJ001",
            project_name="测试项目",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("95000"),
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 6, 30),
            actual_start_date=date(2025, 1, 1),
            actual_end_date=date(2025, 7, 15),
        )

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.side_effect = [mock_project, None]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

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
        from datetime import date
        mock_project = self._create_mock_project(
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

        mock_query = MagicMock()
        mock_filter = MagicMock()
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

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.ProjectLesson")
    @patch("app.services.project.closure_readiness_service.ProjectBestPractice")
    @patch("app.services.project.closure_readiness_service.Project")
    @patch("app.services.project.closure_readiness_service.func")
    def test_retrospective_with_no_data(
        self, mock_func, mock_project_cls, mock_practice_cls, mock_lesson_cls, mock_review_cls, service, mock_db
    ):
        """测试无数据边界 - 项目数据为空或缺失时的处理"""
        mock_project = self._create_mock_project(
            id=1,
            project_code="PRJ003",
            project_name="空数据项目",
            budget_amount=None,
            actual_cost=None,
            planned_start_date=None,
            planned_end_date=None,
            actual_start_date=None,
            actual_end_date=None,
        )

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.side_effect = [mock_project, None]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

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
        from datetime import date
        mock_project = self._create_mock_project(
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

    @patch("app.services.project.closure_readiness_service.ProjectReview")
    @patch("app.services.project.closure_readiness_service.Project")
    def test_retrospective_already_exists(
        self, mock_project_cls, mock_review_cls, service, mock_db
    ):
        """测试回顾已存在 - 不重复创建"""
        mock_project = self._create_mock_project(
            id=1,
            project_code="PRJ005",
            project_name="已有回顾项目",
        )

        mock_existing_review = MagicMock()
        mock_existing_review.id = 500
        mock_existing_review.review_no = "REV-PRJ005-001"

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.side_effect = [mock_project, mock_existing_review]
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        result = service.auto_collect(project_id=1, triggered_by=1)

        assert result["already_exists"] is True
        assert result["review_id"] == 500
        mock_db.add.assert_not_called()

    @patch("app.services.project.closure_readiness_service.Project")
    def test_retrospective_project_not_found(
        self, mock_project_cls, service, mock_db
    ):
        """测试项目不存在时的边界情况"""
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        result = service.auto_collect(project_id=999, triggered_by=1)

        assert "error" in result
        assert result["error"] == "项目不存在"
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()
